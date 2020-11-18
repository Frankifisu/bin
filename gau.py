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
import tempfile #To create teporary files
import socket #Just to get hostname
from feutils import * #My generic functions

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = 'Franco Egidi (franco.egidi@sns.it)'
VERSION = '2020.08.29'
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv('USER')
HOME = os.getenv('HOME')

# ==========
#  DEFAULTS
# ==========
TEST_TMP = ('/scratch', '/tmp', '/var/tmp', '/usr/tmp', HOME+'/tmp', HOME)
PREFIXES = ('/opt/gaussian/', '/home/fegidi/usr/local/gaussian/')
GAUDIR = {
    'a03' : 'g16a03',
    'b01' : 'g16b01',
    'c01' : 'g16c01',
    }
def exepath(ver: str):
    """Find Gaussian path"""
    if os.path.isdir(ver):
        return ver
    for prefix in PREFIXES:
        testdir = os.path.join(prefix, ver)
        if os.path.isdir(testdir):
            return testdir
    return None
NBO = '/opt/nbo7/bin'
GAUFQ = {
        'working' : exepath('working/g16a03_fq'),
        'gauroot' : exepath(GAUDIR['a03']),
        }
BASECMD = 'g16'
INPEXT = frozenset(('.com', '.gjf'))
REGAUINP = {
        'link0'  : r'%',
        'link1'  : r'--link1--',
        'route'  : r'#(t|n|p)?\s',
        'allchk' : r'geom(=|=\(|\()allch(ec)?k',
        }
MEM = '1GB'
TESTGAU = 'test'

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
        # We do it this way because lists are mutable
        if self.link0 is None: self.link0 = []
        if self.route is None: self.route = []
        if self.title is None: self.title = []
        if self.mol   is None: self.mol = []
        if self.tail  is None: self.tail = []
    def gjf(self):
        """Assemble sections into full input line list"""
        gjf = []
        sep = ['\n']
        if self.link0: gjf = gjf + self.link0
        gjf = gjf + self.route + sep
        if self.title: gjf = gjf + self.title + sep
        if self.mol:   gjf = gjf + self.mol + sep
        if self.tail:  gjf = gjf + self.tail + sep
        return gjf
    def default(self):
        """Default input file"""
        self.link0 = ['%NProcShared=1\n', '%Mem=1GB\n']
        self.route = ['# B3LYP/3-21G\n']
        self.title = ['Test calculation\n']
        self.mol   = ['0 1\n', \
            ' C \n', ' O,1,RCO \n', ' H,1,RCH,2,AOCH \n', ' H,1,RCH,2,AOCH,3,180.,0 \n', \
            'Variables:\n', ' RCO=1.22715383 \n', ' RCH=1.10489942 \n', ' AOCH=123.1045244\n' ]
        self.tail  = []
        return None
    def _srcsec(attr, pattern):
        """Search attribute for pattern and return
        the rest of the line after the match
        until the first comment"""
        for line in attr:
            match = re.search(pattern, line.lower().strip())
            if match:
                beg = match.end()
                comment = re.search(r'!', line.lower().strip())
                if comment is None:
                    return line[beg:].rstrip()
                else:
                    fin = comment.start()
                    if fin > beg:
                        return line[beg:fin].rstrip()
        return None
    def chk(self):
        """Return checkpoint file name"""
        checkpoint = gauinput._srcsec(self.link0, r'^%chk=')
        return checkpoint
    def mem(self):
        """Return memory"""
        memory = gauinput._srcsec(self.link0, r'^%mem=')
        return memory
    def nproc(self):
        """Return processors"""
        n = gauinput._srcsec(self.link0, r'^%nproc(shared)?=')
        if n is None:
            return 1
        else:
            return int(n)
    def setmem(self, mem: str):
        """Set memory"""
        self.link0[:] = [x for x in self.link0 if not re.match(r'%mem=', x.lower().lstrip())]
        self.link0.append(f'%Mem={mem}\n')
        return None
    def setnproc(self, nproc: int):
        """Set processors"""
        self.link0[:] = [x for x in self.link0 if not re.match(r'%nproc(shared)?=', x.lower().lstrip())]
        self.link0.append(f'%NProcShared={nproc}\n')
        return None
    def setcpu(self, cpulist: str):
        """Set CPU"""
        self.link0[:] = [x for x in self.link0 if not re.match(r'%cpu=', x.lower().lstrip())]
        self.link0.append(f'%CPU={cpulist}\n')
        return None
    def addchk(self, chknam: str):
        """Add chk file if not already present"""
        if not self.chk():
            self.link0.append(f'%Chk={chknam}\n')
            return True
        else:
            return False
    def __str__(self):
        string = "".join(self.gjf())
        return string


# =================
#  BASIC FUNCTIONS
# =================

# =================
#  PARSING OPTIONS
# =================
def gauparser(parser):
    """Create parsers for Gaussian command"""
    # Add options
    parser.add_argument(dest='gjf', nargs='+', metavar="INPUT",
        help='Input file(s) with .com or .gjf extensions')
    parser.add_argument('-o', '--output', metavar='OUTPUT',
        dest='out', action='store',
        help='Set output file name')
    parser.add_argument('-g', '--gauroot', metavar='GAUROOT',
        dest='gauroot', action='store', default=exepath(GAUDIR['c01']),
        help='Set path to Gaussian16')
    parser.add_argument('-w', '--working', metavar='WRKDIR',
        dest='wrkdir', action='store', default=None,
        help='Set working directory path')
    parser.add_argument('-a', '--add', metavar='KEWORDS',
        dest='add', action='append', type=str, default=[],
        help='Add keyword string to input file(s)')
    parser.add_argument('-m', '--mem', metavar='GAUSS_MDEF',
        dest='mem', action='store', default=None, type=intorstr,
        help='Set memory in Words or Bytes')
    parser.add_argument('-p', '--nproc', metavar='GAUSS_PDEF',
        dest='nproc', default=None,
        help='Set number of processors')
    parser.add_argument('-c', '--cpulist', metavar='GAUSS_CDEF',
        dest='procs', default=None,
        help=argparse.SUPPRESS)
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
        help='Perform a FQ(Fmu) calculation')
   # parser.add_argument('-mail', '--verbose',
   #     dest='mail', action='store_true', default=False,
   #     help='Send the user an email at the end of the script')
    parser.add_argument('-v', '--verbose',
        dest='vrb', action='count', default=0,
        help='Set printing level')
    parser.add_argument('--dry', '-dry',
        dest='dry', action='store_true', default=False,
        help=argparse.SUPPRESS)
    return parser
def parseopt(args=None):
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME,
        formatter_class=wide_help(argparse.HelpFormatter, w=140, h=40),
        description='Gaussian16 easy calculation script')
    parser = gauparser(parser)
    opts = parser.parse_args(args)
    # Check options
    for fil in opts.gjf:
        if fil != TESTGAU:
            check_extension(fil, INPEXT)
    if opts.fq:
        opts.wrkdir = GAUFQ['working']
        opts.gauroot = GAUFQ['gauroot']
    if not os.path.isdir(opts.gauscr):
        errore(f'Invalid Gaussian scratch directory {opts.gauscr}')
    if opts.gauroot in GAUDIR.keys():
        opts.gauroot = exepath(GAUDIR[opts.gauroot])
    if not os.path.isdir(opts.gauroot):
        errore(f'Invalid Gaussian directory {opts.gauroot}')
    if opts.nproc in ["all", "max"]:
        opts.nproc = CPUTOT
    elif opts.nproc in ["half", "hlf"]:
        opts.nproc = max(CPUTOT//2, 1)
    elif opts.nproc in ["free", "rest"]:
        opts.nproc = max(CPUFREE, 1)
    elif opts.nproc in ["halfree", "hlfree"]:
        opts.nproc = max(CPUFREE//2, 1)
    if opts.mem:
        if isinstance(opts.mem, int):
            if opts.mem <= 128:
                opts.mem = f'{opts.mem}GB'
            else:
                opts.mem = f'{opts.mem}MB'
    if opts.wrkdir is not None:
        if not os.path.isdir(opts.wrkdir):
             errore(f'Invalid Gaussian working directory {opts.wrkdir}')
    return opts

# ================
#  WORK FUNCTIONS
# ================
def gauscr() -> str:
    """Set Gaussian scratch directory"""
    # try a few common paths as temporary directories
    for testdir in TEST_TMP:
        if os.path.isdir(testdir):
            # create and set a user scratch subdirectory
            GAUSS_SCRDIR = os.path.join(testdir, USER, 'gaussian')
            try:
                os.makedirs(GAUSS_SCRDIR, exist_ok=True)
                return GAUSS_SCRDIR
            except:
                continue
    return None
def add_source_gauprofile(basecmd:str, gauroot: str) -> str:
    """Add sourcing of gaussian profile to command"""
    gaucmd = basecmd
    profile = gauroot + "/g16/bsd/g16.profile"
    gaucmd = " ".join(["source", profile, ";", gaucmd])
    return gaucmd
def setgauenv(env, gauroot: str, gauscr: str, vrb: int=0) -> str:
    """Set basic Gaussian environment"""
    #Check if NBO analysis is available
    if os.path.isdir(NBO):
        env['PATH'] = NBO + ':' + env['PATH']
        env['NO_STOP_MESSAGE'] = '1'
        if vrb >=1: env['NBODTL'] = 'verbose'
    # Set Gaussian variables
    env['g16root'] = gauroot
    env['GAUSS_SCRDIR'] = gauscr
    if vrb >= 1:
        print(f"Gaussian diretory set to {env['g16root']}")
        print(f"Gaussian scratch diretory set to {env['GAUSS_SCRDIR']}")
    return env
def modgaujob(joblist, gauinp_nam, opts):
    """Modify Gaussian jobs according to options in opts"""
    #If we want a fchk we need at least one chk
    if opts.fchk:
        try:
            for gjf in joblist:
                if gjf.chk():
                    raise Exception
            opts.chk = True
        except:
            pass
    for gjf in joblist:
        if opts.chk:
            gjf.addchk(f'{gauinp_nam}.chk')
        if opts.nproc:
            gjf.setnproc(opts.nproc)
        if opts.procs:
            gjf.setcpu(opts.procs)
        if opts.mem:
            gjf.setmem(opts.mem)
        for add in opts.add:
            gjf.route.append(f'{add}\n')
        if not gjf.mem():
            gjf.setmem(MEM)
        if gjf.nproc() > CPUTOT:
            errore(f'{gjf.nproc()} processors requested, but only {CPUFREE} available')
    return joblist
def wrtgauinp(joblist, scrdir: typing.Optional[str], gauinp: str, vrb=0) -> str:
    """Write list of Gaussian input file objects into file"""
    gauinp_nam, gauinp_ext = os.path.splitext(gauinp)
    tmpinp = tempfile.NamedTemporaryFile(mode='w+t', suffix=gauinp_ext, prefix=gauinp_nam, dir=scrdir, delete=False)
    with tmpinp as fileout:
        fileout.write(str(joblist[0]))
        for gjf in joblist[1:]:
            fileout.write('--Link1--\n')
            fileout.write(str(gjf))
    if vrb >= 1: print(f'Written file {tmpinp.name}')
    return tmpinp.name
def parsegau(lines, joblist):
    """Parse single Gaussian job"""
    newjob = gauinput()
    Route = False
    for nline, line in enumerate(lines):
        if not line.strip():
            #Skip unnecessary empty lines at the beginning
            continue
        elif re.match(REGAUINP['link0'], line.lstrip()):
            #Link0 line found
            newjob.link0.append(line.lstrip())
        elif re.match(REGAUINP['route'], line.lstrip()):
            #Route section found
            nroute = nline
            Route = True
            break
    #Read Route section
    if not Route:
        errore('Route section not found')
    nstart = nroute + readsection(lines[nroute:], newjob.route)
    #Possibly read Title and Molecule
    fullroute = " ".join(newjob.route)
    if not re.search(REGAUINP['allchk'], fullroute, flags=re.IGNORECASE):
        nstart = nstart + readsection(lines[nstart:], newjob.title)
        nstart = nstart + readsection(lines[nstart:], newjob.mol)
    #Read Tail
    lempty = 0
    for nline, line in enumerate(lines[nstart:]):
        if re.match(REGAUINP['link1'], line.lower()):
            #Read next job
            joblist = parsegau(lines[nstart + nline + 1:], joblist)
            break
        newjob.tail.append(line)
        if not line.strip():
            lempty = lempty + 1
            if lempty == 2:
                break
    #Add newly generated gjf object to list
    joblist = [newjob] + joblist
    return joblist
def readsection(lines, toadd):
    """Read section terminated by empty line"""
    nline = 0
    for nline, line in enumerate(lines):
        if not line.strip():
            break
        toadd.append(line)
    return nline + 1
def gaurun(opts):
    """Run Gaussian calculation with given options"""
    # DEFINE GAUSSIAN ENVIRONMENT AND SUBMISSION COMMAND
    os.environ = cleanenv(os.environ)
    os.environ = setgauenv(os.environ, opts.gauroot, opts.gauscr, opts.vrb)
    gaucmd = add_source_gauprofile(BASECMD, opts.gauroot)
    # ASSEMBLE GAUSSIAN COMMAND
    if opts.wrkdir is not None:
        # Add {wrkdir} and {wrkdir/exe-dir} to executable paths
        tmpcmd = add_source_gauprofile("echo $GAUSS_EXEDIR", opts.gauroot)
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
        gauinp_nam, gauinp_ext = os.path.splitext(gauinp)
        # Parse input file to generate Gaussian input file objects
        joblist = []
        try:
            with open(gauinp, 'r') as filein:
                lines = filein.readlines()
                joblist = parsegau(lines, joblist)
        except FileNotFoundError:
            if gauinp_nam == TESTGAU:
                newjob = gauinput()
                newjob.default()
                joblist = [ newjob ] + joblist
            else:
               errore(f'File {gauinp} not found')
        # Modify jobs according to options and write temporary file
        joblist = modgaujob(joblist, gauinp_nam, opts)
        _gauinp = wrtgauinp(joblist, opts.gauscr, gauinp, opts.vrb)
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
        if opts.vrb >= 1 : print(comando)
        if not opts.dry:
            try:
                gaurun = bashrun(comando, env=os.environ, vrb=opts.vrb)
            except:
                print(f'WARNING: Calculation on {gauinp} failed')
            else:
                # POSSIBLY GENERATE FORMATTED CHECKPOINT FILE
                if opts.fchk:
                    chkset = set()
                    for gjf in joblist:
                        chk = gjf.chk()
                        if chk:
                            chkset.add(chk)
                    for chk in chkset:
                        fchk = os.path.splitext(chk)[0] + '.fchk'
                        formchk = add_source_gauprofile(f"formchk {chk} {fchk}", opts.gauroot)
                        try:
                            dofchk = bashrun(formchk, env=os.environ, vrb=opts.vrb)
                        except:
                            print(f'WARNING: formchk {chk} {fchk} failed')
        if _gauinp != gauinp:
            os.remove(_gauinp)
            if opts.vrb >=1 : print(f'File {_gauinp} removed')
        # LOG CALCULATION: TOBEDONE
    return None

# ==============
#  MAIN PROGRAM
# ==============
def main(args=None):
    # CHANGE DIRECTORY UPON PBS BATCH SUBMISSION
    if os.getenv('PBS_ENVIRONMENT') == 'PBS_BATCH' and os.getenv('PBS_O_WORKDIR', default=""):
        print(f'On {socket.gethostname()}')
        goto = os.getenv('PBS_O_WORKDIR')
    else:
        goto = os.getcwd()
    with cd(goto):
        # PARSE OPTIONS
        opts = parseopt(args)
        # RUN JOB
        gaurun(opts)
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
