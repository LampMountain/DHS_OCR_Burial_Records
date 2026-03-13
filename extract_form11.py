"""
OCR Data Extractor and PDF Metadata Writer
This current program is merely a proof of concept for the metadata storage.
The actual implementation will require extensive rule based programming to account for the many file types

Fields extracted:
    1. veteran_name       - Full name of the veteran
    2. date_of_birth      - Veteran's date of birth
    3. date_of_death      - Date (and potentially place) of death
    4. war                - War/conflict veteran served in
    5. branch             - Unit and Organization
    6. burial_location    - Cemetery name and address (If available)
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

import pdfplumber
from pypdf import PdfReader, PdfWriter


# Config
INPUT_FOLDER  = "./input"      # Drop your scanned PDFs here
OUTPUT_FOLDER = "./output"     # Processed PDFs land here

# Text extraction
def extract_text_from_pdf(pdf_path: str) -> str:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
    return full_text


# Field parsers (rule-based regex for Form 11 layout)
# This will need to be far more robust for the actual implementation
def parse_name(text: str) -> str:
    m = re.search(r"(?:^|\n)\s*Name\s+(.+?)\s+Service\s+No\.", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_dob(text: str) -> str:
    m = re.search(r"Date\s+of\s+Birth\s+(.+?)\s+Date\s+and\s+Place", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_date_of_death(text: str) -> str:
    m = re.search(r"Date\s+and\s+Place\s+of\s+Death\s+(.+?)(?:\n|$)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_war(text: str) -> str:
    m = re.search(r"(?:^|\n)\s*War\s+(.+?)\s+Rank\s+", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_branch(text: str) -> str:
    m = re.search(r"Unit\s+and\s+Organization\s+(.+?)(?:\n|$)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def parse_cemetery(text: str) -> str:
    m = re.search(r"Cemetery\s+and\s+Address\s+(.+?)(?:\n|$)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def extract_fields(text: str) -> dict:
    return {
        "veteran_name":    parse_name(text),
        "date_of_birth":   parse_dob(text),
        "date_of_death":   parse_date_of_death(text),
        "war":             parse_war(text),
        "branch":          parse_branch(text),
        "burial_location": parse_cemetery(text),
    }


# Metadata writer
# Data the database team will pull from
def write_metadata(input_path: str, output_path: str, fields: dict) -> None:
    """Embed extracted fields as custom metadata entries in the output PDF."""
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata({
        "/Title":              f"Curial Record - {fields.get('veteran_name', 'Unknown Veteran')}",
        "/Author":             "Allegheny County Veterans Services",
        "/Subject":            "Burial Allowance Application - War Veteran",
        "/Creator":            "DHS Veterans Digitization Project - Phase 1",
        "/CreationDate":       datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "/DHS_VeteranName":    fields.get("veteran_name", ""),
        "/DHS_DateOfBirth":    fields.get("date_of_birth", ""),
        "/DHS_DateOfDeath":    fields.get("date_of_death", ""),
        "/DHS_War":            fields.get("war", ""),
        "/DHS_Branch":         fields.get("branch", ""),
        "/DHS_BurialLocation": fields.get("burial_location", ""),
        "/DHS_ExtractedJSON":  json.dumps(fields, ensure_ascii=False),
    })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)



# Main
def main():
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    pdf_files = list(Path(INPUT_FOLDER).glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in '{INPUT_FOLDER}'. Drop a PDF there and re-run.")
        return

    results = []
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        text = extract_text_from_pdf(str(pdf_path))
        fields = extract_fields(text)

        for key, value in fields.items():
            print(f"  {key:<20} {value or 'MISSING'}")

        out_path = os.path.join(OUTPUT_FOLDER, pdf_path.name)
        write_metadata(str(pdf_path), out_path, fields)
        print(f"  Saved: {out_path}\n")

        results.append({"file": pdf_path.name, **fields})

    summary_path = os.path.join(OUTPUT_FOLDER, "extraction_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Done. {len(results)} file(s) processed. Summary: {summary_path}")

if __name__ == "__main__":
    main()