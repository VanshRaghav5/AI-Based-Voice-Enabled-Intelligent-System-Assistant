# ============================================================
#  OmniAssist AI - Email Configuration Guide
# ============================================================

## Quick Setup for Gmail (Recommended)

### Step 1: Get Gmail App Password
1. Visit: https://myaccount.google.com/apppasswords
2. Sign in to your Google account
3. Create new app password: "OmniAssist"
4. Copy the 16-character password (no spaces)

### Step 2: Set Environment Variables & Start Backend

```powershell
# Run these commands in PowerShell:
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USER = "your-email@gmail.com"
$env:SMTP_PASSWORD = "your16charapppassword"

# Then start the backend
cd "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"
python backend/api_service.py
```

---

## For Other Email Providers

### Outlook/Hotmail
```powershell
$env:SMTP_HOST = "smtp-mail.outlook.com"
$env:SMTP_PORT = "587"
$env:SMTP_USER = "your-email@outlook.com"
$env:SMTP_PASSWORD = "your-password"
```

### Yahoo Mail
```powershell
$env:SMTP_HOST = "smtp.mail.yahoo.com"
$env:SMTP_PORT = "587"
$env:SMTP_USER = "your-email@yahoo.com"
$env:SMTP_PASSWORD = "your-app-password"
```

Note: Yahoo also requires App Passwords for third-party apps

---

##  Testing Email

Once configured, test by saying:
- "send email to test@example.com saying hello world"
- "email yashjainworks@gmail.com with subject test and body testing email"

The system will ask for confirmation before sending!

---

## Troubleshooting

**"SMTP configuration missing" error:**
- Make sure you set ALL 4 environment variables before starting backend
- Variables only persist in the current PowerShell session
- Restart backend after setting variables

**Authentication failed:**
- Gmail: Use App Password, not regular password
- Check email/password are correct
- Ensure "Less secure app access" is enabled (if applicable)

**Connection timeout:**
- Check your internet connection
- Verify SMTP host and port are correct
- Some networks block SMTP port 587

---

## Permanent Configuration (Optional)

To make email settings permanent:

1. Create `.env` file in backend folder:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

2. Backend will auto-load these on startup
