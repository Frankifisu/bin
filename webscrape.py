#!/usr/bin/env python3

# =========
#  MODULES
# =========
import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import platform #Info about the current machine
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import glob #Unix pathname expansion: glob.glob('*.txt')
import re #Regex
import argparse # commandline argument parsers
import math #C library float functions
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import numpy #Scientific computing
import typing #Support for type hints
import datetime #Handle dates
from bs4 import BeautifulSoup #Parse HTTP code
import mechanicalsoup #Fill webpage forms
import webbrowser #Open pages in browser

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
BASEURL = 'https://www.gazzettaufficiale.it'
GZUFURL = BASEURL + '/ricerca/testuale/concorsi?reset=true'
ANNO = 2020
TODAY = datetime.date.today()
GIORNI = [1, 4] #I numeri che mi interessano escono martedi e venerdi
CAPODANNO = datetime.date(ANNO, 1, 1)
FAIL = 'la ricerca effettuata non ha prodotto risultati'
TIPI = {'Concorso', 'Avviso', 'Graduatoria', 'Diario'}
EVIDENZE = {'chimica', 'chimiche', 'tipo b', 'RTD', '03/A2', 'CHIM/02'}
if platform.uname().system == 'Windows':
    OUTFILE = r'C:\Users\franc\Desktop\concorsi.html'
else:
    OUTFILE = '/tmp/concorsi.html'
TEMPLATE = """
<!DOCTYPE html>
<head>
 <style>
  strong { font-weight: bold;
           color: white;
          }
 </style>
</head>
<html>
 <body link="white" vlink="red" style="background-color:#2c3e50 " text="ff5733">
 </body>
</html>
"""

# =========
#  CLASSES
# =========
# Classe atti pubblici
class atto:
    def __init__(self, tipo="atto", rubrica='', ente='', url='', testo=''):
        self.tipo = tipo
        self.rubrica = rubrica
        self.ente = ente
        self.url = url
        self.testo = testo
    def __str__(self):
        return f'{self.tipo}: {self.ente}\n {self.url}'

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
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    # Optional arguments
    parser.add_argument('-f', '--find', type=str,
        default='ricercatore',
        help='Parola da cercare')
    parser.add_argument('-n', '--numero', type=int,
        dest='num', action='store', default=contagiorni(CAPODANNO, TODAY),
        help='Numero della gazzetta da cercare')
    parser.add_argument('-v', '--verbose',
        dest='vrb', action='count', default=0,
        help='Set printing level')
    opts = parser.parse_args()
    if opts.num < 0:
        opts.num = contagiorni(CAPODANNO, TODAY) + opts.num
    # Check options
    return opts

# ================
#  WORK FUNCTIONS
# ================
def contagiorni(start, end):
    """
    Conta i giorni della settimana tra due date
    """
    if start > end :
        return 0
    timediff = end - start
    weeks, extradays = divmod(timediff.days, 7)
    days = 0
    for giorno in GIORNI:
        days = days + weeks
        if extradays > (giorno - start.weekday()) % 7 :
            days = days + 1
    return days
def gzform(numero, anno, tosearch):
    """
    Riempi form quarta sezione Gazzetta Ufficiale
    """
    # Start browser object and load site
    browser = mechanicalsoup.StatefulBrowser() # create browser object
    browser.open(GZUFURL)
    browser.select_form('form[id="ricercaBean"]') # select form to fill
    browser['numero'] = numero 
    browser['annoPubblicazione'] = ANNO
    browser['testo'] = tosearch
    response = browser.submit_selected() # submit form
    return response.text
def estrai_atti(ricerca):
    """
    Estrai informazioni da HTML atto pubblico
    """
    # Analizza HTML e cicla sulle voci taggate 'span'
    soup = BeautifulSoup(ricerca, "html.parser")
   # if soup.find_all("li", string=FAIL):
   #     return None
    atti = list()
    trovato = False
    for span in soup.find_all('span'):
        # Estrai il tipo di informazione
        try:
            classe = span['class'][0]
        except:
            continue
        # Segna il tipo di informazione
        if classe == 'estremi':
            pass # Numero e data Gazzetta
        elif classe == 'rubrica':
            rubrica = span.string.strip()
        elif classe == 'emettitore':
            ente = span.string.strip().title()
       # elif classe == 'risultato_b':
       #     pass # Non contiene il termine cercato
        elif classe == 'risultato' or classe == 'risultato_b':
            if 'ricercatore' not in str(span).lower():
                continue
            trovato = True
            pubblicaz = atto(rubrica=rubrica, ente=ente)
            # Estrai tipo di documento
            risuldata = span.find('span', {'class': 'data'}).contents[0].string.strip().lower()
            for tipo in TIPI:
                if tipo.lower() in risuldata:
                    pubblicaz.tipo = tipo
            # Estrai URL
            risuldata = span.a['href']
            pubblicaz.url = BASEURL + risuldata
            # Estrai testo
            testo = span.find_all('a')[1].contents[0].string.replace('\n',' ').strip()
            pubblicaz.testo = " ".join(testo.split())
            atti.append(pubblicaz)
    if not trovato:
        #errore('Nessun risultato trovato')
        raise ValueError
    return atti
def writepage(atti, num):
    """
    Esporta atti come documento HTML
    """
    newweb = TEMPLATE
    soup = BeautifulSoup(newweb, 'html.parser')
    bodytag = soup.body
    outhtml = f'/tmp/concorsi{num}.html'
    for atto in atti:
        #if 'universit' in atto.rubrica.lower() and 'concorso' in atto.tipo.lower():
        if 'concorso' in atto.tipo.lower():
            # Nuovo paragrafo
            entry = soup.new_tag("p")
            # Crea tag con link al sito sul nome dell'ente
            newtag = soup.new_tag("a", href=atto.url)
            newtag.append(f'{atto.ente}:')
            entry.append(newtag)
            # Crea tag con testo del concorso
            newtag = soup.new_tag("br")
            newtag.append(f'{atto.testo}')
            entry.append(newtag)
            bodytag.append(entry)
    sito = str(soup.prettify())
    for evidenza in EVIDENZE:
        pattern = re.compile(evidenza, re.IGNORECASE)
        sito = pattern.sub('<strong>' + evidenza + '</strong>', sito)
    with open(outhtml, 'w') as concorsi:
        concorsi.write(sito)
    return outhtml

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    # FILL WEBSITE FORM AND SUBMIT
    for numero in range(opts.num, 0, -1):
        print(numero)
        try:
            ricerca = gzform(numero, ANNO, opts.find)
            # PARSE WEBSITE WITH RESULTS
            atti = estrai_atti(ricerca)
            if atti is not None:
                outhtml = writepage(atti, numero)
        except ValueError:
            continue
    # CREATE HTML DOCUMENT
    errore()
    # OPEN HTML DOCUMENT IN BROWSER
    filepath = os.path.realpath(outhtml)
    webbrowser.open('file://' + filepath, new=1)
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
