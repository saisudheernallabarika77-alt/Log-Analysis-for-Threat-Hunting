import sqlite3
import bcrypt

conn = sqlite3.connect('cybersec_log_system.db')
cur = conn.cursor()

new_password = "200608@NBSS"
hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
hashed_str = hashed.decode('utf-8')  # bytes ni string గా convert చేస్తుంది

cur.execute("UPDATE students SET password_hash = ? WHERE student_id = ?", (hashed_str, "25B25A4619"))
conn.commit()

print("Password updated successfully!")
print("New password is:", new_password)