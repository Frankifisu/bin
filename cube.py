#!/usr/bin/env python3

import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import re #Regex
import argparse #Commandline argument parsers
import socket #Module for the fully qualified named of the headnode
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import typing #To add typing to functions
from feutils import * #My generic functions

# ================
#   PROGRAM DATA
# ================
AUTHOR = "FRANCO EGIDI (franco.egidi@gmail.it)"
VERSION = "2020.09.20"
PROGNAME = os.path.basename(sys.argv[0])

# ============
#   DEFAULTS
# ============
CUBEXT = '.cub'
CUBCMD = 'cubegen'

# =================
#  BASIC FUNCTIONS
# =================

# ===================
#   PARSING OPTIONS
# ===================
def cubeparse():
    # CREATE PARSER
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Helps with building cubegen command')
    # MANDATORY ARGUMENTS
    parser.add_argument('fchk', help='Formatted checkpoint file name')
    parser.add_argument('kind', help='Type of cube to be generated')
    # OPTIONAL ARGUMENTS
    parser.add_argument('-n', '--nproc',
        dest='nproc', default=0,
        help='Set number of processors')
    parser.add_argument('-o', '--cubefile',
        dest='cub',
        help='Set cube file name')
    parser.add_argument('-p', '--npts',
        dest='npts', default=0, metavar='NPTS', type=int_or_str,
        help='Set number of points')
    parser.add_argument('-v', '--verbose',
        dest='vrb', action='count', default=0,
        help='Set printing level')
    parser.add_argument('-f', '--format',
        dest='cbfmt', default='h',
        help='Set format')
    parser.add_argument('-w', '--wrkdir',
        dest='wrkdir', metavar='WORKDIR', default='',
        help='Work directory path')
    parser.add_argument('-q2', '--cubefile2',
        dest='cub2', default='junk.cub',
        help=argparse.SUPPRESS)
    parser.add_argument('-a', '--add',
        dest='bonus', default='0',
        help='Additional custom integer flag')
    parser.add_argument('-d', '--denfil',
        dest='denfil',
        help='Set density file name')
#   OPTION PARSING
    opts = parser.parse_args()
#   CONSISTENCY CHECKS
    check_extension(opts.fchk, ['.fchk'])
#   CHECK FILE EXTENSIONS
    if opts.cub is None or opts.cub == '':
        opts.cub = chknam + CUBEXT
#   CHECK NUMBER OF POINTS
    if not isinstance(opts.npts, int):
        testr = str(opts.npts)
        if testr[:3] == 'coa':
            opts.npts = '-2'
        elif testr[:3] == 'med':
            opts.npts = '-3'
        elif testr[:3] == 'fin':
            opts.npts = '-4'
        elif testr[:3] == 'ult':
            opts.npts = '-22'
        else :
            errore('Invalid number of points "{}"'.format(opts.npts))
#   CHECK PROCESSORS
    opts.nproc = str.lower(str(opts.nproc))
    if opts.nproc in ["all", "max"]:
        opts.nproc = CPUTOT
    elif opts.nproc in ["half", "hlf"]:
        opts.nproc = max(CPUTOT//2, 1)
    return opts

# =============
#   FUNCTIONS
# =============
def gencubomando(opts):
     # ASSEMBLE CUBEGEN COMMAND
     # cubegen nprocs  kind  fchkfile  cubefile  npts  format cubefile2 iprint [bonus]
     cubomando = CUBCMD
     cubomando = opts.wrkdir + cubomando
     for word in opts.nproc, opts.kind, opts.fchk, opts.cub, opts.npts, opts.cbfmt, opts.cub2, opts.vrb, opts.bonus, opts.denfil:
         if word is not None:
             cubomando = cubomando + ' ' + str(word)
     return cubomando

# ================
#   MAIN PROGRAM
# ================
def main():
    # Option parsing
    opts = cubeparse()
    # Generate cubegen command
    cubomando = gencubomando(opts)
    # Execute command
    bashrun(comando, opts.vrb)

# =============
#   MAIN CALL
# =============
if __name__ == '__main__':
    main()
