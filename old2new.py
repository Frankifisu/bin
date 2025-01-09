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
import typing  # Support for type hints

# ==============
#  PROGRAM DATA
# ==============
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv("USER")
HOME = os.getenv("HOME")
SHELL = os.getenv("SHELL")

# ==========
#  DEFAULTS
# ==========


# =================
#  BASIC FUNCTIONS
# =================
def errore(message=None):
    """Error function"""
    if message is not None:
        print(f"ERROR: {str(message)}")
    sys.exit(1)


# =================
#  PARSING OPTIONS
# =================
def parseopt():
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME, description="Command-line option parser")
    # Mandatory arguments
    parser.add_argument("opt1", help="First mandatory argument")
    # Optional arguments
    parser.add_argument("-v", "--iprint", dest="iprt", action="count", default=0, help="Set printing level")
    opts = parser.parse_args()
    # Check options
    return opts


# ================
#  WORK FUNCTIONS
# ================
def filparse(input_file):
    newlines = []
    skip = 0
    imol = 1
    wrtcoords = True
    rmend = False
    dofq = False
    with open(input_file, "r") as file_obj:
        lines = file_obj.readlines()
        for nline, line in enumerate(lines):
            if skip > 0:
                skip = skip - 1
                continue
            if "ENDENGINE" in line.upper():
                skip = 0
                imol = 1
                wrtcoords = True
                rmend = False
                dofq = False
                newlines.append(line)
                continue
            if "FQQM" in line.upper():
                dofq = True
                newlines.append(line.replace("FQQM", "QMFQ"))
                if line[0] != "#":
                    rmend = True
                continue
            if "SCREEN" in line.upper() and dofq:
                newlines.append(line.upper().replace("SCREEN", "Kernel"))
                continue
            if "TOTALCHARGE" in line.upper() and dofq:
                newlines.append(line.upper().replace("TOTALCHARGE", "MolCharge"))
                continue
            if "END" in line.upper() and rmend and dofq:
                rmend = False
                continue
            if "FQPAR" in line.upper():
                if "ALPHA" in lines[nline + 4]:
                    skip = 10
                else:
                    skip = 8
                newlines.append("    AtomType\n")
                newlines.append("      Symbol O\n")
                if "ALPHA" in lines[nline + 4]:
                    newlines.append("      Chi 0.2908429850\n")
                    newlines.append("      Eta 0.5625181140\n")
                    newlines.append("      Alpha 2.2187983720\n")
                else:
                    newlines.append("      Chi 0.189194\n")
                    newlines.append("      Eta 0.523700\n")
                newlines.append("    SubEnd\n")
                newlines.append("    AtomType\n")
                newlines.append("      Symbol H\n")
                if "ALPHA" in lines[nline + 4]:
                    newlines.append("      Chi 0.1675711970\n")
                    newlines.append("      Eta 0.6093265770\n")
                    newlines.append("      Alpha 1.1906416090\n")
                else:
                    newlines.append("      Chi 0.012767\n")
                    newlines.append("      Eta 0.537512\n")
                newlines.append("    SubEnd\n")
                continue
            if "GROUP" in line and dofq:
                skip = 5
                if wrtcoords:
                    newlines.append(f"    Coords\n")
                    wrtcoords = False
                newlines.append(f"{lines[nline+2].rstrip()}   {imol}\n")
                newlines.append(f"{lines[nline+3].rstrip()}   {imol}\n")
                newlines.append(f"{lines[nline+4].rstrip()}   {imol}\n")
                imol = imol + 1
            elif not wrtcoords:
                newlines.append(f"    SubEnd\n")
                newlines.append(line)
                wrtcoords = True
            else:
                newlines.append(line)
    print("".join(newlines))


# filout = 'out'
# with open(filout, 'w') as file_obj:
#     for line in newlines:
#         file_obj.write(line)


# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    filparse(opts.opt1)
    sys.exit()


# ===========
#  MAIN CALL
# ===========
if __name__ == "__main__":
    main()
