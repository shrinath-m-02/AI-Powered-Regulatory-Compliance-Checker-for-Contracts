"""
Email Notification System for Contract Compliance Analyzer
Sends email notifications when contract analysis completes
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class EmailNotifier:
    """
    Handles email notifications for contract analysis completion
    Supports Gmail SMTP and other providers
    """
    
    def __init__(self):
        """Initialize email notifier with environment variables"""
        self.sender_email = os.environ.get("EMAIL_SENDER")
        self.sender_password = os.environ.get("EMAIL_PASSWORD")
        self.smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
        self.sender_name = os.environ.get("EMAIL_SENDER_NAME", "Contract Analyzer")
        
        # Validate configuration
        if not self.sender_email or not self.sender_password:
            logger.warning("⚠️ Email credentials not configured. Email notifications disabled.")
            self.is_configured = False
        else:
            self.is_configured = True
            logger.info(f"✅ Email notifier configured with {self.sender_email}")
    
    def is_email_enabled(self) -> bool:
        """Check if email notifications are configured and enabled"""
        return self.is_configured
    
    def _create_html_content(
        self,
        contract_name: str,
        analysis_result: Dict,
        recipient_email: str
    ) -> Tuple[str, str]:
        """
        Create HTML and plain text email content
        
        Args:
            contract_name: Name of the analyzed contract
            analysis_result: Analysis results dictionary
            recipient_email: Email recipient
        
        Returns:
            Tuple of (html_content, text_content)
        """
        
        key_clauses = analysis_result.get('key_clauses', [])
        compliance_issues = analysis_result.get('compliance_issues', [])
        
        # Count issues by risk level
        high_risk = len([i for i in compliance_issues if i.get('risk_level') == 'High'])
        medium_risk = len([i for i in compliance_issues if i.get('risk_level') == 'Medium'])
        low_risk = len([i for i in compliance_issues if i.get('risk_level') == 'Low'])
        
        # Plain text content
        text_content = f"""
Contract Compliance Analysis Complete

Contract: {contract_name}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== SUMMARY ===
Key Clauses Found: {len(key_clauses)}
Compliance Issues: {len(compliance_issues)}
  - High Risk: {high_risk}
  - Medium Risk: {medium_risk}
  - Low Risk: {low_risk}

=== KEY CLAUSES ({len(key_clauses)}) ===
"""
        
        for idx, clause in enumerate(key_clauses[:10], 1):  # Limit to 10 for email
            text_content += f"{idx}. {clause}\n"
        
        if len(key_clauses) > 10:
            text_content += f"... and {len(key_clauses) - 10} more\n"
        
        text_content += "\n=== TOP COMPLIANCE ISSUES ===\n"
        
        for idx, issue in enumerate(compliance_issues[:5], 1):  # Limit to 5 for email
            text_content += f"""
{idx}. {issue.get('title', 'Unknown Issue')}
   Risk Level: {issue.get('risk_level', 'Unknown')}
   Reason: {issue.get('reason', 'N/A')}
"""
        
        if len(compliance_issues) > 5:
            text_content += f"\n... and {len(compliance_issues) - 5} more issues\n"
        
        text_content += f"""
=== NEXT STEPS ===
1. Log in to the Contract Analyzer portal
2. Review the full analysis in the 📊 Risk Analysis page
3. Check 🎯 Clauses & Amendments for recommendations
4. Ask questions in the 💬 Chatbot for more details

Analysis Portal: http://localhost:8503

---
This is an automated notification from Contract Compliance Analyzer
"""
        
        # HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }}
        .metrics {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }}
        .metric {{
            text-align: center;
            padding: 10px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .risk-high {{
            color: #dc3545;
            font-weight: bold;
        }}
        .risk-medium {{
            color: #ffc107;
            font-weight: bold;
        }}
        .risk-low {{
            color: #28a745;
            font-weight: bold;
        }}
        .section {{
            margin: 20px 0;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .clause-item {{
            background-color: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }}
        .issue-item {{
            background-color: #fff3cd;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 3px solid #ffc107;
        }}
        .issue-item.high {{
            background-color: #f8d7da;
            border-left-color: #dc3545;
        }}
        .issue-item.low {{
            background-color: #d4edda;
            border-left-color: #28a745;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }}
        .button {{
            display: inline-block;
            background-color: #667eea;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 0;
            text-align: center;
        }}
        .button:hover {{
            background-color: #764ba2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Contract Analysis Complete</h1>
        </div>
        
        <div class="summary">
            <h2 style="margin-top: 0;">Contract: {contract_name}</h2>
            <p><small>Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">{len(key_clauses)}</div>
                <div class="metric-label">Key Clauses</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color: {['#28a745', '#ffc107', '#dc3545'][min(2, 1 if medium_risk > 0 else (2 if high_risk > 0 else 0))]}">{len(compliance_issues)}</div>
                <div class="metric-label">Issues Found</div>
            </div>
            <div class="metric">
                <div class="metric-value risk-high">{high_risk}</div>
                <div class="metric-label">High Risk</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🔍 Risk Summary</div>
            <p>
                <span class="risk-high">● High Risk: {high_risk}</span> | 
                <span class="risk-medium">● Medium Risk: {medium_risk}</span> | 
                <span class="risk-low">● Low Risk: {low_risk}</span>
            </p>
        </div>
        
        <div class="section">
            <div class="section-title">📌 Key Clauses ({len(key_clauses)})</div>
"""
        
        for idx, clause in enumerate(key_clauses[:10], 1):
            html_content += f'<div class="clause-item"><strong>{idx}.</strong> {clause}</div>\n'
        
        if len(key_clauses) > 10:
            html_content += f'<p><em>... and {len(key_clauses) - 10} more clauses</em></p>\n'
        
        html_content += """
        </div>
        
        <div class="section">
            <div class="section-title">⚠️ Top Compliance Issues</div>
"""
        
        for idx, issue in enumerate(compliance_issues[:5], 1):
            risk_class = issue.get('risk_level', 'medium').lower()
            html_content += f"""
            <div class="issue-item {risk_class}">
                <strong>{idx}. {issue.get('title', 'Unknown Issue')}</strong><br>
                <small>Risk Level: <span class="risk-{risk_class}"><strong>{issue.get('risk_level', 'Unknown')}</strong></span></small><br>
                <small>Reason: {issue.get('reason', 'N/A')}</small>
            </div>
"""
        
        if len(compliance_issues) > 5:
            html_content += f'<p><em>... and {len(compliance_issues) - 5} more issues</em></p>\n'
        
        html_content += f"""
        </div>
        
        <div class="section" style="text-align: center;">
            <a href="http://localhost:8503" class="button">View Full Analysis</a>
        </div>
        
        <div class="section">
            <div class="section-title">📋 Next Steps</div>
            <ol>
                <li>Log in to the Contract Analyzer portal</li>
                <li>Review the full analysis in the <strong>📊 Risk Analysis</strong> page</li>
                <li>Check <strong>✅ Clauses & Amendments</strong> for recommendations</li>
                <li>Ask questions in the <strong>💬 Chatbot</strong> for more details</li>
            </ol>
        </div>
        
        <div class="footer">
            <p>This is an automated notification from <strong>Contract Compliance Analyzer</strong></p>
            <p>If you did not request this analysis, please ignore this email.</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content, text_content
    
    def send_notification(
        self,
        recipient_email: str,
        contract_name: str,
        analysis_result: Dict,
        test_mode: bool = False
    ) -> Tuple[bool, str]:
        """
        Send email notification for completed analysis
        
        Args:
            recipient_email: Email address to send to
            contract_name: Name of the contract analyzed
            analysis_result: Dictionary with analysis results
            test_mode: If True, prints email instead of sending
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        
        if not self.is_configured:
            return False, "❌ Email service not configured. Set EMAIL_SENDER and EMAIL_PASSWORD in .env"
        
        try:
            # Validate email
            if not recipient_email or "@" not in recipient_email:
                return False, "❌ Invalid email address provided"
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"📋 Contract Analysis Completed: {contract_name}"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            message["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            # Create content
            html_content, text_content = self._create_html_content(
                contract_name,
                analysis_result,
                recipient_email
            )
            
            # Attach both text and HTML
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Test mode: just print the email
            if test_mode:
                logger.info("📧 TEST MODE - Email Content:")
                logger.info(f"To: {recipient_email}")
                logger.info(f"Subject: {message['Subject']}")
                logger.info("---")
                logger.info(text_content)
                logger.info("---")
                return True, f"✅ Test mode: Email would be sent to {recipient_email}"
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure connection
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"✅ Email sent successfully to {recipient_email}")
            return True, f"✅ Email notification sent to {recipient_email}"
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "❌ Authentication failed. Check EMAIL_SENDER and EMAIL_PASSWORD in .env"
            logger.error(error_msg)
            return False, error_msg
            
        except smtplib.SMTPException as e:
            error_msg = f"❌ SMTP error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"❌ Error sending email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def send_notification_safe(
        self,
        recipient_email: str,
        contract_name: str,
        analysis_result: Dict
    ) -> Tuple[bool, str]:
        """
        Safely send email notification without breaking the UI
        Logs errors but doesn't raise exceptions
        
        Args:
            recipient_email: Email address to send to
            contract_name: Name of the contract analyzed
            analysis_result: Dictionary with analysis results
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            return self.send_notification(
                recipient_email,
                contract_name,
                analysis_result,
                test_mode=False
            )
        except Exception as e:
            error_msg = f"⚠️ Warning: Email notification failed ({str(e)}), but analysis completed successfully."
            logger.warning(error_msg)
            return False, error_msg
