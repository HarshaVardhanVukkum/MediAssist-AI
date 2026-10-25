import os
import sqlite3
from datetime import datetime, date
from functools import wraps
from pathlib import Path

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mediassist.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

OLLAMA_ENABLED = os.environ.get("OLLAMA_ENABLED", "false").lower() == "true"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")

DOCTORS = [
    ("Dr. Ananya Rao", "General Medicine", "Weekdays, 9:00 AM - 1:00 PM"),
    ("Dr. Kiran Kumar", "Dermatology", "Mon, Wed, Fri, 2:00 PM - 5:00 PM"),
    ("Dr. Meera Iyer", "Pediatrics", "Weekdays, 10:00 AM - 2:00 PM"),
    ("Dr. Rahul Varma", "Cardiology", "Tue, Thu, Sat, 9:00 AM - 12:00 PM"),
]

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'patient',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            availability TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Booked',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        );
    """)
    doctor_count = db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    if doctor_count == 0:
        db.executemany("INSERT INTO doctors(name, specialty, availability) VALUES (?, ?, ?)", DOCTORS)
    admin = db.execute("SELECT id FROM users WHERE email = ?", ("admin@mediassist.local",)).fetchone()
    if not admin:
        db.execute(
            "INSERT INTO users(name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Demo Administrator", "admin@mediassist.local", generate_password_hash("Admin123!"), "admin")
        )
    db.commit()
    db.close()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in as an administrator.", "info")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("This page is only available to the administrator demo account.", "error")
            return redirect(url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}

@app.route("/")
def index():
    db = get_db()
    doctors = db.execute("SELECT * FROM doctors ORDER BY name").fetchall()
    return render_template("index.html", doctors=doctors)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password with at least 8 characters.", "error")
            return render_template("register.html")
        try:
            db = get_db()
            db.execute(
                "INSERT INTO users(name, email, password_hash, role) VALUES (?, ?, ?, 'patient')",
                (name, email, generate_password_hash(password))
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("An account with that email already exists.", "error")
            return render_template("register.html")
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            session["email"] = user["email"]
            return redirect(url_for("admin") if user["role"] == "admin" else url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    appointments = db.execute("""
        SELECT a.*, d.name AS doctor_name, d.specialty
        FROM appointments a JOIN doctors d ON d.id = a.doctor_id
        WHERE a.user_id = ? ORDER BY a.appointment_date, a.appointment_time
    """, (session["user_id"],)).fetchall()
    upcoming = [a for a in appointments if a["appointment_date"] >= date.today().isoformat() and a["status"] == "Booked"]
    return render_template("dashboard.html", appointments=appointments, upcoming_count=len(upcoming))

@app.route("/doctors")
def doctors():
    rows = get_db().execute("SELECT * FROM doctors ORDER BY specialty, name").fetchall()
    return render_template("doctors.html", doctors=rows)

@app.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
    db = get_db()
    if request.method == "POST":
        doctor_id = request.form.get("doctor_id", type=int)
        appt_date = request.form.get("appointment_date", "")
        appt_time = request.form.get("appointment_time", "")
        reason = request.form.get("reason", "").strip()
        doctor = db.execute("SELECT id FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
        try:
            parsed_date = date.fromisoformat(appt_date)
        except ValueError:
            parsed_date = None
        if not doctor or not parsed_date or parsed_date < date.today() or not appt_time or not reason:
            flash("Please select a valid doctor, future date, time, and brief reason.", "error")
        else:
            # Prevent duplicate bookings for the same doctor, date and time.
            conflict = db.execute("""
                SELECT id FROM appointments WHERE doctor_id = ? AND appointment_date = ?
                AND appointment_time = ? AND status = 'Booked'
            """, (doctor_id, appt_date, appt_time)).fetchone()
            if conflict:
                flash("That demo slot is already booked. Please choose another time.", "error")
            else:
                db.execute("""
                    INSERT INTO appointments(user_id, doctor_id, appointment_date, appointment_time, reason)
                    VALUES (?, ?, ?, ?, ?)
                """, (session["user_id"], doctor_id, appt_date, appt_time, reason[:250]))
                db.commit()
                flash("Appointment booked successfully.", "success")
                return redirect(url_for("appointments"))
    doctor_rows = db.execute("SELECT * FROM doctors ORDER BY name").fetchall()
    rows = db.execute("""
        SELECT a.*, d.name AS doctor_name, d.specialty
        FROM appointments a JOIN doctors d ON d.id = a.doctor_id
        WHERE a.user_id = ? ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (session["user_id"],)).fetchall()
    return render_template("appointments.html", doctors=doctor_rows, appointments=rows, today=date.today().isoformat())

@app.post("/appointments/<int:appointment_id>/cancel")
@login_required
def cancel_appointment(appointment_id):
    db = get_db()
    db.execute("""
        UPDATE appointments SET status = 'Cancelled'
        WHERE id = ? AND user_id = ? AND status = 'Booked'
    """, (appointment_id, session["user_id"]))
    db.commit()
    flash("Appointment updated if it was eligible for cancellation.", "success")
    return redirect(url_for("appointments"))

@app.route("/assistant")
@login_required
def assistant():
    return render_template("assistant.html")

URGENT_TERMS = [
    "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
    "severe bleeding", "unconscious", "stroke", "suicidal", "overdose"
]

def rule_based_reply(message):
    text = message.lower()
    if any(term in text for term in URGENT_TERMS):
        return ("Your message may describe an emergency. Please contact your local emergency number "
                "or go to the nearest emergency department now. Do not rely on this website for emergency care.")
    if any(word in text for word in ["appointment", "book", "doctor", "booking"]):
        return ("You can book a visit from the Appointments page after signing in. Choose a listed demo doctor, "
                "a future date, a time, and a brief reason. The doctors and slots in this prototype are fictional.")
    if any(word in text for word in ["water", "hydration", "drink"]):
        return ("General wellness information: hydration needs vary with activity, climate, age, and health conditions. "
                "Drink regularly and follow advice from your healthcare professional if you have fluid restrictions.")
    if any(word in text for word in ["sleep", "insomnia", "rest"]):
        return ("General wellness information: a consistent sleep schedule and a calm bedtime routine may support sleep. "
                "Persistent or severe sleep problems are worth discussing with a qualified healthcare professional.")
    if any(word in text for word in ["fever", "pain", "cough", "symptom", "sick", "medicine", "medication"]):
        return ("I can share general health information, but I cannot diagnose symptoms or recommend medication. "
                "Please contact a qualified healthcare professional for advice specific to you, especially if symptoms "
                "are severe, worsening, or persistent.")
    return ("I can help with general wellness information and navigating this demo website. I cannot diagnose, "
            "prescribe, or replace a healthcare professional. For personal medical advice, contact a qualified clinician.")

@app.post("/api/chat")
@login_required
def chat_api():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"reply": "Please enter a question."}), 400
    if len(message) > 1000:
        return jsonify({"reply": "Please keep your message under 1,000 characters."}), 400

    if OLLAMA_ENABLED:
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content":
                         "You are MediAssist, an educational healthcare information assistant. "
                         "Give brief general wellness information only. Never diagnose, prescribe, recommend dosages, "
                         "or claim certainty. Encourage qualified professional care for personal medical concerns. "
                         "If the user describes an emergency, tell them to contact local emergency services immediately. "
                         "Do not ask for identifying or sensitive patient information."},
                        {"role": "user", "content": message}
                    ]
                },
                timeout=25
            )
            response.raise_for_status()
            reply = response.json().get("message", {}).get("content", "").strip()
            if reply:
                return jsonify({"reply": reply, "mode": "local-model"})
        except (requests.RequestException, ValueError, KeyError):
            pass
    return jsonify({"reply": rule_based_reply(message), "mode": "offline-assistant"})

@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    booked = db.execute("SELECT COUNT(*) FROM appointments WHERE status='Booked'").fetchone()[0]
    cancelled = db.execute("SELECT COUNT(*) FROM appointments WHERE status='Cancelled'").fetchone()[0]
    users = db.execute("SELECT COUNT(*) FROM users WHERE role='patient'").fetchone()[0]
    rows = db.execute("""
        SELECT a.*, u.name AS patient_name, u.email, d.name AS doctor_name, d.specialty
        FROM appointments a JOIN users u ON u.id=a.user_id JOIN doctors d ON d.id=a.doctor_id
        ORDER BY a.created_at DESC LIMIT 100
    """).fetchall()
    specialty_rows = db.execute("""
        SELECT d.specialty, COUNT(a.id) AS count FROM doctors d
        LEFT JOIN appointments a ON a.doctor_id=d.id
        GROUP BY d.specialty ORDER BY count DESC, d.specialty
    """).fetchall()
    return render_template("admin.html", total=total, booked=booked, cancelled=cancelled,
                           users=users, appointments=rows, specialty_rows=specialty_rows)

@app.post("/admin/appointments/<int:appointment_id>/complete")
@admin_required
def complete_appointment(appointment_id):
    get_db().execute("UPDATE appointments SET status='Completed' WHERE id=? AND status='Booked'", (appointment_id,))
    get_db().commit()
    flash("Appointment marked completed if it was booked.", "success")
    return redirect(url_for("admin"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
