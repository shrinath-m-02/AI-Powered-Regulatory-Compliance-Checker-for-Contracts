# 📧 Email Notification Setup Guide

## Overview

The Contract Compliance Analyzer now includes automatic email notifications when contract analysis completes. This guide shows you how to configure it.

---

## ✨ Features

- ✅ **Automatic Notifications** - Email sent when analysis completes
- ✅ **Beautiful HTML Emails** - Professional formatted results
- ✅ **Summary Included** - Key clauses and compliance issues in email
- ✅ **Safe & Secure** - Credentials stored in `.env`, never in code
- ✅ **Error Handling** - Email failures don't break the UI
- ✅ **Test Mode** - Send test emails before going live

---

## 🚀 Quick Setup (Gmail - 5 minutes)

### Step 1: Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Find "2-Step Verification" and enable it
3. Follow Google's prompts to verify your phone

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select **Mail** from first dropdown
3. Select **Windows Computer** from second dropdown
4. Click **Generate**
5. Copy the 16-character password shown (e.g., `xxxx xxxx xxxx xxxx`)

### Step 3: Update `.env` File
1. Open `.env` in your project root (or create one)
2. Add these lines:

```env
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Analyzer
```

Replace:
- `your_email@gmail.com` with your actual Gmail address
- `xxxx xxxx xxxx xxxx` with the 16-char password you copied

### Step 4: Restart Streamlit
```powershell
# Kill existing Streamlit process
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force

# Start it again
cd "Your\Project\Path"
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

### Step 5: Test Email (in Settings page)
1. Open Streamlit app at http://localhost:8503
2. Go to **⚙️ Settings** page
3. Enter test email address
4. Click **📤 Send Test Email**
5. Check your inbox (might be in Spam folder)

✅ Done! Emails will now be sent when you upload contracts.

---

## 🔧 Advanced Setup (Other Email Providers)

### Outlook / Hotmail

```env
EMAIL_SENDER=your_email@outlook.com
EMAIL_PASSWORD=your_outlook_password
EMAIL_SMTP_SERVER=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Analyzer
```

**Note:** If you have 2FA enabled, use an App Password instead of your regular password.

### Yahoo Mail

1. Enable 2-Factor Authentication (similar to Gmail)
2. Generate App Password at: https://login.yahoo.com/account/security
3. Use this in `.env`:

```env
EMAIL_SENDER=your_email@yahoo.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_SMTP_SERVER=smtp.mail.yahoo.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Analyzer
```

### Outlook 365 / Microsoft Exchange

```env
EMAIL_SENDER=your_email@company.com
EMAIL_PASSWORD=your_password
EMAIL_SMTP_SERVER=smtp.office365.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Analyzer
```

### SendGrid (Transactional Email)

If you're using SendGrid API (recommended for production):

1. Create SendGrid account at: https://sendgrid.com
2. Create an API Key at: https://app.sendgrid.com/settings/api_keys
3. Configure `.env`:

```env
EMAIL_SENDER=noreply@yourdomain.com
EMAIL_PASSWORD=SG.xxxxxxxxxxxxxxxxxx_your_api_key
EMAIL_SMTP_SERVER=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Analyzer
```

**Note:** Use `apikey` as the username (it's handled internally)

### Custom SMTP Server

If you have your own SMTP server:

```env
EMAIL_SENDER=your_email@yourdomain.com
EMAIL_PASSWORD=your_password
EMAIL_SMTP_SERVER=mail.yourdomain.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Analyzer
```

Common ports:
- **587** - TLS (most common, recommended)
- **25** - SMTP (older, less common)
- **465** - SSL (some servers)

---

## 🧪 Testing

### In Streamlit UI
1. Navigate to **⚙️ Settings** page
2. Fill in test email address
3. Click **📤 Send Test Email**
4. Check your inbox (including Spam folder)

### Via Python Command Line

```python
from utils.email_notifier import EmailNotifier

notifier = EmailNotifier()

# Create sample analysis
sample_analysis = {
    'key_clauses': ['Confidentiality', 'Non-Compete', 'IP Rights'],
    'compliance_issues': [
        {'title': 'Missing Data Protection', 'risk_level': 'High', 'reason': 'No GDPR mention'},
        {'title': 'Vague Terms', 'risk_level': 'Medium', 'reason': 'Unclear deadlines'},
    ]
}

# Send test email
success, message = notifier.send_notification(
    recipient_email="your_test@gmail.com",
    contract_name="Test Contract",
    analysis_result=sample_analysis,
    test_mode=False
)

print(message)
```

---

## 📋 Email Content

When analysis completes, users receive an email with:

### Subject Line
```
📋 Contract Analysis Completed: [Contract Name]
```

### Email Contents
- ✅ Summary of key clauses found
- ⚠️ Compliance issues by risk level
- 📊 Issue counts (High, Medium, Low)
- 🔗 Link to full analysis portal
- 📝 Next steps for review

### Example Email Structure
```
HEADER
Contract Analysis Complete
Contract: business_contract.txt
Date: 2025-12-09

METRICS
Key Clauses: 5
Issues Found: 8
High Risk: 2

SUMMARY
High Risk: 2 | Medium Risk: 3 | Low Risk: 3

CLAUSES (top 10)
1. Confidentiality Clause
2. Non-Compete Agreement
...

ISSUES (top 5)
1. Missing Data Protection
   Risk: High
   Reason: No GDPR/CCPA language
...

NEXT STEPS
1. Log in to portal
2. Review full analysis
3. Check recommendations
4. Ask questions in chatbot

FOOTER
Automated from Contract Compliance Analyzer
```

---

## 🔐 Security Best Practices

### ✅ DO:
- ✅ Store credentials in `.env` file
- ✅ Never commit `.env` to version control
- ✅ Use App Passwords when available (Gmail, Yahoo)
- ✅ Use `.gitignore` to exclude `.env`
- ✅ Rotate passwords periodically
- ✅ Use SMTP with TLS (port 587)

### ❌ DON'T:
- ❌ Hardcode credentials in Python files
- ❌ Share `.env` files via email/chat
- ❌ Commit `.env` to git
- ❌ Use weak passwords
- ❌ Disable security features (2FA, etc.)
- ❌ Send emails with sensitive data unencrypted

---

## 🆘 Troubleshooting

### Error: "Authentication failed"
**Cause:** Wrong email or password
**Solution:**
- Double-check email address
- Verify App Password is correct
- For Gmail: Use App Password, not regular password
- Test credentials by signing in manually

### Error: "Connection timeout"
**Cause:** Wrong SMTP server or port
**Solution:**
- Verify SMTP server address (no https://)
- Check port is correct (usually 587)
- Test by connecting from command line:
  ```powershell
  Test-NetConnection -ComputerName smtp.gmail.com -Port 587
  ```

### Error: "TLS error"
**Cause:** SMTP server doesn't support TLS on that port
**Solution:**
- Try port 465 (SSL) instead of 587
- Check provider's SMTP documentation
- Some servers need explicit TLS setup

### Email goes to Spam folder
**Cause:** Email authentication/reputation issue
**Solution:**
- Add SPF records to your domain (if using custom domain)
- Try with a smaller test email first
- Check spam folder for Gmail (sometimes filtered)

### "EmailNotifier not configured" message
**Cause:** `.env` file not properly set up
**Solution:**
- Verify `.env` exists in project root
- Check EMAIL_SENDER and EMAIL_PASSWORD are set
- Ensure no extra spaces around values:
  ```env
  # CORRECT
  EMAIL_SENDER=test@gmail.com
  
  # WRONG (spaces around =)
  EMAIL_SENDER = test@gmail.com
  ```
- Restart Streamlit after editing `.env`

---

## 📊 Usage Examples

### Automatic Notification (Happens Automatically)
When user uploads a contract and clicks "Analyze":
1. Analysis completes
2. Email notifier checks if email is configured
3. If user entered email → email is sent
4. User sees success message

### How to Access in Code
```python
from utils.email_notifier import EmailNotifier

# Initialize
notifier = EmailNotifier()

# Check if configured
if notifier.is_email_enabled():
    print("Email is configured")
    
    # Send notification
    success, message = notifier.send_notification_safe(
        recipient_email="user@example.com",
        contract_name="contract.pdf",
        analysis_result=analysis
    )
    
    if success:
        st.success(message)
    else:
        st.warning(message)
```

---

## 🔄 Workflow

```
User Uploads Contract
        ↓
User Enters Email (optional)
        ↓
User Clicks "Analyze"
        ↓
RAG System Analyzes
        ↓
Results Saved to Database
        ↓
Email Service Checks
        ├─ If configured & email provided
        │  └─ Send notification
        └─ If not configured
           └─ Skip (no error)
        ↓
UI Shows Success
```

---

## 📧 Email Customization

### Modify Email Content
Edit `utils/email_notifier.py`:
- `_create_html_content()` - Controls HTML formatting
- Email subject line at line ~89
- Issue limit (currently 5) at various locations
- Colors and styling in CSS

### Add Custom Fields
```python
# In _create_html_content() method
custom_info = f"Analysis ID: {analysis.get('id', 'N/A')}"
# Add to html_content and text_content
```

---

## 🚀 Next Steps

1. ✅ Set up email using this guide
2. ✅ Test with Settings page
3. ✅ Upload a contract and check email
4. ✅ Customize email template if needed
5. ✅ Deploy with confidence!

---

## 📞 Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review logs in terminal/console
3. Test credentials manually with email client
4. Check `response_cache.db` logs for details
5. Verify `.env` file syntax

Happy emailing! 📧✨
