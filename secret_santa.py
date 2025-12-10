from dotenv import load_dotenv
import os
import random
import smtplib
import ssl
from pathlib import Path
from email.message import EmailMessage
import argparse
import sys

# Ruta del .env: misma carpeta que este archivo .py
parent = Path(__file__).resolve().parent

# CLI
parser = argparse.ArgumentParser(
    description="Send Secret Santa emails or preview them (dry-run).")
parser.add_argument("-n", "--dry-run", action="store_true",
                    help="Print emails instead of sending them")
parser.add_argument(
    "--env-file", help="Path to .env file (overrides default names)")
parser.add_argument("--sender", default=os.getenv("SENDER_EMAIL", "shulibel0@gmail.com"),
                    help="Sender email address (default from SENDER_EMAIL env or fallback)")
parser.add_argument("-c", "--confirm", action="store_true",
                    help="Ask for interactive confirmation before sending emails")
parser.add_argument("--test-connect", action="store_true",
                    help="Test SMTP login (no emails sent)")
parser.add_argument("--debug-smtp", action="store_true",
                    help="Enable SMTP debug output (prints SMTP protocol conversation)")
args = parser.parse_args()

# DRY_RUN can come from CLI or environment
dry_run_env = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")
DRY_RUN = args.dry_run or dry_run_env

# Determine which env file to load
if args.env_file:
    env_path = Path(args.env_file)
else:
    env_path = parent / ".env"
    alt_env = parent / "secret_santa.env"
    if not env_path.exists() and alt_env.exists():
        env_path = alt_env
load_dotenv(dotenv_path=env_path)

print("DEBUG env_path:", env_path)
print("DEBUG env_exists:", env_path.exists())


def test_smtp_connect(sender, password):
    if not password:
        print("ERROR: 'password' not set in environment.")
        return False
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            if getattr(args, 'debug_smtp', False):
                server.set_debuglevel(1)
            server.login(sender, password)
        print("SMTP connect: OK (login succeeded)")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print("SMTP auth error:", e)
        print("Hint: For Gmail, create an App Password if your account has 2FA.")
        return False
    except Exception as e:
        print("SMTP connection error:", e)
        return False


def send_email(sender, receiver, recipient):
    body_text = f"Hola! Tu amigo invisible es: {recipient}\n¡Feliz Navidad!"

    # Build a proper MIME message with UTF-8
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "Tu Regalo de tu Amigo Invisible 🎁"
    msg.set_content(body_text, charset="utf-8")

    # If DRY_RUN is enabled, just print the message instead of sending it
    if DRY_RUN:
        print("----- DRY RUN: email preview -----")
        print(f"From: {msg['From']}")
        print(f"To: {msg['To']}")
        print(msg.get_content())
        print("----------------------------------")
        return True

    password = os.getenv("password")
    print("DEBUG: password present?", bool(password))

    if password is None:
        print("ERROR: No se encontró la variable 'password'. Revisá tu archivo .env")
        return False

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            if getattr(args, 'debug_smtp', False):
                server.set_debuglevel(1)
            server.login(sender, password)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        print("SMTP auth error:", e)
        print(
            "Hint: Gmail usually requires an app password (with 2FA) or OAuth. See README.")
        return False
    except smtplib.SMTPException as e:
        print("SMTP error sending to", receiver, "->", e)
        return False
    except Exception as e:
        print("Unexpected error sending to", receiver, "->", e)
        return False

    return True


names_and_emails = [
    ["Matias", "miqueipo16@gmail.com"],
    ["Clara", "claragena4@gmail.com"],
    ["Giuliana", "shulibel0@gmail.com"],
]

if len(names_and_emails) <= 1:
    print("Se necesitan al menos dos participantes para el Amigo Invisible.")
    quit()

# Shuffle the participants so the pairing is random and keeps names/emails together
random.shuffle(names_and_emails)

# If user requested confirmation, prompt before sending (only when not dry-run)
if args.confirm and not DRY_RUN:
    try:
        prompt = input(
            f"About to send {len(names_and_emails)} emails. Type 'yes' to proceed: ").strip().lower()
    except EOFError:
        print("No input available. Cancelling send.")
        sys.exit(1)
    if prompt not in ("yes", "y", "si", "s"):
        print("Cancelled by user. No emails were sent.")
        sys.exit(0)

# If user requested a test connect, do it and exit
if args.test_connect:
    pwd = os.getenv("password")
    ok = test_smtp_connect(args.sender, pwd)
    sys.exit(0 if ok else 1)

successes = 0
failures = []
for i in range(len(names_and_emails)):
    receiver_email = names_and_emails[i][1]
    recipient_name = names_and_emails[(i + 1) % len(names_and_emails)][0]
    ok = send_email(args.sender, receiver_email, recipient_name)
    if ok:
        successes += 1
    else:
        failures.append(receiver_email)

print(
    f"✅ Intentos: {successes} enviados correctamente, {len(failures)} fallos.")
if failures:
    print("Correos fallidos para:")
    for f in failures:
        print(" -", f)

