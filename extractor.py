import PyPDF2


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    
    Args:
        pdf_path (str): The path to the PDF file.
    
    Returns:
        str: Extracted text from the PDF.
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + '\n'
    except Exception as e:
        print(f"An error occurred while extracting text: {e}")
    return text


# Example usage:
# pdf_text = extract_text_from_pdf('sample.pdf')
# print(pdf_text)