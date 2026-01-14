from flask import Flask, render_template, request, redirect, url_for, session
import joblib
import pandas as pd
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change later

# Load ML Model
model = joblib.load("loan_model.pkl")

# -------------------------
# Database Setup
# -------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        age FLOAT,
        income FLOAT,
        loan_amount FLOAT,
        credit_score FLOAT,
        dti_ratio FLOAT,
        education TEXT,
        employment TEXT,
        prediction INTEGER
    )""")

    conn.commit()
    conn.close()

init_db()

# -------------------------
# Helper: Check Login
# -------------------------
def is_logged_in():
    return "user_id" in session


# -------------------------
# SIGNUP
# -------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = sqlite3.connect("database.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                        (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            return "Email already exists."

    return render_template("signup.html")


# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["name"] = user[1]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------
# HOME → Redirect to login
# -------------------------
@app.route("/")
def home():
    if not is_logged_in():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM predictions WHERE user_id=?", (session["user_id"],))
    data = cur.fetchall()
    conn.close()

    safe = len([d for d in data if d[10] == 0])
    danger = len([d for d in data if d[10] == 1])

    return render_template("dashboard.html",
                           name=session["name"],
                           data=data,
                           safe=safe,
                           danger=danger,
                           total=len(data))


# -------------------------
# PREDICT
# -------------------------
@app.route("/predict", methods=["POST"])
def predict():
    if not is_logged_in():
        return redirect(url_for("login"))

    age = float(request.form["age"])
    income = float(request.form["income"])
    loan_amount = float(request.form["loan_amount"])
    credit_score = float(request.form["credit_score"])
    dti_ratio = float(request.form["dti_ratio"])
    education = request.form["education"]
    employment = request.form["employment"]

    input_data = pd.DataFrame([{
        "Age": age,
        "Income": income,
        "LoanAmount": loan_amount,
        "CreditScore": credit_score,
        "DTIRatio": dti_ratio,
        "Education": education,
        "EmploymentType": employment
    }])

    pred = int(model.predict(input_data)[0])

    # Save to DB
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("""INSERT INTO predictions 
        (user_id, age, income, loan_amount, credit_score, dti_ratio, education, employment, prediction)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session["user_id"], age, income, loan_amount,
                 credit_score, dti_ratio, education, employment, pred))
    conn.commit()
    conn.close()

    return render_template("result.html", prediction=pred)


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
