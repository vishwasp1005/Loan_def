from flask import Flask, render_template, request
import joblib
import numpy as np

# Store prediction history in memory
history = []


app = Flask(__name__)

# Load all ML components
model = joblib.load("model.pkl")
scaler = joblib.load("scaler.pkl")
encoder = joblib.load("encoder.pkl")

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Fetch inputs
        data = request.form

        gender = data['gender']
        married = data['married']
        education = data['education']
        self_employed = data['self_employed']
        credit_history = float(data['credit_history'])
        applicant_income = float(data['applicant_income'])
        loan_amount = float(data['loan_amount'])

        # Categorical values
        cat_features = [[gender, married, education, self_employed]]
        cat_encoded = encoder.transform(cat_features)

        # Numerical values
        num_features = np.array([[credit_history, applicant_income, loan_amount]])
        num_scaled = scaler.transform(num_features)

        # Combine
        final_input = np.hstack([cat_encoded, num_scaled])

        # Predict
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

        # Encode
        edu_enc = encoder.transform([[education, employment]])[0]

        # Final input
        final_input = [age, income, loan_amount, loan_term, credit_score, edu_enc[0], edu_enc[1]]
        final_scaled = scaler.transform([final_input])

        # Prediction
        prediction = model.predict(final_scaled)[0]

        # Save to history
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


# Render uses gunicorn in start command
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
