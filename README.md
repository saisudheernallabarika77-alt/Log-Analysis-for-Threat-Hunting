### 5.3 Signup Flow (3 Steps)
| Step | Route | What Happens |
|------|-------|-------------|
| **Step 1** | `POST /signup` | Validates details, generates OTP, sends email |
| **Step 2** | `POST /signup/verify` | Verifies OTP (5 min expiry, 3 attempts max) |
| **Step 3** | `POST /signup/details` | Collects full profile, redirects to login |

### 5.4 Login Security (Multi-Level)
- **Level 1:** Input validation against 16 SQL injection regex patterns
- **Level 2:** SQL injection detected → logs alert, sends email, blocks with siren page
- **Level 3:** Password verification via bcrypt
- **Level 4:** Account lockout after 3 failed attempts (59-second timer)

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
| Signup OTP | `send_otp_email()` |
| Failed Login | `send_failed_login_alert()` |
| SQL Injection Detected | `send_sql_injection_alert()` |
| OTP Attempts Exceeded | `send_otp_failed_alert()` |

---

## 7. SOUND EFFECTS (Web Audio API)

All sounds generated programmatically via `static/js/sounds.js` — no external audio files. Includes button clicks, hover effects, boot sequence, login success/fail, lockout alarm, SQL injection siren, and ambient gate sounds.

---

## 8. SECURITY FEATURES SUMMARY

| Feature | Implementation |
|---------|---------------|
| Password Hashing | bcrypt (salt + hash) |
| Session Management | Flask session + JWT tokens (24h expiry) |
| SQL Injection Detection | 16 compiled regex patterns + heuristic check |
| Input Sanitization | `html.escape()` on all user inputs |
| Account Lockout | 3 failed attempts → 59-second lock |
| OTP Verification | 6-digit code, 5-minute expiry, 3 attempts max |
| IP Logging | Every login attempt records IP + User-Agent |
| Risk Scoring | Weighted algorithm, max 100 |
| Email Alerts | Real-time notifications for security events |
| Threat Logging | All attacks logged with payload + risk score |
| CSRF Protection | Session cookie: HttpOnly, SameSite=Lax |

---

## 9. HOW TO RUN

```bash
# 1. Navigate to project
cd prj_3

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r src/requirements.txt

# 4. Set environment variables for SMTP credentials
# (see config.py for required variable names)

# 5. Run the application
python src/app.py

# 6. Open browser
# → http://127.0.0.1:5000
