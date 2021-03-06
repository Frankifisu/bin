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
import typing #Support for type hints

# ==============
#  PROGRAM DATA
# ==============
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv('USER')
HOME = os.getenv('HOME')
SHELL = os.getenv('SHELL')

# ==========
#  DEFAULTS
# ==========

# =================
#  BASIC FUNCTIONS
# =================
def errore(message=None):
    """Error function"""
    if message is not None:
        print(f'ERROR: {str(message)}')
    sys.exit(1)

# =================
#  PARSING OPTIONS
# =================
def parseopt():
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    # Mandatory arguments
    parser.add_argument('opt1', help='First mandatory argument')
    # Optional arguments
    parser.add_argument('-v', '--iprint',
        dest='iprt', action='count', default=0,
        help='Set printing level')
    opts = parser.parse_args()
    # Check options
    return opts

# ================
#  WORK FUNCTIONS
# ================
def filparse(input_file):
    with open(input_file, 'r') as file_obj:
        for line in file_obj :
            pass

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
