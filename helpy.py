#!/usr/bin/env python3

# =========
#  MODULES
# =========
import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import importlib #Simplifies module importing
import argparse # commandline argument parsers

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
    if message != None:
        print('ERROR: ' + message)
    sys.exit(1)

# =================
#  PARSING OPTIONS
# =================
def parseopt():
    # CREATE PARSER
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    # MANDATORY ARGUMENTS
    parser.add_argument('obj', help='Object to seek help about specified as mod or mod.obj')
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
    # IMPORT MODULE
    help_this = opts.obj
    try:
        modulo = help_this.split('.')[0]
        importlib.import_module(modulo)
    except:
        pass
    finally:
        help(help_this)
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
