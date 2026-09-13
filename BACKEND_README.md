
# BLACKBOX CITY - Patient Risk Model
## Backend Integration Package

### Files

1. patient_risk_model.joblib
   Trained XGBoost model + label encoder.

2. feature_schema.json
   Required input features and output structure.

3. example_prediction.json
   Example JSON response from the ML model.

4. digital_twin_example.json
   Example Patient Digital Twin state.

---

## Model

Algorithm:
XGBoost multiclass classifier

Target:
Risk_Level

Classes:
HIGH, LOW, MODERATE

---

## Pipeline

Patient JSON
    ->
Preprocessing
    ->
XGBoost
    ->
Risk prediction
    ->
Digital Twin
    ->
JSON response
    ->
LLM / Dashboard

---

## Backend usage

Install:

pip install joblib pandas numpy scikit-learn xgboost

Load model:

import joblib

package = joblib.load(
    "patient_risk_model.joblib"
)

model = package["model"]
label_encoder = package["label_encoder"]

Then pass a pandas DataFrame containing
the features listed in feature_schema.json.

---

## Output

The prediction contains:

- risk_level
- predicted_state
- risk_score
- confidence_percentage
- class_probabilities

The Digital Twin additionally maintains:

- baseline
- previous_state
- current_state
- history
- trend
- alerts
- observation_count

---

## Important

This is a prototype model.

The risk categories are derived from
health-camp Health_Score quantiles.

They are NOT clinically validated emergency
severity categories and must NOT be used for
diagnosis or treatment decisions.

---

## Model validation

Validation HIGH-risk recall:
67.75%

The model was selected primarily because
HIGH-risk recall was substantially better than
the Logistic Regression and Random Forest
baselines.

