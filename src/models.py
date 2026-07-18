"""
Database models and initialization for CyberSecure Log System
Database: cybersec_log_system (SQLite)
"""
import sqlite3
import os
from config import Config


def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database with all tables."""
    conn = get_db()
    cursor = conn.cursor()

    # Table 1: students
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id VARCHAR(20) PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            sex VARCHAR(10),
            age INTEGER,
            branch VARCHAR(50),
            year INTEGER,
            section VARCHAR(10),
            village VARCHAR(100),
            state VARCHAR(100),
            fee REAL DEFAULT 0,
            dues REAL DEFAULT 0,
            is_verified INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0,
            locked_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table 2: login_attempts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(20),
            ip_address VARCHAR(45),
            attempt_status VARCHAR(20) CHECK(attempt_status IN ('SUCCESS', 'FAILED')),
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')

    # Table 3: security_alerts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS security_alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(20),
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) CHECK(severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
            message TEXT,
            ip_address VARCHAR(45),
            details TEXT,
            is_resolved INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')

    # Table 4: otp_records
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id VARCHAR(20),
            email VARCHAR(100),
            otp_code VARCHAR(6) NOT NULL,
            attempts INTEGER DEFAULT 0,
            is_used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')

    # Table 5: active_sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            student_id VARCHAR(20),
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')

    # Table 6: threat_logs (for threat hunting)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS threat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type VARCHAR(50) NOT NULL,
            source_ip VARCHAR(45),
            student_id VARCHAR(20),
            payload TEXT,
            risk_score INTEGER DEFAULT 0,
            action_taken VARCHAR(50),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add fee/dues columns to existing databases (migration)
    try:
        cursor.execute('ALTER TABLE students ADD COLUMN fee REAL DEFAULT 0')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE students ADD COLUMN dues REAL DEFAULT 0')
    except Exception:
        pass

    conn.commit()
    conn.close()
    print("[+] Database initialized successfully: cybersec_log_system")


if __name__ == '__main__':
    init_db()
