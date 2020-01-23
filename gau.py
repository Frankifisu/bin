#!/usr/bin/env python3

#
# Run Gaussian16 calculation given input file list
#

# =========
#  MODULES
# =========
import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import argparse # commandline argument parsers
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import typing #Explicit typing of arguments

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = 'Franco Egidi (franco.egidi@sns.it)'
VERSION = '2020.15.01'
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv('USER')
HOME = os.getenv('HOME')

# ==========
#  DEFAULTS
# ==========
BASH = '/bin/bash'
TEST_TMP = ('/tmp', '/var/tmp', HOME+'/tmp')
GAUPATH = {
    'a03' : '/opt/gaussian/g16a03',
    'b01' : '/opt/gaussian/g16b01',
    'c01' : '/opt/gaussian/g16c01',
}
NBO = '/opt/nbo7/bin'
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
def bashrun(comando: str, env=None) -> str:
    """
    Run bash subprocess with sensible defaults
    and return output
    """
    if env is None:
        process = subprocess.run(comando, shell=True, check=True, executable=BASH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        process = subprocess.run(comando, shell=True, check=True, executable=BASH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    output = process.stdout.decode()
    return output
def check_extension(to_check: str, allowed_ext):
    """
    Check file extension
    """
    filnam, filext = os.path.splitext(to_check)
    if filext not in allowed_ext:
        errore(f'Invalid file extension for {to_check}')
def loginshvar(var: str) -> str :
    """
    Get environment variable from the login shell
    """
    comando = " ".join(['env -i', BASH, ' -l -c "printenv', var, '"'])
    out = bashrun(comando)
    return out
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
    if opts.fq :
        opts.wrkdir = FQWRKDIR
        opts.gauroot = GAUPATH['a03']
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
    return opts

# ================
#  WORK FUNCTIONS
# ================
def gauscr() -> str:
    """
    Set Gaussian scratch directory
    """
    # try a few common paths as temporary directories
    tmpdir = HOME
    for testdir in TEST_TMP:
        if os.path.isdir(testdir):
            tmpdir = testdir
            break
    # create and set a user scratch subdirectory
    GAUSS_SCRDIR = os.path.join(tmpdir, USER, 'gauscr')
    if not os.path.isdir(GAUSS_SCRDIR):
        os.makedirs(GAUSS_SCRDIR, exist_ok=True)
    return GAUSS_SCRDIR
def setgaussian(gauroot: str, gauscr: str, vrb: int=0) -> str:
    """
    Set basic Gaussian environment and return Gaussian command
    """
    os.environ.clear()
    # Set basic envvars from current or login shell
    os.environ['USER'] = USER
    os.environ['HOME'] = HOME
    os.environ['PATH'] = loginshvar('PATH')
    if os.path.isdir(NBO):
        os.environ['PATH'] = NBO + ':' + os.environ['PATH']
        if vrb >=2:
            os.environ['NBODTL'] = 'verbose'
    # Set Gaussian variables
    os.environ['g16root'] = gauroot
    os.environ['GAUSS_SCRDIR'] = gauscr
    if vrb >= 1:
        print(f"Gaussian diretory set to {os.getenv('g16root')}")
        print(f"Gaussian scratch diretory set to {os.getenv('GAUSS_SCRDIR')}")
    gaucmd = BASECMD
    profile = gauroot + "/g16/bsd/g16.profile"
    gaucmd = " ".join(["source", profile, ";", gaucmd])
    return gaucmd
#def pembed(gauinp, keyword: str) -> bool:
#    """
#    Check if Route section has PEmbed keyword
#    """
#    to_search = re.compile(r'\bpembed', re.IGNORECASE)
#    haspembed = route_has(gauinp, to_search)
#    return haspembed

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    # DEFINE GAUSSIAN ENVIRONMENT AND SUBMISSION COMMAND
    gaucmd = setgaussian(opts.gauroot, opts.gauscr, opts.vrb)
    # ASSEMBLE GAUSSIAN COMMAND
    gaucmd = " ".join([gaucmd, f'-m="{opts.mem}"'])
    if opts.procs is not None:
        gaucmd = " ".join([gaucmd, f'-c="{opts.procs}"'])
    else:
        gaucmd = " ".join([gaucmd, f'-p="{opts.nproc}"'])
    if opts.wrkdir is not None:
        # Add {wrkdir} and {wrkdir/exe-dir} to executable paths
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
        # RUN COMMAND
        comando = " ".join([gaucmd, da, gauinp, ad, gauout])
        if opts.vrb >= 1:
            print(comando)
        gaurun = bashrun(comando, env=os.environ)
        if opts.vrb >= 1:
            print(gaurun)
        # LOG CALCULATION: TOBEDONE
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
