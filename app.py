from flask import Flask, render_template, request, redirect, url_for
import joblib
import numpy as np

# Store prediction history
history = []

app = Flask(__name__)

# Load ML components
model = joblib.load("model.pkl")
scaler = joblib.load("scaler.pkl")
encoder = joblib.load("encoder.pkl")


# ---------------------- HOME PAGE ----------------------
@app.route('/')
def home():
    return render_template("index.html")


# ---------------------- PREDICT ROUTE ----------------------
employment_map = {
    "Employed": "Full-time",
    "Self-Employed": "Self-emplc",
    "Unemployed": "Unemployme"
}

@app.route('/predict', methods=['POST'])
def predict():
    try:
        age = float(request.form['age'])
        income = float(request.form['income'])
        loan_amount = float(request.form['loan_amount'])
        loan_term = float(request.form['loan_term'])
        credit_score = float(request.form['credit_score'])
        education = request.form['education']
        employment = request.form['employment']

        # FIX: Map UI value → dataset value
        employment_clean = employment_map[employment]

        # Encode
        edu_enc = encoder.transform([[education, employment_clean]])[0]

        # Final input
        final_input = [age, income, loan_amount, loan_term, credit_score, edu_enc[0], edu_enc[1]]
        final_scaled = scaler.transform([final_input])

        # Prediction
        prediction = model.predict(final_scaled)[0]

        history.append({
            "age": age,
            "income": income,
            "loan": loan_amount,
            "term": loan_term,
            "credit": credit_score,
            "education": education,
            "employment": employment,
            "prediction": int(prediction)
        })

        return render_template("result.html", prediction=prediction)

    except Exception as e:
        return str(e)



# ---------------------- DASHBOARD ----------------------
@app.route('/dashboard')
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


# ---------------------- RUN APP ----------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
