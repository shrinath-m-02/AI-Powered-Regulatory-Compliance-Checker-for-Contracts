# 📧 Email Integration - Code Examples & API Reference

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Advanced Usage](#advanced-usage)
3. [Error Handling](#error-handling)
4. [Customization](#customization)
5. [Testing](#testing)

---

## Basic Usage

### Check if Email is Configured
```python
from utils.email_notifier import EmailNotifier

notifier = EmailNotifier()

if notifier.is_email_enabled():
    print("✅ Email notifications are configured")
else:
    print("❌ Email notifications not configured")
```

### Send Email Notification
```python
from utils.email_notifier import EmailNotifier

notifier = EmailNotifier()

# Prepare analysis results
analysis_result = {
    'key_clauses': [
        'Confidentiality Clause',
        'Non-Compete Agreement',
        'Intellectual Property Rights'
    ],
    'compliance_issues': [
        {
            'title': 'Missing Data Protection Clause',
            'risk_level': 'High',
            'reason': 'Contract lacks GDPR/CCPA compliance language'
        },
        {
            'title': 'Vague Termination Terms',
            'risk_level': 'Medium',
            'reason': 'Notice period not clearly specified'
        }
    ]
}

# Send notification
success, message = notifier.send_notification(
    recipient_email="user@example.com",
    contract_name="business_contract.txt",
    analysis_result=analysis_result
)

if success:
    print(message)  # ✅ Email notification sent to user@example.com
else:
    print(message)  # ❌ Error message
```

---

## Advanced Usage

### Safe Email Sending (Recommended for Streamlit)
```python
from utils.email_notifier import EmailNotifier
import streamlit as st

notifier = EmailNotifier()

# Use send_notification_safe() to prevent crashes
success, message = notifier.send_notification_safe(
    recipient_email=st.session_state.get('notification_email'),
    contract_name="contract.pdf",
    analysis_result=analysis_data
)

if success:
    st.success(message)
else:
    st.warning(message)  # Warning, not error
```

### Send with Custom Test Mode
```python
# Send in test mode (prints instead of sending)
success, message = notifier.send_notification(
    recipient_email="test@example.com",
    contract_name="Test Contract",
    analysis_result=sample_analysis,
    test_mode=True  # Prints email to console instead
)

print(message)  # ✅ Test mode: Email would be sent to test@example.com
```

### Conditional Email Sending
```python
from utils.email_notifier import EmailNotifier

notifier = EmailNotifier()

# Only send if configured AND email provided
if notifier.is_email_enabled():
    recipient = st.session_state.get('notification_email', '')
    
    if recipient:
        success, message = notifier.send_notification_safe(
            recipient,
            contract_name,
            analysis_result
        )
        st.session_state['email_status'] = message
```

---

## Error Handling

### Catch Specific Errors
```python
import smtplib
from utils.email_notifier import EmailNotifier

notifier = EmailNotifier()

try:
    success, message = notifier.send_notification(
        "user@example.com",
        "contract.pdf",
        analysis_data
    )
except smtplib.SMTPAuthenticationError:
    print("❌ Email or password incorrect")
except smtplib.SMTPException as e:
    print(f"❌ SMTP error: {str(e)}")
except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")
```

### Log Emails for Debugging
```python
import logging
from utils.email_notifier import EmailNotifier

# Enable logging to see all email operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

notifier = EmailNotifier()
success, message = notifier.send_notification_safe(...)

# Check logs:
# INFO - ✅ Email sent successfully to user@example.com
# WARNING - ⚠️ Warning: Email notification failed
# ERROR - ❌ Error sending email: ...
```

---

## Customization

### Modify Email Subject
**File:** `utils/email_notifier.py` (line ~89)

```python
# Current:
message["Subject"] = f"📋 Contract Analysis Completed: {contract_name}"

# Custom:
message["Subject"] = f"Your Contract Review: {contract_name}"
```

### Customize HTML Template
**File:** `utils/email_notifier.py` (method: `_create_html_content()`)

```python
# Change header gradient color
# OLD:
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

# NEW:
background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
```

### Add Company Logo
**File:** `utils/email_notifier.py` (in HTML section)

```python
html_content += f"""
<div class="header">
    <img src="https://your-company.com/logo.png" 
         style="max-width: 150px; margin: 10px auto;" />
    <h1>Contract Analysis Complete</h1>
</div>
"""
```

### Limit Number of Issues Shown
**File:** `utils/email_notifier.py` (line ~70)

```python
# Current (shows 5 issues):
for idx, issue in enumerate(compliance_issues[:5], 1):

# Change to 10:
for idx, issue in enumerate(compliance_issues[:10], 1):

# Change to all:
for idx, issue in enumerate(compliance_issues, 1):
```

### Add Custom Analysis Fields
**File:** `utils/email_notifier.py` (in `_create_html_content()`)

```python
# Add to method signature:
def _create_html_content(
    self,
    contract_name: str,
    analysis_result: Dict,
    recipient_email: str,
    custom_department: str = None  # NEW
) -> Tuple[str, str]:

# Extract and use:
department = custom_department or "Legal"
html_content += f"<p>Department: {department}</p>"
```

---

## Testing

### Unit Test Example
```python
import unittest
from utils.email_notifier import EmailNotifier

class TestEmailNotifier(unittest.TestCase):
    
    def setUp(self):
        self.notifier = EmailNotifier()
    
    def test_is_configured(self):
        """Test if email is properly configured"""
        result = self.notifier.is_email_enabled()
        self.assertIsInstance(result, bool)
    
    def test_send_notification(self):
        """Test sending notification"""
        sample_analysis = {
            'key_clauses': ['Test Clause'],
            'compliance_issues': [
                {'title': 'Test', 'risk_level': 'High', 'reason': 'Test'}
            ]
        }
        
        success, message = self.notifier.send_notification(
            "test@example.com",
            "test.pdf",
            sample_analysis,
            test_mode=True
        )
        
        self.assertTrue(success)
        self.assertIn("Test mode", message)

if __name__ == '__main__':
    unittest.main()
```

### Integration Test
```python
# test_email_integration.py
import os
from utils.email_notifier import EmailNotifier
from utils.rag_helper import RAGAnalyzer

def test_full_workflow():
    """Test complete analysis + email flow"""
    
    # 1. Load and analyze contract
    analyzer = RAGAnalyzer()
    analyzer.setup()
    contract_text = analyzer.load_contract("test_contract.pdf")
    analysis = analyzer.analyze_contract(contract_text)
    
    # 2. Send email
    notifier = EmailNotifier()
    if notifier.is_email_enabled():
        success, message = notifier.send_notification_safe(
            os.environ.get("TEST_EMAIL"),
            "test_contract.pdf",
            analysis
        )
        assert success, f"Email send failed: {message}"
        print(f"✅ Full workflow test passed: {message}")
    else:
        print("⚠️ Email not configured, skipping email test")

if __name__ == "__main__":
    test_full_workflow()
```

---

## Streamlit Integration Examples

### In Upload Page
```python
# streamlit_app.py
from utils.email_notifier import EmailNotifier

# Email configuration
email_notifier = EmailNotifier()
st.write(f"Email Status: {'✅ Enabled' if email_notifier.is_email_enabled() else '❌ Disabled'}")

# Get recipient email
notification_email = st.text_input("Email for notifications:")

# In analysis button
if st.button("Analyze"):
    # ... run analysis ...
    
    # Send email
    success, msg = email_notifier.send_notification_safe(
        notification_email,
        uploaded_file.name,
        analysis_result
    )
    
    if success:
        st.success(msg)
    else:
        st.warning(msg)
```

### In Settings Page
```python
# Settings page
st.markdown("#### 📧 Email Configuration")

email_notifier = EmailNotifier()

if email_notifier.is_email_enabled():
    st.success("✅ Configured")
    st.write(f"Sender: {email_notifier.sender_email}")
    
    # Test email
    test_email = st.text_input("Test email:")
    if st.button("Send Test"):
        sample = {
            'key_clauses': ['Clause 1'],
            'compliance_issues': [
                {'title': 'Issue 1', 'risk_level': 'High', 'reason': 'Test'}
            ]
        }
        success, msg = email_notifier.send_notification(
            test_email, "Test.pdf", sample
        )
        st.success(msg) if success else st.error(msg)
else:
    st.warning("❌ Not configured")
    st.info("See EMAIL_SETUP_GUIDE.md for setup instructions")
```

---

## Configuration Examples

### Environment Variables
```env
# Gmail
EMAIL_SENDER=john@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Analyzer

# Outlook
EMAIL_SENDER=john@outlook.com
EMAIL_PASSWORD=your_app_password
EMAIL_SMTP_SERVER=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract System

# SendGrid
EMAIL_SENDER=noreply@company.com
EMAIL_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxx
EMAIL_SMTP_SERVER=smtp.sendgrid.net
EMAIL_SMTP_PORT=587
EMAIL_SENDER_NAME=Contract Platform
```

---

## API Reference

### EmailNotifier Class

#### `__init__()`
Initialize notifier with environment variables.

```python
notifier = EmailNotifier()
```

**Attributes:**
- `sender_email` - Email address from EMAIL_SENDER
- `sender_password` - Password from EMAIL_PASSWORD
- `smtp_server` - SMTP server address
- `smtp_port` - SMTP port number
- `sender_name` - Display name for emails
- `is_configured` - Boolean flag for configuration status

#### `is_email_enabled() -> bool`
Check if email notifications are configured.

```python
if notifier.is_email_enabled():
    # Email is ready to use
```

#### `send_notification(recipient_email, contract_name, analysis_result, test_mode=False) -> Tuple[bool, str]`
Send email notification.

**Parameters:**
- `recipient_email` (str) - Email to send to
- `contract_name` (str) - Contract filename
- `analysis_result` (dict) - Analysis results
- `test_mode` (bool) - If True, print instead of send

**Returns:**
- (bool) - Success status
- (str) - Message (success or error)

```python
success, message = notifier.send_notification(
    "user@example.com",
    "contract.pdf",
    analysis_data
)
```

#### `send_notification_safe(recipient_email, contract_name, analysis_result) -> Tuple[bool, str]`
Safely send email without raising exceptions.

```python
success, message = notifier.send_notification_safe(
    "user@example.com",
    "contract.pdf",
    analysis_data
)
```

#### `_create_html_content(contract_name, analysis_result, recipient_email) -> Tuple[str, str]`
Generate HTML and text email content.

**Returns:**
- (str) - HTML content
- (str) - Plain text content

---

## Common Patterns

### Pattern 1: Conditional Sending
```python
email_notifier = EmailNotifier()

if email_notifier.is_email_enabled() and user_email:
    success, msg = email_notifier.send_notification_safe(
        user_email, contract_name, analysis
    )
    st.session_state['email_sent'] = success
```

### Pattern 2: Async Notification (Future Enhancement)
```python
# Could be extended to use:
# - asyncio for non-blocking sends
# - Celery for background task queue
# - Email service (SendGrid, Mailgun) for scalability
```

### Pattern 3: Email Template Variables
```python
# Could extend _create_html_content() to support:
template = {
    "company": "My Company",
    "support_email": "support@company.com",
    "portal_url": "https://portal.company.com",
    "logo_url": "https://company.com/logo.png"
}
```

---

## Troubleshooting Code Issues

### Debug Email Configuration
```python
from utils.email_notifier import EmailNotifier
import os

notifier = EmailNotifier()

print(f"Configured: {notifier.is_configured}")
print(f"Sender: {notifier.sender_email}")
print(f"Server: {notifier.smtp_server}:{notifier.smtp_port}")
print(f"Password set: {bool(notifier.sender_password)}")

# Check environment
print(f"\nEnvironment check:")
print(f"EMAIL_SENDER: {os.environ.get('EMAIL_SENDER', 'NOT SET')}")
print(f"EMAIL_PASSWORD: {'SET' if os.environ.get('EMAIL_PASSWORD') else 'NOT SET'}")
```

### Test SMTP Connection
```python
import smtplib

smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "your@gmail.com"
sender_password = "app_password"

try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    print("✅ SMTP connection successful")
    server.quit()
except Exception as e:
    print(f"❌ SMTP error: {e}")
```

---

**For more information, see:**
- `EMAIL_SETUP_GUIDE.md` - Setup and troubleshooting
- `EMAIL_IMPLEMENTATION.md` - Technical architecture
- `EMAIL_QUICK_REFERENCE.md` - Quick reference

