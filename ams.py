#!/usr/bin/env python3

#
# Run AMS calculation given input files
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
AUTHOR = 'Franco Egidi (egidi@scm.com)'
VERSION = '2020.08.29'
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv('USER')
HOME = os.getenv('HOME')

# ==========
#  DEFAULTS
# ==========
TEST_TMP = ('/scratch', '/tmp', '/var/tmp', '/usr/tmp', HOME+'/tmp', HOME)
AMS_OUTFILS = { 'ams.log', 'ams.rkf', 'adf.rkf', 'output.xyz'}
INPEXT = frozenset(('.in', '.inp', '.ams', '.fcf' ))
TESTAMS = 'test'
AMSDEFAULT = '/home/egidi/usr/local/ams/ams2021.TADF'

# =========
#  CLASSES
# =========

# =================
#  BASIC FUNCTIONS
# =================
def amsdefault (amsin):
    """Define AMSHOME based on input descriptor"""
    if amsin is None:
        if 'AMSHOME' in os.environ:
            if os.path.isdir(os.environ['AMSHOME']): return os.environ['AMSHOME']
        else:
            if os.path.isdir(AMSDEFAULT): return AMSDEFAULT
    else:
        if os.path.isdir(amsin):
            return amsin
        testpath = os.path.join(HOME, 'usr/local/ams/')
        for trydir in [testpath+'ams.'+amsin, testpath+amsin, testpath+'ams2021.'+amsin]:
            if os.path.isdir(trydir):
                return trydir
    errore('Cannot define AMS directory')
    return None

# =================
#  PARSING OPTIONS
# =================
def amsparser(parser):
    """Create parsers for AMS command"""
    # Add options
    parser.add_argument(dest='inp', nargs='+', metavar="INPUT",
        help='Input file(s) with .in or .inp extension')
    parser.add_argument('-o', '--output', metavar='OUTPUT',
        dest='out', action='store',
        help='Set output file name')
    parser.add_argument('-ams', '--amshome', metavar='AMSHOME',
        dest='amshome', action='store', default=None,
        help='Set path to AMSHOME or choose AMS version')
    parser.add_argument('-p', '--nproc', metavar='NSCM', type=int,
        dest='nproc', default=1,
        help='Set number of processors')
   # parser.add_argument('-t', '--tmp', metavar='SCM_TMPDIR',
   #     dest='tmp', action='store', default=None,
   #     help='Set scratch directory')
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
        description='AMS easy calculation script')
    parser = amsparser(parser)
    opts = parser.parse_args(args)
    # Check options
    for fil in opts.inp:
        if fil != TESTAMS:
            check_extension(fil, INPEXT)
   # if not os.path.isdir(opts.gauscr):
   #     errore(f'Invalid scratch directory {opts.gauscr}')
   # if opts.gauroot in GAUDIR.keys():
   #     opts.gauroot = exepath(GAUDIR[opts.gauroot])
    opts.amshome = amsdefault(opts.amshome)
    return opts

# ================
#  WORK FUNCTIONS
# ================
def setamsenv(env, amshome: str, vrb: int=0) -> str:
    """Set basic AMS environment"""
    # Set AMS home directory
    env['AMSHOME'] = amshome
    # Set AMS scratch directory
    tmpdir = bashrun('source ${AMSHOME}/amsbashrc.sh; echo -n ${SCM_TMPDIR}', env=env)
    SCM_TMPDIR = os.path.join(tmpdir, USER, 'ams')
    env['SCM_TMPDIR'] = SCM_TMPDIR
    # Possibly create scratch directory
    os.makedirs(SCM_TMPDIR, exist_ok=True)
    if vrb >= 1:
        print(f"AMS diretory set to {env['AMSHOME']}")
        print(f"SCM scratch diretory set to {env['SCM_TMPDIR']}")
    return env
def amsbuildcmd(env, inp, prog='ams', nproc=1, out='ams.out', ad='>'):
    """Build command to launch AMS"""
    inp_nam, inp_ext = os.path.splitext(inp)
    cmdlist = []
    cmdlist.append('source ${AMSHOME}/amsbashrc.sh')
    cmdlist.append(f'export SCM_TMPDIR={env["SCM_TMPDIR"]}')
    cmdlist.append(f'export NSCM={nproc}')
    cmdlist.append('unset AMS_SWITCH_LOGFILE_AND_STDOUT')
    cmdlist.append(f'AMS_JOBNAME="{prog}.{inp_nam}" AMS_RESULTSDIR=. $AMSBIN/{prog} < "{inp}" {ad} {out}')
    return " ; ".join(cmdlist)
def amsrename(inp):
    """Rename calculation files to prevent future crashes"""
    inp_nam, inp_ext = os.path.splitext(inp)
    for outfil in AMS_OUTFILS:
        if os.path.isfile(outfil):
            n = 1
            dest = f'{inp_nam}.{outfil}'
            while os.path.isfile(dest) and n < 100:
                dest = f'{inp_nam}.{n:02d}.{outfil}'
                n = n + 1
            os.rename(outfil, dest)
    return None
def amsrun(opts):
    """Run AMS calculation with given options"""
    # DEFINE AMS ENVIRONMENT AND SUBMISSION COMMAND
    os.environ = cleanenv(os.environ)
    os.environ = setamsenv(os.environ, opts.amshome, opts.vrb)
    # LOOP OVER INPUT FILES ONE BY ONE
    ad = '>'
    for num, inp in enumerate(opts.inp, start=1):
        inp_nam, inp_ext = os.path.splitext(inp)
        # Select program to run based on file extension
        if inp_ext == '.fcf':
            prog = 'fcf'
        else:
            prog = 'ams'
        # Set output file
        if opts.out is None:
            amsout = inp_nam + '.out'
        else:
            amsout = opts.out
            if num > 1: # if there are multiple inputs but the output filename is set then append output
                ad = '>>'
        # Build calculation command
        amscmd = amsbuildcmd(os.environ, inp, prog, opts.nproc, amsout, ad)
        if opts.vrb >= 1 : print(amscmd)
        # Run calculation
        if not opts.dry:
            try:
                amsjob = bashrun(amscmd, env=os.environ, vrb=opts.vrb)
                print(amsjob)
            except Exception:
                print(f'WARNING: Calculation on {inp} failed')
            amsrename(inp)
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
        amsrun(opts)
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
