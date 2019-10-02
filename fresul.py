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
# Permitted file extensions
OUTEXT = frozenset(('.log', '.out'))
# Patterns to search within file
SRCXPR = {
    'Mode'   : None,
    'Freq'   : ' Frequencies -- ',
    'Sym'    : None,
    'IR'     : ' IR Inten    -- ',
    'Raman'  : ' Raman Activ -- ',
    'redmas' : ' Red. masses -- ',
    'Start'  : ' Initial command:'
    }
# Output strings for column headers
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
    parser.add_argument('-t', '--table',
        dest='tbf', action='store', default='simple',
        help='Set table format')
    parser.add_argument('-f', '--format',
        dest='fmt', action='store', default='.2f',
        help='Set float format')
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
    idres = -1
    results = []
    with open(input_file, 'r') as file_obj:
        # For Gaussian I have to go back two lines for symmetry and mode
        prevline = ['', '']
        modes = []
        for line in file_obj:
            # Store one set of results for every calculation
            if SRCXPR.get('Start') in line:
                idres = idres + 1
                results = padlist(results, idres, [])
            if idres == -1:
                continue
            # Get modes of interest and symmetry
            if SRCXPR.get('Freq') in line:
                modes = [ int(number) for number in prevline[1].split() ]
                syms = prevline[0].split()
                results[idres] = padlist(results[idres], 0, [])
                idxmod, results[idres][0] = listele(results[idres][0], OUTXPR.get('Mode'))
                idxsym, results[idres][0] = listele(results[idres][0], OUTXPR.get('Sym'))
                index = max(idxmod, idxsym)
                for idat, vib in enumerate(modes):
                    results[idres] = padlist(results[idres], vib, [])
                    results[idres][vib] = padlist(results[idres][vib], index, None)
                    results[idres][vib][idxmod] = modes[idat]
                    results[idres][vib][idxsym] = syms[idat]
            # Get info
            results[idres] = datasrc(line, modes, 'Freq',  results[idres])
            results[idres] = datasrc(line, modes, 'IR',    results[idres])
            results[idres] = datasrc(line, modes, 'Raman', results[idres])
            # Save line before overwriting in loop
            prevline[1] = prevline[0]
            prevline[0] = line
    return results

def datasrc(line: str, modes: list, toget: str, vibinfo: list) -> list:
    """
    Parse file with data of the same type expected to be
    listed in rows and extend vibinfo array
    """
    expr = SRCXPR.get(toget)
    if expr is None:
        return vibinfo
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
    for calc in results:
        print(tabulate(calc, headers='firstrow', floatfmt=opts.fmt, tablefmt=opts.tbf))
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
