from pypdf import PdfReader


def extract_pdf_text(pdf_path: str) -> str:
    try:
        print("Reading text from PDF...")
        # Extract text from the first page
        reader = PdfReader(pdf_path)
        page = reader.pages[0]
        extracted_text = page.extract_text()

        if not extracted_text.strip():
            raise Exception(
                "PDF contains no readable text. It might be a scanned image. Use Method 1 instead."
            )

        return extracted_text

    except Exception as e:
        print(f"Error: {e}")
