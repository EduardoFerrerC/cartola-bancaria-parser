import pdfplumber

# Assuming the rest of your code follows here...

def extract_data_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Process the PDF pages
        for page in pdf.pages:
            text = page.extract_text()
            # Your logic to handle extracted text
            print(text)