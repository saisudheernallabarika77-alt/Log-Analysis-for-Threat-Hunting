# Multi-Level Secured Log Analysis & Threat Hunting Web Application
## With Real-Time Email Alert System

**Institution:** KIET GROUP OF INSTITUTIONS — Department of Computer Science & Engineering
**Technology:** Python Flask | SQLite | Web Audio API | Gmail SMTP
**Version:** 1.0 | **Server:** http://127.0.0.1:5000

---

## 1. PROJECT OVERVIEW

A cybersecurity-themed web application that provides:
- **3-Step Signup** with OTP email verification
- **Multi-Level Login Security** (lockout after 3 failed attempts, 59-second timer)
- **Real-Time SQL Injection Detection & Blocking** with emergency siren alert page
- **Student Dashboard** with personal data in 4 grouped cards
- **Security Center** with risk scoring, charts, and threat hunting APIs
- **Real-Time Email Alerts** via Gmail SMTP for every security event
- **Immersive Cyber Sound Effects** (Web Audio API — no external files)

---

## 2. FOLDER STRUCTURE

prj_3/
- src/
  - app.py — Main entry point, Flask app factory
  - config.py — All configuration constants
  - models.py — SQLite database schema (6 tables)
  - auth.py — Signup (3 steps), OTP, Login, Logout
  - dashboard.py — Dashboard, Security Center, Student APIs
  - security.py — SQL injection detection, input validation, risk scoring
  - threat_hunter.py — Threat hunting API endpoints
  - email_service.py — Gmail SMTP: OTP, login alerts, SQL injection alerts
  - requirements.txt — Flask 3.0.0, bcrypt 4.1.2, PyJWT 2.8.0
  - cybersec_log_system.db — SQLite database file
  - templates/
    - base.html, splash.html, welcome.html, login.html
    - signup_step1.html, signup_step2.html, signup_step3.html
    - dashboard.html, security_page.html, students.html, sqli_blocked.html
  - static/
    - css/style.css
    - js/matrix.js, main.js, dashboard.js, sounds.js

---

## 3. DATABASE SCHEMA (SQLite)

**File:** cybersec_log_system.db | **Mode:** WAL | **Foreign Keys:** ON

| # | Table | Purpose |
|---|-------|---------|
| 1 | students | Student records |
| 2 | login_attempts | Every login (success/fail) |
| 3 | security_alerts | All security events |
| 4 | otp_records | OTP codes for signup |
| 5 | active_sessions | Session tracking |
| 6 | threat_logs | Threat hunting data |

---

## 4. CONFIGURATION

| Setting | Value | Purpose |
|---------|-------|---------|
| MAX_FAILED_LOGIN_ATTEMPTS | 3 | Lock account after 3 wrong passwords |
| ACCOUNT_LOCK_SECONDS | 59 | Lock duration in seconds |
| OTP_EXPIRY_MINUTES | 5 | OTP valid for 5 minutes |
| OTP_MAX_ATTEMPTS | 3 | Max OTP entry attempts |
| JWT_EXPIRY_HOURS | 24 | Session token lifetime |
| SMTP_SERVER | smtp.gmail.com:587 | Gmail SMTP with TLS |

> SMTP email and app password are stored securely via environment variables and are not committed to this repository.

---

## 5. APPLICATION FLOW

### 5.1 Startup

python src/app.py
- create_app()
- Flask(__name__)
- Register blueprints: auth_bp, dashboard_bp, threat_bp
- init_db() creates 6 tables if not exist
- Runs on http://127.0.0.1:5000

### 5.2 Page Flow

Splash Page (/) leads to a Welcome popup, then click "INITIALIZE".
Welcome Page (/welcome) offers LOGIN or SIGN UP.
Login (/login) leads to Dashboard (/dashboard), then Security (/security), then Students (/students).
Signup Step 1 leads to Step 2 OTP, then Step 3 Details, then redirects to Login.

### 5.3 Signup Flow (3 Steps)

| Step | Route | What Happens |
|------|-------|-------------|
| Step 1 | POST /signup | Validates details, generates OTP, sends email |
| Step 2 | POST /signup/verify | Verifies OTP (5 min expiry, 3 attempts max) |
| Step 3 | POST /signup/details | Collects full profile, redirects to login |

### 5.4 Login Security (Multi-Level)

- Level 1: Input validation against 16 SQL injection regex patterns
- Level 2: SQL injection detected — logs alert, sends email, blocks with siren page
- Level 3: Password verification via bcrypt
- Level 4: Account lockout after 3 failed attempts (59-second timer)

### 5.5 Dashboard

4 cards: Personal Info, Academic Info, Location Info, Financial Info — each editable via password-gated modal.

### 5.6 Security Center

Risk meter, 14-day login chart, recent alerts and login attempts tables.

### 5.7 Threat Hunting APIs

Overview, login analysis, IP analysis, recent threats, advanced hunt search.

---

## 6. EMAIL ALERTS (Gmail SMTP)

| Trigger | Function |
|---------|----------|
| Signup OTP | send_otp_email() |
| Failed Login | send_failed_login_alert() |
| SQL Injection Detected | send_sql_injection_alert() |
| OTP Attempts Exceeded | send_otp_failed_alert() |

---

## 7. SOUND EFFECTS (Web Audio API)

All sounds generated programmatically via static/js/sounds.js — no external audio files. Includes button clicks, hover effects, boot sequence, login success/fail, lockout alarm, SQL injection siren, and ambient gate sounds.

---

## 8. SECURITY FEATURES SUMMARY

| Feature | Implementation |
|---------|---------------|
| Password Hashing | bcrypt (salt + hash) |
| Session Management | Flask session + JWT tokens (24h expiry) |
| SQL Injection Detection | 16 compiled regex patterns + heuristic check |
| Input Sanitization | html.escape() on all user inputs |
| Account Lockout | 3 failed attempts leads to 59-second lock |
| OTP Verification | 6-digit code, 5-minute expiry, 3 attempts max |
| IP Logging | Every login attempt records IP + User-Agent |
| Risk Scoring | Weighted algorithm, max 100 |
| Email Alerts | Real-time notifications for security events |
| Threat Logging | All attacks logged with payload + risk score |
| CSRF Protection | Session cookie: HttpOnly, SameSite=Lax |

---

## 9. HOW TO RUN

Step 1 — Navigate to project folder: cd prj_3

Step 2 — Create virtual environment:
python -m venv .venv
.venv\Scripts\activate   (on Windows)

Step 3 — Install dependencies:
pip install -r src/requirements.txt

Step 4 — Set environment variables for SMTP credentials (see config.py for required variable names)

Step 5 — Run the application:
python src/app.py

Step 6 — Open browser at http://127.0.0.1:5000

**Dependencies:** Flask 3.0.0, bcrypt 4.1.2, PyJWT 2.8.0

---

## 10. API REFERENCE

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET/POST | /signup | No | Step 1 registration |
| GET/POST | /signup/verify | Session | Step 2 OTP verification |
| POST | /signup/resend-otp | Session | Resend OTP |
| GET/POST | /signup/details | Session | Step 3 full details |
| GET/POST | /login | No | Login with security checks |
| GET | /logout | No | Clear session |
| GET | /dashboard | JWT | Student's dashboard |
| GET | /security | JWT | Security center |
| GET | /students | JWT | All students table |
| GET | /api/students/<id> | JWT | Single student JSON |
| POST | /api/students/update | JWT | Update student details |
| GET | /api/dashboard/stats | JWT | Real-time security stats |
| GET | /api/dashboard/login-chart | JWT | 14-day login chart data |
| GET | /api/threat/overview | JWT | Threat landscape summary |
| GET | /api/threat/login-analysis | JWT | Time-based login analysis |
| GET | /api/threat/ip-analysis | JWT | IP-based threat analysis |
| GET | /api/threat/recent | JWT | Latest 20 threat logs |
| GET | /api/threat/hunt | JWT | Advanced threat search |

---

*Developed for KIET Group of Institutions — CyberSecure Log Analysis & Threat Hunting System*
