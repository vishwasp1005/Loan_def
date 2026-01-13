from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)

model = joblib.load("model.pkl")
scaler = joblib.load("scaler.pkl")
encoder = joblib.load("encoder.pkl")

@app.route("/")
def home():
    return "Loan Default Prediction API is Running!"

@app.route("/predict_api", methods=["POST"])
def predict_api():
    data = request.get_json()

    age = float(data['age'])
    income = float(data['income'])
    loan_amount = float(data['loan_amount'])
    loan_term = float(data['loan_term'])
    credit_score = float(data['credit_score'])
    education = data['education']
    employment = data['employment']

    input_data = np.array([[age, income, loan_amount, loan_term, credit_score,
                            education, employment]])

    encoded = encoder.transform(input_data)
    scaled = scaler.transform(encoded)
    pred = model.predict(scaled)[0]

    result = "Loan Default: YES" if pred == 1 else "Loan Default: NO"

    return jsonify({"prediction": result})

if __name__ == "__main__":
    app.run()
