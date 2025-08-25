# openbiollm_qa.py
import subprocess

PROMPT = """
Question: What is the most likely diagnosis and follow-up plan for the following case?

Context: 68-year-old male with COPD and history of smoking, presents with persistent cough and shortness of breath. Imaging reveals a 2.3 cm lesion in the left upper lobe. WBC is 15.2 (elevated), CRP is 8.3 (elevated).
"""

def run_openbiollm(prompt):
    process = subprocess.Popen(
        ["ollama", "run", "koesn/llama3-openbiollm-8b"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output, error = process.communicate(input=prompt)

    if error:
        print("Error:", error)
    else:
        print("\n=== OpenBioLLM Response ===")
        print(output.strip())

if __name__ == "__main__":
    run_openbiollm(PROMPT)
