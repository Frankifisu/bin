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
from feutils import bashrun, errore, HOSTNAME, int_or_str, wide_help
import ams, gau

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = 'Franco Egidi (franco.egidi@sns.it)'
VERSION = '2021.07'
PROGNAME = os.path.basename(sys.argv[0])

# ==========
#  DEFAULTS
# ==========
def standardqueue():
    """Return default queue"""
    if '.scm.com' in HOSTNAME:
        return 'sky'
    if 'trantor'  in HOSTNAME:
        return 'q07diamond'
DESCRIPTION=f"""
This script allows one to easily submit any command through the queing system
"""
EPILOG=f"""
Examples:

    Script submissions:
        {PROGNAME} -v -p 1 -m 16 myscript.sh

"""

# =================
#  BASIC FUNCTIONS
# =================
class AMS(Exception):
    pass
class Gaussian(Exception):
    pass

# =================
#  PARSING OPTIONS
# =================
def queueparser(parser):
    """Create parsers for submission command"""
    # Optional arguments
    parser.add_argument('-q', '--queue', metavar='QUEUE',
        dest='queue', action='store', default=standardqueue(), type=str,
        help='Select queue')
    parser.add_argument('-j', '--job', metavar='JOB',
        dest='job', action='store', default='job', type=str,
        help='Set job name')
    parser.add_argument('-m', '--mem', metavar='MEM',
        dest='mem', action='store', default=64, type=int_or_str,
        help='Set RAM')
    parser.add_argument('-p', '--nproc', metavar='PROC',
        dest='ppn', default=8, type=int,
        help='Set number of processors')
    #parser.add_argument('-mpi',
    #    dest='mpi', default=False, action='store_true',
    #    help='Request MPI parallelization')
    parser.add_argument('-v', '--verbose',
        dest='vrb', action='count', default=0,
        help='Set printing level')
    parser.add_argument('-h', '--help',
        dest='hlp', action='store_true', default=False,
        help='Print help message and exit')
    parser.add_argument('--dry',
        dest='dry', action='store_true', default=False,
        help=argparse.SUPPRESS)
    return parser
def parseopt(args=None):
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME, add_help=False)
    helparser = argparse.ArgumentParser(prog=PROGNAME,
        formatter_class=wide_help(argparse.RawDescriptionHelpFormatter, w=140, h=40),
        usage=f"{PROGNAME} [OPTIONS] [SCRIPT or AMS_INP or G16_INP]",
        description=DESCRIPTION, epilog=EPILOG,
        add_help=False, conflict_handler='resolve')
    if '.scm.com' not in HOSTNAME:
        import gau #Gaussian script
        gaussian = helparser.add_argument_group('g16 options')
        gaussian = gau.gauparser(gaussian)
    import ams #AMS script
    amsargs = helparser.add_argument_group('AMS options')
    amsargs = ams.amsparser(amsargs)
    # sub parser
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
    # Parse options
    opts, other = parseopt()
    if shutil.which('sbatch'):
        sub = f'sbatch -v -N 1 --tasks-per-node={opts.ppn} -p {opts.queue} -o {opts.job}.out -J {opts.job}'
    elif shutil.which('qsub'):
        sub = 'qsub -r n -V'
        subl = f'-l select=1:ncpus={opts.ppn}:mem={opts.mem}'
        if opts.mpi:
            subl = subl + f':mpiprocs={opts.ppn} -l place=pack'
        subN = f'-N {opts.job}'
        #subo = f'-o {opts.job}.o -e {opts.job}.e'
        subq = f'-q {opts.queue}'
        sub = ' '.join([ sub, subl, subN, subq ])
    try:
        # Submission of generic script
        for n, therest in enumerate(other):
            filnam, filext = os.path.splitext(therest)
            #if filext in {'.in', '.inp', '.ams', '.fcf', '.oldfcf', '.nmr', '.run'}:
            if filext in ams.INPEXT:
                raise AMS
            if filext in gau.INPEXT:
                raise Gaussian
            elif os.path.isfile(therest) and os.access(therest, os.X_OK):
                other[n] = os.path.abspath(therest)
        sub = sub + ' --'
        sub = ' '.join([sub] + other)
    except AMS:
        # Submission of AMS, relies on ams.py script
        progr = shutil.which('ams.py')
        if progr is None: errore('ams.py not found')
        sub = ' -- '.join([sub, progr])
        if opts.ppn: other = other + [f'-p {opts.ppn}']
        if opts.vrb > 0: other = other + ['-v']
        sub = ' '.join([sub] + other)
    except Gaussian:
        # Submission of Gaussian, relies on gau.py script
        progr = shutil.which('gau.py')
        if progr is None:
            errore('gau.py not found')
        try:
            pythontre = shutil.which('python3')
            if pythontre is None:
                raise Exception
        except Exception:
            pythontre = '/home/fegidi/.conda/envs/wrk/bin/python3'
        progr = ' '.join([pythontre, progr])
        sub = ' -- '.join([sub, progr])
        if opts.mem:     other = other + [f'-m {opts.mem}B']
        if opts.ppn:     other = other + [f'-p {opts.ppn}']
        if opts.vrb > 0: other = other + ['-v']
        sub = ' '.join([sub] + other)
    try:
        if opts.vrb > 0: print(sub)
        if not opts.dry:
            subrun = bashrun(sub, env=os.environ, vrb=opts.vrb)
    except Exception:
        errore(f'Submission failed')
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
