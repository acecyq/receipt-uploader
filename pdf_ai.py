import os
from typing import Literal, Optional

import gspread
import ollama
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pydantic import BaseModel, Field

from pdf_reader import extract_pdf_text


# 1. Define your rigid data schema using Pydantic
class ExtractedReceipt(BaseModel):
    # Enforcing strict ISO format string
    date: str = Field(
        description="The date of the receipt strictly in YYYY-MM-DD format only."
    )
    month: str = Field(
        description="The month and year in MMM YYYY format (e.g., May 2026)."
    )
    vendor: str = Field(description="The name of the store or merchant")
    description: str = Field(
        description="A brief description of what is purchased in less than 5 words"
    )

    # Enforce exact allowed enum strings here
    category: Literal[
        "Teaching materials (books/worksheets)",
        "Supplies (stationery/printing/snacks)",
        "Software & subscriptions",
        "Utilities (electricity/water/internet)",
        "Marketing & advertising",
        "Transport",
        "Equipment & devices",
        "Professional fees",
        "Furniture",
        "Rent",
        "Training",
        "Other",
    ]
    payment_method: Literal["Card", "Debit", "PayNow", "Cash"]
    amount: float = Field(description="The total amount paid")
    suggested_filename: str = Field(
        description="A clean filename formatted exactly as: description_DDMMYY.pdf. "
                    "Remove spaces, punctuation, or special characters from the vendor name, "
                    "make it lowercase, and replace spaces with underscores. "
                    "Example: 'quantum_leap_math_assessment-020326.pdf'"
    )
    drive_url: Optional[str] = None

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
                        print(
                            f"⚠️ Invalid number format. Keeping original value: {current_value}"
                        )
                else:
                    setattr(self, key, user_input)

        print(self.model_dump_json())

    def save_to_google_sheets(self, authenticated_creds):
        """
        Appends data to the bottom, applies formatting, and asks Google Sheets
        to natively sort the sheet. This permanently protects all manual hyperlinks!
        """
        print(f"\nAppending and sorting data natively for '{self.vendor}'...")
        try:

            gc = gspread.authorize(authenticated_creds)
            spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
            spreadsheet = gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.worksheet("Expenses")

            # 1. Find the next truly empty row
            all_values = worksheet.get_all_values()
            next_row_index = len(all_values) + 1  # 1-indexed for standard API calls

            # 2. Build the new row layout
            link_formula = f'=HYPERLINK("{self.drive_url}", "{self.suggested_filename}")' if self.drive_url else ""

            new_row = [
                self.date,
                self.month,
                self.vendor,
                self.description,
                self.category,
                'Tuition',
                self.payment_method,
                f"S${self.amount:.2f}",
                link_formula,
                ""
            ]

            # 3. Append the new row to the very bottom
            worksheet.update(f'A{next_row_index}', [new_row], value_input_option='USER_ENTERED')

            # 4. NATIVE FORMAT CLONING & SORT
            # Google's API uses 0-indexing for batch updates
            body = {
                "requests": [
                    # A. Clone EXACT visual formatting (Alignments, Fonts, Clip) from Row 4 to the new row
                    {
                        "copyPaste": {
                            "source": {
                                "sheetId": worksheet.id,
                                "startRowIndex": 3,               # Row 4
                                "endRowIndex": 4,
                                "startColumnIndex": 0,
                                "endColumnIndex": 10
                            },
                            "destination": {
                                "sheetId": worksheet.id,
                                "startRowIndex": next_row_index - 1,
                                "endRowIndex": next_row_index,
                                "startColumnIndex": 0,
                                "endColumnIndex": 10
                            },
                            "pasteType": "PASTE_FORMAT"           # Copies visual layout only
                        }
                    },
                    # B. Copy Validation (Dropdowns) from Row 4 to the new row
                    {
                        "copyPaste": {
                            "source": {
                                "sheetId": worksheet.id,
                                "startRowIndex": 3,
                                "endRowIndex": 4,
                                "startColumnIndex": 4,
                                "endColumnIndex": 7
                            },
                            "destination": {
                                "sheetId": worksheet.id,
                                "startRowIndex": next_row_index - 1,
                                "endRowIndex": next_row_index,
                                "startColumnIndex": 4,
                                "endColumnIndex": 7
                            },
                            "pasteType": "PASTE_DATA_VALIDATION"  # Copies dropdown rules only
                        }
                    },
                    # C. NATIVELY SORT THE RANGE
                    {
                        "sortRange": {
                            "range": {
                                "sheetId": worksheet.id,
                                "startRowIndex": 3,
                                "endRowIndex": next_row_index,
                                "startColumnIndex": 0,
                                "endColumnIndex": 10
                            },
                            "sortSpecs": [
                                {
                                    "dimensionIndex": 0,
                                    "sortOrder": "ASCENDING"
                                }
                            ]
                        }
                    }
                ]
            }

            spreadsheet.batch_update(body)

            print("✅ Successfully appended, natively sorted, and formatted Google Sheets!")

        except Exception as e:
            print(f"❌ Failed to update Google Sheets: {e}")

    def upload_to_google_drive(
            self,
            credentials_filename: str,
            local_pdf_path: str,
            folder_id: str = None
        ) -> UserCredentials:
        """
        Uploads the local PDF file directly as the authenticated user,
        completely bypassing Service Account storage quota limitations.
        """
        print(f"Uploading file to Google Drive as '{self.suggested_filename}'...")

        # We use the full drive scope as an actual user
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = None

        # token.json stores your user access/refresh tokens after logging in once
        if os.path.exists('token.json'):
            from google.oauth2.credentials import Credentials as UserCredentials
            creds = UserCredentials.from_authorized_user_file('token.json', SCOPES)

        # If there are no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_filename, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        try:
            service = build('drive', 'v3', credentials=creds)

            file_metadata = {'name': self.suggested_filename}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(local_pdf_path, mimetype='application/pdf')

            # This will execute flawlessly because it's using your account's massive storage quota
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            file_id = uploaded_file.get('id')

            # Construct the standard shareable link
            self.drive_url = f"https://drive.google.com/file/d/{file_id}/view"
            print("✅ Successfully uploaded to Drive! URL generated.")
            return creds

        except Exception as e:
            print(f"❌ Failed to upload to Google Drive: {e}")
            return None

def pdf_info(pdf_path, cli_mode=True) -> ExtractedReceipt: # <-- Added parameter
    extracted_text = extract_pdf_text(pdf_path)

    prompt = f"""
    Analyze the following text extracted from a document. Extract the data accurately according to these specific rules:
    - Convert any date found into a strict 'YYYY-MM-DD' format (e.g., if you see '11/05/26', convert it to '2026-05-11')
    - Month should be in the 'MMM YYYY' format.
    - Classify category carefully. Items meant for teaching or curriculum must be categorized as 'Teaching Materials'
    - Do not use raw text items like 'Merchandise Subtotal' as the type of expense.

    Extracted Text:
    \"\"\"
    {extracted_text}
    \"\"\"
    """

    response = ollama.generate(
        model="llama3.2:latest",
        prompt=prompt,
        format=ExtractedReceipt.model_json_schema(),
        options={
            "temperature": 0.0
        },
    )

    if response and "response" in response:
        try:
            receipt = ExtractedReceipt.model_validate_json(response["response"])

            # 🌟 Only run the terminal input prompt if we are in CLI mode!
            if cli_mode:
                receipt.verify_and_correct()

            return receipt

        except Exception as e:
            print(f"Failed to parse or validate the AI response: {e}")
            print("Raw text was:", response["response"])
