from pypdf import PdfReader

def extract_pdf_text(pdf_path: str) -> str:
    try:
        print("Reading text from PDF...")
        # Extract text from the first page
        reader = PdfReader(pdf_path)
        page = reader.pages[0]
        extracted_text = page.extract_text()

        if not extracted_text.strip():
            raise Exception("PDF contains no readable text. It might be a scanned image. Use Method 1 instead.")

        # prompt = f"""
        # Analyze the following receipt text and extract the information.

        # Strictly map the following fields to these exact allowed categories (Enums):
        # - 'type_of_expense': Choose ONLY from [Teaching materials, Supplies, Software, Utilities, Marketing, Transport, Equipment, Professional fees, Furniture, Rent, Training, Others]
        # - 'payment_method': Choose ONLY from [Credit, Debit, PayNow, Cash]

        # Respond STRICTLY with a valid JSON object matching this schema:
        # {{
        # "vendor": "string",
        # "date": "YYYY-MM-DD",
        # "month": "MMM YYYY",
        # "transaction_amount": float,
        # "type_of_expense": "string (matching enums)",
        # "payment_method": "string (matching enums)"
        # }}

        # Receipt Text:
        # \"\"\"
        # {extracted_text}
        # \"\"\"
        # """

        # print("Analyzing text with Ollama...")
        # # We can use a standard text model here, which is faster than a vision model
        # response = ollama.generate(
        #     model='llama3.2:latest', 
        #     prompt=prompt,
        #     format='json',
        #     options={
        #         'temperature': 0.0  # Forces deterministic, identical outputs on every run
        #     }
        # )

        # receipt_data = json.loads(response['response'].strip())
        # print("\n--- Extracted Information ---")
        # print(json.dumps(receipt_data, indent=4))
        return extracted_text

    except Exception as e:
        print(f"Error: {e}")