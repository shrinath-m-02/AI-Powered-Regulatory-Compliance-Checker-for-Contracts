# 📧 Email Feature - Quick Reference

## ⚡ 60-Second Setup (Gmail)

### Step 1: Generate App Password
- Go to: https://myaccount.google.com/apppasswords
- Select Mail + Windows Computer
- Copy: `xxxx xxxx xxxx xxxx`

### Step 2: Create .env File
```env
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Analyzer
```

### Step 3: Restart Streamlit
```powershell
Get-Process streamlit | Stop-Process -Force
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

### Step 4: Test
- Go to ⚙️ Settings
- Enter test email
- Click 📤 Send Test Email

✅ Done!

---

## 📧 File Locations

| File | Purpose | Lines |
|------|---------|-------|
| `utils/email_notifier.py` | Email system | 271 |
| `.env` | Credentials | Custom |
| `.env.example` | Template | 46 |
| `streamlit_app.py` | UI integration | Modified |
| `EMAIL_SETUP_GUIDE.md` | Full guide | 450+ |
| `EMAIL_IMPLEMENTATION.md` | Technical docs | 400+ |

---

## 🎯 Key Features

| Feature | Status | Details |
|---------|--------|---------|
| Auto-send on analysis | ✅ Active | Sends when user completes analysis |
| HTML emails | ✅ Active | Beautiful formatted emails |
| Error handling | ✅ Active | Failures don't break UI |
| Test mode | ✅ Active | Send test emails in Settings |
| Multiple providers | ✅ Active | Gmail, Outlook, Yahoo, SendGrid |
| Credential storage | ✅ Active | Stored in `.env`, not in code |

---

## 🔌 Configuration Quick Link

```env
# Gmail (Recommended)
EMAIL_SENDER=your@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# Outlook
EMAIL_SENDER=your@outlook.com
EMAIL_SMTP_SERVER=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587

# Yahoo
EMAIL_SENDER=your@yahoo.com
EMAIL_SMTP_SERVER=smtp.mail.yahoo.com
EMAIL_SMTP_PORT=587

# SendGrid
EMAIL_SENDER=noreply@yourdomain.com
EMAIL_PASSWORD=SG.your_api_key
EMAIL_SMTP_SERVER=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
```

---

## 📊 Email Content

**Subject:** `📋 Contract Analysis Completed: [filename]`

**Contains:**
- ✅ Key clauses found
- ✅ Compliance issues (High/Medium/Low)
- ✅ Risk summary
- ✅ Link to analysis portal
- ✅ Next steps

---

## 🧪 Testing Checklist

- [ ] `.env` file created
- [ ] EMAIL_SENDER set
- [ ] EMAIL_PASSWORD set (App Password for Gmail)
- [ ] SMTP server configured
- [ ] Streamlit restarted
- [ ] Settings page shows ✅ configured
- [ ] Test email sent successfully
- [ ] Email appears in inbox
- [ ] HTML formatting looks good

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Not configured" | Create `.env` with EMAIL_SENDER/PASSWORD |
| Auth failed | Use App Password (Gmail), not regular password |
| Connection timeout | Check SMTP server/port are correct |
| Email to spam | Mark as not spam, check email reputation |
| Email not sent | Check terminal logs for errors |

---

## 🔐 Security

✅ Credentials in `.env` (not in code)
✅ Use `.gitignore` to exclude `.env`
✅ TLS/STARTTLS encryption
✅ No plaintext passwords in logs

---

## 📞 Documentation

- **Setup Guide:** `EMAIL_SETUP_GUIDE.md`
- **Technical Docs:** `EMAIL_IMPLEMENTATION.md`
- **Token Guide:** `TOKEN_OPTIMIZATION_GUIDE.md`

---

**Status:** ✅ Ready to use!

See `EMAIL_SETUP_GUIDE.md` for detailed instructions.
