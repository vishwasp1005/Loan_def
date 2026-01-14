from flask import Flask, render_template, request, redirect, url_for
import joblib
import pandas as pd
import os

app = Flask(__name__)

# -------------------------
# LOAD MODEL
# -------------------------
model = joblib.load("loan_model.pkl")

# -------------------------
# CSV FILE FOR HISTORY
# -------------------------
HISTORY_FILE = "history.csv"

# If CSV doesn't exist, create empty file
if not os.path.exists(HISTORY_FILE):
    pd.DataFrame(columns=[
        "age", "income", "loan_amount", "credit_score",
        "dti_ratio", "education", "employment", "prediction"
    ]).to_csv(HISTORY_FILE, index=False)


# -------------------------
# HOME PAGE
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# PREDICT ROUTE
# -------------------------
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return redirect(url_for("home"))

    try:
        # Collect data
        age = float(request.form["age"])
        income = float(request.form["income"])
        loan_amount = float(request.form["loan_amount"])
        credit_score = float(request.form["credit_score"])
        dti_ratio = float(request.form["dti_ratio"])
        education = request.form["education"]
        employment = request.form["employment"]

        # Create DataFrame for prediction
        input_data = pd.DataFrame([{
            "Age": age,
            "Income": income,
            "LoanAmount": loan_amount,
            "CreditScore": credit_score,
            "DTIRatio": dti_ratio,
            "Education": education,
            "EmploymentType": employment
        }])

        # Predict
        pred = int(model.predict(input_data)[0])

        # Save record to CSV
        pd.DataFrame([{
            "age": age,
            "income": income,
            "loan_amount": loan_amount,
            "credit_score": credit_score,
            "dti_ratio": dti_ratio,
            "education": education,
            "employment": employment,
            "prediction": pred
        }]).to_csv(HISTORY_FILE, mode='a', header=False, index=False)

        return render_template("result.html", prediction=pred)

    except Exception as e:
        return f"Error: {str(e)}"


# -------------------------
# DASHBOARD PAGE
# -------------------------
@app.route("/dashboard")
def dashboard():
    # Load full history
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
# SERVER RUN (Render uses gunicorn)
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
