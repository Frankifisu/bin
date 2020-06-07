#!/usr/bin/env python3

#
# Run Gaussian16 calculation given input files
#

# =========
#  MODULES
# =========
import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import re #Regex
import argparse # commandline argument parsers
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import typing #Explicit typing of arguments

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = 'Franco Egidi (franco.egidi@sns.it)'
VERSION = '2020.06.08'
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv('USER')
HOME = os.getenv('HOME')
PWD = os.getcwd()

# ==========
#  DEFAULTS
# ==========
BASH = '/bin/bash'
TEST_TMP = ('/tmp', '/var/tmp', HOME+'/tmp', HOME)
GAUPATH = {
    'a03' : '/opt/gaussian/g16a03',
    'b01' : '/opt/gaussian/g16b01',
    'c01' : '/opt/gaussian/g16c01',
    }
NBO = '/opt/nbo7/bin'
GAUFQ = {
        'working' : '/opt/gaussian/working/g16a03_fq',
        'gauroot' : GAUPATH['a03'],
        }
BASECMD = 'g16'
INPEXT = frozenset(('.com', '.gjf'))
GAUINP = {
        'link0'  : r'%',
        'link1'  : r'--link1--',
        'route'  : r'#(t|n|p)?\s',
        'allchk' : r'geom(=|=\(|\()allch(ec)?k',
        }

# =========
#  CLASSES
# =========
# Gaussian input file class
class gauinput:
    def __init__(self,
                 link0 = None,
                 route = None,
                 title = None,
                 mol   = None,
                 tail  = None):
        self.link0 = link0
        self.route = route
        self.title = title
        self.mol   = mol
        self.tail  = tail
        if self.link0 is None:
            self.link0 = []
        if self.route is None:
            self.route = []
        if self.title is None:
            self.title = []
        if self.mol is None:
            self.mol = []
        if self.tail is None:
            self.tail = []
    def gjf(self):
        gjf = []
        sep = ['\n']
        if self.link0:
            gjf = gjf + self.link0
        gjf = gjf + self.route + sep
        print(gjf)
        if self.title:
            gjf = gjf + self.title + sep
        if self.mol:
            gjf = gjf + self.mol + sep
        if self.tail:
            gjf = gjf + self.tail + sep
        return gjf
    def default(self):
        self.route = ['# HF/3-21G', 'Geom=(ModelA)']
        self.title = ['Test calculation']
        self.mol   = ['0 1', ' C O H H ']
        return self
    def __str__(self):
        string = "".join(self.gjf())
        return string

# =================
#  BASIC FUNCTIONS
# =================
def errore(message=None):
    """Error function"""
    if message != None:
        print(f'ERROR: {message}')
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
    output = process.stdout.decode().rstrip()
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
        dest='add', action='store', type=str, default=None,
        help='Add keyword string to input file(s)')
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
    parser.add_argument('-chk',
        dest='chk', action='store_true', default=False,
        help='Generate an unformatted checkpoint file')
    parser.add_argument('-fchk',
        dest='fchk', action='store_true', default=False,
        help='Generate a formatted checkpoint file')
    parser.add_argument('-fq',
        dest='fq', action='store_true', default=False,
        help='Perform a FQFmu calculation')
    parser.add_argument('-v', '--verbose',
        dest='vrb', action='count', default=0,
        help='Set printing level')
    parser.add_argument('--dry',
        dest='dry', action='store_true', default=False,
        help=argparse.SUPPRESS)
    opts = parser.parse_args()
    # Check options
    for fil in opts.gjf:
        check_extension(fil, INPEXT)
    if opts.fq :
        opts.wrkdir = GAUFQ['working']
        opts.gauroot = GAUFQ['gauroot']
    if not os.path.isdir(opts.gauscr):
        errore(f'Invalid Gaussian scratch directory {opts.gauscr}')
    if opts.gauroot in GAUPATH.keys():
        opts.gauroot = GAUPATH[opts.gauroot]
    if not os.path.isdir(opts.gauroot):
        errore(f'Invalid Gaussian directory {opts.gauroot}')
    if opts.nproc in ["all", "max"]:
        opts.nproc = ncpuavail()
    elif opts.nproc in ["half", "hlf"]:
        opts.nproc = max(ncpuavail()//2, 1)
    elif int(opts.nproc) > ncpuavail():
        errore('Too many processors requested')
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
    for testdir in TEST_TMP:
        if os.path.isdir(testdir):
            tmpdir = testdir
            break
    # create and set a user scratch subdirectory
    GAUSS_SCRDIR = os.path.join(tmpdir, USER, 'gaussian')
    if not os.path.isdir(GAUSS_SCRDIR):
        os.makedirs(GAUSS_SCRDIR, exist_ok=True)
    return GAUSS_SCRDIR
def cleanenv(env):
    """
    Get clean environment
    """
    env.clear()
    # Set basic envvars from current or login shell
    env['USER'] = USER
    env['HOME'] = HOME
    env['PATH'] = loginshvar('PATH')
    env['PWD']  = PWD
    return env
def setgaussian(basecmd:str, gauroot: str, gauscr: str, vrb: int=0) -> str:
    """
    Set basic Gaussian environment and return Gaussian command
    """
    #Check if NBO analysis is available
    if os.path.isdir(NBO):
        os.environ['PATH'] = NBO + ':' + os.environ['PATH']
        os.environ['NO_STOP_MESSAGE'] = '1'
        if vrb >=2:
            os.environ['NBODTL'] = 'verbose'
    # Set Gaussian variables
    os.environ['g16root'] = gauroot
    os.environ['GAUSS_SCRDIR'] = gauscr
    if vrb >= 1:
        print(f"Gaussian diretory set to {os.getenv('g16root')}")
        print(f"Gaussian scratch diretory set to {os.getenv('GAUSS_SCRDIR')}")
    gaucmd = basecmd
    profile = gauroot + "/g16/bsd/g16.profile"
    gaucmd = " ".join(["source", profile, ";", gaucmd])
    return gaucmd
def parsegau(gauinp: str, vrb: int=0) -> str:
    """
    Parse Gaussian Input file and generate a revised Input
    """
    listfil = []
    #Parse input file to generate Gaussian input file objects
    with open(gauinp, 'r') as filein:
        lines = filein.readlines()
        listfil = parsemul(lines, listfil)
    #Write output file
    tmpinp = '._' + gauinp
    with open(tmpinp, 'w') as fileout:
        for gjf in listfil:
            fileout.write(str(gjf))
    if vrb >= 1:
        print(f'Written file tmpinp')
    errore()
    return tmpinp
#
def parsemul(lines, listfil):
    """Parse single Gaussian job"""
    newfil = gauinput()
    Route = False
    for nline, line in enumerate(lines):
        if not line.strip():
            #Skip unnecessary empty lines at the beginning
            continue
        elif re.match(GAUINP['link0'], line.lstrip()):
            #Link0 line found
            newfil.link0.append(line.lstrip())
        elif re.match(GAUINP['route'], line.lstrip()):
            #Route section found
            nroute = nline
            Route = True
            break
    #Read Route section
    if not Route:
        errore('Route section not found')
    nstart = nroute + readsection(lines[nroute:], newfil.route)
    #Possibly read Title and Molecule
    fullroute = " ".join(newfil.route)
    if not re.search(GAUINP['allchk'], fullroute):
        nstart = nstart + readsection(lines[nstart:], newfil.title)
        nstart = nstart + readsection(lines[nstart:], newfil.mol)
    #Read Tail
    lempty = 0
    for nline, line in enumerate(lines[nstart:]):
        #DA RIVEDERE PER CONTROLLARE RIGHE VUOTE
        if re.match(GAUINP['link1'], line.lower()):
            listfil = parsemul(lines[nline + nstart + 1:], listfil)
            break
        newfil.tail.append(line.lstrip())
        if not line.strip():
            lempty = lempty + 1
            if lempty == 2:
                break
    listfil = [newfil] + listfil
    return listfil
def readsection(lines, toadd):
    """Read section terminated by empty line"""
    for nline, line in enumerate(lines):
        if not line.strip():
            break
        toadd.append(line)
    return nline + 1

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    # DEFINE GAUSSIAN ENVIRONMENT AND SUBMISSION COMMAND
    os.environ = cleanenv(os.environ)
    gaucmd = setgaussian(BASECMD, opts.gauroot, opts.gauscr, opts.vrb)
    # ASSEMBLE GAUSSIAN COMMAND
    gaucmd = " ".join([gaucmd, f'-m="{opts.mem}"'])
    if opts.procs is not None:
        gaucmd = " ".join([gaucmd, f'-c="{opts.procs}"'])
    else:
        gaucmd = " ".join([gaucmd, f'-p="{opts.nproc}"'])
    if opts.wrkdir is not None:
        # Add {wrkdir} and {wrkdir/exe-dir} to executable paths
        tmpcmd = setgaussian("echo $GAUSS_EXEDIR", opts.gauroot, opts.gauscr, opts.vrb)
        exedir = bashrun(tmpcmd, env=os.environ)
        exedir = ":".join([opts.wrkdir, exedir])
        srcexe = os.path.join(opts.wrkdir, 'exe-dir')
        if os.path.isdir(srcexe):
            exedir = ":".join([srcexe, exedir])
        gaucmd = " ".join([gaucmd, f'-exedir="{exedir}"'])
    da = '<'
    ad = '>'
    # LOOP OVER INPUT FILES ONE BY ONE
    for num, gauinp in enumerate(opts.gjf, start=1):
        # CREATE NEW TEMPORARY INPUT FILE
        _gauinp = parsegau(gauinp, opts.vrb)
        if opts.vrb >= 1:
            print(f'Using modified file {gauinp} as input')
        else:
            _gauinp = gauinp
        if not os.path.isfile(gauinp):
            errore(f'File {gauinp} not found')
        gauinp_nam, gauinp_ext = os.path.splitext(gauinp)
        # ADD KEYWORDS ON THE FLY
        if opts.add:
            gaucmd = " ".join([gaucmd, f'-r="{opts.add}"'])
        # SPECIFY CHECKPOINT FILES
        if opts.chk:
            gaucmd = " ".join([gaucmd, f'-y="{gauinp_nam}.chk"'])
        if opts.fchk:
            gaucmd = " ".join([gaucmd, f'-fchk="{gauinp_nam}.fchk"'])
        # SET OUTPUT FILE
        if opts.out is None:
            gauout = gauinp_nam + '.log'
        else:
            gauout = opts.out
            if num > 1:
                # if there are multiple inputs but the output filename is set then append output
                ad = '>>'
        # RUN COMMAND
        comando = " ".join([gaucmd, da, _gauinp, ad, gauout])
        if opts.vrb >= 1:
            print(comando)
        if not opts.dry:
            gaurun = bashrun(comando, env=os.environ)
            if opts.vrb >= 1:
                print(gaurun)
        if _gauinp != gauinp:
            os.remove(_gauinp)
            if opts.vrb >=1 :
                print(f'File {_gauinp} removed')
        # LOG CALCULATION: TOBEDONE
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
