"""
Email Service for CyberSecure Log System
Handles OTP emails, login alerts, and critical security notifications via Gmail SMTP.
"""
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


def generate_otp():
    """Generate a 6-digit OTP code."""
    return ''.join(random.choices(string.digits, k=6))


def send_email(to_email, subject, html_body):
    """Send an email via Gmail SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = Config.SMTP_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"[+] Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[-] Email failed to {to_email}: {e}")
        return False


def _cyber_email_template(title, body_content, severity_color="#00FF00"):
    """Create a cyber-themed HTML email template."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ 
                background-color: #0a0a0a; 
                color: #00FF00; 
                font-family: 'Courier New', monospace; 
                padding: 20px; 
            }}
            .container {{ 
                max-width: 600px; 
                margin: 0 auto; 
                background: #111; 
                border: 1px solid {severity_color}; 
                border-radius: 10px; 
                padding: 30px; 
                box-shadow: 0 0 20px {severity_color}40; 
            }}
            .header {{ 
                text-align: center; 
                border-bottom: 2px solid {severity_color}; 
                padding-bottom: 15px; 
                margin-bottom: 20px; 
            }}
            .header h1 {{ 
                color: {severity_color}; 
                font-size: 22px; 
                text-shadow: 0 0 10px {severity_color}; 
            }}
            .shield {{ font-size: 48px; }}
            .content {{ 
                padding: 15px 0; 
                line-height: 1.8; 
                color: #ccc; 
            }}
            .otp-box {{ 
                background: #1a1a2e; 
                border: 2px solid {severity_color}; 
                border-radius: 8px; 
                padding: 20px; 
                text-align: center; 
                margin: 20px 0; 
            }}
            .otp-code {{ 
                font-size: 36px; 
                letter-spacing: 8px; 
                color: {severity_color}; 
                font-weight: bold; 
                text-shadow: 0 0 10px {severity_color}; 
            }}
            .alert-box {{ 
                background: #1a0000; 
                border: 2px solid {severity_color}; 
                border-radius: 8px; 
                padding: 15px; 
                margin: 15px 0; 
            }}
            .footer {{ 
                text-align: center; 
                margin-top: 20px; 
                padding-top: 15px; 
                border-top: 1px solid #333; 
                color: #666; 
                font-size: 12px; 
            }}
            .severity {{ 
                display: inline-block; 
                padding: 3px 10px; 
                border-radius: 4px; 
                font-weight: bold; 
                color: #fff; 
                background: {severity_color}30; 
                border: 1px solid {severity_color}; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="shield">🛡️</div>
                <h1>{title}</h1>
            </div>
            <div class="content">
                {body_content}
            </div>
            <div class="footer">
                CyberSecure Log Analysis &amp; Threat Hunting System<br>
                This is an automated security notification. Do not reply.
            </div>
        </div>
    </body>
    </html>
    """


def send_otp_email(to_email, otp_code, student_name="Student"):
    """Send OTP verification email."""
    body = f"""
    <p>Hello <strong>{student_name}</strong>,</p>
    <p>Your One-Time Password (OTP) for account verification:</p>
    <div class="otp-box">
        <div class="otp-code">{otp_code}</div>
        <p style="color: #888; margin-top: 10px;">Valid for {Config.OTP_EXPIRY_MINUTES} minutes</p>
    </div>
    <p>If you did not request this OTP, please ignore this email and secure your account immediately.</p>
    <p><span class="severity">SEVERITY: LOW</span></p>
    """
    html = _cyber_email_template("🔐 OTP Verification", body, "#00FF00")
    return send_email(to_email, "🛡️ CyberSecure - OTP Verification Code", html)


def send_failed_login_alert(to_email, student_id, ip_address, attempt_count, student_name="Student"):
    """Send failed login attempt alert email."""
    severity_color = "#FF4444" if attempt_count >= 5 else "#FFA500"
    severity = "CRITICAL" if attempt_count >= 5 else "MEDIUM"
    
    lock_msg = ""
    if attempt_count >= 5:
        lock_msg = f"""
        <div class="alert-box" style="border-color: #FF0000;">
            <p style="color: #FF0000; font-weight: bold;">🚨 ACCOUNT TEMPORARILY LOCKED</p>
            <p>Your account has been temporarily locked due to {attempt_count} failed login attempts.
            It will be automatically unlocked after {Config.ACCOUNT_LOCK_MINUTES} minutes.</p>
        </div>
        """
    
    body = f"""
    <p>Hello <strong>{student_name}</strong>,</p>
    <div class="alert-box">
        <p><strong>⚠️ Warning:</strong> Someone attempted to access your account with an incorrect password.</p>
        <p><strong>Student ID:</strong> {student_id}</p>
        <p><strong>IP Address:</strong> {ip_address}</p>
        <p><strong>Failed Attempts:</strong> {attempt_count}</p>
    </div>
    {lock_msg}
    <p>If this was not you, please change your password immediately and contact support.</p>
    <p><span class="severity">SEVERITY: {severity}</span></p>
    """
    html = _cyber_email_template("⚠️ Failed Login Attempt Alert", body, severity_color)
    return send_email(to_email, f"🛡️ CyberSecure - Failed Login Alert [{severity}]", html)


def send_sql_injection_alert(to_email, student_id, ip_address, payload, student_name="Student"):
    """Send CRITICAL SQL injection detection alert email."""
    body = f"""
    <p>Hello <strong>{student_name}</strong>,</p>
    <div class="alert-box" style="border-color: #FF0000; background: #2a0000;">
        <p style="color: #FF0000; font-size: 18px; font-weight: bold; text-align: center;">
            🚨 CRITICAL SECURITY BREACH ATTEMPT DETECTED 🚨
        </p>
        <p><strong>Attack Type:</strong> SQL Injection Attempt</p>
        <p><strong>Student ID:</strong> {student_id}</p>
        <p><strong>Source IP:</strong> {ip_address}</p>
        <p><strong>Malicious Payload:</strong> <code style="color:#FF4444; background:#1a0000; padding:2px 6px; border-radius:3px;">{payload}</code></p>
    </div>
    <p style="color: #FF4444;">
        <strong>CRITICAL ALERT:</strong> A SQL Injection attack attempt was detected on your account.
        The malicious request has been blocked and logged. Your account and data remain secure.
    </p>
    <p>Our security team has been notified. If you believe your credentials have been compromised, 
    change your password immediately.</p>
    <p><span class="severity" style="background: #FF000030; border-color: #FF0000;">SEVERITY: CRITICAL</span></p>
    """
    html = _cyber_email_template("🚨 CRITICAL: SQL Injection Detected", body, "#FF0000")
    return send_email(to_email, "🚨 CyberSecure - CRITICAL: SQL Injection Attack Detected!", html)


def send_otp_failed_alert(to_email, attempts, student_name="Student"):
    """Send OTP verification failure alert."""
    body = f"""
    <p>Hello <strong>{student_name}</strong>,</p>
    <div class="alert-box">
        <p>Your OTP verification failed. <strong>{attempts}</strong> incorrect attempt(s) recorded.</p>
        <p>If this was not you, please secure your account immediately.</p>
    </div>
    <p><span class="severity">SEVERITY: LOW</span></p>
    """
    html = _cyber_email_template("🔐 OTP Verification Failed", body, "#FFA500")
    return send_email(to_email, "🛡️ CyberSecure - OTP Verification Failed", html)
