from pydantic import BaseModel, Field
from datetime import date

class ReceiptSchema(BaseModel):
    vendor: str = Field(description="The name of the store or merchant")
    total_amount: float = Field(description="The total amount paid, including GST")
    transaction_date: date = Field(description="The date of the transaction")
    expense_type: str = Field(description="Category: e.g., Food, Transport, Software, Utilities")

def main():
    print("Hello from receipt-uploader!")

if __name__ == "__main__":
    main()
