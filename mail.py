#!/usr/bin/env python3

#
# Send email from command line
#

# =========
#  MODULES
# =========
# Basic modules
import os  # OS interface: os.getcwd(), os.chdir('dir'), os.system('mkdir dir')
import platform  # Computer info
import sys  # System-specific functions: sys.argv(), sys.stderr.write()
import argparse  # commandline argument parsers

# To send the email
import smtplib  # To send emails
from email.message import EmailMessage
import mimetypes  # Handle file types over Internet

# encryption
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from pathlib import Path
import base64
import getpass
import json

# ==============
#  PROGRAM DATA
# ==============
AUTHOR = "Franco Egidi"
VERSION = "2026.30.03"
PROGNAME = os.path.basename(sys.argv[0])
HOSTNAME = platform.node()
USER = os.getenv("USER", "unknown")

# ============
#  ENCRYPTION
# ============
SCRIPT_DIR = Path(__file__).resolve().parent
SECRET_FILE = SCRIPT_DIR / ".config" / "mail" / "passkey.json"


def derive_fernet_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    key = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(key)

def load_email(secret_file: Path = SECRET_FILE) -> str:
    if not secret_file.exists():
        raise FileNotFoundError(f"Secret file not found: {secret_file}")

    data = json.loads(secret_file.read_text(encoding="utf-8"))

    try:
        email = data["email"]
    except KeyError as exc:
        raise ValueError(f"Missing email field in secret file: {exc}") from exc

    return email

def load_passkey(secret_file: Path = SECRET_FILE) -> str:
    if not secret_file.exists():
        raise FileNotFoundError(f"Secret file not found: {secret_file}")

    data = json.loads(secret_file.read_text(encoding="utf-8"))

    try:
        salt = base64.b64decode(data["salt"])
        token = data["token"].encode("ascii")
    except KeyError as exc:
        raise ValueError(f"Missing field in secret file: {exc}") from exc

    unlock_password = getpass.getpass("Unlock password: ")
    fernet_key = derive_fernet_key(unlock_password, salt)

    try:
        passkey = Fernet(fernet_key).decrypt(token).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Wrong password or corrupted secret file.") from exc

    return passkey


# ==========
#  DEFAULTS
# ==========
SMTP_DATA = {
    "SERVER": "smtp.gmail.com",
    "PORT": 465,
}
SIGNED = f"Message from {USER}@{HOSTNAME}"

# =================
#  PARSING OPTIONS
# =================
def parseopt(args=None):
    """Parse options for email message"""
    parser = argparse.ArgumentParser(prog=PROGNAME, description="Send email from the command line via Gmail SMTP.")

    parser.add_argument("-to", "--to", nargs="*", default=[], help="Recipient addresses")
    parser.add_argument("-cc", nargs="*", default=[], help="CC addresses")
    parser.add_argument("-bcc", nargs="*", default=[], help="BCC addresses")
    parser.add_argument("-s", "--subject", dest="sbj", default="", help="Mail subject")
    parser.add_argument(
        "-m", "--msg", dest="msg", default="", help="Email body as text, or path to a text file",
    )
    parser.add_argument("-a", "--att", nargs="+", default=[], help="Attachments")
    parser.add_argument("-v", "--verbose", dest="vrb", action="count", default=0, help="Verbose mode")
    parser.add_argument("--dry", action="store_true", default=False, help="Build message but do not send")

    opts = parser.parse_args(args)
    # Check options
    alladdr = opts.to + opts.cc + opts.bcc
    if not alladdr and not opts.msg and not opts.att and not opts.sbj and not opts.dry:
        parser.print_help()
        raise Exception("Must include at least one option")
    if not opts.sbj:
        opts.sbj = SIGNED

    return opts


# ================
#  WORK FUNCTIONS
# ================
def resolve_body(msg: str) -> str:
    if not msg:
        return ""

    msg_path = Path(msg).expanduser()
    if msg_path.is_file():
        return msg_path.read_text(encoding="utf-8")

    return msg

def build_message(sbj="", msg="", fro="", to=None, cc=None, att=None):
    """Create email message object"""
    # Restore defaults to mutable empty lists
    if to is None:
        to = []
    if cc is None:
        cc = []
    if att is None:
        att = []
    # Create message object
    emsg = EmailMessage()
    # Assign fields
    emsg["Subject"] = sbj
    emsg["To"] = ", ".join(to)
    emsg["From"] = fro
    if cc: emsg["Cc"] = ", ".join(cc)
    # Body
    body = resolve_body(msg)
    # Subject
    if sbj != SIGNED:
        emsg.set_content(f"{body}\n{SIGNED}" if body else SIGNED)
    else:
        emsg.set_content(body)
    # Attachments
    for attfil in att:
        path = Path(attfil).expanduser()
        if not path.is_file():
            continue
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = mimetypes.guess_type(attfil)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = "application/octet-stream"

        maintype, subtype = ctype.split("/", 1)

        with path.open("rb") as fp:
            emsg.add_attachment(fp.read(), maintype=maintype, subtype=subtype, filename=path.name)

    return emsg


def send_message(emsg: EmailMessage, fro: str, recipients, passkey: str, verbose: int = 0) -> None:
    with smtplib.SMTP_SSL(SMTP_DATA["SERVER"], SMTP_DATA["PORT"]) as server:
        server.login(fro, passkey)
        server.send_message(emsg, to_addrs=recipients)

    if verbose >= 1:
        print("Message successfully sent")


# ==============
#  MAIN PROGRAM
# ==============
def main(args=None) -> int:
    # PARSE ARGUMENTS
    opts = parseopt(args)
    # LOAD MAIL AND INCLUDE IT IN ADDRESSES
    email_addr = load_email()
    alladdr = opts.to + opts.cc + opts.bcc
    if not alladdr:
        opts.to.append(email_addr)
    elif email_addr not in alladdr:
        opts.bcc.append(email_addr)
    # CREATE MESSAGE
    emsg = build_message(
        sbj=opts.sbj, msg=opts.msg, fro=email_addr, to=opts.to, cc=opts.cc, att=opts.att
    )
    if opts.vrb >= 1:
        print(emsg)
    if opts.dry:
        return 0
    # SEND MESSAGE
    recipients = opts.to + opts.cc + opts.bcc
    # RETRIEVE PASSWORD
    try:
        passkey = load_passkey()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    try:
        send_message(emsg, fro=email_addr, recipients=recipients, passkey=passkey, verbose=opts.vrb)
    except Exception as exc:
        print(f"Error sending message: {exc}", file=sys.stderr)
        return 1

    return 0


# ===========
#  MAIN CALL
# ===========
if __name__ == "__main__":
    raise SystemExit(main())
