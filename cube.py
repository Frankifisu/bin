#!/usr/bin/env python3

import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import re #Regex
import argparse #Commandline argument parsers
import socket #Module for the fully qualified named of the headnode
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import typing #To add typing to functions

# ================
#   PROGRAM DATA
# ================
AUTHOR = "FRANCO EGIDI (franco.egidi@sns.it)"
VERSION = "2019.01.03"
# Program name is generated from commandline
PROGNAME = os.path.basename(sys.argv[0])

# ============
#   DEFAULTS
# ============
CUBEXT = '.cub'
CUBCMD = 'cubegen'

# =================
#  BASIC FUNCTIONS
# =================
def cuberr(message=None) :
    # ERROR FUNCTION
    if message != None:
        print('ERROR: ' + message)
    sys.exit(1)

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
        dest='npts', default=0, metavar='NPTS', type=str,
        help='Set number of points')
    parser.add_argument('-v', '--iprint',
        dest='iprint', action='count', default=0,
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
    chknam, chkext = os.path.splitext(opts.fchk)
    if ( chkext != '.fchk') :
        cuberr('File {} does not have a .fchk extension'.format(chknam))
#   CHECK FILE EXTENSIONS
    if opts.cub == None or opts.cub == '':
        opts.cub = chknam + CUBEXT
#   CHECK NUMBER OF POINTS
    opts.npts = str.lower(str(opts.npts))
    if opts.npts[:3] == 'coa':
        opts.npts = '-2'
    elif opts.npts[:3] == 'med':
        opts.npts = '-3'
    elif opts.npts[:3] == 'fin':
        opts.npts = '-4'
    elif opts.npts[:3] == 'ult':
        opts.npts = '-22'
    else :
        try:
            int(opts.npts)
        except ValueError:
            cuberr('Invalid number of points "{}"'.format(opts.npts))
#   CHECK PROCESSORS
    opts.nproc = str.lower(str(opts.nproc))
    if opts.nproc in ["all", "max"]:
        opts.nproc = ncpuavail()
    elif opts.nproc in ["half", "hlf"]:
        opts.nproc = max(ncpuavail()//2, 1)
    return opts

# =============
#   FUNCTIONS
# =============
def ncpuavail() -> int :
    # NUMBER OF AVAILABLE PROCESSORS
    try:
        result = subprocess.run('nproc', stdout=subprocess.PIPE)
        nprocs = result.stdout.decode('utf-8').split()[0]
    except:
        nprocs = 1
    return int(nprocs)
def gencubomand(opts):
     # ASSEMBLE CUBEGEN COMMAND
     # cubegen nprocs  kind  fchkfile  cubefile  npts  format cubefile2 iprint [bonus]
     cubomando = CUBCMD
     cubomando = opts.wrkdir + cubomando
     for word in opts.nproc, opts.kind, opts.fchk, opts.cub, opts.npts, opts.cbfmt, opts.cub2, opts.iprint, opts.bonus, opts.denfil:
         cubomando = cubomando + ' ' + str(word)
     return cubomando

# ================
#   MAIN PROGRAM
# ================
def main():
    # Option parsing
    opts = cubeparse()
    # Generate cubegen command
    cubomando = gencubomand(opts)
    # Execute command
    print(cubomando)
    subprocess.run(cubomando, shell=True, executable='/bin/bash')

# =============
#   MAIN CALL
# =============
if __name__ == '__main__':
    main()
