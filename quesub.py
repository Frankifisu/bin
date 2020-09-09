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
import devgau
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

# =================
#  BASIC FUNCTIONS
# =================

# =================
#  PARSING OPTIONS
# =================
def parseopt(args=None):
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    queue = parser.add_argument_group('queue options')
    # Optional arguments
    queue.add_argument('-q', '--queue', metavar='QUEUE',
        dest='queue', action='store', default='q07diamond', type=str,
        help='Select queue')
    queue.add_argument('-j', '--job', metavar='JOB',
        dest='job', action='store', default='job', type=str,
        help='Set job name')
    #queue.add_argument('-P', '--project', metavar='PROJ',
    #    dest='project', default=None,
    #    help='Defines the project to run the calculation')
    queue.add_argument('-m', '--mem', metavar='MEM',
        dest='mem', action='store', default=64, type=intorstr,
        help='Set RAM')
    queue.add_argument('-p', '--nproc', metavar='PROC',
        dest='ppn', default=28,
        help='Set number of processors')
    queue.add_argument('-v', '--iprint',
        dest='vrb', action='count', default=0,
        help='Set printing level')
    opts, other = parser.parse_known_args(args)
    if opts.mem:
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
    qsubN = f'-N {opts.job}'
    #qsubo = f'-o {opts.job}.o -e {opts.job}.e'
    qsubq = f'-q {opts.queue}'
    qsub = ' '.join([ qsub, qsubl, qsubN, qsubq ])
    try:
        # Submission of generic script
        for therest in other:
            filnam, filext = os.path.splitext(therest)
            if filext in {'.com', '.gjf'}:
                raise Exception
        qsub = ' -- '.join([qsub] + other)
    except:
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
        if opts.vrb > 0:
            print(qsub)
        qsubrun = bashrun(qsub, env=os.environ, vrb=opts.vrb)
    except:
        errore(f'Submission failed')
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
