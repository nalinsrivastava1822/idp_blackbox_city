# BLACKBOX CITY LLM HANDOFF

This package contains the working LLM explanation layer for the BLACKBOX CITY prototype.

## Model
Base model:
Qwen/Qwen2.5-1.5B-Instruct

## Important
This is the WORKING prompted base-model implementation.
The earlier experimental LoRA adapter is NOT included because it produced
unreliable output during testing.

## Files
- llm_inference.py        Main LLM inference code
- system_prompt.txt       BLACKBOX CITY system prompt
- example_input.json       Input contract example
- example_output.json      Expected output structure
- requirements.txt         Python dependencies

## Pipeline
Patient/Stethoscope JSON
    ->
XGBoost prediction
    ->
Digital Twin
    ->
LLM
    ->
Structured explanation JSON

## Backend usage

Install:
pip install -r requirements.txt

Then:
from llm_inference import explain_patient

result = explain_patient(patient_json)

The LLM should receive the structured output of the ML model and
Digital Twin. It should NOT independently determine or override the
ML risk classification.

## Safety
This is a prototype explanation layer. It is not a medical diagnostic
system and must not be used to make diagnosis or treatment decisions.
