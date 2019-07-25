#!/usr/bin/env python3

##
## GET HELP ON PYTHON MODULES AND COMMANDS
##

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

# =================
#  PARSING OPTIONS
# =================
def parseopt():
    # CREATE PARSER
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    # MANDATORY ARGUMENTS
    parser.add_argument('obj', help='Object to seek help about specified as mod or mod.obj')
    # OPTION PARSING
    opts = parser.parse_args()
    # OPTION CHECKING
    return opts

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    help_this = opts.obj
    try:
        # POSSIBLY IMPORT MODULE
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
