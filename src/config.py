"""
Configuration for CyberSecure Log Analysis & Threat Hunting System
"""
import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cybersec-super-secret-key-change-in-production')
    
    # Database
    DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cybersec_log_system.db')
    
    # JWT
    JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt-secret-key-change-in-production')
    JWT_EXPIRY_HOURS = 24
    
    # OTP
    OTP_EXPIRY_MINUTES = 5
    OTP_MAX_ATTEMPTS = 3
    
    # Login Security
    MAX_FAILED_LOGIN_ATTEMPTS = 3
    ACCOUNT_LOCK_SECONDS = 59
    
    # Email (Gmail SMTP)
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_EMAIL = os.environ.get('SMTP_EMAIL', 'darlapraveen87@gmail.com')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'cihq twbg zwnw kjrp')
    
    # SQL Injection Patterns (tuned to avoid false positives on normal input)
    SQL_INJECTION_PATTERNS = [
        r"('(\s)*(OR|AND)(\s)*')",
        r"('(\s)*OR(\s)+.*=.*)",
        r"(UNION\s+SELECT)",
        r"(DROP\s+TABLE)",
        r"(INSERT\s+INTO)",
        r"(DELETE\s+FROM)",
        r"(UPDATE\s+.*\s+SET)",
        r"(xp_cmdshell)",
        r"(INFORMATION_SCHEMA)",
        r"('(\s)*;(\s)*--)",
        r"(1(\s)*=(\s)*1)",
        r"('(\s)*OR(\s)+'1'(\s)*=(\s)*'1)",
        r"(;\s*DROP\b)",
        r"(;\s*DELETE\b)",
        r"(--\s*$)",
        r"(\/\*.*\*\/)",
    ]
