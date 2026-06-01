import ollama
from pydantic import BaseModel, Field
from typing import Literal
from pdf_reader import extract_pdf_text

# 1. Define your rigid data schema using Pydantic
class ExtractedReceipt(BaseModel):
    # Enforcing strict ISO format string
    date: str = Field(description="The date of the receipt strictly in YYYY-MM-DD format only.")
    month: str = Field(description="The month and year in MMM YYYY format (e.g., May 2026).")
    vendor: str = Field(description="The name of the store or merchant")
    description: str = Field(description="A brief description of what is purchased in less than 5 words")
    
    # Enforce exact allowed enum strings here
    category: Literal[
        'Teaching materials', 'Supplies', 'Software', 'Utilities', 'Marketing', 'Transport', 
        'Equipment', 'Professional fees', 'Furniture', 'Rent', 'Training', 'Others'
    ]
    payment_method: Literal['Credit', 'Debit', 'PayNow', 'Cash']
    amount: float = Field(description="The total amount paid")

def pdf_info(pdf_path):
    extracted_text = extract_pdf_text(pdf_path)

    # 2. Refine the prompt to explicitly mention your transformation rules
    prompt = f"""
    Analyze the following text extracted from a document. Extract the data accurately according to these specific rules:
    - Convert any date found into a strict 'YYYY-MM-DD' format (e.g., if you see '11/05/26', convert it to '2026-05-11').
    - Classify the category carefully. Items meant for educational use or curriculum must be categorized as 'Teaching Materials'. Do not use raw text items like 'Merchandise Subtotal' as the type of expense.

    Extracted Text:
    \"\"\"
    {extracted_text}
    \"\"\"
    """

    # 3. Request the structured completion from Ollama
    response = ollama.generate(
        model='llama3.2:latest',
        prompt=prompt,

        # .model_json_schema() converts your Python class into a valid JSON schema constraints ruleset
        format=ExtractedReceipt.model_json_schema(), 
        options={
            'temperature': 0.0 # Eliminates creativity entirely
        }
    )

    # Print the resulting perfectly-conformed object
    print(response['response'])