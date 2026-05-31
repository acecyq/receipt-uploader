import json
import ollama
from pypdf import PdfReader

def get_pdf_info(pdf_path):
    try:
        print("Reading text from PDF...")
        # Extract text from the first page
        reader = PdfReader(pdf_path)
        page = reader.pages[0]
        extracted_text = page.extract_text()

        if not extracted_text.strip():
            raise Exception("PDF contains no readable text. It might be a scanned image. Use Method 1 instead.")

        prompt = f"""
        Analyze the following receipt text and extract the information.
        Return the output strictly as a JSON object with these keys:
        - vendor (string)
        - date (string, formatted as YYYY-MM-DD if possible)
        - transaction_amount (float or string with currency)
        - type_of_expense (string)

        Receipt Text:
        \"\"\"
        {extracted_text}
        \"\"\"
        """

        print("Analyzing text with Ollama...")
        # We can use a standard text model here, which is faster than a vision model
        response = ollama.generate(
            model='llama3.2', 
            prompt=prompt,
            format='json'
        )

        receipt_data = json.loads(response['response'].strip())
        print("\n--- Extracted Information ---")
        print(json.dumps(receipt_data, indent=4))

    except Exception as e:
        print(f"Error: {e}")