#!/usr/bin/env python3

#
# Useful python functions used often
#

# =========
#  MODULES
# =========
import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import re #Regex
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import typing #Explicit typing of arguments

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = 'Franco Egidi (franco.egidi@gmail.it)'
USER = os.getenv('USER')
HOME = os.getenv('HOME')
PWD = os.getcwd()

# ==========
#  DEFAULTS
# ==========
BASH = '/bin/bash'

# =========
#  CLASSES
# =========
class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)

# =================
#  BASIC FUNCTIONS
# =================
def wide_help(formatter, w=120, h=36):
    """Return a wider HelpFormatter, if possible."""
    try:
        # https://stackoverflow.com/a/5464440
        # beware: "Only the name of this class is considered a public API."
        kwargs = {'width': w, 'max_help_position': h}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        print("argparse help formatter failed, falling back.")
        return formatter
def errore(message=None):
    """Error function"""
    if message is not None:
        print(f'ERROR: {str(message)}', file=sys.stderr)
    sys.exit(1)
def intorstr(string):
    """Check if string could be integer"""
    if string is None:
        return None
    try:
        toint = int(string)
        return toint
    except:
        return string
def bashrun(comando: str, env=None, vrb=0) -> str:
    """Run bash subprocess with sensible defaults
    and return output"""
    if env is None:
        process = subprocess.run(comando, shell=True, check=True, executable=BASH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        process = subprocess.run(comando, shell=True, check=True, executable=BASH, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    output = process.stdout.decode().rstrip()
    if vrb >= 1:
        print(output)
    return output
def check_extension(to_check: str, allowed_ext):
    """Check file extension"""
    filnam, filext = os.path.splitext(to_check)
    if filext not in allowed_ext:
        raise ValueError
def loginshvar(var: str) -> str :
    """Get environment variable from the login shell"""
    comando = " ".join(['env -i', BASH, ' -l -c "printenv', var, '"'])
    out = bashrun(comando)
    return out
def ncpuavail() -> int :
    """Find number of processors in the machine"""
    try:
        result = subprocess.run('nproc', stdout=subprocess.PIPE)
        nprocs = result.stdout.decode('utf-8').split()[0]
    except:
        nprocs = 1
    return int(nprocs)
def nfreecpu() -> int :
    """Find number of free processors in the machine"""
    ntot = ncpuavail()
    vmstat = bashrun('vmstat -w -S M', env=os.environ)
    # r: The number of runnable processes (running or waiting for run time).
    # b: The number of processes in uninterruptible sleep.
    info = vmstat.split('\n')[2].split()[0:2]
    r, b = map(int, info)
    nfree = max(ntot - r - b, 0)
    return nfree
def cleanenv(env):
    """Get clean environment"""
    env.clear()
    # Set basic envvars from current or login shell
    env['USER'] = USER
    env['HOME'] = HOME
    env['PATH'] = loginshvar('PATH')
    env['PWD']  = PWD
    return env
CPUFREE = nfreecpu()
CPUTOT  = ncpuavail()

