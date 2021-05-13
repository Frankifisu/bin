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
import collections
import numpy

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
Element = collections.namedtuple('Element', 'name atomic_number atomic_mass group')
ELEMENTS = {
    'H'  : Element('Hydrogen',    1,   1, 'Non Metals'),
    'He' : Element('Helium',      2,   4, 'Noble Gases'),
    'Li' : Element('Lithium',     3,   7, 'Alkali Metals'),
    'Be' : Element('Berylium',    4,   9, 'Alkaline Earth Metals'),
    'B'  : Element('Boron',       5,  11, 'Non Metals'),
    'C'  : Element('Carbon',      6,  12, 'Non Metals'),
    'N'  : Element('Nitrogen',    7,  14, 'Non Metals'),
    'O'  : Element('Oxygen',      8,  16, 'Non Metals'),
    'F'  : Element('Fluorine',    9,  19, 'Halogens'),
    'Ne' : Element('Neon',       10,  20, 'Noble Gasses'),
    'Na' : Element('Sodium',     11,  23, 'Alkali Metals'),
    'Mg' : Element('Magnesium',  12,  24, 'Alkaline Earth Metal'),
    'Al' : Element('Aluminium',  13,  27, 'Other Metals'),
    'Si' : Element('Silicon',    14,  28, 'Non Metals'),
    'P'  : Element('Phosphorus', 15,  31, 'Non Metals'),
    'S'  : Element('Sulphur',    16,  32, 'Non Metals'),
    'Cl' : Element('Chlorine',   17, 35.5, 'Halogens'),
    'Ar' : Element('Argon',      18,  40, 'Noble Gasses'),
    'K'  : Element('Potassium',  19,  39, 'Alkali Metals'),
    'Ca' : Element('Calcium',    20,  40, 'Alkaline Earth Metals'),
    'Sc' : Element('Scandium',   21,  45, 'Transition Metals'),
    'Ti' : Element('Titanium',   22,  48, 'Transition Metals'),
    'V'  : Element('Vanadium',   23,  51, 'Transition Metals'),
    'Cr' : Element('Chromium',   24,  52, 'Transition Metals'),
    'Mn' : Element('Manganese',  25,  55, 'Transition Metals'),
    'Fe' : Element('Iron',       26,  56, 'Transition Metals'),
    'Co' : Element('Cobalt',     27,  59, 'Transition Metals'),
    'Ni' : Element('Nickel',     28,  59, 'Transition Metals'),
    'Cu' : Element('Copper',     29, 63.5, 'Transition Metals'),
    'Zn' : Element('Zinc',       30,  65, 'Transition Metals'),
    'Ga' : Element('Gallium',    31,  70, 'Other Metals'),
    'Ge' : Element('Germanium',  32,  73, 'Other Metals'),
    'As' : Element('Arsenic',    33,  75, 'Non Metals'),
    'Se' : Element('Selenium',   34,  79, 'Non Metals'),
    'Br' : Element('Bromine',    35,  80, 'Halogens'),
    'Kr' : Element('Krypton',    36,  84, 'Noble Gasses'),
    'Rb' : Element('Rubidium',   37,  85, 'Alkali Metals'),
    'Sr' : Element('Strontium',  38,  88, 'Alkaline Earth Metals'),
    'Y'  : Element('Yttrium',    39,  89, 'Transition Metals'),
    'Zr' : Element('Zirconium',  40,  91, 'Transition Metals'),
    'Nb' : Element('Niobium',    41,  93, 'Transition Metals'),
    'Mo' : Element('Molybdenum', 42,  96, 'Transition Metals'),
    'Tc' : Element('Technetium', 43,  98, 'Transition Metals'),
    'Ru' : Element('Ruthenium',  44, 101, 'Transition Metals'),
    'Rh' : Element('Rhodium',    45, 103, 'Transition Metals'),
    'Pd' : Element('Palladium',  46, 106, 'Transition Metals'),
    'Ag' : Element('Silver',     47, 108, 'Transition Metals'),
    'Cd' : Element('Cadmium',    48, 112, 'Transition Metals'),
    'In' : Element('Indium',     49, 115, 'Other Metals'),
    'Sn' : Element('Tin',        50, 119, 'Other Metals'),
    'Sb' : Element('Antimony',   51, 122, 'Other Metals'),
    'Te' : Element('Tellurium',  52, 128, 'Non Metals'),
    'I'  : Element('Iodine',     53, 127, 'Halogens'),
    'Xe' : Element('Xenon',      54, 131, 'Noble Gasses'),
    'Cs' : Element('Caesium',    55, 133, 'Alkali Metals'),
    'Ba' : Element('Barium',     56, 137, 'Alkaline Earth Metals'),
    'La' : Element('Lanthanum',  57, 139, 'Rare Earth Metals'),
}
#Reverse element to atomic number lookup
Z2SYMB = { element.atomic_number : El for El, element in ELEMENTS.items()}

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

class atom:
    """Atom class"""
    def __init__(self,
                 symbol,
                 coord = None,
                 props = dict()):
        self.symbol = symbol
        self.coord = numpy.array([ float(x) for x in coord ])
        self.props = props
    def prtxyz(self, fmtxyz=' 11.6f'):
        return f'{self.symbol.ljust(2)} {self.coord[0]:{fmtxyz}} {self.coord[1]:{fmtxyz}} {self.coord[2]:{fmtxyz}}'
    def __str__(self):
        return f'{self.symbol} {self.coord}'

class molecule:
    """Molecule class"""
    def __init__(self,
                 charge = 0,
                 spinmul = 1,
                 name = '',
                 atoms = None):
        self.charge = charge
        self.spinmul = spinmul
        self.name = name
        self.atoms = atoms
        # We do it this way because lists are mutable
        if self.atoms is None: self.atoms = []

    def add_atom(self, atom):
        self.atoms = self.atoms + [atom]

    def coc(self, layer=None, condition=True):
        Ztot = 0
        coc = [ 0., 0., 0. ]
        for atom in self.atoms:
            Z = ELEMENTS[atom.symbol].atomic_number
            Ztot = Ztot + Z
            for i in range(3):
                coc[i] = coc[i] + Z*atom.coord[i]
        coc = [ x/Ztot for x in coc ]
        return coc

#    def cocH(self, layer=None, condition=True):
#        Ztot = 0
#        coc = [ 0., 0., 0. ]
#        for atom in self.atoms:
#            if atom.props['layer'] != 'H':
#                continue
#            Z = ELEMENTS[atom.symbol].atomic_number
#            Ztot = Ztot + Z
#            for i in range(3):
#                coc[i] = coc[i] + Z*atom.coord[i]
#        for i in range(3):
#            coc[i] = coc[i]/Ztot
#        return coc
#
#    def recenter(self):
#        coc = self.cocH()
#        print(self)
#        for i, at in enumerate(self.atoms):
#            self.atoms[i].coord = at.coord - coc
#        #for atom in molecule.atoms:
#        errore(self)
#        return self

    def prtxyz(self):
        out = ''
        for atom in self.atoms:
            out = out + f'{atom.prtxyz()}\n'
        return out

    def __str__(self):
        out = ''
        if self.name:
            out = out + f'{self.name}\n'
        out = out + f'Charge = {self.charge} ; SpinMul = {self.spinmul}\n'
        for atom in self.atoms:
            out = out + f'{atom.prtxyz()}'
        return out


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
    if vrb >= 1: print(output)
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
    try:
        vmstat = bashrun('vmstat -w -S M', env=os.environ)
        # r: The number of runnable processes (running or waiting for run time).
        # b: The number of processes in uninterruptible sleep.
        info = vmstat.split('\n')[2].split()[0:2]
        r, b = map(int, info)
        nfree = max(ntot - r - b, 0)
    except Exception:
        nfree = ntot
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
CPUTOT  = ncpuavail()

