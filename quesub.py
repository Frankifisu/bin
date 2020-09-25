#!/usr/bin/env python3

# =========
#  MODULES
# =========
import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import glob #Unix pathname expansion: glob.glob('*.txt')
import shutil
import re #Regex
import argparse # commandline argument parsers
import math #C library float functions
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import typing #Support for type hints
import gau #Gaussian script
from feutils import *

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = 'Franco Egidi (franco.egidi@sns.it)'
VERSION = '2020.08.29'
PROGNAME = os.path.basename(sys.argv[0])

# ==========
#  DEFAULTS
# ==========
QSUB = 'qsub -r n -V'
DESCRIPTION="""
This script allows one to easily submit any command through the PBS system
"""
EPILOG="""
Examples:

    Gaussian calculations:
        quesub.py -v -q q14diamond -w $HOME/myworking gaussian.com
        quesub.py -v -chk -p 16 -m 8 -a NoSymm gaussian.com

    Script submissions:
        quesub.py -v -p 1 -m 16 -mpi myscript.sh
"""

# =================
#  BASIC FUNCTIONS
# =================
class Gaussian(Exception):
    pass

# =================
#  PARSING OPTIONS
# =================
def queueparser(parser):
    """Create parsers for qsub command"""
    # Optional arguments
    parser.add_argument('-q', '--queue', metavar='QUEUE',
        dest='queue', action='store', default='q07diamond', type=str,
        help='Select queue')
    parser.add_argument('-j', '--job', metavar='JOB',
        dest='job', action='store', default='job', type=str,
        help='Set job name')
    parser.add_argument('-m', '--mem', metavar='MEM',
        dest='mem', action='store', default=64, type=intorstr,
        help='Set RAM')
    parser.add_argument('-p', '--nproc', metavar='PROC',
        dest='ppn', default=28,
        help='Set number of processors')
    parser.add_argument('-mpi',
        dest='mpi', default=False, action='store_true',
        help='Request MPI parallelization')
    parser.add_argument('-v', '--verbose',
        dest='vrb', action='count', default=0,
        help='Set printing level')
    parser.add_argument('-h', '--help',
        dest='hlp', action='store_true', default=False,
        help='Print help message and exit')
    return parser
def parseopt(args=None):
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME, add_help=False)
    helparser = argparse.ArgumentParser(prog=PROGNAME,
        formatter_class=wide_help(argparse.RawDescriptionHelpFormatter, w=140, h=40),
        usage="quesub.py [OPTIONS] [SCRIPT or G16_INP]",
        description=DESCRIPTION, epilog=EPILOG,
        add_help=False, conflict_handler='resolve')
    # G16 parser
    gaussian = helparser.add_argument_group('g16 options')
    gaussian = gau.gauparser(gaussian)
    # qsub parser
    queue = helparser.add_argument_group('queue options')
    queue = queueparser(queue)
    parser = queueparser(parser)
    opts, other = parser.parse_known_args(args)
    if not other or opts.hlp:
        helparser.print_help()
        sys.exit()
    if opts.mem:
        # If memory is given as an integer, try to guess if it's MB or GB
        if isinstance(opts.mem, int):
            if opts.mem <= 128:
                opts.mem = f'{opts.mem}G'
            else:
                opts.mem = f'{opts.mem}M'
    # Check options
    return opts, other

# ================
#  WORK FUNCTIONS
# ================

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts, other = parseopt()
    qsub = f'{QSUB}'
    qsubl = f'-l select=1:ncpus={opts.ppn}:mem={opts.mem}'
    if opts.mpi:
        qsubl = qsubl + f':mpiprocs={opts.ppn} -l place=pack'
    qsubN = f'-N {opts.job}'
    #qsubo = f'-o {opts.job}.o -e {opts.job}.e'
    qsubq = f'-q {opts.queue}'
    qsub = ' '.join([ qsub, qsubl, qsubN, qsubq ])
    try:
        # Submission of generic script
        for n, therest in enumerate(other):
            filnam, filext = os.path.splitext(therest)
            if filext in {'.com', '.gjf'}:
                raise Gaussian
            elif os.path.isfile(therest) and os.access(therest, os.X_OK):
                other[n] = os.path.abspath(therest)
        qsub = qsub + ' --'
        qsub = ' '.join([qsub] + other)
    except Gaussian:
        # Submission of Gaussian
        progr = shutil.which('gau.py')
        if progr is None:
            errore('gau.py not found')
        try:
            pythontre = shutil.which('python3')
            if pythontre is None:
                raise Exception
        except:
            pythontre = '/home/fegidi/.conda/envs/wrk/bin/python3'
        progr = ' '.join([pythontre, progr])
        qsub = ' -- '.join([qsub, progr])
        if opts.mem:
            other = other + [f'-m {opts.mem}B']
        if opts.ppn:
            other = other + [f'-p {opts.ppn}']
        if opts.vrb > 0:
            other = other + ['-v']
        qsub = ' '.join([qsub] + other)
    try:
        if opts.vrb > 0: print(qsub)
        qsubrun = bashrun(qsub, env=os.environ, vrb=opts.vrb)
    except:
        errore(f'Submission failed')
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
