import json

import ollama


# Path to your receipt image
image_path = "path/to/your/receipt.jpg"

# Define the prompt asking for specific structured data
prompt = """
Analyze this receipt and extract the following information.
Return the output strictly as a JSON object with these keys:
- vendor (string)
- date (string, formatted as YYYY-MM-DD if possible)
- transaction_amount (float or string with currency)
- type_of_expense (string, e.g., Meals, Travel, Office Supplies, etc.)

Do not include any conversational text or markdown formatting in your response. Just return the raw JSON object.
"""

try:
    print("Analyzing receipt... (this may take a few seconds)")

    # Call the Ollama API
    response = ollama.generate(model="llava", prompt=prompt, images=[image_path])

    # Extract the text response
    response_text = response["response"].strip()

    # Parse the text into a Python dictionary
    receipt_data = json.loads(response_text)

    # Print the structured result
    print("\n--- Extracted Information ---")
    print(json.dumps(receipt_data, indent=4))

except json.JSONDecodeError:
    print("\nFailed to parse JSON. Raw output from model:")
    print(response_text)
except Exception as e:
    print(f"\nAn error occurred: {e}")
