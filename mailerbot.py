#!/usr/bin/env python3
"""
MailerBot - Bot to send personalized job application emails
Author : OxoGhost01
Usage  : python mailerbot.py --csv example.csv --cv CV.pdf --provider proton --dry-run
"""

import argparse
import csv
import smtplib
import ssl
import sys
import time
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

# ── Configuration providers ───────────────────────────────────────────────────

PROVIDERS = {
    "proton": {
        "host": "127.0.0.1",
        "port": 1025,
        "ssl_verify": False,
    },
    "gmail": {
        "host": "smtp.gmail.com",
        "port": 587,
        "ssl_verify": True,
    },
}

GITHUB_REPO = "https://github.com/YOUR_HANDLE"

SENDER_INFO = {
    "proton": {
        "name":    "Firstname LASTNAME",
        "email":   "you@proton.me",
        "phone":   "+XX x xx xx xx xx",
        "website": "yourwebsite.dev",
        "github":  GITHUB_REPO,
    },
    "gmail": {
        "name":    "Firstname LASTNAME",
        "email":   "you@gmail.com",
        "phone":   "+XX x xx xx xx xx",
        "website": "yourwebsite.dev",
        "github":  GITHUB_REPO,
    },
}

SUBJECT_TEMPLATE = "Candidature spontanée – [Your title]"

# ── Templates ─────────────────────────────────────────────────────────────────

LETTER_TEMPLATE = """\
Objet : [Your subject line]

{civilite}{contact_name}

[Your cover letter here. Available variables:
  {company_name}   → injected from CSV
  {sender_name}    → from SENDER_INFO
  {sender_email}   → from SENDER_INFO
  {sender_phone}   → from SENDER_INFO
  {sender_website} → from SENDER_INFO
  {website}        → from SENDER_INFO
  {github}         → from SENDER_INFO
  {github_repo}    → from SENDER_INFO
]

Best regards,

{sender_name}
{sender_email}
{sender_phone}
{sender_website}

---
This email was sent via a custom application bot.
Source code available on GitHub: {github_repo}
"""

LETTER_TEMPLATE_HTML = """\
<html><body style="font-family: Arial, sans-serif; font-size: 14px; color: #1e1030; max-width: 680px;">

<p>{civilite}{contact_name}</p>

<p>[Your cover letter here in HTML. Same variables as above.]</p>

<p>Best regards,</p>

<p>
  <strong>{sender_name}</strong><br>
  {sender_email}<br>
  {sender_phone}<br>
  <a href="https://{sender_website}">{sender_website}</a>
</p>

<hr style="border: none; border-top: 1px solid #e9d5ff; margin-top: 24px;">
<p style="font-size: 12px; color: #94a3b8;">
  This email was sent via a custom application bot.<br>
  Source code available on GitHub:
  <a href="{github_repo}" style="color: #7e22ce;">{github_repo}</a>
</p>

</body></html>
"""

# ── CSV ───────────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = {"company_name", "email"}

def load_companies(csv_path: str) -> list[dict]:
    companies = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]
        missing = REQUIRED_FIELDS - set(reader.fieldnames)
        if missing:
            print(f"[ERROR] Missing columns : {missing}")
            sys.exit(1)
        for i, row in enumerate(reader, start=2):
            row = {k.strip().lower(): v.strip() for k, v in row.items()}
            if not row.get("email"):
                print(f"[WARN] Lign {i} ignored : email empty.")
                continue
            companies.append(row)
    return companies

# ── Mail builder ──────────────────────────────────────────────────────────────

def build_greeting(contact_name: str) -> tuple[str, str]:
    name = contact_name.strip() if contact_name else ""
    if not name or name.lower() in ("none", ""):
        return "Mrs, Mr,", ""
    return "Mrs, Mr ", name + ","

def build_email(company: dict, cv_path: str, sender: dict) -> MIMEMultipart:
    civilite, cname = build_greeting(company.get("contact_name", ""))

    fmt = dict(
        civilite        = civilite,
        contact_name    = cname,
        company_name    = company["company_name"],
        sender_name     = sender["name"],
        sender_email    = sender["email"],
        sender_phone    = sender["phone"],
        sender_website  = sender["website"],
        website         = sender["website"],
        github          = sender["github"],
        github_repo     = sender["github"],
    )

    msg = MIMEMultipart("alternative")
    msg["From"]    = formataddr((sender["name"], sender["email"]))
    msg["To"]      = company["email"]
    msg["Subject"] = SUBJECT_TEMPLATE

    msg.attach(MIMEText(LETTER_TEMPLATE.format(**fmt),      "plain", "utf-8"))
    msg.attach(MIMEText(LETTER_TEMPLATE_HTML.format(**fmt), "html",  "utf-8"))

    cv_bytes = Path(cv_path).read_bytes()
    attachment = MIMEApplication(cv_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename="CV-firstname-LASTNAME.pdf")
    msg.attach(attachment)

    return msg

# ── SMTP sender ───────────────────────────────────────────────────────────────

def send_email(msg: MIMEMultipart, sender: dict, password: str,
               provider_cfg: dict, dry_run: bool) -> bool:
    if dry_run:
        print(f"  [DRY-RUN] Would be sent to : {msg['To']}")
        print(f"  Sujet  : {msg['Subject']}")
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                print("  --- Corps (extrait) ---")
                print(part.get_payload(decode=True).decode("utf-8")[:400])
                print("  [...]")
                break
        return True

    try:
        context = ssl.create_default_context()
        if not provider_cfg["ssl_verify"]:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        with smtplib.SMTP(provider_cfg["host"], provider_cfg["port"]) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(sender["email"], password)
            server.sendmail(sender["email"], msg["To"], msg.as_string())
        return True
    except Exception as e:
        print(f"  [SMTP ERROR] {e}")
        return False

# ── Main ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Personalized email bot")
    p.add_argument("--csv",      required=True, help="Path to the CSV file")
    p.add_argument("--cv",       required=True, help="Path to the CV (PDF)")
    p.add_argument("--provider", choices=["proton", "gmail"], default="proton",
                   help="Provider SMTP : proton (default) or gmail")
    p.add_argument("--delay",    type=float, default=3.0,
                   help="Delay between each send in seconds (default: 3)")
    p.add_argument("--dry-run",  action="store_true",
                   help="Preview mode, no emails sent")
    p.add_argument("--limit",    type=int, default=None,
                   help="Limit the number of sends (useful for testing)")
    return p.parse_args()


def main():
    args = parse_args()

    if not Path(args.csv).exists():
        print(f"[ERROR] No CSV found : {args.csv}"); sys.exit(1)
    if not Path(args.cv).exists():
        print(f"[ERROR] No CV found : {args.cv}"); sys.exit(1)

    provider_cfg = PROVIDERS[args.provider]
    sender       = SENDER_INFO[args.provider]

    print(f"Provider    : {args.provider.upper()} ({provider_cfg['host']}:{provider_cfg['port']})")
    print(f"Sender  : {sender['email']}")

    password = ""
    if not args.dry_run:
        import getpass
        label = "SMTP password" if args.provider == "proton" else "Gmail App Password"
        password = getpass.getpass(f"{label} : ")

    companies = load_companies(args.csv)
    total = len(companies) if args.limit is None else min(args.limit, len(companies))

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''} sending {total} entreprise(s)...\n")

    sent_ok = sent_err = 0
    log_rows = []

    for i, company in enumerate(companies[:total], start=1):
        print(f"[{i}/{total}] {company['company_name']} <{company['email']}>")
        msg = build_email(company, args.cv, sender)
        ok  = send_email(msg, sender, password, provider_cfg, args.dry_run)

        status = "OK" if ok else "ERREUR"
        sent_ok += ok; sent_err += not ok
        log_rows.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "company":   company["company_name"],
            "email":     company["email"],
            "provider":  args.provider,
            "status":    status,
        })

        if i < total:
            time.sleep(args.delay)

    print(f"\n{'='*50}")
    print(f"Done : {sent_ok} sent, {sent_err} errors")

    log_path = f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "company", "email", "provider", "status"])
        writer.writeheader()
        writer.writerows(log_rows)
    print(f"Log saved : {log_path}")


if __name__ == "__main__":
    main()
