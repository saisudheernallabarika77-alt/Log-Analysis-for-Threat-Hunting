"""
Threat Hunting Module for CyberSecure Log System
Provides IP tracking, time-based analysis, pattern detection, and risk assessment.
"""
from flask import Blueprint, jsonify, session
from models import get_db
from security import calculate_risk_score
from functools import wraps

threat_bp = Blueprint('threat', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


@threat_bp.route('/api/threat/overview')
@login_required
def threat_overview():
    """Get overall threat landscape overview."""
    db = get_db()
    try:
        # Total security alerts
        total_alerts = db.execute(
            'SELECT COUNT(*) as count FROM security_alerts'
        ).fetchone()['count']

        # Alerts by severity
        severity_counts = {}
        for row in db.execute('''
            SELECT severity, COUNT(*) as count FROM security_alerts 
            GROUP BY severity
        ''').fetchall():
            severity_counts[row['severity']] = row['count']

        # Recent alerts (last 7 days)
        recent = db.execute('''
            SELECT COUNT(*) as count FROM security_alerts
            WHERE timestamp > datetime('now', '-7 days')
        ''').fetchone()['count']

        # SQL injection attempts
        sqli_count = db.execute('''
            SELECT COUNT(*) as count FROM security_alerts
            WHERE alert_type = 'SQL_INJECTION'
        ''').fetchone()['count']

        # Failed login count
        failed_logins = db.execute('''
            SELECT COUNT(*) as count FROM login_attempts
            WHERE attempt_status = 'FAILED'
        ''').fetchone()['count']

        # Unique threat IPs
        unique_ips = db.execute('''
            SELECT COUNT(DISTINCT ip_address) as count FROM threat_logs
        ''').fetchone()['count']

        return jsonify({
            'total_alerts': total_alerts,
            'severity_counts': severity_counts,
            'recent_alerts': recent,
            'sqli_attempts': sqli_count,
            'failed_logins': failed_logins,
            'unique_threat_ips': unique_ips
        })
    finally:
        db.close()


@threat_bp.route('/api/threat/login-analysis')
@login_required
def login_analysis():
    """Time-based login analysis."""
    student_id = session.get('student_id')
    db = get_db()
    try:
        # Hourly login distribution (last 7 days)
        hourly = db.execute('''
            SELECT strftime('%H', timestamp) as hour, 
                   attempt_status, COUNT(*) as count
            FROM login_attempts
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY hour, attempt_status
            ORDER BY hour
        ''').fetchall()

        hourly_data = {}
        for row in hourly:
            h = row['hour']
            if h not in hourly_data:
                hourly_data[h] = {'SUCCESS': 0, 'FAILED': 0}
            hourly_data[h][row['attempt_status']] = row['count']

        # Daily login trend (last 30 days)
        daily = db.execute('''
            SELECT strftime('%Y-%m-%d', timestamp) as day,
                   attempt_status, COUNT(*) as count
            FROM login_attempts
            WHERE timestamp > datetime('now', '-30 days')
            GROUP BY day, attempt_status
            ORDER BY day
        ''').fetchall()

        daily_data = {}
        for row in daily:
            d = row['day']
            if d not in daily_data:
                daily_data[d] = {'SUCCESS': 0, 'FAILED': 0}
            daily_data[d][row['attempt_status']] = row['count']

        # User-specific data
        user_logins = db.execute('''
            SELECT ip_address, attempt_status, user_agent, timestamp
            FROM login_attempts
            WHERE student_id = ?
            ORDER BY timestamp DESC LIMIT 20
        ''', (student_id,)).fetchall()

        return jsonify({
            'hourly_distribution': hourly_data,
            'daily_trend': daily_data,
            'recent_logins': [dict(r) for r in user_logins]
        })
    finally:
        db.close()


@threat_bp.route('/api/threat/ip-tracking')
@login_required
def ip_tracking():
    """Track IP addresses and detect multiple location access."""
    student_id = session.get('student_id')
    db = get_db()
    try:
        # IPs for current user
        user_ips = db.execute('''
            SELECT ip_address, COUNT(*) as count,
                   MAX(timestamp) as last_seen,
                   MIN(timestamp) as first_seen,
                   SUM(CASE WHEN attempt_status = 'FAILED' THEN 1 ELSE 0 END) as failed_count
            FROM login_attempts
            WHERE student_id = ?
            GROUP BY ip_address
            ORDER BY last_seen DESC
        ''', (student_id,)).fetchall()

        # All suspicious IPs (multiple failed attempts)
        suspicious_ips = db.execute('''
            SELECT ip_address, COUNT(*) as total_attempts,
                   SUM(CASE WHEN attempt_status = 'FAILED' THEN 1 ELSE 0 END) as failed_attempts,
                   COUNT(DISTINCT student_id) as unique_accounts
            FROM login_attempts
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY ip_address
            HAVING failed_attempts >= 3
            ORDER BY failed_attempts DESC
        ''').fetchall()

        # Multi-location detection
        multi_location = len(user_ips) > 2

        return jsonify({
            'user_ips': [dict(r) for r in user_ips],
            'suspicious_ips': [dict(r) for r in suspicious_ips],
            'multi_location_detected': multi_location,
            'total_unique_ips': len(user_ips)
        })
    finally:
        db.close()


@threat_bp.route('/api/threat/alerts')
@login_required
def get_alerts():
    """Get security alerts with filtering."""
    student_id = session.get('student_id')
    severity = session.get('filter_severity')
    db = get_db()
    try:
        # User-specific alerts
        user_alerts = db.execute('''
            SELECT * FROM security_alerts
            WHERE student_id = ?
            ORDER BY timestamp DESC LIMIT 50
        ''', (student_id,)).fetchall()

        # All recent critical alerts
        critical_alerts = db.execute('''
            SELECT * FROM security_alerts
            WHERE severity = 'CRITICAL'
            ORDER BY timestamp DESC LIMIT 20
        ''').fetchall()

        return jsonify({
            'user_alerts': [dict(r) for r in user_alerts],
            'critical_alerts': [dict(r) for r in critical_alerts]
        })
    finally:
        db.close()


@threat_bp.route('/api/threat/risk-score')
@login_required
def risk_score():
    """Get current user's risk score."""
    student_id = session.get('student_id')
    score = calculate_risk_score(student_id)

    if score >= 70:
        level = 'CRITICAL'
        color = '#FF0000'
    elif score >= 40:
        level = 'HIGH'
        color = '#FF6600'
    elif score >= 20:
        level = 'MEDIUM'
        color = '#FFA500'
    else:
        level = 'LOW'
        color = '#00FF00'

    return jsonify({
        'risk_score': score,
        'risk_level': level,
        'risk_color': color
    })


@threat_bp.route('/api/threat/suspicious-patterns')
@login_required
def suspicious_patterns():
    """Detect suspicious login patterns."""
    db = get_db()
    try:
        patterns = []

        # Pattern 1: Rapid-fire login attempts (more than 5 in 5 minutes)
        rapid = db.execute('''
            SELECT student_id, ip_address, COUNT(*) as count
            FROM login_attempts
            WHERE attempt_status = 'FAILED'
            AND timestamp > datetime('now', '-5 minutes')
            GROUP BY student_id, ip_address
            HAVING count >= 5
        ''').fetchall()
        for r in rapid:
            patterns.append({
                'type': 'BRUTE_FORCE',
                'description': f'Rapid login attempts from {r["ip_address"]} on {r["student_id"]}',
                'severity': 'HIGH',
                'count': r['count']
            })

        # Pattern 2: Same IP targeting multiple accounts
        multi_target = db.execute('''
            SELECT ip_address, COUNT(DISTINCT student_id) as targets
            FROM login_attempts
            WHERE attempt_status = 'FAILED'
            AND timestamp > datetime('now', '-1 hour')
            GROUP BY ip_address
            HAVING targets >= 3
        ''').fetchall()
        for r in multi_target:
            patterns.append({
                'type': 'CREDENTIAL_STUFFING',
                'description': f'IP {r["ip_address"]} targeting {r["targets"]} different accounts',
                'severity': 'CRITICAL',
                'count': r['targets']
            })

        # Pattern 3: SQL injection attempts
        sqli = db.execute('''
            SELECT source_ip, COUNT(*) as count
            FROM threat_logs
            WHERE event_type = 'SQL_INJECTION'
            AND timestamp > datetime('now', '-24 hours')
            GROUP BY source_ip
        ''').fetchall()
        for r in sqli:
            patterns.append({
                'type': 'SQL_INJECTION',
                'description': f'SQL injection attempts from {r["source_ip"]}',
                'severity': 'CRITICAL',
                'count': r['count']
            })

        return jsonify({'patterns': patterns})
    finally:
        db.close()


@threat_bp.route('/api/threat/timeline')
@login_required
def threat_timeline():
    """Get recent threat events timeline."""
    db = get_db()
    try:
        events = db.execute('''
            SELECT * FROM threat_logs
            ORDER BY timestamp DESC LIMIT 50
        ''').fetchall()
        return jsonify({'events': [dict(e) for e in events]})
    finally:
        db.close()
