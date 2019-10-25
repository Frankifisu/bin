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

# ==============
#  PROGRAM DATA
# ==============
PROGNAME = os.path.basename(sys.argv[0])
USERNAME = os.getenv('USER')
HOMEDIR = os.getenv('HOME')

# ==========
#  DEFAULTS
# ==========

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

# =================
#  PARSING OPTIONS
# =================
def parseopt():
    """
    Parse options
    """
    # CREATE PARSER
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    # MANDATORY ARGUMENTS
    parser.add_argument('opt1', help='First mandatory argument')
    # OPTIONAL ARGUMENTS
    parser.add_argument('-v', '--iprint',
        dest='iprt', action='count', default=0,
        help='Set printing level')
    # OPTION PARSING
    opts = parser.parse_args()
    # OPTION CHECKING
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
