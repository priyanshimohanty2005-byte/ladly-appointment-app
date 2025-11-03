# db.py
import sqlite3
from datetime import datetime

DB_PATH = "ladly.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # customers
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        created_at TEXT
    )
    """)
    # staff
    cur.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialty TEXT,
        created_at TEXT
    )
    """)
    # appointments
    cur.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        staff_id INTEGER,
        service TEXT,
        date TEXT,         -- ISO date YYYY-MM-DD
        time TEXT,         -- HH:MM
        amount REAL,
        status TEXT DEFAULT 'scheduled', -- scheduled / completed / cancelled
        created_at TEXT,
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY(staff_id) REFERENCES staff(staff_id)
    )
    """)
    # invoices (we'll add later)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        invoice_date TEXT,
        total_amount REAL,
        FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
    )
    """)
    conn.commit()
    conn.close()

# CUSTOMER FUNCTIONS
def add_customer(name, phone=None, email=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO customers (name, phone, email, created_at) VALUES (?, ?, ?, ?)",
        (name, phone, email, datetime.utcnow().isoformat())
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid

def get_customers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# STAFF FUNCTIONS
def add_staff(name, specialty=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO staff (name, specialty, created_at) VALUES (?, ?, ?)",
        (name, specialty, datetime.utcnow().isoformat())
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid

def get_staff():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM staff ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# APPOINTMENT FUNCTIONS
def add_appointment(customer_id, staff_id, service, date, time, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO appointments (customer_id, staff_id, service, date, time, amount, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, staff_id, service, date, time, amount, datetime.utcnow().isoformat()))
    conn.commit()
    appt_id = cur.lastrowid
    conn.close()
    return appt_id

def get_appointments(filter_date=None, status=None):
    conn = get_conn()
    cur = conn.cursor()
    query = "SELECT a.*, c.name AS customer_name, s.name AS staff_name FROM appointments a LEFT JOIN customers c ON a.customer_id=c.customer_id LEFT JOIN staff s ON a.staff_id=s.staff_id"
    conditions = []
    params = []
    if filter_date:
        conditions.append("a.date = ?")
        params.append(filter_date)
    if status:
        conditions.append("a.status = ?")
        params.append(status)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY a.date, a.time"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_appointment_status(appointment_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE appointments SET status = ? WHERE appointment_id = ?", (status, appointment_id))
    conn.commit()
    conn.close()
