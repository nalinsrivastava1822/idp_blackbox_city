import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

SYSTEM_PROMPT = """You are BLACKBOX CITY's Patient Digital Twin explanation assistant.

You receive structured information produced by:
1. a machine-learning patient risk model
2. a patient digital twin
3. a stethoscope observation layer

Your job is ONLY to explain the provided information.

STRICT RULES:
- Never invent patient measurements.
- Never change the ML model's risk_level.
- Never diagnose a disease.
- Never prescribe medication.
- Never claim that a prototype risk score is a medical probability.
- Clearly state that the system is a prototype.
- Explain the current state and trend.
- Mention important alerts.
- Return ONLY valid JSON.
"""

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
    torch_dtype=torch.float16
)
model.eval()

def explain_patient(patient_data):
    user_prompt = f"""
Analyze this BLACKBOX CITY patient state:

{json.dumps(patient_data, indent=2, default=str)}

Return exactly this JSON structure:

{{
  "summary": "short explanation",
  "key_observations": [],
  "risk_assessment": {{
    "level": "LOW | MODERATE | HIGH",
    "trend": "INITIAL_ASSESSMENT | STABLE | IMPROVING | DETERIORATING"
  }},
  "alerts": [],
  "recommended_action": "non-diagnostic recommendation",
  "safety_note": "prototype disclaimer"
}}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        text,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=350,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )

    generated = outputs[0][inputs.input_ids.shape[-1]:]
    response = tokenizer.decode(
        generated,
        skip_special_tokens=True
    )

    return response

# Example:
# with open("example_input.json") as f:
#     patient = json.load(f)
# print(explain_patient(patient))
