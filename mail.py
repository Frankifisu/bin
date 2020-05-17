#!/usr/bin/env python3

#
# Send email from command line
#

# =========
#  MODULES
# =========
import os #OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import platform #Computer info
import sys #System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import glob #Unix pathname expansion: glob.glob('*.txt')
import re #Regex
import argparse # commandline argument parsers
import subprocess #Spawn process: subprocess.run('ls', stdout=subprocess.PIPE)
import typing #Support for type hints
import smtplib #To send emails
import email #To send emails
import mimetypes #Handle file types over Internet

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = 'Franco Egidi (franco.egidi@gmail.it)'
VERSION = '2020.15.05'
PROGNAME = os.path.basename(sys.argv[0])
USER = os.getenv('USER')
HOME = os.getenv('HOME')
SHELL = os.getenv('SHELL')
HOSTNAME = platform.node()

# ==========
#  DEFAULTS
# ==========
SMTP_DATA = {
    'MAIL'   : 'franco.egidi@gmail.com',
    'PASSWD' : 'pvxk dgia dpwc gvox',
    'SERVER' : 'smtp.gmail.com',
    'PORT'   : 465,
    }
SIGNED = f'Message from {USER}@{HOSTNAME}'
FOOTER = f"""
  <html>
    <head></head>
    <body>
      <TT>
        <p>{"-"*len(SIGNED)}</p>
        <p>{SIGNED}</p>
      </TT>
    </body>
  </html>
  """

# =================
#  BASIC FUNCTIONS
# =================
def errore(message=None):
    """Error function"""
    if message != None:
        print('ERROR: ' + message)
    sys.exit(1)

# =================
#  PARSING OPTIONS
# =================
def parseopt():
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME,
        description='Command-line option parser')
    # Optional arguments
    parser.add_argument('-to', '--to', nargs='*',
        dest='to', action='store', default=[ SMTP_DATA.get('MAIL') ],
        help='Specify recepients')
    parser.add_argument('-cc', nargs='*',
        dest='cc', action='store', default=list(),
        help='Carbon Copy addresses')
    parser.add_argument('-bcc', nargs='*',
        dest='bcc', action='store', default=list(),
        help='Blind Carbon Copy addresses')
    parser.add_argument('-s', '--subject', type=str,
        dest='sbj', action='store', default=SIGNED,
        help='Mail subject')
    parser.add_argument('-m', '--msg', type=str,
        dest='msg', action='store', default=" ",
        help='Email body as string or text file')
    parser.add_argument('-a', '--att', nargs='+',
        dest='att', action='store', default=list(),
        help='Attachments')
    parser.add_argument('-v', '--verbose',
        dest='vrb', action='count', default=0,
        help='Verbose mode')
    parser.add_argument('--dry',
        dest='dry', action='store_true', default=False,
        help=argparse.SUPPRESS)
    opts = parser.parse_args()
    # Check options
    for attfil in opts.att:
        if not os.path.isfile(attfil):
            errore(f'File {attfil} not found')
    if SMTP_DATA.get('MAIL') not in opts.to + opts.cc + opts.bcc:
        opts.bcc.append( SMTP_DATA.get('MAIL') )
    return opts

# ================
#  WORK FUNCTIONS
# ================
def emailmsg( sbj='', msg='', fro='', to=[], cc=[], bcc=[], att=[] ):
    """Create email message object"""
    emsg = email.message.EmailMessage()
    #Fields
    emsg['Subject'] = sbj
    emsg['To'] = ', '.join(to)
    emsg['From'] = fro
    emsg['Cc'] = ', '.join(cc)
    emsg['Bcc'] = ', '.join(bcc)
    #Body
    try:
        with open(msg, 'r') as filobj:
            body = filobj.read()
    except:
        body = msg
    body = body + f'\n{"-"*len(SIGNED)}\n{SIGNED}'
    emsg.set_content(body)
    emsg.add_alternative(FOOTER, subtype='html')
    #Attachments
    for attfil in att:
        if not os.path.isfile(attfil):
            continue
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = mimetypes.guess_type(attfil)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with open(attfil, 'rb') as fp:
            emsg.add_attachment(fp.read(),
                                maintype=maintype,
                                subtype=subtype,
                                filename=attfil)
    return emsg

# ==============
#  MAIN PROGRAM
# ==============
def main():
    # PARSE OPTIONS
    opts = parseopt()
    # CREATE MESSAGE
    emsg = emailmsg(sbj=opts.sbj, msg=opts.msg,
                    fro=SMTP_DATA.get('MAIL'), to=opts.to, cc=opts.cc, bcc=opts.bcc,
                    att=opts.att)
    if opts.vrb >= 1:
        print(emsg)
    if opts.dry:
        sys.exit()
    # SEND MESSAGE
    with smtplib.SMTP_SSL(SMTP_DATA.get('SERVER'), SMTP_DATA.get('PORT')) as server:
        server.login(SMTP_DATA.get('MAIL'), SMTP_DATA.get('PASSWD'))
        try:
            server.send_message(emsg)
            if opts.vrb >= 1:
               print('Message successfully sent')
        except:
            errore('Failed to send message')
    sys.exit()

# ===========
#  MAIN CALL
# ===========
if __name__ == '__main__':
    main()
