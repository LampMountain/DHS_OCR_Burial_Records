# DHS_OCR_Burial_Records
Requirements:
  Python 3.9+
  pdfplumber
  pypdf

Usage:
Place an OCR'd Form 11 (Format provided by DHS) PDF into the input/ folder.
Run the script:
  python extract_form11.py
The processed PDF with embedded metadata will appear in output/

Fields Extracted:
Metadata Key          Form 11 Field
/DHS_VeteranName      Name
/DHS_DateOfBirth      Date of Birth
/DHS_DateOfDeath      Date and Place of Death
/DHS_War              War
/DHS_Branch           Unit and Organization (raw)
/DHS_BurialLocation   Cemetery and Address

Notes:
PDFs must be OCR'd before processing (Adobe Acrobat Pro).
