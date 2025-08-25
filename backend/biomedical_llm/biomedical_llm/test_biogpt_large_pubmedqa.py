import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import BioGptTokenizer, BioGptForCausalLM

# Load BioGPT-Large PubMedQA model
print("\nLoading BioGPT-Large-PubMedQA...")
tokenizer = BioGptTokenizer.from_pretrained("microsoft/BioGPT-Large-PubMedQA")
model = BioGptForCausalLM.from_pretrained("microsoft/BioGPT-Large-PubMedQA")
tokenizer.pad_token = tokenizer.eos_token  # Required for attention mask padding

# Build the QA-style prompt
prompt = (
    "Question: What is the most likely diagnosis and follow-up plan for the following case?\n"
    "Context: 68-year-old male with COPD and history of smoking, presents with persistent cough and shortness of breath. "
    "Imaging reveals a 2.3 cm lesion in the left upper lobe. WBC is 15.2 (elevated), CRP is 8.3 (elevated).\n"
    "Answer:"
)

# Tokenize
inputs = tokenizer(prompt, return_tensors="pt", padding=True)
eos_id = getattr(tokenizer, "eos_token_id", tokenizer.convert_tokens_to_ids("</s>"))

# Generate answer
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        num_beams=1,
        do_sample=False,
        temperature=0.7,
        eos_token_id=eos_id
    )

# Decode
result = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("\n=== BioGPT-PubMedQA Answer ===")
print(result)
