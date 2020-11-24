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
from scipy.optimize import curve_fit #Fitting
import pandas #Libary for data analysis
import typing #Support for type hints
from urllib.error import HTTPError, URLError # To handle error exceptions
import datetime as dt #Dates parsing

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = 'Franco Egidi'
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv('USER')
HOME = os.getenv('HOME')
SHELL = os.getenv('SHELL')

# ==========
#  DEFAULTS
# ==========
PROVINCIA = 'Pisa'
UCWD = [ 9789, 9794, 9791, 9795, 9792, 9796, 9737 ]
ITWD = [ 'L', 'M', 'M', 'G', 'V', 'S', 'D' ]
TODAY = dt.datetime.today()
FMTFIL = '%Y-%m-%dT%H:%M:%S'
FMTNAM = '%Y%m%d'
LOCALDIR = os.path.join(HOME, "data/COVID-19/")
GITURL = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/"
GITPREFS = {
    "dir"   : "dati-",
    "fil"   : "dpc-covid19-ita-"
    }
GITNAMS = {
    "nazione"   : "andamento-nazionale",
    "regione"   : "regioni",
    "provincia" : "province"
    }
GITHEDS = {
    "nazione"     : "stato", 
    "regione"     : "denominazione_regione",
    "provincia"   : "denominazione_provincia",
    }
PRIMOGIORNO = dt.datetime.strptime('20200224', FMTNAM)
CAPODANNO   = dt.datetime.strptime('20200101', FMTNAM)
TOSEARCH = 'totale_casi'
TEST0 = 1.e-16

# =================
#  BASIC FUNCTIONS
# =================
def errore(message=None):
    """Error function"""
    if message != None:
        print('ERROR: ' + message)
    sys.exit(1)

# ===================
#  PARSING FUNCTIONS
# ===================
# Parsing command-line options
def parseopt():
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    # Mandatory arguments
    parser.add_argument('luogo', type=str, nargs='?', default='pisa',
        action='store', help='Luogo di cui cercare i dati')
    # Optional arguments
    parser.add_argument('-media', '-m', '-average', action='store_true',
        dest='media', default=False,
        help='Media sulla settimana')
    parser.add_argument('-log', action='store_true',
        dest='log', default=False,
        help='Plotta scala logaritmica')
    parser.add_argument('-diff', '-nuovi', '-delta', action='store_true',
        dest='diff', default=False,
        help='Plotta nuovi casi per giorno')
    parser.add_argument('-s', '--search', type=str, default=TOSEARCH,
        dest='src', action='store',
        help='Cosa cercare')
    parser.add_argument('-t', '--type', choices=GITNAMS.keys(),
        dest='tipo', help=argparse.SUPPRESS)
    parser.add_argument('-v', '--iprint',
        dest='iprt', action='count', default=0,
        help='Livello di stampa')
    opts = parser.parse_args()
    # Check options
    opts.luogo = opts.luogo.lower()
    if opts.luogo in ['nazione', 'italia', 'andamento-nazionale']:
        opts.luogo = 'nazione'
        opts.tipo  = 'nazione'
    else:
        if tipoluogo(opts.luogo, 'regione'):
            opts.tipo = 'regione'
        elif tipoluogo(opts.luogo, 'provincia'):
            opts.tipo = 'provincia'
        else:
            errore('Luogo non valido')
    return opts
# Parsing input file
def filparse(input_file, andamento, provincia):
    """Cerca dati nel file"""
    trovati = list()
    with open(input_file, 'r') as file_obj:
        # skip the first line which holds the headers
        next(file_obj)
        # loop over data to extract the province of interest
        for line in file_obj :
            linea = covid19prv(line.rstrip().split(','))
            if linea.provincia.casefold() == provincia.casefold():
                trovati = trovati + [ linea ]
    return trovati

# ================
#  WORK FUNCTIONS
# ================
def fileurl(tipoluogo, desinenza):
    """Find source for sought after data"""
    subpath = GITPREFS['dir'] + GITNAMS[tipoluogo] + '/' + GITPREFS['fil'] + GITNAMS[tipoluogo] + '-' + desinenza + '.csv'
    # Cerca in locale
    for trydir in (LOCALDIR, os.getcwd()):
        testfil = os.path.join(trydir, subpath)
        if os.path.isfile(testfil):
            return testfil
    # Altrimenti prova GitHub
    return GITURL + subpath
def tipoluogo(luogo, luoghi):
    """Cerca luogo tra regioni e province"""
    urlfil = fileurl(luoghi, 'latest')
    dataframe = pandas.read_csv(urlfil, encoding='latin-1')
    trovato = dataframe[GITHEDS[luoghi]].str.contains(luogo, case=False).any()
    return trovato
def discretize(z, zmax, zmin, LZ, action=None):
    """Find value placement in discretized axis"""
    if action == 'log':
        if zmin < 0.0 or zmax < 0.0 or z < 0.0: errore('Log scale with negative values')
        if (z - zmin) <= TEST0:
            zrel = 0.0
        else:
            zrel = ( math.log10(z - zmin) ) / ( math.log10(zmax - zmin) )
    else:
        zrel = ( z - zmin ) / ( zmax - zmin )
    Z = float(LZ) * zrel
    return int(Z)
def newasciiplot(xy, marker='X', xmod=None, ymod=None, LX=84, LY=22, action=None):
    """Print pairs as ascii plot"""
    # Find max and min values for both coords
    xmin, ymin = numpy.amin(xy, axis=0)
    xmax, ymax = numpy.amax(xy, axis=0)
    # Prepare empty image
    XY = numpy.full((LY+1, LX+1), ' ')
    # Fill image with points
    for x, y in xy[:]:
        X = discretize(x, xmax, xmin, LX)
        Y = discretize(y, ymax, ymin, LY, action)
        XY[Y, X] = marker[0]
    # Print image
    space = len(f'{ymax}')
    print(f'{ymax} ^{"".join(XY[LY])}')
    for Y in range(LY, -1, -1):
        print(f'{space*" "} |{"".join(XY[Y])}')
    print(f'{str(ymin).rjust(space)} +{LX*"-"}->')
    FMTDAT = '%d %b'
    startx = dt.datetime.strftime(INIZIO, FMTDAT)
    deltax = int(xmax - xmin)
    endx   = dt.datetime.strftime(INIZIO + dt.timedelta(days=deltax), FMTDAT )
    print(' '*(space+1) + startx + ' '*(LX+2-len(startx)-len(endx)) + endx)

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    # READ FILES
    andamento = list()
    data = PRIMOGIORNO
    gg = list()
    casi = list()
    while data <= TODAY:
        # Build URL of specfic file with its date
        urlfil = fileurl(opts.tipo, dt.datetime.strftime(data, FMTNAM))
        # Get data frame and slice it to only get info we care about
        try:
            dataframe = pandas.read_csv(urlfil, encoding='latin-1')
        except (HTTPError, URLError, FileNotFoundError):
            data = data + dt.timedelta(days=1)
            continue
        dataframe = dataframe.loc[:, ['data', GITHEDS[opts.tipo], opts.src]]
        # Slice data frame so we only get the location we care about
        if opts.tipo != 'nazione':
            dataframe = dataframe[dataframe[GITHEDS[opts.tipo]].str.contains(opts.luogo, case=False)]
        dataframe = dataframe.loc[:, ['data', opts.src]]
        # Get date and cases
        gg   = gg   + [ (dt.datetime.strptime(dataframe.iloc[0, 0], FMTFIL) - CAPODANNO ).days ]
        casi = casi + [ int(dataframe.iloc[0, 1]) ]
        # Go to next day
        data = data + dt.timedelta(days=1)
    # ELABORA
    nuovicasi = [ casi[day+1] - casi[day] for day in range(len(casi)-1) ]
    gstart = 0
    if opts.media:
        casi = [ int(sum(casi[i:i+7])/7.) for i in range(len(casi)-6) ]
        nuovicasi = [ int(sum(nuovicasi[i:i+7])/7.) for i in range(len(nuovicasi)-6) ]
        gstart = 6
    casi = numpy.asarray(casi)
    gg   = numpy.asarray(gg)
    nuovicasi = numpy.asarray(nuovicasi)
    # STAMPA GRAFICO
    global INIZIO
    if opts.diff:
        casixgiorno = numpy.stack([gg[gstart:-1], nuovicasi], axis=-1)
        INIZIO = PRIMOGIORNO + dt.timedelta(days=7)
    else:
        casixgiorno = numpy.stack([gg[gstart:], casi], axis=-1)
        INIZIO = PRIMOGIORNO
    #asciiplot(casixgiorno)
    if opts.log: action = 'log'
    else: action = None
    newasciiplot(casixgiorno, action=action)
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
