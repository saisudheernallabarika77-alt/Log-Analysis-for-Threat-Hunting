"""
Authentication routes for CyberSecure Log System
Handles signup (3 pages), OTP verification, and login with multi-level security.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timedelta
import bcrypt
import jwt

from config import Config
from models import get_db
from email_service import (
    generate_otp, send_otp_email, send_failed_login_alert,
    send_otp_failed_alert
)
from security import (
    check_all_inputs, sanitize_input, validate_email,
    validate_student_id, log_security_alert, log_threat,
    get_client_ip, detect_sql_injection
)

auth_bp = Blueprint('auth', __name__)


# ─────────────────────────────────────────────
# SIGNUP STEP 1: Basic Registration
# ─────────────────────────────────────────────
@auth_bp.route('/signup', methods=['GET', 'POST'])
@check_all_inputs
def signup_step1():
    if request.method == 'GET':
        return render_template('signup_step1.html')
    
    first_name = sanitize_input(request.form.get('first_name', ''))
    last_name = sanitize_input(request.form.get('last_name', ''))
    student_id = sanitize_input(request.form.get('student_id', ''))
    password = request.form.get('password', '')
    email = sanitize_input(request.form.get('email', ''))
    
    errors = []
    if not first_name or len(first_name) < 2:
        errors.append('First name must be at least 2 characters.')
    if not last_name or len(last_name) < 2:
        errors.append('Last name must be at least 2 characters.')
    if not validate_student_id(student_id):
        errors.append('Student ID must be 3-20 alphanumeric characters.')
    if not validate_email(email):
        errors.append('Please enter a valid email address.')
    if len(password) < 6:
        errors.append('Password must be at least 6 characters.')
    
    if errors:
        return render_template('signup_step1.html', errors=errors,
                             first_name=first_name, last_name=last_name,
                             student_id=student_id, email=email)
    
    db = get_db()
    try:
        # Clean up stale unverified records for this student_id or email
        # Must delete child records FIRST to satisfy foreign key constraints
        stale_ids = db.execute('''
            SELECT student_id FROM students 
            WHERE (student_id = ? OR email = ?) AND is_verified = 0
        ''', (student_id, email)).fetchall()
        
        for row in stale_ids:
            sid = row['student_id']
            db.execute('DELETE FROM otp_records WHERE student_id = ?', (sid,))
            db.execute('DELETE FROM login_attempts WHERE student_id = ?', (sid,))
            db.execute('DELETE FROM security_alerts WHERE student_id = ?', (sid,))
            db.execute('DELETE FROM active_sessions WHERE student_id = ?', (sid,))
            db.execute('DELETE FROM threat_logs WHERE student_id = ?', (sid,))
            db.execute('DELETE FROM students WHERE student_id = ?', (sid,))
        db.commit()
        
        # Check if student_id or email already exists (only verified accounts)
        existing = db.execute(
            'SELECT student_id FROM students WHERE (student_id = ? OR email = ?) AND is_verified = 1',
            (student_id, email)
        ).fetchone()
        
        if existing:
            return render_template('signup_step1.html',
                                 errors=['Student ID or Email already registered.'],
                                 first_name=first_name, last_name=last_name,
                                 student_id=student_id, email=email)
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert basic student data (unverified)
        db.execute('''
            INSERT INTO students (student_id, first_name, last_name, email, password_hash, is_verified)
            VALUES (?, ?, ?, ?, ?, 0)
        ''', (student_id, first_name, last_name, email, password_hash))
        db.commit()
        
        # Generate and store OTP
        otp_code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        db.execute('''
            INSERT INTO otp_records (student_id, email, otp_code, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (student_id, email, otp_code, expires_at.strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
        
        # Send OTP email (also print to console for testing)
        print(f"\n{'='*50}")
        print(f"  OTP CODE FOR {student_id}: {otp_code}")
        print(f"  Email: {email}")
        print(f"  Expires in {Config.OTP_EXPIRY_MINUTES} minutes")
        print(f"{'='*50}\n")
        send_otp_email(email, otp_code, first_name)
        
        # Store in session for next step
        session['signup_student_id'] = student_id
        session['signup_email'] = email
        session['signup_name'] = first_name
        
        return redirect(url_for('auth.signup_step2'))
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[-] Signup error: {e}")
        return render_template('signup_step1.html',
                             errors=[f'An error occurred: {e}'],
                             first_name=first_name, last_name=last_name,
                             student_id=student_id, email=email)
    finally:
        db.close()


# ─────────────────────────────────────────────
# SIGNUP STEP 2: OTP Verification
# ─────────────────────────────────────────────
@auth_bp.route('/signup/verify', methods=['GET', 'POST'])
@check_all_inputs
def signup_step2():
    student_id = session.get('signup_student_id')
    email = session.get('signup_email')
    name = session.get('signup_name', 'Student')
    
    if not student_id or not email:
        flash('Please complete step 1 first.', 'error')
        return redirect(url_for('auth.signup_step1'))
    
    if request.method == 'GET':
        return render_template('signup_step2.html', email=email)
    
    otp_input = sanitize_input(request.form.get('otp', ''))
    
    db = get_db()
    try:
        # Get the latest OTP for this student
        otp_record = db.execute('''
            SELECT * FROM otp_records 
            WHERE student_id = ? AND is_used = 0 
            ORDER BY created_at DESC LIMIT 1
        ''', (student_id,)).fetchone()
        
        if not otp_record:
            return render_template('signup_step2.html', email=email,
                                 error='No OTP found. Please request a new one.')
        
        # Check if OTP expired
        expires_at = datetime.strptime(otp_record['expires_at'], '%Y-%m-%d %H:%M:%S')
        if datetime.now() > expires_at:
            return render_template('signup_step2.html', email=email,
                                 error='OTP has expired. Please request a new one.',
                                 show_resend=True)
        
        # Check attempts
        attempts = otp_record['attempts'] + 1
        if attempts > Config.OTP_MAX_ATTEMPTS:
            # Log security alert
            log_security_alert(student_id, 'OTP_MAX_ATTEMPTS', 'LOW',
                             f'Maximum OTP attempts exceeded for {student_id}',
                             get_client_ip())
            send_otp_failed_alert(email, attempts, name)
            return render_template('signup_step2.html', email=email,
                                 error='Maximum attempts exceeded. Please request a new OTP.',
                                 show_resend=True, blocked=True)
        
        # Update attempt count
        db.execute('UPDATE otp_records SET attempts = ? WHERE id = ?',
                  (attempts, otp_record['id']))
        db.commit()
        
        # Verify OTP
        if otp_input == otp_record['otp_code']:
            # OTP correct
            db.execute('UPDATE otp_records SET is_used = 1 WHERE id = ?', (otp_record['id'],))
            db.execute('UPDATE students SET is_verified = 1 WHERE student_id = ?', (student_id,))
            db.commit()
            
            session['otp_verified'] = True
            return redirect(url_for('auth.signup_step3'))
        else:
            # OTP incorrect
            remaining = Config.OTP_MAX_ATTEMPTS - attempts
            log_security_alert(student_id, 'OTP_FAILED', 'LOW',
                             f'Wrong OTP attempt ({attempts}/{Config.OTP_MAX_ATTEMPTS})',
                             get_client_ip())
            
            if remaining <= 0:
                send_otp_failed_alert(email, attempts, name)
            
            error_msg = f'OTP incorrect. {remaining} attempt(s) remaining.' if remaining > 0 else 'Maximum attempts exceeded.'
            return render_template('signup_step2.html', email=email,
                                 error=error_msg,
                                 show_resend=(remaining <= 0))
    finally:
        db.close()


@auth_bp.route('/signup/resend-otp', methods=['POST'])
def resend_otp():
    student_id = session.get('signup_student_id')
    email = session.get('signup_email')
    name = session.get('signup_name', 'Student')
    
    if not student_id or not email:
        return jsonify({'error': 'Session expired'}), 400
    
    db = get_db()
    try:
        # Generate new OTP
        otp_code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)
        
        db.execute('''
            INSERT INTO otp_records (student_id, email, otp_code, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (student_id, email, otp_code, expires_at.strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
        
        # Print OTP to console for testing
        print(f"\n{'='*50}")
        print(f"  RESENT OTP FOR {student_id}: {otp_code}")
        print(f"  Email: {email}")
        print(f"{'='*50}\n")
        send_otp_email(email, otp_code, name)
        return jsonify({'success': True, 'message': 'New OTP sent to your email.'})
    finally:
        db.close()


# ─────────────────────────────────────────────
# SIGNUP STEP 3: Full Details
# ─────────────────────────────────────────────
@auth_bp.route('/signup/details', methods=['GET', 'POST'])
@check_all_inputs
def signup_step3():
    student_id = session.get('signup_student_id')
    
    if not student_id or not session.get('otp_verified'):
        flash('Please complete verification first.', 'error')
        return redirect(url_for('auth.signup_step1'))
    
    if request.method == 'GET':
        return render_template('signup_step3.html')
    
    sex = sanitize_input(request.form.get('sex', ''))
    age = request.form.get('age', '')
    branch = sanitize_input(request.form.get('branch', ''))
    year = request.form.get('year', '')
    section = sanitize_input(request.form.get('section', ''))
    village = sanitize_input(request.form.get('village', ''))
    state = sanitize_input(request.form.get('state', ''))
    fee = request.form.get('fee', '0')
    dues = request.form.get('dues', '0')
    
    errors = []
    if not sex:
        errors.append('Please select your gender.')
    if not age or not age.isdigit() or int(age) < 15 or int(age) > 60:
        errors.append('Please enter a valid age (15-60).')
    if not branch:
        errors.append('Please enter your branch.')
    if not year or not year.isdigit() or int(year) < 1 or int(year) > 5:
        errors.append('Please enter a valid year (1-5).')
    if not section:
        errors.append('Please enter your section.')
    if not village:
        errors.append('Please enter your village.')
    if not state:
        errors.append('Please enter your state.')
    
    # Validate fee and dues
    try:
        fee_val = float(fee) if fee else 0
        if fee_val < 0:
            errors.append('Fee cannot be negative.')
    except ValueError:
        errors.append('Please enter a valid fee amount.')
        fee_val = 0
    
    try:
        dues_val = float(dues) if dues else 0
        if dues_val < 0:
            errors.append('Dues cannot be negative.')
    except ValueError:
        errors.append('Please enter a valid dues amount.')
        dues_val = 0
    
    if errors:
        return render_template('signup_step3.html', errors=errors,
                             sex=sex, age=age, branch=branch, year=year,
                             section=section, village=village, state=state,
                             fee=fee, dues=dues)
    
    db = get_db()
    try:
        db.execute('''
            UPDATE students SET sex=?, age=?, branch=?, year=?, section=?, village=?, state=?, fee=?, dues=?
            WHERE student_id=?
        ''', (sex, int(age), branch, int(year), section, village, state, fee_val, dues_val, student_id))
        db.commit()
        
        # Clear signup session data
        session.pop('signup_student_id', None)
        session.pop('signup_email', None)
        session.pop('signup_name', None)
        session.pop('otp_verified', None)
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        print(f"[-] Details save error: {e}")
        return render_template('signup_step3.html', errors=['An error occurred. Please try again.'])
    finally:
        db.close()


# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
@check_all_inputs
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    student_id = sanitize_input(request.form.get('student_id', ''))
    password = request.form.get('password', '')
    ip_address = get_client_ip()
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Also do inline SQL injection check on raw values
    for field_name, field_value in [('student_id', request.form.get('student_id', '')),
                                      ('password', request.form.get('password', ''))]:
        is_malicious, pattern = detect_sql_injection(field_value)
        if is_malicious:
            log_security_alert(student_id or 'UNKNOWN', 'SQL_INJECTION', 'CRITICAL',
                             f'SQL Injection in login field: {field_name}',
                             ip_address, f'Pattern: {pattern}')
            log_threat('SQL_INJECTION', ip_address, student_id or 'UNKNOWN',
                      field_value[:500], 100, 'BLOCKED')
            return render_template('login.html',
                                 sql_injection_detected=True,
                                 error='🚨 CRITICAL SECURITY BREACH ATTEMPT DETECTED 🚨')
    
    if not student_id or not password:
        return render_template('login.html', error='Please enter both Student ID and Password.')
    
    db = get_db()
    try:
        # Find the student
        student = db.execute(
            'SELECT * FROM students WHERE student_id = ?', (student_id,)
        ).fetchone()
        
        if not student:
            # Log failed attempt for unknown ID
            db.execute('''
                INSERT INTO login_attempts (student_id, ip_address, attempt_status, user_agent)
                VALUES (?, ?, 'FAILED', ?)
            ''', (student_id, ip_address, user_agent))
            db.commit()
            return render_template('login.html', error='Invalid Student ID or Password.')
        
        # Check if account is locked
        if student['is_locked'] and student['locked_until']:
            locked_until = datetime.strptime(student['locked_until'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() < locked_until:
                remaining = int((locked_until - datetime.now()).total_seconds())
                if remaining < 1:
                    remaining = 1
                return render_template('login.html',
                                     error='Account is temporarily locked.',
                                     account_locked=True,
                                     lockout_seconds=remaining)
            else:
                # Unlock the account
                db.execute('UPDATE students SET is_locked = 0, locked_until = NULL WHERE student_id = ?',
                          (student_id,))
                db.commit()
        
        # Check if verified
        if not student['is_verified']:
            return render_template('login.html', error='Please complete email verification first.')
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), student['password_hash'].encode('utf-8')):
            # SUCCESS
            db.execute('''
                INSERT INTO login_attempts (student_id, ip_address, attempt_status, user_agent)
                VALUES (?, ?, 'SUCCESS', ?)
            ''', (student_id, ip_address, user_agent))
            db.commit()
            
            # Create JWT token
            token = jwt.encode({
                'student_id': student_id,
                'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRY_HOURS)
            }, Config.JWT_SECRET, algorithm='HS256')
            
            # Store session
            session['student_id'] = student_id
            session['student_name'] = student['first_name']
            session['token'] = token
            session['logged_in'] = True
            
            return redirect(url_for('dashboard.home'))
        else:
            # FAILED LOGIN - Level 2 Security
            db.execute('''
                INSERT INTO login_attempts (student_id, ip_address, attempt_status, user_agent)
                VALUES (?, ?, 'FAILED', ?)
            ''', (student_id, ip_address, user_agent))
            db.commit()
            
            # Count recent failed attempts
            failed_count = db.execute('''
                SELECT COUNT(*) as count FROM login_attempts
                WHERE student_id = ? AND attempt_status = 'FAILED'
                AND timestamp > datetime('now', '-1 hour')
            ''', (student_id,)).fetchone()['count']
            
            # Log security alert
            severity = 'CRITICAL' if failed_count >= Config.MAX_FAILED_LOGIN_ATTEMPTS else 'MEDIUM'
            log_security_alert(student_id, 'FAILED_LOGIN', severity,
                             f'Failed login attempt #{failed_count} from IP {ip_address}',
                             ip_address)
            
            # Send email alert
            send_failed_login_alert(
                student['email'], student_id, ip_address,
                failed_count, student['first_name']
            )
            
            # Lock account if too many attempts
            if failed_count >= Config.MAX_FAILED_LOGIN_ATTEMPTS:
                locked_until = datetime.now() + timedelta(seconds=Config.ACCOUNT_LOCK_SECONDS)
                db.execute(
                    'UPDATE students SET is_locked = 1, locked_until = ? WHERE student_id = ?',
                    (locked_until.strftime('%Y-%m-%d %H:%M:%S'), student_id)
                )
                db.commit()
                
                log_threat('ACCOUNT_LOCKED', ip_address, student_id,
                          f'{failed_count} failed attempts', 80, 'ACCOUNT_LOCKED')
                
                return render_template('login.html',
                                     error=f'Account locked due to {failed_count} failed attempts.',
                                     account_locked=True, failed_attempts=failed_count,
                                     lockout_seconds=Config.ACCOUNT_LOCK_SECONDS)
            
            return render_template('login.html',
                                 error='Invalid Student ID or Password.',
                                 failed_login=True, failed_attempts=failed_count)
    finally:
        db.close()


# ─────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
