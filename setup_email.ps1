# Email SMTP Configuration Setup
# Run this script to configure email sending for OmniAssist AI

$WorkspaceRoot = "D:\AI Based Voice Intelligent System\AI-Based-Voice-Enabled-Intelligent-System-Assistant"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "    OmniAssist AI - Email SMTP Configuration Setup    " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Write-Host "Select your email provider:" -ForegroundColor Yellow
Write-Host "  1. Gmail (recommended)"
Write-Host "  2. Outlook/Hotmail"
Write-Host "  3. Yahoo Mail"
Write-Host "  4. Custom SMTP Server"
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`nGmail Selected" -ForegroundColor Green
        $env:SMTP_HOST = "smtp.gmail.com"
        $env:SMTP_PORT = "587"
        
        Write-Host "`n⚠️  IMPORTANT: Gmail requires an App Password!" -ForegroundColor Yellow
        Write-Host "   1. Go to: https://myaccount.google.com/apppasswords" -ForegroundColor White
        Write-Host "   2. Sign in to your Google account" -ForegroundColor White
        Write-Host "   3. Create a new app password for 'OmniAssist'" -ForegroundColor White
        Write-Host "   4. Copy the 16-character password" -ForegroundColor White
        Write-Host ""
        
        $email = Read-Host "Enter your Gmail address (e.g., yourname@gmail.com)"
        $password = Read-Host "Enter your Gmail App Password (16 characters, no spaces)" -AsSecureString
        
        $env:SMTP_USER = $email
        # Convert secure string to plain text for environment variable
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
        $env:SMTP_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    }
    "2" {
        Write-Host "`nOutlook/Hotmail Selected" -ForegroundColor Green
        $env:SMTP_HOST = "smtp-mail.outlook.com"
        $env:SMTP_PORT = "587"
        
        $email = Read-Host "Enter your Outlook email address"
        $password = Read-Host "Enter your Outlook password" -AsSecureString
        
        $env:SMTP_USER = $email
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
        $env:SMTP_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    }
    "3" {
        Write-Host "`nYahoo Mail Selected" -ForegroundColor Green
        $env:SMTP_HOST = "smtp.mail.yahoo.com"
        $env:SMTP_PORT = "587"
        
        Write-Host "`n⚠️  Yahoo may require an App Password" -ForegroundColor Yellow
        
        $email = Read-Host "Enter your Yahoo email address"
        $password = Read-Host "Enter your Yahoo password/app password" -AsSecureString
        
        $env:SMTP_USER = $email
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
        $env:SMTP_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    }
    "4" {
        Write-Host "`nCustom SMTP Configuration" -ForegroundColor Green
        
        $env:SMTP_HOST = Read-Host "Enter SMTP server (e.g., smtp.example.com)"
        $env:SMTP_PORT = Read-Host "Enter SMTP port (usually 587 or 465)"
        $env:SMTP_USER = Read-Host "Enter your email address"
        $password = Read-Host "Enter your password" -AsSecureString
        
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
        $env:SMTP_PASSWORD = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    }
    default {
        Write-Host "`n❌ Invalid choice. Exiting..." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n✅ SMTP Configuration Set:" -ForegroundColor Green
Write-Host "   Host: $env:SMTP_HOST" -ForegroundColor White
Write-Host "   Port: $env:SMTP_PORT" -ForegroundColor White
Write-Host "   User: $env:SMTP_USER" -ForegroundColor White
Write-Host "   Password: ********" -ForegroundColor White
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Starting OmniAssist Backend with Email Configuration..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📧 Email functionality is now enabled!" -ForegroundColor Green
Write-Host "   You can now send emails through the assistant." -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the backend" -ForegroundColor Yellow
Write-Host ""

# Start the backend with environment variables
Set-Location -Path $WorkspaceRoot
python backend/api_service.py
