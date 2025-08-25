# Updated script using Stanford BioMedLM instead of BioGPT

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    AutoModelForMaskedLM
)

device = torch.device("cpu")


# ----------------------------------------------------------
# Load ClinicalBERT for EHR-related context prediction
print("\nLoading ClinicalBERT...")
clinicalbert_model = AutoModelForMaskedLM.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
clinicalbert_tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")

clinical_pipeline = pipeline("fill-mask", model=clinicalbert_model, tokenizer=clinicalbert_tokenizer)

masked_text = "Patient has a history of [MASK]."
clinical_results = clinical_pipeline(masked_text.replace("[MASK]", clinicalbert_tokenizer.mask_token))
print("\nClinicalBERT context predictions:")
for result in clinical_results[:3]:
    print(f"> {result['sequence']} (score={result['score']:.3f})")

# ----------------------------------------------------------
# Simulated Patient Data (structured)
sample_patient = {
    "age": 68,
    "sex": "Male",
    "symptoms": ["persistent cough", "shortness of breath"],
    "history": ["COPD", "smoking"],
    "imaging": "2.3 cm lesion in the left upper lobe",
    "labs": {
        "WBC": "15.2 (elevated)",
        "CRP": "8.3 (elevated)"
    }
}

# ----------------------------------------------------------
# Prompt Builder
def build_clinical_prompt(patient):
    prompt = (
        f"Patient Case Summary:\n"
        f"- Age: {patient.get('age', 'N/A')}\n"
        f"- Sex: {patient.get('sex', 'N/A')}\n"
        f"- Symptoms: {', '.join(patient.get('symptoms', [])) or 'None reported'}\n"
        f"- Medical History: {', '.join(patient.get('history', [])) or 'No prior conditions'}\n"
        f"- Imaging Findings: {patient.get('imaging', 'None reported')}\n"
        f"- Lab Results:\n"
    )
    for lab, value in patient.get("labs", {}).items():
        prompt += f"  • {lab}: {value}\n"

    # Seed the continuation
    prompt += (
        "\nDiagnosis: The patient is likely suffering from "
        "\n\nRecommended Next Steps: The clinician should "
    )
    return prompt

# ----------------------------------------------------------
# Load BioMedLM (Stanford)
print("\nLoading BioMedLM...")
biomed_model_id = "stanford-crfm/biomedlm"
biomed_tokenizer = AutoTokenizer.from_pretrained(biomed_model_id)
biomed_model = AutoModelForCausalLM.from_pretrained(biomed_model_id)

# Ensure padding token is defined
biomed_tokenizer.pad_token = biomed_tokenizer.eos_token

# ----------------------------------------------------------
# Build prompt and generate response
prompt = build_clinical_prompt(sample_patient)
print("\n" + prompt)

inputs = biomed_tokenizer(prompt, return_tensors="pt", padding=True).to(device)
biomed_model = biomed_model.to(device)

outputs = biomed_model.generate(
    input_ids=inputs["input_ids"],
    attention_mask=inputs["attention_mask"],
    max_new_tokens=80,
    pad_token_id=biomed_tokenizer.eos_token_id
)

result = biomed_tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\n=== BioMedLM Response ===")
print(result)
