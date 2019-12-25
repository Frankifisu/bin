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

# ==============
#  PROGRAM DATA
# ==============
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv('USER')
HOME = os.getenv('HOME')
LD_LIBRARY_PATH = os.getenv('LD_LIBRARY_PATH')
SHELL = os.getenv('SHELL')
TEST_TMP = ('/tmp', '/var/tmp', HOME)

# ==========
#  DEFAULTS
# ==========
GAUPATH = {
    'a03' : '/opt/gaussian/g16a03',
    'b01' : '/opt/gaussian/g16b01',
    'c01' : '/opt/gaussian/g16c01',
}
FQWRKDIR = '/opt/gaussian/working/fqqm_a03'
BASECMD = 'g16'
INPEXT = frozenset(('.com', '.gjf'))

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
def check_extension(to_check: str, allowed_ext):
    """
    Check file extension
    """
    filnam, filext = os.path.splitext(to_check)
    if filext not in allowed_ext:
        errore(f'Invalid file extension for {to_check}')
def envsource(tosource: str) -> dict :
    """
    Source bash file to update environment
    """
    comando = " ".join(['source', tosource, '&&', 'env']) # command to source file and get environment
    process = subprocess.run(comando, shell=True, executable='/bin/bash', stdout=subprocess.PIPE)
    dictenv = dict() # create a dictionary to hold the generated environment
    for line in process.stdout.decode().split('\n'):
        (key, _, value) = line.partition("=")
        dictenv[key] = value
    return dictenv
def ncpuavail() -> int :
    """
    Find number of processors in the machine
    """
    try:
        result = subprocess.run('nproc', stdout=subprocess.PIPE)
        nprocs = result.stdout.decode('utf-8').split()[0]
    except:
        nprocs = 1
    return int(nprocs)

# =================
#  PARSING OPTIONS
# =================
def parseopt():
    """
    Parse options
    """
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    parser.add_argument(dest='gjf', nargs='+', metavar="INPUT",
        help='Input file(s) with .com or .gjf extensions')
    parser.add_argument('-o', '--output', metavar='OUTPUT',
        dest='out', action='store',
        help='Set output file name')
    parser.add_argument('-g', '--gauroot', metavar='GAUROOT',
        dest='gauroot', action='store', default=GAUPATH['c01'],
        help='Set output file name')
    parser.add_argument('-w', '--working', metavar='WRKDIR',
        dest='wrkdir', action='store', default=None,
        help='Set working directory path')
    parser.add_argument('-a', '--add', metavar='KEWORDS',
        dest='keywords', action='append',
        help='Add keywords to input file(s)')
    parser.add_argument('-m', '--mem', metavar='GAUSS_MDEF',
        dest='mem', action='store', default='1GB',
        help='Set memory in Words or Bytes')
    parser.add_argument('-p', '--nproc', metavar='GAUSS_PDEF',
        dest='nproc', default=1,
        help='Set number of processors')
    parser.add_argument('-c', '--cpulist', metavar='GAUSS_CDEF',
        dest='procs', default=None,
        help='Set list of processors, overrides --nproc')
    parser.add_argument('-t', '--tmp', metavar='GAUSS_SCRDIR',
        dest='gauscr', action='store', default=gauscr(),
        help='Set scratch directory')
    parser.add_argument('-fq',
        dest='fq', action='store_true', default=False,
        help='Perform a FQFmu calculation')
    parser.add_argument('-v', '--verbose',
        dest='vrb', action='count', default=0,
        help='Set printing level')
    opts = parser.parse_args()
    # Check options
    for fil in opts.gjf:
        check_extension(fil, INPEXT)
    if not os.path.isdir(opts.gauscr):
         errore(f'Invalid Gaussian scratch directory {opts.gauscr}')
    if not os.path.isdir(opts.gauroot):
         errore(f'Invalid Gaussian directory {opts.gauroot}')
    if opts.nproc in ["all", "max"]:
        opts.nproc = ncpuavail()
    elif opts.nproc in ["half", "hlf"]:
        opts.nproc = max(ncpuavail()//2, 1)
    if opts.wrkdir is not None:
        if not os.path.isdir(opts.wrkdir):
             errore(f'Invalid Gaussian working directory {opts.wrkdir}')
    if opts.fq :
        opts.wrkdir = FQWRKDIR
        opts.gauroot = GAUPATH['a03']
    return opts

# ================
#  WORK FUNCTIONS
# ================
def gauscr() -> str:
    """
    Set Gaussian scratch directory
    """
    # try a few commomn path for temporary directories
    for testdir in TEST_TMP:
        if os.path.isdir(testdir):
            tmpdir = testdir
            break
    # create and set a user scratch subdirectory
    GAUSS_SCRDIR = os.path.join(tmpdir, USER, 'GauScr')
    if not os.path.isdir(GAUSS_SCRDIR):
        os.makedirs(GAUSS_SCRDIR, exist_ok=True)
    return GAUSS_SCRDIR
def setgaussian(gauroot, gauscr):
    """
    Set Gaussian environment
    """
    # Existence checks
    if not os.path.isdir(gauscr):
         errore(f'Invalid Gaussian scratch directory {opgs.gauscr}')
    if not os.path.isdir(gauroot):
         errore(f'Invalid Gaussian directory {opts.gauroot}')
    # Set gaussian root
    os.environ.clear()
    os.environ['g16root'] = gauroot
    os.environ['GAUSS_SCRDIR'] = gauscr
    for key, value in envsource(gauroot + '/g16/bsd/g16.profile').items() :
        os.environ[key] = value
#def filparse(input_file):
#    with open(input_file, 'r') as file_obj:
#        for line in file_obj :
#            pass

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    # DEFINE GAUSSIAN ENVIRONMENT
    setgaussian(opts.gauroot, opts.gauscr)
    if opts.vrb >= 1:
        print(f"Gaussian diretory set to {os.getenv('g16root')}")
        print(f"Gaussian scratch diretory set to {os.getenv('GAUSS_SCRDIR')}")
    # ASSEMBLE GAUSSIAN COMMAND
    gaucmd = BASECMD
    if opts.procs is not None:
        gaucmd = " ".join([gaucmd, f'-c="{opts.procs}"'])
    else:
        gaucmd = " ".join([gaucmd, f'-p="{opts.nproc}"'])
    gaucmd = " ".join([gaucmd, f'-m="{opts.mem}"'])
    if opts.wrkdir is not None:
        exedir = os.getenv("GAUSS_EXEDIR")
        exedir = ":".join([opts.wrkdir, exedir])
        srcexe = os.path.join(opts.wrkdir, 'exe-dir')
        if os.path.isdir(srcexe):
            exedir = ":".join([srcexe, exedir])
        gaucmd = " ".join([gaucmd, f'-exedir="{exedir}"'])
    da = '<'
    ad = '>'
    # LOOP OVER INPUT FILES ONE BY ONE
    for num, gauinp in enumerate(opts.gjf, start=1):
        if not os.path.isfile(gauinp):
            errore(f'File {gauinp} not found')
        # ADD KEYWORDS ON THE FLY: TOBEDONE
        # SET OUTPUT FILE
        if opts.out is None:
            filnam, filext = os.path.splitext(gauinp)
            gauout = filnam + '.log'
        else:
            gauout = opts.out
            if num > 1: # if there are multiple inputs but the output filename is set then append output
                ad = '>>'
        # ASSEMBLE COMMAND
        comando = " ".join([gaucmd, da, gauinp, ad, gauout])
        if opts.vrb >= 1:
            print(comando)
        gaurun = subprocess.run(comando, shell=True, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(time1-time0)
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
