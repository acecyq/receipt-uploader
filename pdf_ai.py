import os
import gspread
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

    def verify_and_correct(self):
        """
        Interactively prompts the user to verify each field on this instance.
        Updates the instance attributes directly in place.
        """
        print("\n==== 📝 REVIEW EXTRACTED DATA ====")
        print("Press [ENTER] to accept the value, or type the correction below:\n")
        
        # We loop through self.model_dump() to get key-value pairs
        for key, current_value in self.model_dump().items():
            display_key = key.replace("_", " ").title()
            user_input = input(f"{display_key} [{current_value}]: ").strip()
            
            if user_input != "":
                # Dynamically update the attribute on 'self' if the user types a correction
                if isinstance(current_value, float):
                    try:
                        setattr(self, key, float(user_input))
                    except ValueError:
                        print(f"⚠️ Invalid number format. Keeping original value: {current_value}")
                else:
                    setattr(self, key, user_input)
        
        print(self.model_dump_json())
    
    def save_to_google_sheets(self):
        """
        Appends this specific instance's data into Google Sheets.
        """
        print(f"\nSaving data for '{self.vendor}' to Google Sheets...")
        try:
            credentials_filepath = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            gc = gspread.service_account(filename=credentials_filepath)
            
            spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
            sheet = gc.open_by_key(spreadsheet_id).sheet1
            
            # Map the self attributes directly to your spreadsheet row
            row_to_append = [
                self.date,
                self.month,
                self.vendor,
                self.description,
                self.category,
                'Tuition',
                self.payment_method,
                self.amount,
                'url'
            ]
            
            sheet.append_row(row_to_append)
            print("✅ Successfully added to Google Sheets!")
            
        except Exception as e:
            print(f"❌ Failed to update Google Sheets: {e}")

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

    # 1. Check if the response contains the 'response' key
    if response and 'response' in response:
        try:
            # 2. Extract the string and parse it using .model_validate_json()
            receipt = ExtractedReceipt.model_validate_json(response['response'])
            
            # 3. Run your interactive correction method
            receipt.verify_and_correct()
            
        except Exception as e:
            print(f"Failed to parse or validate the AI response: {e}")
            print("Raw text was:", response['response'])
