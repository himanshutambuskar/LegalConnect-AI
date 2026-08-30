import fitz
import re
import json
import csv
import os
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "cyber.pdf"

OUTPUT_JSON = BASE_DIR / "legal_dataset.json"
OUTPUT_JSONL = BASE_DIR / "legal_dataset.jsonl"
OUTPUT_CSV = BASE_DIR / "legal_dataset.csv"


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(text):
    """
    Clean extracted PDF text.
    """

    # Remove strange control characters
    text = text.replace("\x00", "")

    # Replace different dash characters with normal hyphen
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("−", "-")

    # Remove repeated spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()


# ============================================================
# REMOVE PDF HEADERS / FOOTERS
# ============================================================

def remove_headers_footers(text):
    """
    Remove common repeated headers/footers from this legal PDF.
    """

    lines = text.splitlines()

    cleaned_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            cleaned_lines.append("")
            continue

        # Remove standalone page numbers
        if re.fullmatch(r"\d+", line):
            continue

        # Repeated document title
        if line.upper() == "THE INFORMATION TECHNOLOGY ACT, 2000":
            continue

        # Common page/header text
        if line.upper() == "SECTIONS":
            continue

        # Remove parsed page markers if present
        if re.match(r"^<PARSED TEXT FOR PAGE:", line):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


# ============================================================
# EXTRACT PDF PAGE BY PAGE
# ============================================================

def extract_pdf(pdf_path):

    print("=" * 60)
    print("Reading PDF...")
    print("=" * 60)

    doc = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(doc, start=1):

        text = page.get_text("text")

        text = clean_text(text)
        text = remove_headers_footers(text)

        pages.append({
            "page": page_number,
            "text": text
        })

        print(f"Extracted page {page_number}/{len(doc)}")

    doc.close()

    return pages


# ============================================================
# CHAPTER DETECTION
# ============================================================

def detect_chapter(line):
    """
    Detect chapter headings such as:

    CHAPTER I
    CHAPTER II
    CHAPTER IX
    CHAPTER XI
    """

    pattern = r"^CHAPTER\s+([IVXLCDM]+)\s*$"

    match = re.match(pattern, line.strip(), re.IGNORECASE)

    if match:
        return "Chapter " + match.group(1).upper()

    return None


# ============================================================
# SECTION DETECTION
# ============================================================

def detect_section(line):
    """
    Detect legal section headings.

    Examples:

    1. Short title...
    2. Definitions.
    43. Penalty and compensation...
    43A. Compensation...
    66C. Punishment for identity theft.
    70B. Indian Computer Emergency Response Team...
    """

    line = line.strip()

    # Section number:
    # 1
    # 43
    # 43A
    # 66C
    # 70B
    #
    # Followed by "."
    pattern = r"^(\d+[A-Z]?)\.\s+(.+)$"

    match = re.match(pattern, line)

    if not match:
        return None

    section_number = match.group(1)
    section_title = match.group(2).strip()

    return {
        "section_number": section_number,
        "section_title": section_title
    }


# ============================================================
# DETECT SUBSECTIONS / CLAUSES
# ============================================================

def is_subsection(line):
    """
    Detect:

    (1)
    (2)
    (a)
    (b)
    (i)
    (ii)
    """

    line = line.strip()

    patterns = [
        r"^\(\d+\)",
        r"^\([a-z]\)",
        r"^\([ivxlcdm]+\)"
    ]

    for pattern in patterns:

        if re.match(pattern, line, re.IGNORECASE):
            return True

    return False


# ============================================================
# PARSE LEGAL SECTIONS
# ============================================================

def parse_sections(pages):

    records = []

    current_chapter = None
    current_section = None
    current_content = []
    current_start_page = None

    def save_current_section():

        nonlocal current_section
        nonlocal current_content
        nonlocal current_start_page

        if current_section is None:
            return

        content = "\n".join(current_content)

        content = clean_text(content)

        if not content:
            return

        record = {
            "id": f"IT_ACT_SEC_{current_section['section_number']}",
            "act": "Information Technology Act, 2000",
            "chapter": current_chapter,
            "section_number": current_section["section_number"],
            "section_title": current_section["section_title"],
            "content": content,
            "page": current_start_page,
            "source": "Information Technology Act, 2000"
        }

        records.append(record)

    # --------------------------------------------------------
    # PROCESS EVERY PAGE
    # --------------------------------------------------------

    for page_data in pages:

        page_number = page_data["page"]
        text = page_data["text"]

        lines = text.splitlines()

        for line in lines:

            line = line.strip()

            if not line:
                continue

            # ----------------------------------------------
            # CHAPTER
            # ----------------------------------------------

            chapter = detect_chapter(line)

            if chapter:

                # Don't save section here.
                #
                # A chapter heading can appear before
                # the first section or between sections.

                current_chapter = chapter

                continue

            # ----------------------------------------------
            # SECTION
            # ----------------------------------------------

            section = detect_section(line)

            if section:

                # Save previous section
                save_current_section()

                # Start new section
                current_section = section

                current_content = []

                current_start_page = page_number

                continue

            # ----------------------------------------------
            # NORMAL CONTENT
            # ----------------------------------------------

            if current_section is not None:

                current_content.append(line)

    # Save final section
    save_current_section()

    return records


# ============================================================
# CLEAN LEGAL RECORDS
# ============================================================

def clean_records(records):

    cleaned = []

    for record in records:

        content = record["content"]

        # Remove excessive spaces
        content = re.sub(r"[ \t]+", " ", content)

        # Fix spaces around new lines
        content = re.sub(r"\n+", "\n", content)

        # Remove footnote references like:
        #
        # 1
        # 2
        # 3
        #
        # ONLY when they appear alone as a line

        lines = content.splitlines()

        new_lines = []

        for line in lines:

            line = line.strip()

            if re.fullmatch(r"\d+", line):
                continue

            new_lines.append(line)

        content = "\n".join(new_lines)

        record["content"] = content.strip()

        cleaned.append(record)

    return cleaned


# ============================================================
# SAVE JSON
# ============================================================

def save_json(records, output_path):

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nJSON created: {output_path}")


# ============================================================
# SAVE JSONL
# ============================================================

def save_jsonl(records, output_path):

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        for record in records:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )

    print(f"JSONL created: {output_path}")


# ============================================================
# SAVE CSV
# ============================================================

def save_csv(records, output_path):

    if not records:
        print("No records available for CSV.")
        return

    fieldnames = [
        "id",
        "act",
        "chapter",
        "section_number",
        "section_title",
        "content",
        "page",
        "source"
    ]

    with open(
        output_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for record in records:

            writer.writerow(record)

    print(f"CSV created: {output_path}")


# ============================================================
# PRINT SAMPLE RECORDS
# ============================================================

def show_samples(records):

    print("\n")
    print("=" * 60)
    print("SAMPLE RECORDS")
    print("=" * 60)

    for record in records[:5]:

        print("\nID:", record["id"])

        print(
            "Chapter:",
            record["chapter"]
        )

        print(
            "Section:",
            record["section_number"]
        )

        print(
            "Title:",
            record["section_title"]
        )

        print(
            "Page:",
            record["page"]
        )

        print(
            "Content:",
            record["content"][:500],
            "..."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # Check PDF
    pdf_path = str(PDF_PATH)
    if not os.path.exists(pdf_path):

        print(
            f"ERROR: PDF not found: {pdf_path}"
        )

        print(
            "Put your PDF in the same folder as this script or update the PDF path."
        )

        return

    # Create output folder (same directory as script)
    os.makedirs(
        str(BASE_DIR),
        exist_ok=True
    )

    # Step 1
    pages = extract_pdf(PDF_PATH)

    # Step 2
    print("\n")
    print("=" * 60)
    print("Parsing legal sections...")
    print("=" * 60)

    records = parse_sections(pages)

    # Step 3
    records = clean_records(records)

    # Step 4
    save_json(
        records,
        OUTPUT_JSON
    )

    # Step 5
    save_jsonl(
        records,
        OUTPUT_JSONL
    )

    # Step 6
    save_csv(
        records,
        OUTPUT_CSV
    )

    # Step 7
    show_samples(records)

    # Final information
    print("\n")
    print("=" * 60)
    print("CONVERSION COMPLETE")
    print("=" * 60)

    print(
        f"Total legal sections extracted: {len(records)}"
    )

    print(
        f"\nJSON : {OUTPUT_JSON}"
    )

    print(
        f"JSONL: {OUTPUT_JSONL}"
    )

    print(
        f"CSV  : {OUTPUT_CSV}"
    )


if __name__ == "__main__":
    main()