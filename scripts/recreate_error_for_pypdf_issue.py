"""
Often when errors happen they are underlying issues in pypdf.
This is code that can be copy/pasted into a pypdf bug report.
"""
from pypdf import PdfReader
from sys import argv


with open(argv[1], 'rb') as pdf_file:
    PdfReader(pdf_file)

    for page_number, page in enumerate(PdfReader(pdf_file).pages, start=1):
        print(f"Parsing page {page_number}...")
        image_number = 1

        for image_number, image in enumerate(page.images, start=1):
            print(f"  Page {page_number} image_number {image_number}: {image}")
