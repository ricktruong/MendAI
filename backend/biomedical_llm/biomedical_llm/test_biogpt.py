# Libraries
import torch
from monai.networks.nets import UNet
from monai.transforms import (
    Compose, LoadImage, Spacingd,
    Orientationd, ScaleIntensityd, ToTensord
)
from monai.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForMaskedLM,
    pipeline,
    AutoModelForCausalLM
)
from transformers import BioGptTokenizer, BioGptForCausalLM

def build_clinical_prompt(patient):
    """
    Constructs a dynamic prompt for BioGPT from structured patient data.
    """
    prompt = (
    f"<ABSTRACT>\n"
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

    question = "What is this patient diagnosis and what follow-up they need?"
    return prompt, question

#-------------------------------------------------
# Simulated output from MONAI image inference
imaging_output = {
    "lesion_location": "left upper lobe",
    "lesion_size_cm": 2.3
}
#-------------------------------------------------
# Clinical Note Input (EHR-style)
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

#-------------------------------------------------
# Extract Concepts with ClinicalBERT
print("\nLoading ClinicalBERT...")
clinicalbert_model = AutoModelForMaskedLM.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
clinicalbert_tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")

clinical_pipeline = pipeline("fill-mask", model=clinicalbert_model, tokenizer=clinicalbert_tokenizer)

# Example: find likely fill-in-the-blank predictions for masked tokens
print("\nClinicalBERT context predictions:")
masked_text = "Patient has a history of [MASK]."
clinical_results = clinical_pipeline(masked_text.replace("[MASK]", clinicalbert_tokenizer.mask_token))
for result in clinical_results[:3]:
    print(f"> {result['sequence']} (score={result['score']:.3f})")

#------------------------------------------------
# Build prompt for BioGPT
prompt = (
    f"Findings:\n"
    f"- Lesion: {imaging_output['lesion_size_cm']} cm in {imaging_output['lesion_location']}\n"
    f"- WBC: 15.2 (elevated)\n"
    f"- History: COPD, smoking\n"
    f"Symptoms: persistent cough, shortness of breath\n\n"
    f"What are possible diagnoses and follow-up recommendations?"
)

#------------------------------------------------
# Build prompt for BioGPT
context, question = build_clinical_prompt(sample_patient)
print(prompt)

#------------------------------------------------
# Load BioGPT
print("\nLoading BioGPT...")
biogpt_tokenizer = BioGptTokenizer.from_pretrained("microsoft/BioGPT-Large")
biogpt_model = BioGptForCausalLM.from_pretrained("microsoft/BioGPT-Large")


# Feed into BioGPT
inputs = biogpt_tokenizer(question, context, return_tensors="pt", padding=True)

attention_mask = inputs["attention_mask"]

eos_id = getattr(biogpt_tokenizer, "eos_token_id", biogpt_tokenizer.convert_tokens_to_ids("</s>"))

outputs = biogpt_model.generate(
    input_ids=inputs["input_ids"],
    max_new_tokens=160,
    do_sample=True,
    top_k=40,
    top_p=0.90,
    temperature=0.85,
)

result = biogpt_tokenizer.decode(outputs[0], skip_special_tokens=True)
result = result.replace("< / FREETEXT >", "").replace("< / ABSTRACT >", "").replace("< PARAGRAPH >", "").replace("< / PARAGRAPH >", "").replace("< FREETEXT >", "").strip()
print("\n=== BioGPT Response ===")
print(result)
