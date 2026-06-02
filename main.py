import os
from datetime import date

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from pdf_ai import pdf_info


class ReceiptSchema(BaseModel):
    vendor: str = Field(description="The name of the store or merchant")
    total_amount: float = Field(description="The total amount paid, including GST")
    transaction_date: date = Field(description="The date of the transaction")
    expense_type: str = Field(
        description="Category: e.g., Food, Transport, Software, Utilities"
    )


load_dotenv()


def main():
    # spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
    # credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    # test_gsheet_connection(credentials_path, spreadsheet_id)

    receipt_path = os.getenv("RECEIPT_PATH")
    pdf_info(receipt_path)


if __name__ == "__main__":
    main()
