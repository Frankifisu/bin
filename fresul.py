#!/usr/bin/env python3

# =========
#  MODULES
# =========
import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import glob #Unix pathname expansion: glob.glob('*.txt')
import re #Regex
import argparse # commandline argument parsers
import math #C library float functions
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import numpy #Scientific computing
import typing
from tabulate import tabulate

# ==============
#  PROGRAM DATA
# ==============
PROGNAME = os.path.basename(sys.argv[0])
USERNAME = os.getenv('USER')
HOMEDIR = os.getenv('HOME')

# ==========
#  DEFAULTS
# ==========
OUTEXT = frozenset(('.log', '.out'))
SRCXPR = {
    'Mode'   : None,
    'Freq'   : ' Frequencies -- ',
    'Sym'    : None,
    'IR'     : ' IR Inten    -- ',
    'Raman'  : ' Raman Activ -- ',
    'redmas' : ' Red. masses -- '
    }
OUTXPR = {
    'Mode'   : 'Mode',
    'Freq'   : 'Freq',
    'Sym'    : 'Sym',
    'IR'     : 'IR',
    'Raman'  : 'Raman',
    'redmas' : 'Red Mas'
    }

# =================
#  BASIC FUNCTIONS
# =================
def errore(message=None):
    """
    Error function
    """
    if message != None:
        print('ERROR: ' + message)
    sys.exit(1)

# =================
#  PARSING OPTIONS
# =================
def parseopt():
    """
    Parse options
    """
    # CREATE PARSER
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    # MANDATORY ARGUMENTS
    parser.add_argument('outfil', help='Gaussian output file')
    # OPTIONAL ARGUMENTS
    parser.add_argument('-v', '--iprint',
        dest='iprt', action='count', default=0,
        help='Set printing level')
    # OPTION PARSING
    opts = parser.parse_args()
    # CONSISTENCY CHECKS
    filnam, filext = os.path.splitext(opts.outfil)
    if filext not in OUTEXT:
        errore('Invalid file extension')
    return opts

# ================
#  WORK FUNCTIONS
# ================
def filparse(input_file) -> list:
    """
    Parse file and return result list
    """
    # Array to collect all vibrational info
    results = [[[]]]
    with open(input_file, 'r') as file_obj:
        # For Gaussian I have to go back two lines for symmetry and mode
        prevline = ['', '']
        modes = []
        for line in file_obj:
            # Get modes of interest and symmetry
            if SRCXPR.get('Freq') in line:
                modes = [ int(number) for number in prevline[1].split() ]
                syms = prevline[0].split()
                idxmod, results[0][0] = listele(results[0][0], OUTXPR.get('Mode'))
                idxsym, results[0][0] = listele(results[0][0], OUTXPR.get('Sym'))
                index = max(idxmod, idxsym)
                for idat, vib in enumerate(modes):
                    results[0] = padlist(results[0], vib, [])
                    results[0][vib] = padlist(results[0][vib], index, None)
                    results[0][vib][idxmod] = modes[idat]
                    results[0][vib][idxsym] = syms[idat]
            # Get info
            results[0] = datasrc(line, modes, 'Freq', results[0])
            results[0] = datasrc(line, modes, 'IR', results[0])
            results[0] = datasrc(line, modes, 'Raman', results[0])
            # Save line before overwriting in loop
            prevline[1] = prevline[0]
            prevline[0] = line
    print(tabulate(results[0], headers='firstrow'))
    return results

def datasrc(line: str, modes: list, toget: str, vibinfo: list) -> list:
    """
    Parse file with data of the same type expected to be
    listed in rows and extend vibinfo array
    """
    expr = SRCXPR.get(toget)
    if expr in line:
        datard = line.replace(expr, "").split()
        if len(modes) != len (datard):
            errore('Incompatibility between number of modes and available data')
        # Take care of header list
        index, vibinfo[0] = listele(vibinfo[0], OUTXPR.get(toget))
        for idat, vib in enumerate(modes):
            # Store results but first pad lists so we don't get errors
            vibinfo = padlist(vibinfo, vib, [])
            vibinfo[vib] = padlist(vibinfo[vib], index, None)
            vibinfo[vib][index] = datard[idat]
    return vibinfo

def padlist(inlist: list, index, padding) -> list:
    """
    Pad list to length
    """
    if len(inlist) < index + 1:
        inlist = inlist + (index + 1 - len(inlist)) * [padding]
    return inlist

def listele(inlist: list, header: str) -> typing.Tuple[int, list]:
    """
    Checks if inlist contains element otherwise add it.
    A (possibly) new list and the element index are returned
    """
    outlist = inlist
    try:
        headpos = outlist.index(header)
    except:
        headpos = len(outlist)
        outlist.append(header)
    return headpos, outlist

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    results = filparse(opts.outfil)
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
