"""
Dashboard routes for CyberSecure Log System
Provides the main dashboard with security insights and threat data.
"""
from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from functools import wraps
import bcrypt
from models import get_db
from security import calculate_risk_score

dashboard_bp = Blueprint('dashboard', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route('/dashboard')
@login_required
def home():
    """Main dashboard page — shows logged-in student's details."""
    student_id = session.get('student_id')
    student_name = session.get('student_name', 'User')

    db = get_db()
    try:
        student = db.execute(
            'SELECT * FROM students WHERE student_id = ?', (student_id,)
        ).fetchone()

        return render_template('dashboard.html',
            student_name=student_name,
            student_id=student_id,
            student=student
        )
    finally:
        db.close()


@dashboard_bp.route('/security')
@login_required
def security_center():
    """Security dashboard page — alerts, charts, threat hunting."""
    student_id = session.get('student_id')
    student_name = session.get('student_name', 'User')

    db = get_db()
    try:
        student = db.execute(
            'SELECT * FROM students WHERE student_id = ?', (student_id,)
        ).fetchone()

        failed_logins = db.execute('''
            SELECT COUNT(*) as count FROM login_attempts
            WHERE student_id = ? AND attempt_status = 'FAILED'
            AND timestamp > datetime('now', '-1 day')
        ''', (student_id,)).fetchone()['count']

        total_logins = db.execute('''
            SELECT COUNT(*) as count FROM login_attempts
            WHERE student_id = ?
        ''', (student_id,)).fetchone()['count']

        last_login = db.execute('''
            SELECT ip_address, timestamp FROM login_attempts
            WHERE student_id = ? AND attempt_status = 'SUCCESS'
            ORDER BY timestamp DESC LIMIT 1
        ''', (student_id,)).fetchone()

        alert_counts = db.execute('''
            SELECT severity, COUNT(*) as count FROM security_alerts
            WHERE student_id = ?
            GROUP BY severity
        ''', (student_id,)).fetchall()
        alerts = {row['severity']: row['count'] for row in alert_counts}

        total_system_alerts = db.execute(
            'SELECT COUNT(*) as count FROM security_alerts'
        ).fetchone()['count']

        recent_alerts = db.execute('''
            SELECT * FROM security_alerts
            WHERE student_id = ?
            ORDER BY timestamp DESC LIMIT 10
        ''', (student_id,)).fetchall()

        recent_logins = db.execute('''
            SELECT * FROM login_attempts
            WHERE student_id = ?
            ORDER BY timestamp DESC LIMIT 10
        ''', (student_id,)).fetchall()

        risk_score = calculate_risk_score(student_id)

        unique_ips = db.execute('''
            SELECT COUNT(DISTINCT ip_address) as count FROM login_attempts
            WHERE student_id = ?
        ''', (student_id,)).fetchone()['count']

        sqli_count = db.execute('''
            SELECT COUNT(*) as count FROM security_alerts
            WHERE student_id = ? AND alert_type = 'SQL_INJECTION'
        ''', (student_id,)).fetchone()['count']

        return render_template('security_page.html',
            student=student,
            student_name=student_name,
            student_id=student_id,
            failed_logins=failed_logins,
            total_logins=total_logins,
            last_login=last_login,
            alerts=alerts,
            total_system_alerts=total_system_alerts,
            recent_alerts=recent_alerts,
            recent_logins=recent_logins,
            risk_score=risk_score,
            unique_ips=unique_ips,
            sqli_count=sqli_count
        )
    finally:
        db.close()


@dashboard_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """API endpoint for real-time dashboard stats."""
    student_id = session.get('student_id')
    db = get_db()
    try:
        failed_24h = db.execute('''
            SELECT COUNT(*) as count FROM login_attempts
            WHERE student_id = ? AND attempt_status = 'FAILED'
            AND timestamp > datetime('now', '-1 day')
        ''', (student_id,)).fetchone()['count']
        
        success_24h = db.execute('''
            SELECT COUNT(*) as count FROM login_attempts
            WHERE student_id = ? AND attempt_status = 'SUCCESS'
            AND timestamp > datetime('now', '-1 day')
        ''', (student_id,)).fetchone()['count']
        
        alerts_24h = db.execute('''
            SELECT COUNT(*) as count FROM security_alerts
            WHERE student_id = ? AND timestamp > datetime('now', '-1 day')
        ''', (student_id,)).fetchone()['count']
        
        risk_score = calculate_risk_score(student_id)
        
        # Latest alert
        latest_alert = db.execute('''
            SELECT * FROM security_alerts
            WHERE student_id = ?
            ORDER BY timestamp DESC LIMIT 1
        ''', (student_id,)).fetchone()
        
        return jsonify({
            'failed_24h': failed_24h,
            'success_24h': success_24h,
            'alerts_24h': alerts_24h,
            'risk_score': risk_score,
            'latest_alert': dict(latest_alert) if latest_alert else None
        })
    finally:
        db.close()


@dashboard_bp.route('/api/dashboard/login-chart')
@login_required
def login_chart():
    """Login frequency data for charts."""
    student_id = session.get('student_id')
    db = get_db()
    try:
        data = db.execute('''
            SELECT strftime('%Y-%m-%d', timestamp) as day,
                   attempt_status, COUNT(*) as count
            FROM login_attempts
            WHERE student_id = ? AND timestamp > datetime('now', '-14 days')
            GROUP BY day, attempt_status
            ORDER BY day
        ''', (student_id,)).fetchall()
        
        chart_data = {}
        for row in data:
            d = row['day']
            if d not in chart_data:
                chart_data[d] = {'SUCCESS': 0, 'FAILED': 0}
            chart_data[d][row['attempt_status']] = row['count']
        
        return jsonify(chart_data)
    finally:
        db.close()


# ─────────────────────────────────────────────
# RESET / CLEAR ALL SECURITY ALERTS & LOGS
# ─────────────────────────────────────────────
@dashboard_bp.route('/api/security/reset-alerts', methods=['POST'])
@login_required
def reset_alerts():
    """Clear all security alerts, login attempts, and threat logs for the logged-in student.
       Requires login password verification before proceeding.
       Resets every reading back to 0."""
    student_id = session.get('student_id')
    if not student_id:
        return jsonify({'error': 'Not authenticated.'}), 401

    # Require password in request body
    data = request.get_json() or {}
    password = data.get('password', '')
    if not password:
        return jsonify({'error': 'Password is required to reset alerts.'}), 400

    db = get_db()
    try:
        # Verify password against stored hash
        student = db.execute(
            'SELECT password_hash FROM students WHERE student_id = ?', (student_id,)
        ).fetchone()
        if not student:
            return jsonify({'error': 'Student not found.'}), 404

        if not bcrypt.checkpw(password.encode('utf-8'), student['password_hash'].encode('utf-8')):
            return jsonify({'error': 'Incorrect password. Access denied.'}), 403

        # Password verified — proceed with reset
        # Delete all security alerts for this student
        db.execute('DELETE FROM security_alerts WHERE student_id = ?', (student_id,))
        # Delete all login attempts for this student
        db.execute('DELETE FROM login_attempts WHERE student_id = ?', (student_id,))
        # Delete all threat logs for this student
        db.execute('DELETE FROM threat_logs WHERE student_id = ?', (student_id,))
        # Reset account lock flags
        db.execute('''
            UPDATE students SET is_locked = 0, locked_until = NULL
            WHERE student_id = ?
        ''', (student_id,))
        db.commit()
        return jsonify({'success': True, 'message': 'All alerts and logs cleared. Readings reset to 0.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ─────────────────────────────────────────────
# STUDENT DETAILS TABLE PAGE
# ─────────────────────────────────────────────
@dashboard_bp.route('/students')
@login_required
def students_list():
    """Page showing all students in a table."""
    db = get_db()
    try:
        students = db.execute('''
            SELECT * FROM students ORDER BY created_at DESC
        ''').fetchall()

        total_dues = sum(float(s['dues'] or 0) for s in students)

        return render_template('students.html',
                               students=students,
                               total_dues=total_dues)
    finally:
        db.close()


@dashboard_bp.route('/api/students/<student_id>')
@login_required
def get_student(student_id):
    """API: return a single student's data as JSON."""
    db = get_db()
    try:
        s = db.execute('SELECT * FROM students WHERE student_id = ?',
                       (student_id,)).fetchone()
        if not s:
            return jsonify({'error': 'Student not found.'}), 404
        return jsonify({
            'student_id': s['student_id'],
            'first_name': s['first_name'],
            'last_name': s['last_name'],
            'email': s['email'],
            'sex': s['sex'],
            'age': s['age'],
            'branch': s['branch'],
            'year': s['year'],
            'section': s['section'],
            'village': s['village'],
            'state': s['state'],
            'fee': float(s['fee'] or 0),
            'dues': float(s['dues'] or 0),
        })
    finally:
        db.close()


@dashboard_bp.route('/api/students/update', methods=['POST'])
@login_required
def update_student():
    """API: update a student's details (owner-protected on frontend)."""
    data = request.get_json()
    if not data or not data.get('student_id'):
        return jsonify({'error': 'Missing student ID.'}), 400

    sid = data['student_id']
    db = get_db()
    try:
        existing = db.execute('SELECT student_id FROM students WHERE student_id = ?',
                              (sid,)).fetchone()
        if not existing:
            return jsonify({'error': 'Student not found.'}), 404

        db.execute('''
            UPDATE students
            SET first_name=?, last_name=?, email=?,
                sex=?, age=?, branch=?, year=?, section=?,
                village=?, state=?, fee=?, dues=?
            WHERE student_id=?
        ''', (
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('email', ''),
            data.get('sex', ''),
            int(data['age']) if data.get('age') and str(data['age']).isdigit() else None,
            data.get('branch', ''),
            int(data['year']) if data.get('year') and str(data['year']).isdigit() else None,
            data.get('section', ''),
            data.get('village', ''),
            data.get('state', ''),
            float(data['fee']) if data.get('fee') else 0,
            float(data['dues']) if data.get('dues') else 0,
            sid
        ))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
