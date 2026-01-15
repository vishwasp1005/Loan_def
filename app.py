from flask import Flask, render_template, request, redirect, url_for, session
import joblib
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "loan_secret_key_123"   # Needed for sessions


# -------------------------
# LOAD MODEL
# -------------------------
model = joblib.load("loan_model.pkl")


# -------------------------
# CSV FILE FOR PREDICTION HISTORY
# -------------------------

HISTORY_FILE = "history.csv"

# Create history.csv if missing
if not os.path.exists(HISTORY_FILE):
    pd.DataFrame(columns=[
        "age", "income", "loan_amount", "credit_score",
        "dti_ratio", "education", "employment", "prediction"
    ]).to_csv(HISTORY_FILE, index=False)

# -------------------------
# CSV FILE FOR USERS (SIGNUP LOGIN)
# -------------------------

USERS_FILE = "users.csv"

# Create users.csv if missing
if not os.path.exists(USERS_FILE):
    pd.DataFrame([{
        "username": "admin",
        "password": "12345"
    }]).to_csv(USERS_FILE, index=False)



# -------------------------
# HARD-CODED LOGIN (Render Safe)
# -------------------------
def validate_user(username, password):
    return username == "admin" and password == "12345"


# -------------------------
# LOGIN PAGE
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if validate_user(username, password):
            session["user"] = username
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# -------------------------
# SIGNUP PAGE
# -------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        df = pd.read_csv(USERS_FILE)

        # Check if username exists
        if username in df["username"].values:
            return render_template("signup.html", error="Username already exists!")

        # Add new user
        new_user = pd.DataFrame([{"username": username, "password": password}])
        new_user.to_csv(USERS_FILE, mode='a', header=False, index=False)

        return redirect(url_for("login"))

    return render_template("signup.html")


# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------
# LOGIN PROTECTION
# -------------------------
def login_required():
    return "user" in session


# -------------------------
# HOME PAGE
# -------------------------
@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("index.html")


# -------------------------
# PREDICT ROUTE
# -------------------------
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if not login_required():
        return redirect(url_for("login"))

    if request.method == "GET":
        return redirect(url_for("home"))

    try:
        age = float(request.form["age"])
        income = float(request.form["income"])
        loan_amount = float(request.form["loan_amount"])
        credit_score = float(request.form["credit_score"])
        dti_ratio = float(request.form["dti_ratio"])
        education = request.form["education"]
        employment = request.form["employment"]

        # Prepare data for model
        input_data = pd.DataFrame([{
            "Age": age,
            "Income": income,
            "LoanAmount": loan_amount,
            "CreditScore": credit_score,
            "DTIRatio": dti_ratio,
            "Education": education,
            "EmploymentType": employment
        }])

        prediction = int(model.predict(input_data)[0])

        # Save to CSV
        pd.DataFrame([{
            "age": age,
            "income": income,
            "loan_amount": loan_amount,
            "credit_score": credit_score,
            "dti_ratio": dti_ratio,
            "education": education,
            "employment": employment,
            "prediction": prediction
        }]).to_csv(HISTORY_FILE, mode='a', header=False, index=False)

        return render_template("result.html", prediction=prediction)

    except Exception as e:
        return f"Error: {str(e)}"


# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    df = pd.read_csv(HISTORY_FILE)

    safe = len(df[df["prediction"] == 0])
    danger = len(df[df["prediction"] == 1])
    total = len(df)

    history = df.to_dict(orient="records")

    return render_template(
        "dashboard.html",
        history=history,
        safe=safe,
        danger=danger,
        total=total
    )


# -------------------------
# RUN SERVER
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
