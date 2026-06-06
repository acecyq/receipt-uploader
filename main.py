import os

from dotenv import load_dotenv

from pdf_ai import pdf_info


load_dotenv()


def main():
    # spreadsheet_id = os.getenv('GOOGLE_SHEET_ID')
    # credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    # test_gsheet_connection(credentials_path, spreadsheet_id)

    credentials_filename = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    receipt_path = os.getenv("RECEIPT_PATH")
    google_drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

    receipt = pdf_info(receipt_path)
    authenticated_creds = receipt.upload_to_google_drive(credentials_filename, receipt_path, google_drive_folder_id)
    receipt.save_to_google_sheets(authenticated_creds)


if __name__ == "__main__":
    main()
