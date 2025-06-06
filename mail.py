#!/usr/bin/env python3

#
# Send email from command line
#

# =========
#  MODULES
# =========
import os  # OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import platform  # Computer info
import sys  # System-specific functions: sys.argv(), sys.exit(), sys.stderr.write()
import argparse  # commandline argument parsers

# import typing  # Support for type hints
import smtplib  # To send emails
import email  # To send emails
import mimetypes  # Handle file types over Internet
from feutils import errore, USER  # My generic functions

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = "Franco Egidi (franco.egidi@gmail.it)"
VERSION = "2020.09.20"
PROGNAME = os.path.basename(sys.argv[0])
HOSTNAME = platform.node()

# ==========
#  DEFAULTS
# ==========
SMTP_DATA = {
    "MAIL": "franco.egidi@gmail.com",
    "PASSWD": "pvxk dgia dpwc gvox",
    "SERVER": "smtp.gmail.com",
    "PORT": 465,
}
SIGNED = f"Message from {USER}@{HOSTNAME}"
FOOTER = f"""\
<!DOCTYPE html>
  <html>
    <head></head>
    <body><TT>
      <p>{"-"*len(SIGNED)}</p>
      <p>{SIGNED}</p>
    </TT></body>
  </html>
  """

# =================
#  BASIC FUNCTIONS
# =================


# =================
#  PARSING OPTIONS
# =================
def parseopt(args=None):
    """Parse options"""
    # Create parser
    parser = argparse.ArgumentParser(prog=PROGNAME, description="Command-line option parser")
    # Optional arguments
    parser.add_argument("-to", "--to", nargs="*", dest="to", action="store", default=list(), help="Specify recepients")
    parser.add_argument("-cc", nargs="*", dest="cc", action="store", default=list(), help="Carbon Copy addresses")
    parser.add_argument(
        "-bcc", nargs="*", dest="bcc", action="store", default=list(), help="Blind Carbon Copy addresses"
    )
    parser.add_argument("-s", "--subject", type=str, dest="sbj", action="store", default="", help="Mail subject")
    parser.add_argument(
        "-m", "--msg", type=str, dest="msg", action="store", default="", help="Email body as string or text file"
    )
    parser.add_argument("-a", "--att", nargs="+", dest="att", action="store", default=list(), help="Attachments")
    parser.add_argument("-v", "--verbose", dest="vrb", action="count", default=0, help="Verbose mode")
    parser.add_argument("--dry", dest="dry", action="store_true", default=False, help=argparse.SUPPRESS)
    opts = parser.parse_args(args)
    # Check options
    for attfil in opts.att:
        if not os.path.isfile(attfil):
            errore(f"File {attfil} not found")
    alladdr = opts.to + opts.cc + opts.bcc
    if not alladdr and not opts.msg and not opts.att and not opts.sbj:
        parser.print_help()
        errore()
    if not opts.sbj:
        opts.sbj = SIGNED
    if not alladdr:
        opts.to.append(SMTP_DATA.get("MAIL"))
    elif SMTP_DATA.get("MAIL") not in alladdr:
        opts.bcc.append(SMTP_DATA.get("MAIL"))
    return opts


# ================
#  WORK FUNCTIONS
# ================
def emailmsg(sbj="", msg="", fro="", to=None, cc=None, bcc=None, att=None):
    """Create email message object"""
    # Restore defaults to mutable empty lists
    if to is None:
        to = []
    if cc is None:
        cc = []
    if bcc is None:
        bcc = []
    if att is None:
        att = []
    # Create message object
    emsg = email.message.EmailMessage()
    # Assign fields
    emsg["Subject"] = sbj
    emsg["To"] = ", ".join(to)
    emsg["From"] = fro
    emsg["Cc"] = ", ".join(cc)
    emsg["Bcc"] = ", ".join(bcc)
    # Body
    try:
        with open(msg, "r") as filobj:
            body = filobj.read()
    except Exception:
        body = msg
    if sbj != SIGNED:
        emsg.set_content(body + "\n" + SIGNED)
    else:
        emsg.set_content(body)
    # Attachments
    for attfil in att:
        if not os.path.isfile(attfil):
            continue
        filnam, filext = os.path.splitext(attfil)
        if filext == ".com":
            import shutil

            renamed = f"{filnam}.gjf"
            shutil.copy(attfil, renamed)
            attfil = renamed
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = mimetypes.guess_type(attfil)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(attfil, "rb") as fp:
            emsg.add_attachment(fp.read(), maintype=maintype, subtype=subtype, filename=attfil)
    return emsg


# ==============
#  MAIN PROGRAM
# ==============
def main(args=None):
    # PARSE ARGUMENTS
    opts = parseopt(args)
    # CREATE MESSAGE
    emsg = emailmsg(
        sbj=opts.sbj, msg=opts.msg, fro=SMTP_DATA.get("MAIL"), to=opts.to, cc=opts.cc, bcc=opts.bcc, att=opts.att
    )
    if opts.vrb >= 1:
        print(emsg)
    if opts.dry:
        return
    # SEND MESSAGE
    with smtplib.SMTP_SSL(SMTP_DATA.get("SERVER"), SMTP_DATA.get("PORT")) as server:
        server.login(SMTP_DATA.get("MAIL"), SMTP_DATA.get("PASSWD"))
        try:
            server.send_message(emsg)
            if opts.vrb >= 1:
                print("Message successfully sent")
        except Exception:
            errore("Failed to send message")
    sys.exit()


# ===========
#  MAIN CALL
# ===========
if __name__ == "__main__":
    main()
