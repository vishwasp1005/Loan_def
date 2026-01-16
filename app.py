from flask import Flask, render_template, request, redirect, url_for, session
import joblib
import sqlite3
import pandas as pd
import os

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "loan_secret_key_123"


# -------------------------------------------------
# LOAD ML MODEL SAFELY
# -------------------------------------------------
try:
    model = joblib.load("loan_model.pkl")
except:
    model = None
    print("⚠️ MODEL FAILED TO LOAD — Check loan_model.pkl")


# -------------------------------------------------
# DATABASE
# -------------------------------------------------
DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # DEFAULT ADMIN
    c.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  ("admin", "12345"))

    # HISTORY TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            age REAL,
            income REAL,
            loan_amount REAL,
            credit_score REAL,
            dti_ratio REAL,
            education TEXT,
            employment TEXT,
            prediction INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()


# -------------------------------------------------
# LOGIN HELPERS
# -------------------------------------------------
def login_required():
    return "user" in session


def validate_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None


# -------------------------------------------------
# AUTH ROUTES
# -------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if login_required():
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if validate_user(username, password):
            session["user"] = username
            return redirect(url_for("home"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if login_required():
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, password))

            conn.commit()
            conn.close()
            return redirect(url_for("login"))

        except:
            return render_template("signup.html", error="Username already exists!")

    return render_template("signup.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------
@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("home.html")


# -------------------------------------------------
# PREDICT FORM (GET)
# -------------------------------------------------
@app.route("/predict", methods=["GET"])
def predict_page():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("predict.html")


# -------------------------------------------------
# PREDICT RESULT (POST)
# -------------------------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    if not login_required():
        return redirect(url_for("login"))

    try:
        age = float(request.form["age"])
        income = float(request.form["income"])
        loan_amount = float(request.form["loan_amount"])
        credit_score = float(request.form["credit_score"])
        dti_ratio = float(request.form["dti_ratio"])
        education = request.form["education"]
        employment = request.form["employment"]

        # Prepare ML input
        data = pd.DataFrame([{
            "Age": age,
            "Income": income,
            "LoanAmount": loan_amount,
            "CreditScore": credit_score,
            "DTIRatio": dti_ratio,
            "Education": education,
            "EmploymentType": employment
        }])

        prediction = int(model.predict(data)[0])

        # SAVE TO DB
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO history (age, income, loan_amount, credit_score, dti_ratio, education, employment, prediction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (age, income, loan_amount, credit_score, dti_ratio, education, employment, prediction))

        conn.commit()
        conn.close()

        return render_template("result.html", prediction=prediction)

    except Exception as e:
        return f"Error: {str(e)}"


# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM history", conn)
    conn.close()

    safe = len(df[df["prediction"] == 0])
    danger = len(df[df["prediction"] == 1])
    total = len(df)

    return render_template(
        "dashboard.html",
        history=df.to_dict(orient="records"),
        safe=safe,
        danger=danger,
        total=total
    )


# -------------------------------------------------
# RUN SERVER
# -------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
