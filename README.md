# MailerBot

A Python bot that sends personalized job application emails with your CV attached — built to automate spontaneous applications at scale.

Supports **Proton Mail** (via Bridge) and **Gmail** (via App Password).

---

## Features

- Sends personalized emails from a CSV list of companies
- Injects company name and contact name into the letter automatically
- Attaches your CV as PDF
- Sends both plain text and HTML versions of the email
- `--dry-run` mode to preview without sending
- `--limit` to cap the number of sends
- Logs every send to a timestamped CSV file
- Supports multiple SMTP providers via `--provider`

---

## Requirements

Python 3.10+, no external dependencies (stdlib only).

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/OxoGhost01/MailerBot
cd MailerBot
```

### 2. Configure your sender info

Edit the `SENDER_INFO` dict at the top of `mailerbot.py` :

```python
SENDER_INFO = {
    "proton": {
        "name":    "Your Name",
        "email":   "you@proton.me",
        "phone":   "+XX x xx xx xx xx",
        "website": "yourwebsite.dev",
        "github":  "https://github.com/yourhandle",
    },
    "gmail": {
        "name":    "Your Name",
        "email":   "you@gmail.com",
        ...
    },
}
```

### 3. Configure your SMTP provider

**Proton Mail** — install and run [Proton Bridge](https://proton.me/mail/bridge), then update `SMTP_PORT` in `PROVIDERS["proton"]` with the port shown in the Bridge UI (usually `1025` or `1143`).

**Gmail** — enable 2FA, then generate an [App Password](https://myaccount.google.com/apppasswords) (`Google Account → Security → 2-Step Verification → App Passwords`). Use this as your password when prompted.

### 4. Prepare your CSV

Use the provided `exemple.csv` as a template :

```csv
company_name,email,contact_name,notes
Acme Corp,jobs@acme.com,Marie Dupont,startup embedded Paris
Tech Labs,hr@techlabs.io,,open application
```

- `company_name` and `email` are **required**
- `contact_name` is optional — if provided, the greeting becomes `Madame, Monsieur Dupont,` instead of `Madame, Monsieur,`
- `notes` is ignored by the bot, for your own reference

### 5. Update the letter template

Edit `LETTER_TEMPLATE` and `LETTER_TEMPLATE_HTML` in `mailerbot.py` to match your own profile, projects, and availability.

Available template variables :

| Variable | Description |
|---|---|
| `{company_name}` | Injected from CSV |
| `{civilite}` | Auto-generated greeting |
| `{contact_name}` | Injected from CSV (empty if none) |
| `{sender_name}` | From `SENDER_INFO` |
| `{sender_email}` | From `SENDER_INFO` |
| `{sender_phone}` | From `SENDER_INFO` |
| `{website}` | From `SENDER_INFO` |
| `{github}` | From `SENDER_INFO` |

---

## Usage

```bash
# Dry-run — preview without sending
python mailerbot.py --csv example.csv --cv CV.pdf --dry-run

# Send via Proton Bridge
python mailerbot.py --csv example.csv --cv CV.pdf --provider proton

# Send via Gmail
python mailerbot.py --csv example.csv --cv CV.pdf --provider gmail

# Test on first entry only
python mailerbot.py --csv example.csv --cv CV.pdf --limit 1

# Custom delay between sends (default: 3s)
python mailerbot.py --csv example.csv --cv CV.pdf --delay 5
```

### All flags

| Flag | Default | Description |
|---|---|---|
| `--csv` | required | Path to companies CSV |
| `--cv` | required | Path to CV PDF |
| `--provider` | `proton` | `proton` or `gmail` |
| `--delay` | `3.0` | Seconds between sends |
| `--dry-run` | off | Preview mode, no emails sent |
| `--limit` | none | Cap number of sends |

---

## Output

Each run generates a log file :

```
log_20260511_143022.csv
```

```csv
timestamp,company,email,provider,status
2026-05-11T14:30:22,Acme Corp,jobs@acme.com,proton,OK
2026-05-11T14:30:25,Tech Labs,hr@techlabs.io,proton,OK
```

---

## File structure

```
candidature-bot/
├── mailerbot.py # Main bot
├── exemple.csv  # CSV template
├── LICENSE
└── README.md
```

---

## License

MIT - See [LICENSE](LICENSE)