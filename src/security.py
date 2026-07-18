"""
Security Module for CyberSecure Log System
Handles SQL injection detection, input validation, and security logging.
"""
import re
import html
from functools import wraps
from flask import request, jsonify, session, render_template
from config import Config
from models import get_db
from email_service import send_sql_injection_alert


# Compile SQL injection patterns for performance
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in Config.SQL_INJECTION_PATTERNS]


def detect_sql_injection(input_string):
    """
    Check if input contains SQL injection patterns.
    Returns (is_malicious: bool, matched_pattern: str or None)
    """
    if not input_string:
        return False, None
    
    # Decode URL encoding
    decoded = input_string
    try:
        from urllib.parse import unquote
        decoded = unquote(input_string)
    except:
        pass
    
    # Check against each pattern
    for pattern in COMPILED_PATTERNS:
        match = pattern.search(decoded)
        if match:
            return True, match.group(0)
    
    # Additional heuristic checks
    suspicious_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', '@@']
    suspicious_count = sum(1 for c in suspicious_chars if c in decoded)
    if suspicious_count >= 3:
        return True, f"Multiple suspicious characters detected ({suspicious_count})"
    
    return False, None


def sanitize_input(input_string):
    """Sanitize user input by escaping HTML and removing dangerous characters."""
    if not input_string:
        return input_string
    sanitized = html.escape(str(input_string).strip())
    return sanitized


def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_student_id(student_id):
    """Validate student ID format (alphanumeric, 3-20 chars)."""
    pattern = r'^[a-zA-Z0-9_-]{3,20}$'
    return bool(re.match(pattern, student_id))


def log_security_alert(student_id, alert_type, severity, message, ip_address=None, details=None):
    """Log a security alert to the database."""
    db = get_db()
    try:
        db.execute('''
            INSERT INTO security_alerts (student_id, alert_type, severity, message, ip_address, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, alert_type, severity, message, ip_address, details))
        db.commit()
        print(f"[ALERT] {severity}: {alert_type} - {message}")
    except Exception as e:
        print(f"[-] Failed to log security alert: {e}")
    finally:
        db.close()


def log_threat(event_type, source_ip, student_id, payload, risk_score, action_taken):
    """Log a threat event for threat hunting."""
    db = get_db()
    try:
        db.execute('''
            INSERT INTO threat_logs (event_type, source_ip, student_id, payload, risk_score, action_taken)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event_type, source_ip, student_id, payload, risk_score, action_taken))
        db.commit()
    except Exception as e:
        print(f"[-] Failed to log threat: {e}")
    finally:
        db.close()


def check_all_inputs(func):
    """
    Decorator to check ALL request inputs for SQL injection attempts.
    Applies to routes that accept user input.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        ip_address = request.remote_addr
        inputs_to_check = []
        
        # Collect all form data
        if request.form:
            for key, value in request.form.items():
                inputs_to_check.append((key, value))
        
        # Collect all query parameters
        if request.args:
            for key, value in request.args.items():
                inputs_to_check.append((key, value))
        
        # Collect JSON body
        if request.is_json and request.json:
            for key, value in request.json.items():
                inputs_to_check.append((key, str(value)))
        
        # Check each input
        for field_name, field_value in inputs_to_check:
            is_malicious, pattern = detect_sql_injection(field_value)
            if is_malicious:
                student_id = (request.form.get('student_id') or 
                            request.args.get('student_id') or 
                            session.get('student_id') or 'UNKNOWN')
                
                # Log the alert
                log_security_alert(
                    student_id=student_id,
                    alert_type='SQL_INJECTION',
                    severity='CRITICAL',
                    message=f'SQL Injection attempt detected in field: {field_name}',
                    ip_address=ip_address,
                    details=f'Pattern: {pattern} | Value: {field_value[:200]}'
                )
                
                # Log threat for hunting
                log_threat(
                    event_type='SQL_INJECTION',
                    source_ip=ip_address,
                    student_id=student_id,
                    payload=field_value[:500],
                    risk_score=100,
                    action_taken='BLOCKED'
                )
                
                # Try to send email alert
                try:
                    db = get_db()
                    student = db.execute(
                        'SELECT email, first_name FROM students WHERE student_id = ?',
                        (student_id,)
                    ).fetchone()
                    db.close()
                    if student:
                        send_sql_injection_alert(
                            student['email'], student_id, ip_address,
                            field_value[:100], student['first_name']
                        )
                except:
                    pass
                
                return render_template('sqli_blocked.html'), 403
        
        return func(*args, **kwargs)
    return wrapper


def get_client_ip():
    """Get real client IP address."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-Ip'):
        return request.headers.get('X-Real-Ip')
    return request.remote_addr


def calculate_risk_score(student_id):
    """Calculate risk score for a student based on their activity."""
    db = get_db()
    try:
        # Failed login attempts in last 24 hours
        failed_logins = db.execute('''
            SELECT COUNT(*) as count FROM login_attempts 
            WHERE student_id = ? AND attempt_status = 'FAILED'
            AND timestamp > datetime('now', '-1 day')
        ''', (student_id,)).fetchone()['count']
        
        # Security alerts in last 7 days
        alerts = db.execute('''
            SELECT COUNT(*) as count, 
                   SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count
            FROM security_alerts 
            WHERE student_id = ? AND timestamp > datetime('now', '-7 days')
        ''', (student_id,)).fetchone()
        
        # Unique IPs in last 24 hours
        unique_ips = db.execute('''
            SELECT COUNT(DISTINCT ip_address) as count FROM login_attempts 
            WHERE student_id = ? AND timestamp > datetime('now', '-1 day')
        ''', (student_id,)).fetchone()['count']
        
        score = 0
        score += min(failed_logins * 10, 40)  # Max 40 from failed logins
        score += min((alerts['count'] or 0) * 5, 20)  # Max 20 from alerts
        score += (alerts['critical_count'] or 0) * 20  # 20 per critical alert
        score += max(0, (unique_ips - 2)) * 10  # 10 per extra IP beyond 2
        
        return min(score, 100)
    except Exception as e:
        print(f"[-] Risk score calculation error: {e}")
        return 0
    finally:
        db.close()
