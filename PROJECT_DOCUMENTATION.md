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

```
prj_3/
├── src/
│   ├── app.py                  # Main entry point, Flask app factory
│   ├── config.py               # All configuration constants
│   ├── models.py               # SQLite database schema (6 tables)
│   ├── auth.py                 # Signup (3 steps), OTP, Login, Logout
│   ├── dashboard.py            # Dashboard, Security Center, Student APIs
│   ├── security.py             # SQL injection detection, input validation, risk scoring
│   ├── threat_hunter.py        # Threat hunting API endpoints
│   ├── email_service.py        # Gmail SMTP: OTP, login alerts, SQL injection alerts
│   ├── requirements.txt        # Flask 3.0.0, bcrypt 4.1.2, PyJWT 2.8.0
│   ├── cybersec_log_system.db  # SQLite database file
│   ├── templates/
│   │   ├── base.html           # Base layout (matrix rain, flash messages, sounds.js)
│   │   ├── splash.html         # KIET intro — "Welcome to WEBSITE" gate + boot sound
│   │   ├── welcome.html        # Login / Sign Up option cards
│   │   ├── login.html          # Login form + lockout overlay (59s timer)
│   │   ├── signup_step1.html   # Step 1: Name, ID, Email, Password
│   │   ├── signup_step2.html   # Step 2: OTP verification
│   │   ├── signup_step3.html   # Step 3: Gender, Age, Branch, Year, Section, Village, State, Fee, Dues
│   │   ├── dashboard.html      # 4 info cards (Personal, Academic, Location, Financial)
│   │   ├── security_page.html  # Security stats, risk meter, charts, alerts, threat hunting
│   │   ├── students.html       # All students table with edit modal
│   │   └── sqli_blocked.html   # "GOO BYE MISTER" — SQL injection block page + siren
│   └── static/
│       ├── css/style.css       # Full cyber theme (black + neon green, ~1300 lines)
│       └── js/
│           ├── matrix.js       # Matrix rain canvas animation
│           ├── main.js         # Password toggle, flash auto-dismiss
│           ├── dashboard.js    # Chart.js login chart, risk meter, threat refresh
│           └── sounds.js       # Web Audio API — 11 cyber sound effects
```

---

## 3. DATABASE SCHEMA (SQLite)

**File:** `cybersec_log_system.db` | **Mode:** WAL | **Foreign Keys:** ON

| # | Table | Purpose | Key Columns |
|---|-------|---------|-------------|
| 1 | **students** | Student records | `student_id` (PK), `first_name`, `last_name`, `email` (UNIQUE), `password_hash`, `sex`, `age`, `branch`, `year`, `section`, `village`, `state`, `fee`, `dues`, `is_verified`, `is_locked`, `locked_until` |
| 2 | **login_attempts** | Every login (success/fail) | `id`, `student_id` (FK), `ip_address`, `attempt_status` (SUCCESS/FAILED), `user_agent`, `timestamp` |
| 3 | **security_alerts** | All security events | `alert_id`, `student_id` (FK), `alert_type`, `severity` (LOW/MEDIUM/HIGH/CRITICAL), `message`, `ip_address`, `details`, `is_resolved` |
| 4 | **otp_records** | OTP codes for signup | `id`, `student_id` (FK), `email`, `otp_code`, `attempts`, `is_used`, `expires_at` |
| 5 | **active_sessions** | Session tracking | `session_id` (PK), `student_id` (FK), `ip_address`, `user_agent`, `expires_at` |
| 6 | **threat_logs** | Threat hunting data | `id`, `event_type`, `source_ip`, `student_id`, `payload`, `risk_score`, `action_taken` |

---

## 4. CONFIGURATION (config.py)

| Setting | Value | Purpose |
|---------|-------|---------|
| `MAX_FAILED_LOGIN_ATTEMPTS` | 3 | Lock account after 3 wrong passwords |
| `ACCOUNT_LOCK_SECONDS` | 59 | Lock duration in seconds |
| `OTP_EXPIRY_MINUTES` | 5 | OTP valid for 5 minutes |
| `OTP_MAX_ATTEMPTS` | 3 | Max OTP entry attempts |
| `JWT_EXPIRY_HOURS` | 24 | Session token lifetime |
| `SMTP_SERVER` | smtp.gmail.com:587 | Gmail SMTP with TLS |
| `SMTP_EMAIL` | darlapraveen87@gmail.com | Sender email |
| `SMTP_PASSWORD` | cihq twbg zwnw kjrp | Gmail App Password |
| `SQL_INJECTION_PATTERNS` | 16 regex patterns | Detects OR, UNION SELECT, DROP, etc. |

---

## 5. APPLICATION FLOW (Pin-to-Pin)

### 5.1 Startup
```
python src/app.py
  → create_app()
    → Flask(__name__)
    → Register blueprints: auth_bp, dashboard_bp, threat_bp
    → init_db() → Creates 6 tables if not exist, adds fee/dues migration
    → Routes: / → splash.html, /welcome → welcome.html
  → Runs on http://127.0.0.1:5000
```

### 5.2 Page Flow
```
[Splash Page /] → "Welcome to WEBSITE" popup → Click "INITIALIZE"
    ↓ (ambient hum plays, then boot scan sound, 5.5s)
[Welcome Page /welcome] → Two cards: LOGIN or SIGN UP
    ↓
[Login /login] ←─── OR ───→ [Signup Step 1 /signup]
    ↓                              ↓
[Dashboard /dashboard]        [Step 2 /signup/verify] → OTP email sent
    ↓                              ↓
[Security /security]          [Step 3 /signup/details] → Full profile
    ↓                              ↓
[Students /students]          [Redirect → Login]
```

### 5.3 Signup Flow (3 Steps)
| Step | Route | What Happens |
|------|-------|-------------|
| **Step 1** | `POST /signup` | Validates name, ID, email, password → Cleans stale unverified records (deletes FK children first) → Inserts student (`is_verified=0`) → Generates 6-digit OTP → Stores in `otp_records` → Sends OTP email via Gmail SMTP → Redirects to Step 2 |
| **Step 2** | `POST /signup/verify` | User enters OTP → Checks expiry (5 min) → Checks attempts (max 3) → If correct: sets `is_verified=1` → Redirects to Step 3. If wrong: logs `OTP_FAILED` alert. Resend OTP via `POST /signup/resend-otp` |
| **Step 3** | `POST /signup/details` | Collects: Gender, Age, Branch (CSC/CSD/CSM/AID/ECE/EEE/MECH/CIVIL/IT), Year, Section, Village, State, Fee (₹), Dues (₹) → Updates student row → Clears session → Flash "Registration successful!" → Redirects to login |

### 5.4 Login Security (Multi-Level)

**Level 1 — Input Validation:**
- `@check_all_inputs` decorator scans ALL form fields, query params, JSON body
- Tests each value against 16 compiled SQL injection regexes
- Also checks heuristic: ≥3 suspicious characters (`'`, `"`, `;`, `--`, `/*`, etc.)

**Level 2 — SQL Injection Detected:**
```
Input matched → log_security_alert(CRITICAL) → log_threat(risk=100, BLOCKED)
  → Send email: send_sql_injection_alert() → Render sqli_blocked.html (403)
  → Page shows "GOO BYE MISTER" with siren alarm sound (14 wail cycles)
```

**Level 3 — Password Verification:**
- `bcrypt.checkpw()` against stored hash
- **Success:** Log SUCCESS attempt → Create JWT token (24h) → Set session → Redirect to `/dashboard`
- **Fail:** Log FAILED attempt → Count recent failures → Send email alert

**Level 4 — Account Lockout (3 attempts):**
```
failed_count ≥ 3 → Set is_locked=1, locked_until=now+59s
  → Log threat (risk=80, ACCOUNT_LOCKED)
  → Render login.html with lockout overlay
  → Full-screen red shield, 59-second SVG ring countdown
  → lockoutAlarm() sound plays, login button disabled
  → Timer expires → overlay fades, login re-enabled, loginSuccess() sound
```

### 5.5 Dashboard
- **Route:** `GET /dashboard` (requires `login_required`)
- Fetches logged-in student's record only
- Displays 4 cards:
  1. **Personal Info** — Email, Gender, Age
  2. **Academic Info** — Branch, Year, Section
  3. **Location Info** — Village, State
  4. **Financial Info** — Fee (₹), Dues (₹)
- Each card has an **Edit** button → Owner password gate (`"NIKU EYNDUKURA"`) → Edit modal → `POST /api/students/update`
- **Navigation:** Security button → `/security`, Logout → `/logout`

### 5.6 Security Center
- **Route:** `GET /security`
- **Stats Grid:** Failed logins (24h), Total logins, Risk score, Alert counts, Unique IPs, SQL injection count
- **Risk Meter:** 0–100 score with color gradient (green/yellow/red)
- **Charts:** 14-day login history (Chart.js bar chart)
- **Tables:** Recent 10 security alerts, Recent 10 login attempts
- **API endpoints:** `/api/dashboard/stats`, `/api/dashboard/login-chart`

### 5.7 Threat Hunting APIs
| Endpoint | Returns |
|----------|---------|
| `GET /api/threat/overview` | Total alerts, severity breakdown, SQL injection count, failed logins, unique threat IPs |
| `GET /api/threat/login-analysis` | Hourly distribution, daily trends, IP-based analysis |
| `GET /api/threat/ip-analysis` | Top suspicious IPs, login counts per IP |
| `GET /api/threat/recent` | Latest 20 threat log entries |
| `GET /api/threat/hunt` | Pattern-based threat search with advanced queries |

---

## 6. EMAIL ALERTS (Gmail SMTP)

All emails use a **cyber-themed HTML template** (dark background, neon green/red, shield icon).

| Trigger | Function | Severity Color |
|---------|----------|----------------|
| Signup OTP | `send_otp_email()` | Green (#00FF00) |
| Failed Login | `send_failed_login_alert()` | Orange (#FFA500) or Red (#FF4444 if ≥5) |
| SQL Injection Detected | `send_sql_injection_alert()` | Red (#FF0000) |
| OTP Attempts Exceeded | `send_otp_failed_alert()` | Orange (#FFA500) |

---

## 7. SOUND EFFECTS (Web Audio API)

**File:** `static/js/sounds.js` — All sounds generated programmatically, zero external audio files.

| # | Sound | Function | Trigger |
|---|-------|----------|---------|
| 1 | **Button Click** | `CyberSound.click()` | Auto-attached to all buttons/links globally |
| 2 | **Hover** | `CyberSound.hover()` | Welcome page card hover |
| 3 | **Boot Scan** | `CyberSound.bootScan()` | Splash page after clicking "INITIALIZE" — 8-phase 5-second sequence: sub-bass rumble → dual frequency sweep → 14 rapid data beeps → noise hiss → analysis pulses → encryption locks → firewall tones → "SYSTEM READY" chime |
| 4 | **Login Success** | `CyberSound.loginSuccess()` | Success flash, lockout expire, save success |
| 5 | **Login Failed** | `CyberSound.loginFailed()` | Wrong password, save fail |
| 6 | **Notification** | `CyberSound.notification()` | Dashboard load, edit modal open |
| 7 | **Lockout Alarm** | `CyberSound.lockoutAlarm()` | Lockout overlay appears |
| 8 | **Siren** | `CyberSound.sirenStart()` | SQL injection "GOO BYE MISTER" page — impact boom + 14-cycle wailing siren (400Hz↔900Hz) |
| 9 | **Page Transition** | `CyberSound.transition()` | Splash → welcome redirect |
| 10 | **Typing** | `CyberSound.type()` | Edit form inputs, password fields |
| 11 | **Gate Ambient** | `CyberSound.gateAmbient()` | Splash page gate — looping sub-bass drone + pulsing hum + radar pings + data blips + sweep tones (stops on "INITIALIZE" click) |

---

## 8. FRONTEND ARCHITECTURE

### Templates (Jinja2)
- **base.html** — Master layout loaded by all pages (except `sqli_blocked.html`). Includes: matrix rain canvas, flash messages, `matrix.js`, `main.js`, `sounds.js`, `{% block extra_scripts %}`.
- **sqli_blocked.html** — Standalone HTML (no base.html). Has its own inline siren sound code.

### CSS Theme
- **Font:** Orbitron (headings), Share Tech Mono (body)
- **Colors:** Background `#0a0a14`, Cards `#0f0f1a`, Neon Green `#00FF00`, Border `#1a1a2e`
- **Effects:** Matrix rain, scan lines, pulsing glows, corner brackets

### Key UI Components
| Component | Page | Description |
|-----------|------|-------------|
| Click Gate Popup | splash.html | "Welcome to WEBSITE" card with shield, divider, "CLICK TO INITIALIZE" button, corner marks |
| Loading Bar | splash.html | Animated fill bar (0→100% over 3.5s) |
| Option Cards | welcome.html | LOGIN (green) and SIGN UP (blue) with hover glow, arrow reveal |
| Lockout Overlay | login.html | Full-screen red shield, SVG ring countdown (59s), pulsing bars |
| 4 Info Cards | dashboard.html | 2×2 grid — each with icon header, data table, Edit button |
| Password Gate Modal | dashboard.html | Owner password → `"NIKU EYNDUKURA"` → unlocks edit modal |
| Edit Modal | dashboard.html | Full form with all student fields, saves via `POST /api/students/update` |
| Risk Meter | security_page.html | SVG gauge 0–100 with gradient colors |
| GOO BYE MISTER | sqli_blocked.html | Red theme, shaking shield, warning bars, X marks, emergency siren |

---

## 9. SECURITY FEATURES SUMMARY

| Feature | Implementation |
|---------|---------------|
| Password Hashing | bcrypt (salt + hash) |
| Session Management | Flask session + JWT tokens (24h expiry) |
| SQL Injection Detection | 16 compiled regex patterns + heuristic check (≥3 suspicious chars) |
| Input Sanitization | `html.escape()` on all user inputs |
| Account Lockout | 3 failed attempts → 59-second lock with DB flag |
| OTP Verification | 6-digit code, 5-minute expiry, 3 attempts max |
| IP Logging | Every login attempt records IP + User-Agent |
| Risk Scoring | Algorithm: failed_logins×10 + alerts×5 + critical×20 + extra_IPs×10 (max 100) |
| Email Alerts | Immediate notification for: failed logins, SQL injection, OTP failures |
| Threat Logging | All attacks logged in `threat_logs` table with payload + risk score |
| CSRF Protection | Session cookie: HttpOnly, SameSite=Lax |
| Stale Record Cleanup | Signup deletes unverified records (FK children first) to prevent duplication |

---

## 10. HOW TO RUN

```bash
# 1. Navigate to project
cd prj_3

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r src/requirements.txt

# 4. Run the application
python src/app.py

# 5. Open browser
# → http://127.0.0.1:5000
```

**Dependencies:** Flask 3.0.0, bcrypt 4.1.2, PyJWT 2.8.0 (all other modules are Python standard library).

---

## 11. API REFERENCE

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET/POST | `/signup` | No | Step 1 registration |
| GET/POST | `/signup/verify` | Session | Step 2 OTP verification |
| POST | `/signup/resend-otp` | Session | Resend OTP |
| GET/POST | `/signup/details` | Session | Step 3 full details |
| GET/POST | `/login` | No | Login with security checks |
| GET | `/logout` | No | Clear session |
| GET | `/dashboard` | JWT | Student's 4-card dashboard |
| GET | `/security` | JWT | Security center with charts |
| GET | `/students` | JWT | All students table |
| GET | `/api/students/<id>` | JWT | Single student JSON |
| POST | `/api/students/update` | JWT | Update student details |
| GET | `/api/dashboard/stats` | JWT | Real-time security stats |
| GET | `/api/dashboard/login-chart` | JWT | 14-day login chart data |
| GET | `/api/threat/overview` | JWT | Threat landscape summary |
| GET | `/api/threat/login-analysis` | JWT | Time-based login analysis |
| GET | `/api/threat/ip-analysis` | JWT | IP-based threat analysis |
| GET | `/api/threat/recent` | JWT | Latest 20 threat logs |
| GET | `/api/threat/hunt` | JWT | Advanced threat search |

---

*Document generated for KIET Group of Institutions — CyberSecure Log Analysis & Threat Hunting System*
