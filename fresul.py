#!/usr/bin/env python3

# =========
#  MODULES
# =========
import os  # OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys  # System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import glob  # Unix pathname expansion: glob.glob('*.txt')
import re  # Regex
import argparse  # commandline argument parsers
import math  # C library float functions
import subprocess  # Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import numpy  # Scientific computing
import typing
from tabulate import tabulate

# ==============
#  PROGRAM DATA
# ==============
PROGNAME = os.path.basename(sys.argv[0])
USERNAME = os.getenv("USER")
HOMEDIR = os.getenv("HOME")

# ==========
#  DEFAULTS
# ==========
# Permitted file extensions
OUTEXT = frozenset((".log", ".out"))
# Patterns to search within file
WANT = ("Freq", "IR", "Raman", "redmas")
SRCXPR = {
    "Mode": None,
    "Freq": " Frequencies -- ",
    "Sym": None,
    "IR": " IR Inten    -- ",
    "Raman": " Raman Activ -- ",
    "redmas": " Red. masses -- ",
    "Start": " Initial command:",
}
# Units for data read in input
INUNIT = {
    "Mode": "",
    "Sym": "",
    "Freq": f"cm\N{SUPERSCRIPT MINUS}\N{SUPERSCRIPT ONE}",
    "IR": "km/mol",
    "Raman": f"\N{ANGSTROM SIGN}\N{SUPERSCRIPT FOUR}/amu",
    "redmas": "amu",
}
# Output strings for column headers
OUTXPR = {"Mode": "Mode", "Freq": "Freq", "Sym": "Sym", "IR": "IR", "Raman": "Raman", "redmas": "Red Mas"}


# =========
#  CLASSES
# =========
# Normal coordinate class
class norcor:
    def __init__(self, nmod, sym="?"):
        self.nmod = nmod
        self.sym = sym

    def __str__(self):
        return f"Mode {self.nmod} ({self.sym})"


# Class for generic property
class prop:
    def __init__(self, name, value, unit="?"):
        self.name = name
        self.value = value
        self.unit = unit

    def __str__(self):
        return f"{self.name} = {self.value} {self.unit}"


# Class for normal coordinate with properties
class vibprop:
    def __init__(self, norcor):
        self.norcor = norcor
        self.props = list()

    def addprop(self, name, value, unit="?"):
        newprop = prop(name, value, unit)
        self.props.append(newprop)

    def getval(self, name):
        value = None
        for prop in self.props:
            if prop.name is name:
                value = theprop.value
        return value

    def getunit(self, name):
        unit = None
        for prop in self.props:
            if prop.name is name:
                unit = prop.unit
        return unit

    def propnames(self):
        names = list()
        for prop in self.props:
            names.append(prop.name)
        return names

    def propvalues(self):
        values = list()
        for prop in self.props:
            values.append(prop.value)
        return values

    def propunits(self):
        units = list()
        for prop in self.props:
            units.append(prop.unit)
        return units

    def getinfo(self):
        mode = [self.norcor.nmod, self.norcor.sym] + self.propvalues()
        return mode

    def __str__(self):
        toprint = str(self.norcor)
        for prop in self.props:
            toprint = toprint + " " + str(prop)
        return toprint


# =================
#  BASIC FUNCTIONS
# =================
def errore(message=None):
    """
    Error function
    """
    if message != None:
        print("ERROR: " + message)
    sys.exit(1)


# =================
#  PARSING OPTIONS
# =================
def parseopt():
    """
    Parse options
    """
    # CREATE PARSER
    parser = argparse.ArgumentParser(prog=PROGNAME, description="Command-line option parser")
    # MANDATORY ARGUMENTS
    parser.add_argument("outfil", nargs="+", help="Gaussian output file")
    # OPTIONAL ARGUMENTS
    parser.add_argument("-t", "--table", dest="tbf", action="store", default="simple", help="Set table format")
    parser.add_argument("-f", "--format", dest="fmt", action="store", default=".2f", help="Set float format")
    parser.add_argument("-v", "--iprint", dest="iprt", action="count", default=0, help="Set printing level")
    # OPTION PARSING
    opts = parser.parse_args()
    # CONSISTENCY CHECKS
    for fil in opts.outfil:
        filnam, filext = os.path.splitext(fil)
        if filext not in OUTEXT:
            errore("Invalid file extension")
    return opts


# ================
#  WORK FUNCTIONS
# ================
def filparse(input_file) -> list:
    """
    Parse file and return result list
    """
    # Array to collect all vibrational info
    idres = -1
    results = list()
    with open(input_file, "r") as file_obj:
        # For Gaussian I have to go back two lines for symmetry and mode
        prevline = ["", ""]
        modes = list()
        syms = list()
        idnew = 0
        for line in file_obj:
            # Store one set of results for every calculation
            if SRCXPR.get("Start") in line:
                idres = idres + 1
                results = results + [[]]
            if idres < 0:
                continue
            # Get modes of interest and symmetry
            if SRCXPR.get("Freq") in line:
                idnew = len(results[idres])
                modes = [int(number) for number in prevline[1].split()]
                syms = prevline[0].split()
                for mode, sym in zip(modes, syms):
                    results[idres].append(vibprop(norcor(mode, sym)))
            # Get info
            for prop in WANT:
                data = datard(line, modes, prop)
                for newvibprop, datum in zip(results[idres][idnew:], data):
                    newvibprop.addprop(prop, datum, INUNIT.get(prop))
            # Save line before overwriting in loop
            prevline[1] = prevline[0]
            prevline[0] = line
    return results


#
def datard(line: str, modes: list, toget: str) -> list:
    expr = SRCXPR.get(toget)
    if expr is None:
        return None
    data = list()
    if expr in line:
        data = line.replace(expr, "").split()
        if len(modes) != len(data):
            errore("Incompatibility between number of modes and available data")
    return data


# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    for fil in opts.outfil:
        results = filparse(fil)
        for calc in results:
            if len(calc) == 0:
                break
            # BUILD TABLE HEADER
            header = [OUTXPR.get("Mode"), OUTXPR.get("Sym")] + calc[0].propnames()
            units = ["", ""] + calc[0].propunits()
            # BUILD VALUE LISTS
            table = list()
            for mode in calc:
                table.append(mode.getinfo())
            print(tabulate(table, headers=header, floatfmt=opts.fmt, tablefmt=opts.tbf))
    sys.exit()


# ===========
#  MAIN CALL
# ===========
if __name__ == "__main__":
    main()
