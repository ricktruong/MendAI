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
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

class BioGPTInference:
    """
    A class for running BioGPT inference on clinical cases.
    Handles model loading and text generation with proper error handling.
    """
    
    def __init__(self, model_name="microsoft/BioGPT-Large-PubMedQA"):
        """
        Initialize the BioGPT inference class.
        
        Args:
            model_name (str): Hugging Face model name for BioGPT
        """
        self.model_name = model_name
        self.biogpt_model = None
        self.biogpt_tokenizer = None
        self.clinicalbert_model = None
        self.clinicalbert_tokenizer = None
        self.clinical_pipeline = None
        
    def load_models(self):
        """
        Load both ClinicalBERT and BioGPT models.
        This should be called once before running inference.
        """
        print("Loading ClinicalBERT...")
        self.clinicalbert_model = AutoModelForMaskedLM.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
        self.clinicalbert_tokenizer = AutoTokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT")
        self.clinical_pipeline = pipeline("fill-mask", model=self.clinicalbert_model, tokenizer=self.clinicalbert_tokenizer)
        
        print("Loading BioGPT...")
        self.biogpt_tokenizer = BioGptTokenizer.from_pretrained(self.model_name)
        self.biogpt_model = BioGptForCausalLM.from_pretrained(self.model_name)
        
        print("✅ Models loaded successfully!")
    
    def build_clinical_prompt(self, patient):
        """
        Constructs a dynamic prompt for BioGPT from structured patient data.
        
        Args:
            patient (dict): Patient data containing age, sex, symptoms, history, imaging, labs
            
        Returns:
            tuple: (context, question) for BioGPT input
        """
        prompt = (
            f"<ABSTRACT>\n"
            f"Patient Case Summary:\n"
            f"- Name: {patient.get('name', 'N/A')}\n"
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
    
    def run_clinical_bert_analysis(self, text):
        """
        Run ClinicalBERT analysis on masked text.
        
        Args:
            text (str): Text with [MASK] token for analysis
            
        Returns:
            list: List of predictions with scores
        """
        if not self.clinical_pipeline:
            raise ValueError("Models not loaded. Call load_models() first.")
            
        masked_text = text.replace("[MASK]", self.clinicalbert_tokenizer.mask_token)
        results = self.clinical_pipeline(masked_text)
        return results
    
    def generate_diagnosis(self, patient, max_tokens=160, use_sampling=False):
        """
        Generate diagnosis and recommendations for a patient case.
        
        Args:
            patient (dict): Patient data dictionary
            max_tokens (int): Maximum number of tokens to generate
            use_sampling (bool): Whether to use sampling (False = greedy decoding)
            
        Returns:
            str: Generated diagnosis and recommendations
        """
        if not self.biogpt_model or not self.biogpt_tokenizer:
            raise ValueError("Models not loaded. Call load_models() first.")
        
        # Build the clinical prompt
        context, question = self.build_clinical_prompt(patient)
        
        # Prepare inputs for BioGPT
        inputs = self.biogpt_tokenizer(question, context, return_tensors="pt", padding=True)
        attention_mask = inputs["attention_mask"]
        
        # Generate response
        try:
            if use_sampling:
                outputs = self.biogpt_model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=attention_mask,
                    max_new_tokens=max_tokens,
                    do_sample=True,
                    top_k=50,
                    top_p=0.95,
                    temperature=0.7,
                    pad_token_id=self.biogpt_tokenizer.eos_token_id,
                    eos_token_id=self.biogpt_tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                )
            else:
                # Greedy decoding (more stable)
                outputs = self.biogpt_model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=attention_mask,
                    max_new_tokens=max_tokens,
                    do_sample=False,
                    pad_token_id=self.biogpt_tokenizer.eos_token_id,
                    eos_token_id=self.biogpt_tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                )
            
            # Decode and clean up the response
            result = self.biogpt_tokenizer.decode(outputs[0], skip_special_tokens=True)
            result = result.replace("< / FREETEXT >", "").replace("< / ABSTRACT >", "").replace("< PARAGRAPH >", "").replace("< / PARAGRAPH >", "").replace("< FREETEXT >", "").strip()
            
            return result
            
        except Exception as e:
            print(f"Error during generation: {e}")
            return f"Error generating response: {str(e)}"
    
    def run_full_analysis(self, patient, imaging_output=None):
        """
        Run complete analysis including ClinicalBERT and BioGPT.
        
        Args:
            patient (dict): Patient data
            imaging_output (dict, optional): Imaging analysis results
            
        Returns:
            dict: Complete analysis results
        """
        results = {}
        
        # ClinicalBERT analysis
        if self.clinical_pipeline:
            print("\nClinicalBERT context predictions:")
            masked_text = "Patient has a history of [MASK]."
            clinical_results = self.run_clinical_bert_analysis(masked_text)
            results['clinicalbert_predictions'] = clinical_results[:3]
            
            for result in clinical_results[:3]:
                print(f"> {result['sequence']} (score={result['score']:.3f})")
        
        # BioGPT diagnosis
        print(f"\nGenerating diagnosis for patient...")
        diagnosis = self.generate_diagnosis(patient)
        results['biogpt_diagnosis'] = diagnosis
        
        print("\n=== BioGPT Response ===")
        print(diagnosis)
        
        return results

#-------------------------------------------------
# Example Usage and Test Cases
#-------------------------------------------------

def main():
    """
    Example usage of the BioGPTInference class.
    """
    # Initialize the inference class
    biogpt = BioGPTInference()
    
    # Load models once (this takes time but only needs to be done once)
    biogpt.load_models()
    
    # Example patient cases
    patient_cases = [
        {
            "name": "John Doe",
            "age": 68,
            "sex": "Male",
            "symptoms": ["persistent cough", "shortness of breath"],
            "history": ["COPD", "smoking"],
            "imaging": "2.3 cm lesion in the left upper lobe",
            "labs": {
                "WBC": "15.2 (elevated)",
                "CRP": "8.3 (elevated)"
            }
        },
        {
            "name": "Jane Smith",
            "age": 45,
            "sex": "Female",
            "symptoms": ["chest pain", "fatigue"],
            "history": ["hypertension", "diabetes"],
            "imaging": "Normal chest X-ray",
            "labs": {
                "Troponin": "0.02 (normal)",
                "ECG": "Normal sinus rhythm"
            }
        },
        {
            "name": "Jim Beam",
            "age": 72,
            "sex": "Male",
            "symptoms": ["confusion", "fever"],
            "history": ["dementia", "UTI"],
            "imaging": "No acute findings",
            "labs": {
                "WBC": "12.5 (elevated)",
                "Urine Culture": "E. coli positive"
            }
        }
    ]
    
    # Run analysis on each patient case
    for i, patient in enumerate(patient_cases, 1):
        print(f"\n{'='*60}")
        print(f"PATIENT CASE {i}")
        print(f"{'='*60}")
        
        # Run full analysis (ClinicalBERT + BioGPT)
        results = biogpt.run_full_analysis(patient)
        
        print(f"\n--- Summary for Patient {i} ---")
        print(f"Name: {patient['name']}")
        print(f"Age: {patient['age']}, Sex: {patient['sex']}")
        print(f"Symptoms: {', '.join(patient['symptoms'])}")
        print(f"Key Finding: {patient['imaging']}")
        
        # You can also run just the diagnosis without ClinicalBERT
        # diagnosis = biogpt.generate_diagnosis(patient, max_tokens=200)
        # print(f"Diagnosis: {diagnosis}")

def quick_inference_example():
    """
    Quick example showing how to use the class for single inference.
    """
    # Initialize and load models
    biogpt = BioGPTInference()
    biogpt.load_models()
    
    # Single patient case
    patient = {
        "name": "Jane Smith",
        "age": 55,
        "sex": "Female",
        "symptoms": ["abdominal pain", "nausea"],
        "history": ["gallstones"],
        "imaging": "Gallbladder wall thickening",
        "labs": {
            "Bilirubin": "2.1 (elevated)",
            "ALT": "85 (elevated)"
        }
    }
    
    # Generate diagnosis
    diagnosis = biogpt.generate_diagnosis(patient, max_tokens=150)
    print("\n=== BioGPT Response ===")
    print(diagnosis)

if __name__ == "__main__":
    # Run the main example with multiple patient cases
    # main()
    
    # Uncomment to run quick inference example
    quick_inference_example()
