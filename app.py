from flask import Flask, render_template, request, redirect, url_for
import joblib
import pandas as pd

app = Flask(__name__)

# Load the single ML pipeline model
model = joblib.load("loan_model.pkl")

# Store prediction history
history = []


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
    # If user tries to open /predict directly → redirect
    if request.method == "GET":
        return redirect(url_for("home"))

    try:
        # Collect form data
        age = float(request.form["age"])
        income = float(request.form["income"])
        loan_amount = float(request.form["loan_amount"])
        credit_score = float(request.form["credit_score"])
        dti_ratio = float(request.form["dti_ratio"])
        education = request.form["education"]
        employment = request.form["employment"]

        # Build DataFrame matching training columns
        input_data = pd.DataFrame([{
            "Age": age,
            "Income": income,
            "LoanAmount": loan_amount,
            "CreditScore": credit_score,
            "DTIRatio": dti_ratio,
            "Education": education,
            "EmploymentType": employment
        }])

        # Predict using the pipeline model
        pred = int(model.predict(input_data)[0])

        # Save history
        history.append({
            "age": age,
            "income": income,
            "loan_amount": loan_amount,
            "credit_score": credit_score,
            "dti_ratio": dti_ratio,
            "education": education,
            "employment": employment,
            "prediction": pred
        })

        return render_template("result.html", prediction=pred)

    except Exception as e:
        return f"Error: {str(e)}"


# -------------------------
# DASHBOARD PAGE
# -------------------------
@app.route("/dashboard")
def dashboard():
    safe = sum(1 for h in history if h["prediction"] == 0)
    danger = sum(1 for h in history if h["prediction"] == 1)
    total = len(history)

    return render_template(
        "dashboard.html",
        history=history,
        safe=safe,
        danger=danger,
        total=total
    )


# -------------------------
# RUN SERVER (local)
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
