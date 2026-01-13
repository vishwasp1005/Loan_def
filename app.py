from flask import Flask, render_template, request
import joblib
import numpy as np

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
        prediction = model.predict(final_input)[0]

        result = "Approved ✔" if prediction == 1 else "Rejected ❌"

        return render_template("result.html", prediction=result)

    except Exception as e:
        return f"Error: {str(e)}"

# Render uses gunicorn in start command
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
