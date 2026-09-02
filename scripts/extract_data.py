#!/usr/bin/env python3
"""
Legal Data Extraction Pipeline
------------------------------
Extracts official Indian legal texts (PDF/HTML) into structured JSON format
conforming to the project schema.

Preserves exact legal wording without summarization, paraphrasing, or invention.
"""

import os
import sys
import json
import re
import argparse
import datetime
import logging
import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("LegalExtractor")


SCHEMA_TEMPLATE = {
    "id": "",
    "act": "",
    "category": "",
    "subcategory": "",
    "section": "",
    "section_number": "",
    "title": "",
    "content": "",
    "source": "",
    "source_url": "",
    "document_type": "",
    "page": None,
    "language": "English",
    "retrieved_date": ""
}

NOISE_PATTERNS = [
    r'THE GAZETTE OF INDIA EXTRAORDINARY',
    r'REGISTERED NO\.',
    r'PUBLISHED BY AUTHORITY',
    r'MINISTRY OF LAW AND JUSTICE',
    r'\(Legislative Department\)',
    r'\[Part II—',
    r'Sec\. \d+\]',
    r'^\d+\s+THE GAZETTE OF INDIA',
    r'^_{3,}$'
]


def clean_title_string(title_raw: str) -> str:
    """Clean title string by normalizing whitespace and stripping trailing punctuation."""
    if not title_raw:
        return ""
    t = re.sub(r'\s+', ' ', title_raw).strip()
    t = re.sub(r'[\.\,\:\;\—\–\-]+$', '', t).strip()
    t = re.sub(r'\s+\d+\s+of\s+\d{4}$', '', t, flags=re.IGNORECASE)
    return t


def download_official_file(url: str, output_path: str, timeout: int = 30) -> bool:
    """Download official file from a given URL with error handling."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    logger.info(f"Downloading official source from: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        response.raise_for_status()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Successfully saved raw source to: {output_path} ({len(response.content)} bytes)")
        return True
    except Exception as e:
        logger.error(f"Failed to download from {url}: {e}")
        return False


def extract_bns_pdf(
    pdf_path: str,
    source_url: str,
    max_sections: int = 358,
    act_key: str = "bns",
    act_name: str = "Bharatiya Nyaya Sanhita, 2023",
    category: str = "Criminal Laws",
    subcategory: str = "Criminal Law",
    source: str = "India Code / BPRD",
    act_year: str = "2023",
) -> list:
    """
    Extract section-wise legal content from a numbered Act PDF.
    Preserves exact legal wording.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    logger.info(f"Opened PDF '{pdf_path}' with {len(doc)} pages.")

    # Step 1: Collect side-margin section titles by page
    margin_titles_by_page = {}
    for pno in range(len(doc)):
        page = doc[pno]
        pdict = page.get_text('dict')
        m_blocks = []
        for b in pdict['blocks']:
            if 'lines' in b:
                bbox = b['bbox']
                # Left/right margin section titles. Some titles extend into the main
                # column, so use their left edge rather than their right edge.
                if bbox[0] < 110 or bbox[0] > 480:
                    txt = ' '.join([''.join([s['text'] for s in l['spans']]) for l in b['lines']]).strip()
                    txt = clean_title_string(txt)
                    if txt and not re.match(r'^\d+\s+of\s+\d+$', txt, re.IGNORECASE):
                        if not any(re.search(p, txt) for p in ['GAZETTE', 'REGISTERED', 'PUBLISHED', 'AUTHORITY', 'MINISTRY']):
                            m_blocks.append((bbox[1], bbox[3], txt))
        margin_titles_by_page[pno + 1] = m_blocks

    # Step 2: Collect main column lines with page & y0
    main_lines = []
    for pno in range(len(doc)):
        page = doc[pno]
        pdict = page.get_text('dict')
        for b in pdict['blocks']:
            if 'lines' in b:
                for l in b['lines']:
                    if l['bbox'][0] >= 110:
                        ltxt = ''.join([s['text'] for s in l['spans']]).strip()
                        if not ltxt:
                            continue
                        # Skip noise lines
                        if any(re.search(p, ltxt) for p in NOISE_PATTERNS):
                            continue
                        main_lines.append((pno + 1, l['bbox'][1], ltxt))

    # Step 3: Locate start index for sections 1..max_sections
    sec_entries = []
    current_sec = 1

    for idx, (pno, y0, ltxt) in enumerate(main_lines):
        pattern = rf'^{current_sec}\.\s*(.*)'
        m = re.match(pattern, ltxt)
        if m:
            # Match title in margin blocks
            best_title = ""
            min_dist = 9999
            for my0, my1, mtxt in margin_titles_by_page.get(pno, []):
                dist = abs(my0 - y0)
                if dist < min_dist and dist < 80:
                    min_dist = dist
                    best_title = mtxt

            sec_entries.append({
                'sec_num': current_sec,
                'page': pno,
                'line_idx': idx,
                'title': best_title
            })
            current_sec += 1
            if current_sec > max_sections:
                break

    today_str = datetime.date.today().isoformat()
    extracted_records = []

    # Step 4: Extract exact content between section boundaries
    for i in range(len(sec_entries)):
        entry = sec_entries[i]
        start_idx = entry['line_idx']
        end_idx = sec_entries[i+1]['line_idx'] if i + 1 < len(sec_entries) else len(main_lines)

        # The final section is followed by schedules/forms, not another section
        # number. Do not append those non-section materials to the final record.
        if i + 1 == len(sec_entries):
            for j in range(start_idx + 1, len(main_lines)):
                if re.match(r'^THE\s+(?:FIRST\s+)?SCHEDULE\b', main_lines[j][2], re.IGNORECASE):
                    end_idx = j
                    break

        sec_lines = [main_lines[j][2] for j in range(start_idx, end_idx)]
        content_text = '\n'.join(sec_lines).strip()

        sec_num_str = str(entry['sec_num'])
        record = {
            "id": f"{act_key.upper()}-{act_year}-SECTION-{sec_num_str}",
            "act": act_name,
            "category": category,
            "subcategory": subcategory,
            "section": f"Section {sec_num_str}",
            "section_number": sec_num_str,
            "title": entry['title'],
            "content": content_text,
            "source": source,
            "source_url": source_url,
            "document_type": "Act",
            "page": entry['page'],
            "language": "English",
            "retrieved_date": today_str
        }
        extracted_records.append(record)

    logger.info(f"Extracted {len(extracted_records)} section records.")
    return extracted_records


def extract_pwdva_pdf(pdf_path: str, source_url: str, config: dict) -> list:
    """
    Extract section-wise legal content for Protection of Women from Domestic Violence Act, 2005.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    logger.info(f"Opened PDF '{pdf_path}' with {len(doc)} pages.")

    full_text = ""
    page_offsets = []
    for pno, page in enumerate(doc):
        txt = page.get_text('text')
        txt = re.sub(r'IndiaCode\s*', '', txt)
        page_offsets.append((pno + 1, len(full_text)))
        full_text += txt + '\n'

    sec_titles = {
        1: 'Short title, extent and commencement',
        2: 'Definitions',
        3: 'Definition of domestic violence',
        4: 'Information to Protection Officer and exclusion of liability of informant',
        5: 'Duties of police officers, service providers and Magistrate',
        6: 'Duties of shelter homes',
        7: 'Duties of medical facilities',
        8: 'Appointment of Protection Officers',
        9: 'Duties and functions of Protection Officers',
        10: 'Service providers',
        11: 'Duties of Government',
        12: 'Application to Magistrate',
        13: 'Service of notice',
        14: 'Counselling',
        15: 'Assistance of welfare expert',
        16: 'Proceedings to be held in camera',
        17: 'Right to reside in a shared household',
        18: 'Protection orders',
        19: 'Residence orders',
        20: 'Monetary reliefs',
        21: 'Custody orders',
        22: 'Compensation orders',
        23: 'Power to grant interim and ex parte orders',
        24: 'Court to give copies of order free of cost',
        25: 'Duration and alteration of orders',
        26: 'Relief in other suits and legal proceedings',
        27: 'Jurisdiction',
        28: 'Procedure',
        29: 'Appeal',
        30: 'Protection Officers and members of service providers to be public servants',
        31: 'Penalty for breach of protection order by respondent',
        32: 'Cognizance and proof',
        33: 'Penalty for not discharging duty by Protection Officer',
        34: 'Cognizance of offence committed by Protection Officer',
        35: 'Protection of action taken in good faith',
        36: 'Act not in derogation of any other law',
        37: 'Power of Central Government to make rules'
    }

    sec_positions = []
    for sec_num in range(1, config["max_sections"] + 1):
        pattern = rf'\n{sec_num}\.\s+'
        matches = [m.start() for m in re.finditer(pattern, full_text)]
        chosen_pos = None
        for m in matches:
            if m > 500:
                chosen_pos = m
                break
        if chosen_pos is None and matches:
            chosen_pos = matches[-1]
        
        if chosen_pos is not None:
            sec_positions.append((sec_num, chosen_pos))

    sec_positions.sort(key=lambda x: x[1])
    today_str = datetime.date.today().isoformat()
    extracted_records = []

    for idx in range(len(sec_positions)):
        sec_num, start_pos = sec_positions[idx]
        end_pos = sec_positions[idx+1][1] if idx + 1 < len(sec_positions) else len(full_text)
        
        sec_text = full_text[start_pos:end_pos].strip()
        title = sec_titles.get(sec_num, f'Section {sec_num}')

        page_num = 1
        for pno, poff in page_offsets:
            if start_pos >= poff:
                page_num = pno

        extracted_records.append({
            'id': f'PWDVA-2005-SECTION-{sec_num}',
            'act_key': 'pwdva',
            'act_name': config['name'],
            'act_year': config['act_year'],
            'category': config['category'],
            'subcategory': config['subcategory'],
            'section': str(sec_num),
            'title': title,
            'content': sec_text,
            'source': config['source'],
            'source_url': source_url,
            'page': page_num,
            'ingestion_date': today_str
        })

    logger.info(f"Extracted {len(extracted_records)} section records.")
    return extracted_records


def main():
    parser = argparse.ArgumentParser(description="Legal Data Extraction Script")
    parser.add_argument("--act", type=str, default="bns", choices=["bns", "bnss", "bsa", "cpa", "css", "pwdva"], help="Act key to extract (default: bns)")
    parser.add_argument("--pdf", type=str, help="Path to input PDF file")
    parser.add_argument("--output", type=str, help="Path to output JSON file")
    parser.add_argument("--download", action="store_true", help="Download raw PDF if not present")
    args = parser.parse_args()

    act_configs = {
        "bns": {
            "pdf": "data/raw/criminal/bns/bns_2023.pdf",
            "output": "data/raw/criminal/bns/bns_sections.json",
            "url": "https://bprd.nic.in/uploads/pdf/1706692028_eeccb6a2701f4c13ac9b.pdf",
            "max_sections": 358,
            "name": "Bharatiya Nyaya Sanhita, 2023",
            "category": "Criminal Laws",
            "subcategory": "Criminal Law",
            "source": "India Code / BPRD",
            "act_year": "2023",
        },
        "bnss": {
            "pdf": "data/raw/criminal/bnss/bnss_2023.pdf",
            "output": "data/raw/criminal/bnss/bnss_sections.json",
            "url": "https://www.mha.gov.in/sites/default/files/250884_2_english_01042024.pdf",
            "max_sections": 531,
            "name": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "category": "Criminal Laws",
            "subcategory": "Criminal Procedure",
            "source": "India Code / Ministry of Home Affairs",
            "act_year": "2023",
        },
        "bsa": {
            "pdf": "data/raw/criminal/bsa/bsa_2023.pdf",
            "output": "data/raw/criminal/bsa/bsa_sections.json",
            "url": "https://www.mha.gov.in/sites/default/files/250882_english_01042024.pdf",
            "max_sections": 170,
            "name": "Bharatiya Sakshya Adhiniyam, 2023",
            "category": "Criminal Laws",
            "subcategory": "Evidence Law",
            "source": "India Code / Ministry of Home Affairs",
            "act_year": "2023",
        },
        "cpa": {
            "pdf": "data/raw/consumer/cpa/cpa_2019.pdf",
            "output": "data/raw/consumer/cpa/cpa_sections.json",
            "url": "https://egazette.gov.in/WriteReadData/2019/210422.pdf",
            "max_sections": 107,
            "name": "Consumer Protection Act, 2019",
            "category": "Consumer Protection",
            "subcategory": "Consumer Law",
            "source": "The Gazette of India / Legislative Department",
            "act_year": "2019",
        },
        "css": {
            "pdf": "data/raw/labour/social_security/code_on_social_security_2020.pdf",
            "output": "data/raw/labour/social_security/social_security_sections.json",
            "url": "https://egazette.gov.in/WriteReadData/2020/222111.pdf",
            "max_sections": 164,
            "name": "Code on Social Security, 2020",
            "category": "Labour Laws",
            "subcategory": "Labour Welfare",
            "source": "The Gazette of India / Legislative Department",
            "act_year": "2020",
        },
        "pwdva": {
            "pdf": "data/raw/womens_rights/pwdva/pwdva_2005.pdf",
            "output": "data/raw/womens_rights/pwdva/pwdva_sections.json",
            "url": "https://indiacode.gov.in/handle/123456789/2021",
            "max_sections": 37,
            "name": "Protection of Women from Domestic Violence Act, 2005",
            "category": "Women's Rights",
            "subcategory": "Women Protection",
            "source": "India Code",
            "act_year": "2005",
        },
    }
    config = act_configs[args.act]
    pdf_path = args.pdf or config["pdf"]
    output_path = args.output or config["output"]

    if not os.path.exists(pdf_path) or args.download:
        success = download_official_file(config["url"], pdf_path)
        if not success:
            logger.error(f"Could not obtain raw {args.act.upper()} PDF. Stopping extraction.")
            sys.exit(1)

    if args.act == "pwdva":
        records = extract_pwdva_pdf(pdf_path, source_url=config["url"], config=config)
    else:
        records = extract_bns_pdf(
            pdf_path,
            source_url=config["url"],
            max_sections=config["max_sections"],
            act_key=args.act,
            act_name=config["name"],
            category=config.get("category", "Criminal Laws"),
            subcategory=config["subcategory"],
            source=config["source"],
            act_year=config.get("act_year", "2023"),
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=4, ensure_ascii=False)

    logger.info(f"Saved extracted legal JSON to: {output_path}")


if __name__ == "__main__":
    main()
