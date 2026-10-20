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


def extract_rti_pdf(pdf_path: str, source_url: str, config: dict) -> list:
    """
    Extract section-wise legal content for Right to Information Act, 2005.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    logger.info(f"Opened PDF '{pdf_path}' with {len(doc)} pages.")

    full_text = ""
    page_offsets = []
    for pno in range(5, min(24, len(doc))):
        txt = doc[pno].get_text('text')
        txt = re.sub(r'Right to Information Act,?\s*2005\s*', '', txt)
        txt = re.sub(r'\(Chapter\s+[^\)]+\)\s*', '', txt)
        page_offsets.append((pno + 1, len(full_text)))
        full_text += txt + '\n'

    sec_titles = {
        1: 'Short title, extent and commencement',
        2: 'Definitions',
        3: 'Right to information',
        4: 'Obligations of public authorities',
        5: 'Designation of Public Information Officers',
        6: 'Request for obtaining information',
        7: 'Disposal of request',
        8: 'Exemption from disclosure of information',
        9: 'Grounds for rejection to access in certain cases',
        10: 'Severability',
        11: 'Third party information',
        12: 'Constitution of Central Information Commission',
        13: 'Term of office and conditions of service',
        14: 'Removal of Chief Information Commissioner or Information Commissioner',
        15: 'Constitution of State Information Commission',
        16: 'Term of office and conditions of service',
        17: 'Removal of State Chief Information Commissioner or State Information Commissioner',
        18: 'Powers and functions of Information Commissions',
        19: 'Appeal',
        20: 'Penalties',
        21: 'Protection of action taken in good faith',
        22: 'Act to have overriding effect',
        23: 'Bar of jurisdiction of courts',
        24: 'Act not to apply in certain organizations',
        25: 'Monitoring and reporting',
        26: 'Appropriate Government to prepare programmes',
        27: 'Power to make rules by appropriate Government',
        28: 'Power to make rules by competent authority',
        29: 'Laying of rules',
        30: 'Power to remove difficulties',
        31: 'Repeal'
    }

    sec_positions = []
    for sec_num in range(1, 32):
        pattern = rf'\n\s*{sec_num}\.\s*'
        matches = [m.start() for m in re.finditer(pattern, full_text)]
        if matches:
            sec_positions.append((sec_num, matches[0]))

    sec_positions.sort(key=lambda x: x[1])
    today_str = datetime.date.today().isoformat()
    extracted_records = []

    for idx in range(len(sec_positions)):
        sec_num, start_pos = sec_positions[idx]
        end_pos = sec_positions[idx+1][1] if idx + 1 < len(sec_positions) else len(full_text)

        sec_text = full_text[start_pos:end_pos].strip()
        title = sec_titles.get(sec_num, f'Section {sec_num}')

        page_num = 6
        for pno, poff in page_offsets:
            if start_pos >= poff:
                page_num = pno

        extracted_records.append({
            'id': f'RTI-2005-SECTION-{sec_num}',
            'act': config['name'],
            'act_key': 'rti',
            'act_name': config['name'],
            'act_year': config['act_year'],
            'category': config['category'],
            'subcategory': config['subcategory'],
            'section': f'Section {sec_num}',
            'section_number': str(sec_num),
            'title': title,
            'content': sec_text,
            'source': config['source'],
            'source_url': source_url,
            'document_type': 'Act',
            'page': page_num,
            'language': 'English',
            'retrieved_date': today_str
        })

    logger.info(f"Extracted {len(extracted_records)} section records.")
    return extracted_records


def extract_lsa_pdf(pdf_path: str, source_url: str, config: dict) -> list:
    """
    Extract section-wise legal content for Legal Services Authorities Act, 1987.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    logger.info(f"Opened PDF '{pdf_path}' with {len(doc)} pages.")

    full_text = ""
    page_offsets = []

    for pno in range(2, len(doc)):
        page = doc[pno]
        blocks = page.get_text("blocks")
        page_text_blocks = []
        for b in blocks:
            txt = b[4].strip()
            # Standalone page number at bottom of page
            if txt.isdigit() and b[1] > 770:
                continue
            # Legislative footnote blocks at the bottom of page
            if b[1] > 650 and any(kw in txt for kw in ["Subs. by", "Ins. by", "w.e.f.", "omitted by", "The words", "vide notification"]):
                continue
            page_text_blocks.append(b[4])

        page_offsets.append((pno + 1, len(full_text)))
        full_text += "\n".join(page_text_blocks) + "\n"

    sec_titles = {
        "1": "Short title, extent and commencement",
        "2": "Definitions",
        "3": "Constitution of the National Legal Services Authority",
        "3A": "Supreme Court Legal Services Committee",
        "4": "Functions of the Central Authority",
        "5": "Central Authority to work in coordination with other agencies",
        "6": "Constitution of State Legal Services Authority",
        "7": "Functions of the State Authority",
        "8": "State Authority to act in coordination with other agencies, etc., and be subject to directions given by the Central Authority",
        "8A": "High Court Legal Services Committee",
        "9": "District Legal Services Authority",
        "10": "Functions of the District Authority",
        "11": "District Authority to act in coordination with other agencies and be subject to directions given by the Central Authority, etc.",
        "11A": "Taluk Legal Services Committee",
        "11B": "Functions of Taluk Legal Services Committee",
        "12": "Criteria for giving legal services",
        "13": "Entitlement of legal services",
        "14": "Grants by the Central Government",
        "15": "National Legal Aid Fund",
        "16": "State Legal Aid Fund",
        "17": "District Legal Aid Fund",
        "18": "Accounts and audit",
        "19": "Organisation of Lok Adalats",
        "20": "Cognizance of cases by Lok Adalats",
        "21": "Award of Lok Adalat",
        "22": "Powers of Lok Adalat or Permanent Lok Adalat",
        "22A": "Definitions",
        "22B": "Establishment of Permanent Lok Adalats",
        "22C": "Cognizance of cases by Permanent Lok Adalat",
        "22D": "Procedure of Permanent Lok Adalat",
        "22E": "Award of Permanent Lok Adalat to be final",
        "23": "Members and staff of Authorities, Committees and Lok Adalats to be public servants",
        "24": "Protection of action taken in good faith",
        "25": "Act to have overriding effect",
        "26": "Power to remove difficulties",
        "27": "Power of Central Government to make rules",
        "28": "Power of State Government to make rules",
        "29": "Power of Central Authority to make regulations",
        "29A": "Power of State Authority to make regulations",
        "30": "Laying of rules and regulations"
    }

    sections = [
        "1", "2", "3", "3A", "4", "5", "6", "7", "8", "8A", "9", "10", "11", "11A", "11B",
        "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22",
        "22A", "22B", "22C", "22D", "22E", "23", "24", "25", "26", "27", "28", "29", "29A", "30"
    ]

    sec_positions = []
    for s in sections:
        pattern = rf'(?:^|\n)\s*(?:\[\d+\]|\d+\[)?\s*{re.escape(s)}\.\s*[A-Z]'
        m = re.search(pattern, full_text)
        if not m:
            logger.error(f"Could not locate Section {s} in LSA text!")
        else:
            sec_positions.append((s, m.start()))

    today_str = datetime.date.today().isoformat()
    extracted_records = []

    for idx in range(len(sec_positions)):
        sec_num_str, start_pos = sec_positions[idx]
        end_pos = sec_positions[idx + 1][1] if idx + 1 < len(sec_positions) else len(full_text)

        sec_text = full_text[start_pos:end_pos].strip()
        sec_text = re.sub(r'^\s*(?:\[\d+\]|\d+\[)\s*', '', sec_text)
        sec_text = re.sub(r'\n\s*CHAPTER\s+[IVXLCDMA-Z0-9]+\s*\n.*$', '', sec_text, flags=re.DOTALL).strip()

        title = sec_titles.get(sec_num_str, f"Section {sec_num_str}")

        page_num = 3
        for pno, poff in page_offsets:
            if start_pos >= poff:
                page_num = pno

        extracted_records.append({
            "id": f"LSA-1987-SECTION-{sec_num_str}",
            "act": config["name"],
            "act_key": "lsa",
            "act_name": config["name"],
            "act_year": config["act_year"],
            "category": config["category"],
            "subcategory": config["subcategory"],
            "section": f"Section {sec_num_str}",
            "section_number": sec_num_str,
            "title": title,
            "content": sec_text,
            "source": config["source"],
            "source_url": source_url,
            "document_type": "Act",
            "page": page_num,
            "language": "English",
            "retrieved_date": today_str
        })

    logger.info(f"Extracted {len(extracted_records)} section records for {config['name']}.")
    return extracted_records


def extract_hma_pdf(pdf_path: str, source_url: str, config: dict) -> list:
    """
    Extract section-wise legal content for Hindu Marriage Act, 1955.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    logger.info(f"Opened PDF '{pdf_path}' with {len(doc)} pages.")

    full_text = ""
    page_offsets = []

    for pno in range(2, len(doc)):
        page = doc[pno]
        blocks = page.get_text("blocks")
        page_text_blocks = []
        for b in blocks:
            txt = b[4].strip()
            txt_clean = re.sub(r'^\s*\d{1,4}\s*\n', '', b[4])
            # Exclude legislative amendment footnote blocks at bottom of page
            if b[1] > 670 and any(kw in txt for kw in ["Subs. by", "Ins. by", "w.e.f.", "omitted by", "The words", "vide notification", "The Act has been extended"]):
                continue
            page_text_blocks.append(txt_clean)

        page_offsets.append((pno + 1, len(full_text)))
        full_text += "\n".join(page_text_blocks) + "\n"

    sec_titles = {
        "1": "Short title and extent",
        "2": "Application of Act",
        "3": "Definitions",
        "4": "Overriding effect of Act",
        "5": "Conditions for a Hindu marriage",
        "6": "Guardianship in marriage (Omitted)",
        "7": "Ceremonies for a Hindu marriage",
        "8": "Registration of Hindu marriages",
        "9": "Restitution of conjugal rights",
        "10": "Judicial separation",
        "11": "Void marriages",
        "12": "Voidable marriages",
        "13": "Divorce",
        "13A": "Alternate relief in divorce proceedings",
        "13B": "Divorce by mutual consent",
        "14": "No petition for divorce to be presented within one year of marriage",
        "15": "Divorced persons when may marry again",
        "16": "Legitimacy of children of void and voidable marriages",
        "17": "Punishment of bigamy",
        "18": "Punishment for contravention of certain other conditions for a Hindu marriage",
        "19": "Court to which petition shall be presented",
        "20": "Contents and verification of petitions",
        "21": "Application of Act 5 of 1908",
        "21A": "Power to transfer petitions in certain cases",
        "21B": "Special provision relating to trial and disposal of petitions under the Act",
        "21C": "Documentary evidence",
        "22": "Proceedings to be in camera and may not be printed or published",
        "23": "Decree in proceedings",
        "23A": "Relief for respondent in divorce and other proceedings",
        "24": "Maintenance pendente lite and expenses of proceedings",
        "25": "Permanent alimony and maintenance",
        "26": "Custody of children",
        "27": "Disposal of property",
        "28": "Appeals from decrees and orders",
        "28A": "Enforcement of decrees and orders",
        "29": "Savings",
        "30": "Repeals (Repealed)"
    }

    sections = [
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "11", "12", "13", "13A", "13B", "14", "15", "16", "17", "18",
        "19", "20", "21", "21A", "21B", "21C", "22", "23", "23A", "24",
        "25", "26", "27", "28", "28A", "29", "30"
    ]

    sec_positions = []
    for s in sections:
        pattern = rf'(?:^|\n)\s*(?:\[\d+\]|\d+\[)?\s*{re.escape(s)}\.\s*[A-Za-z\[]'
        m = re.search(pattern, full_text)
        if not m:
            logger.error(f"Could not locate Section {s} in HMA text!")
        else:
            sec_positions.append((s, m.start()))

    today_str = datetime.date.today().isoformat()
    extracted_records = []

    for idx in range(len(sec_positions)):
        sec_num_str, start_pos = sec_positions[idx]
        end_pos = sec_positions[idx + 1][1] if idx + 1 < len(sec_positions) else len(full_text)

        sec_text = full_text[start_pos:end_pos].strip()
        sec_text = re.sub(r'^\s*(?:\[\d+\]|\d+\[)\s*', '', sec_text)
        sec_text = re.sub(r'\n\s*[A-Z\s]{4,}\s*$', '', sec_text).strip()

        title = sec_titles.get(sec_num_str, f"Section {sec_num_str}")

        page_num = 3
        for pno, poff in page_offsets:
            if start_pos >= poff:
                page_num = pno

        extracted_records.append({
            "id": f"HMA-1955-SECTION-{sec_num_str}",
            "act": config["name"],
            "act_key": "hma",
            "act_name": config["name"],
            "act_year": config["act_year"],
            "category": config["category"],
            "subcategory": config["subcategory"],
            "section": f"Section {sec_num_str}",
            "section_number": sec_num_str,
            "title": title,
            "content": sec_text,
            "source": config["source"],
            "source_url": source_url,
            "document_type": "Act",
            "page": page_num,
            "language": "English",
            "retrieved_date": today_str
        })

    logger.info(f"Extracted {len(extracted_records)} section records for {config['name']}.")
    return extracted_records


def extract_posh_pdf(pdf_path: str, source_url: str, config: dict) -> list:
    """
    Extract section-wise legal content for Sexual Harassment of Women at Workplace Act, 2013.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    logger.info(f"Opened PDF '{pdf_path}' with {len(doc)} pages.")

    full_text = ""
    page_offsets = []

    for pno in range(3, len(doc)):
        page = doc[pno]
        blocks = page.get_text("blocks")
        page_text_blocks = []
        for b in blocks:
            txt = b[4].strip()
            # Standalone page number
            if txt.isdigit() and (b[1] < 60 or b[1] > 770):
                continue
            if "Gazette of India" in txt and b[1] < 70:
                continue
            page_text_blocks.append(b[4])

        page_offsets.append((pno + 1, len(full_text)))
        full_text += "\n".join(page_text_blocks) + "\n"

    # Normalize typographical quirk in Gazette print (Section 18 printed as l8.)
    full_text = re.sub(r'(?:^|\n)\s*l8\.\s*', '\n18. ', full_text)

    sec_titles = {
        1: "Short title, extent and commencement",
        2: "Definitions",
        3: "Prevention of sexual harassment",
        4: "Constitution of Internal Complaints Committee",
        5: "Notification of District Officer",
        6: "Constitution and jurisdiction of Local Complaints Committee",
        7: "Composition, tenure and other terms and conditions of Local Complaints Committee",
        8: "Grants and audit",
        9: "Complaint of sexual harassment",
        10: "Conciliation",
        11: "Inquiry into complaint",
        12: "Action during pendency of inquiry",
        13: "Inquiry report",
        14: "Punishment for false or malicious complaint and false evidence",
        15: "Determination of compensation",
        16: "Prohibition of publication or making known contents of complaint and inquiry proceedings",
        17: "Penalty for publication or making known contents of complaint and inquiry proceedings",
        18: "Appeal",
        19: "Duties of employer",
        20: "Duties and powers of District Officer",
        21: "Committee to submit annual report",
        22: "Employer to include information in annual report",
        23: "Appropriate Government to monitor implementation and maintain data",
        24: "Appropriate Government to take measures to publicise the Act",
        25: "Power to call for information and inspection of records",
        26: "Penalty for non-compliance with provisions of Act",
        27: "Cognizance of offence by courts",
        28: "Act not in derogation of any other law",
        29: "Power of appropriate Government to make rules",
        30: "Power to remove difficulties"
    }

    sections = list(range(1, 31))
    sec_positions = []
    for s in sections:
        pattern = rf'(?:^|\n)\s*{s}\.\s*([A-Za-z\[][^\n]+)'
        m = re.search(pattern, full_text)
        if not m:
            logger.error(f"Could not locate Section {s} in POSH text!")
        else:
            sec_positions.append((s, m.start()))

    today_str = datetime.date.today().isoformat()
    extracted_records = []

    for idx in range(len(sec_positions)):
        sec_num, start_pos = sec_positions[idx]
        end_pos = sec_positions[idx + 1][1] if idx + 1 < len(sec_positions) else len(full_text)

        sec_text = full_text[start_pos:end_pos].strip()
        sec_text = re.sub(r'^\s*(?:\[\d+\]|\d+\[)\s*', '', sec_text)
        sec_text = re.sub(r'\n\s*CHAPTER[\s\-]+[IVXLCDMA-Z0-9]+.*$', '', sec_text, flags=re.DOTALL).strip()

        title = sec_titles.get(sec_num, f"Section {sec_num}")

        page_num = 4
        for pno, poff in page_offsets:
            if start_pos >= poff:
                page_num = pno

        extracted_records.append({
            "id": f"POSH-2013-SECTION-{sec_num}",
            "act": config["name"],
            "act_key": "posh",
            "act_name": config["name"],
            "act_year": config["act_year"],
            "category": config["category"],
            "subcategory": config["subcategory"],
            "section": f"Section {sec_num}",
            "section_number": str(sec_num),
            "title": title,
            "content": sec_text,
            "source": config["source"],
            "source_url": source_url,
            "document_type": "Act",
            "page": page_num,
            "language": "English",
            "retrieved_date": today_str
        })

    logger.info(f"Extracted {len(extracted_records)} section records for {config['name']}.")
    return extracted_records


def extract_mva_pdf(pdf_path: str, source_url: str, config: dict) -> list:
    """
    Extract section-wise legal content for Motor Vehicles Act, 1988 (Act No. 59 of 1988).
    Extracts all substantive sections from Section 1 to 217A.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    logger.info(f"Opened PDF '{pdf_path}' with {len(doc)} pages.")

    # 1. Parse ARRANGEMENT OF SECTIONS from pages 1 to 7 (0-indexed 0 to 6)
    arr_text = ""
    for p in range(min(7, len(doc))):
        arr_text += doc[p].get_text() + "\n"

    lines = [l.strip() for l in arr_text.split('\n') if l.strip()]
    sec_titles = {}
    current_sec = None
    for l in lines:
        m = re.match(r'^(\d+[A-Z]?)\.\s*(.*)', l)
        if m:
            current_sec = m.group(1)
            sec_titles[current_sec] = m.group(2).strip()
        elif current_sec and not l.startswith('CHAPTER') and not l.startswith('SECTIONS') and not l.isupper():
            sec_titles[current_sec] += ' ' + l

    # Filter out stray non-section entries and clean punctuation
    sec_titles = {
        k: re.sub(r'[\.\[\]]+$', '', v).strip()
        for k, v in sec_titles.items()
        if int(re.match(r'\d+', k).group()) <= 220
    }

    # 2. Extract substantive text from pages 8 to 99 (0-indexed 7 to 98)
    full_text = ""
    page_offsets = []

    for pno in range(7, min(99, len(doc))):
        page = doc[pno]
        blocks = page.get_text("blocks")
        page_text_blocks = []
        for b in blocks:
            txt = b[4].strip()
            # Standalone page number
            if txt.isdigit() and b[1] < 60:
                continue
            page_text_blocks.append(b[4])

        page_offsets.append((pno + 1, len(full_text)))
        full_text += "\n".join(page_text_blocks) + "\n"

    # 3. Locate all sections
    sec_positions = []
    for s_num in sec_titles.keys():
        pattern = rf'(?:^|\n)\s*(?:\[\d+\]|\d+\[)?\s*{re.escape(s_num)}\.\s*([A-Za-z\[][^\n]+)'
        m = re.search(pattern, full_text)
        if m:
            sec_positions.append((s_num, m.start()))
        else:
            logger.warning(f"Could not locate Section {s_num} in MVA full text!")

    sec_positions = sorted(sec_positions, key=lambda x: x[1])

    today_str = datetime.date.today().isoformat()
    extracted_records = []

    for idx in range(len(sec_positions)):
        sec_num_str, start_pos = sec_positions[idx]
        end_pos = sec_positions[idx + 1][1] if idx + 1 < len(sec_positions) else len(full_text)

        sec_text = full_text[start_pos:end_pos].strip()
        # Clean chapter headings
        sec_text = re.sub(r'\n\s*CHAPTER\s+[IVXLCDMA-Z0-9]+.*\n', '\n', sec_text)
        # Clean footnote divider lines
        sec_text = re.sub(r'\n\s*_{3,}\s*\n.*$', '', sec_text, flags=re.DOTALL).strip()
        # Clean leading footnote bracket numbers e.g. 1[ or [1]
        sec_text = re.sub(r'^\s*(?:\[\d+\]|\d+\[)\s*', '', sec_text)

        title = sec_titles.get(sec_num_str, f"Section {sec_num_str}")

        page_num = 8
        for pno, poff in page_offsets:
            if start_pos >= poff:
                page_num = pno

        extracted_records.append({
            "id": f"MVA-1988-SECTION-{sec_num_str}",
            "act": config["name"],
            "act_key": "mva",
            "act_name": config["name"],
            "act_year": config["act_year"],
            "category": config["category"],
            "subcategory": config["subcategory"],
            "section": f"Section {sec_num_str}",
            "section_number": sec_num_str,
            "title": title,
            "content": sec_text,
            "source": config["source"],
            "source_url": source_url,
            "document_type": "Act",
            "page": page_num,
            "language": "English",
            "retrieved_date": today_str
        })

    logger.info(f"Extracted {len(extracted_records)} section records for {config['name']}.")
    return extracted_records


def extract_tpa_pdf(pdf_path: str, source_url: str, config: dict) -> list:
    """
    Extract section-wise legal content for Transfer of Property Act, 1882 (Act No. 4 of 1882).
    Extracts all substantive sections from Section 1 to Section 137.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = fitz.open(pdf_path)
    logger.info(f"Opened PDF '{pdf_path}' with {len(doc)} pages.")

    # 1. Parse ARRANGEMENT OF SECTIONS from pages 1 to 6 (0-indexed 0 to 5)
    arr_text = ""
    for p in range(min(6, len(doc))):
        arr_text += doc[p].get_text() + "\n"

    lines = [l.strip() for l in arr_text.split('\n') if l.strip()]
    sec_titles = {}
    current_sec = None
    for l in lines:
        m = re.match(r'^(\d+[A-Z]?)\.\s*(.*)', l)
        if m:
            current_sec = m.group(1)
            sec_titles[current_sec] = m.group(2).strip()
        elif current_sec and not l.startswith('CHAPTER') and not l.startswith('SECTIONS') and not l.isupper():
            sec_titles[current_sec] += ' ' + l

    # Filter out non-section numbers and clean trailing periods and brackets
    sec_titles = {
        k: re.sub(r'[\.\[\]]+$', '', v).strip()
        for k, v in sec_titles.items()
        if int(re.match(r'\d+', k).group()) <= 137
    }

    # 2. Extract substantive text from pages 7 to 45 (0-indexed 6 to 44)
    full_text = ""
    page_offsets = []

    for pno in range(6, min(45, len(doc))):
        page = doc[pno]
        blocks = page.get_text("blocks")
        page_text_blocks = []
        for b in blocks:
            txt = b[4].strip()
            # Standalone page number
            if txt.isdigit() and b[1] < 60:
                continue
            page_text_blocks.append(b[4])

        page_offsets.append((pno + 1, len(full_text)))
        full_text += "\n".join(page_text_blocks) + "\n"

    # 3. Locate all sections using title-aware matching to avoid footnote false positives
    sec_positions = []
    for s_num, s_title in sec_titles.items():
        title_words = re.findall(r'[A-Za-z]+', s_title)
        first_word = title_words[0] if title_words else ''
        pat = rf'(?:^|\n)\s*(?:\d+\s*\[|\[\d+\]|\d+\[|\d+)?\s*{re.escape(s_num)}\.\s*(?:\[|\"|“)?\s*{re.escape(first_word)}'
        m = re.search(pat, full_text, re.IGNORECASE)
        if m:
            sec_positions.append((s_num, m.start()))
        else:
            pat_fallback = rf'(?:^|\n)\s*(?:\d+\s*\[|\[\d+\]|\d+\[|\d+)?\s*{re.escape(s_num)}\.\s*([A-Za-z\[“\"\'].*)'
            m2 = re.search(pat_fallback, full_text)
            if m2:
                sec_positions.append((s_num, m2.start()))
            else:
                logger.warning(f"Could not locate Section {s_num} in TPA full text!")

    sec_positions = sorted(sec_positions, key=lambda x: x[1])

    today_str = datetime.date.today().isoformat()
    extracted_records = []

    for idx in range(len(sec_positions)):
        sec_num_str, start_pos = sec_positions[idx]
        end_pos = sec_positions[idx + 1][1] if idx + 1 < len(sec_positions) else len(full_text)

        sec_text = full_text[start_pos:end_pos].strip()
        # Clean chapter headings
        sec_text = re.sub(r'\n\s*CHAPTER\s+[IVXLCDMA-Z0-9]+.*\n', '\n', sec_text)
        # Clean footnote divider lines
        sec_text = re.sub(r'\n\s*_{3,}\s*\n.*$', '', sec_text, flags=re.DOTALL).strip()
        # Clean leading footnote bracket numbers e.g. 1[ or 2 [
        sec_text = re.sub(r'^\s*(?:\d+\s*\[|\[\d+\]|\d+\[)\s*', '', sec_text)

        title = sec_titles.get(sec_num_str, f"Section {sec_num_str}")

        page_num = 7
        for pno, poff in page_offsets:
            if start_pos >= poff:
                page_num = pno

        extracted_records.append({
            "id": f"TPA-1882-SECTION-{sec_num_str}",
            "act": config["name"],
            "act_key": "tpa",
            "act_name": config["name"],
            "act_year": config["act_year"],
            "category": config["category"],
            "subcategory": config["subcategory"],
            "section": f"Section {sec_num_str}",
            "section_number": sec_num_str,
            "title": title,
            "content": sec_text,
            "source": config["source"],
            "source_url": source_url,
            "document_type": "Act",
            "page": page_num,
            "language": "English",
            "retrieved_date": today_str
        })

    logger.info(f"Extracted {len(extracted_records)} section records for {config['name']}.")
    return extracted_records


def extract_epa_pdf(pdf_path: str, source_url: str, config: dict) -> list:
    """Extracts section records from Environment (Protection) Act, 1986 PDF."""
    logger.info(f"Extracting EPA records from: {pdf_path}")
    doc = fitz.open(pdf_path)

    page_texts = []
    for pno in range(1, len(doc)):
        page_texts.append((pno + 1, doc[pno].get_text()))

    full_text = ""
    page_offsets = []
    for pno, txt in page_texts:
        page_offsets.append((pno, len(full_text)))
        full_text += txt + "\n"

    clean_text = re.sub(r'The Environment \(Protection\) Act, 1986\s*\n\s*\d+', '', full_text)
    clean_text = re.sub(r'Act \d+ of \d+', '', clean_text)

    sec_pattern = re.compile(r'(?:^|\n)\s*(\d+)\s*\.\s*([A-Z0-9\s,\-\(\)\/\.]+?)\s*[\.\-]+\s*\n', re.MULTILINE)
    matches = list(sec_pattern.finditer(clean_text))

    chapter_map = {
        (1, 2): ("Chapter I", "Preliminary"),
        (3, 6): ("Chapter II", "General Powers of the Central Government"),
        (7, 17): ("Chapter III", "Prevention, Control and Abatement of Environmental Pollution"),
        (18, 26): ("Chapter IV", "Miscellaneous")
    }

    records = []
    today_str = datetime.date.today().isoformat()

    for i, m in enumerate(matches):
        sec_num = m.group(1)
        raw_title = m.group(2).strip()
        title = raw_title.replace('\n', ' ').strip()
        title = re.sub(r'\s+', ' ', title).title()

        start_pos = m.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(clean_text)
        content = clean_text[start_pos:end_pos].strip()
        content = re.sub(r'\n\s*CHAPTER\s+[IVXLCDM]+.*?\n', '\n', content)
        content = re.sub(r'\n\s*_{3,}.*$', '', content, flags=re.DOTALL).strip()

        s_int = int(sec_num)
        ch_num, ch_title = "", ""
        for (s_start, s_end), (cnum, ctitle) in chapter_map.items():
            if s_start <= s_int <= s_end:
                ch_num = cnum
                ch_title = ctitle
                break

        page_num = 2
        for pno, poff in page_offsets:
            if m.start() >= poff:
                page_num = pno

        records.append({
            "id": f"EPA-1986-SECTION-{sec_num}",
            "act": config["name"],
            "act_key": "epa",
            "act_name": config["name"],
            "act_year": config["act_year"],
            "category": config["category"],
            "subcategory": config["subcategory"],
            "chapter": f"{ch_num}: {ch_title}" if ch_num else "",
            "section": f"Section {sec_num}",
            "section_number": sec_num,
            "title": title,
            "content": f"{sec_num}. {title}.— {content}",
            "source": config["source"],
            "source_url": source_url,
            "document_type": "Act",
            "page": page_num,
            "language": "English",
            "retrieved_date": today_str
        })

    logger.info(f"Extracted {len(records)} sections for EPA 1986.")
    return records


def main():
    parser = argparse.ArgumentParser(description="Legal Data Extraction Script")
    parser.add_argument("--act", type=str, default="bns", choices=["bns", "bnss", "bsa", "cpa", "css", "pwdva", "rti", "lsa", "hma", "posh", "mva", "tpa", "epa"], help="Act key to extract (default: bns)")
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
        "rti": {
            "pdf": "data/raw/rti/rti_2005.pdf",
            "output": "data/raw/rti/rti_sections.json",
            "url": "https://cic.gov.in/sites/default/files/RTI-Act_English.pdf",
            "max_sections": 31,
            "name": "Right to Information Act, 2005",
            "category": "RTI",
            "subcategory": "Public Information",
            "source": "Central Information Commission / Ministry of Law and Justice",
            "act_year": "2005",
        },
        "lsa": {
            "pdf": "data/raw/legal_aid/lsa_1987.pdf",
            "output": "data/raw/legal_aid/lsa_sections.json",
            "url": "https://cdnbbsr.s3waas.gov.in/s32e45f93088c7db59767efef516b306aa/uploads/2025/04/202504081796627129.pdf",
            "max_sections": 40,
            "name": "Legal Services Authorities Act, 1987",
            "category": "Legal Aid",
            "subcategory": "Access to Justice",
            "source": "NALSA / India Code",
            "act_year": "1987",
        },
        "hma": {
            "pdf": "data/raw/family/hma_1955.pdf",
            "output": "data/raw/family/hma_sections.json",
            "url": "https://dms.hp.gov.in/ViewPDF.aspx?fn=cbOUjYHu1Pa%2B8vT2R7dS7%2FIPmvhAVQbTjec%2BSrQU%2BLJLVjJKYoaqeZw7yhodAnTv&ot=2LiD6ggCMIp9mzvYCQJmrg%3D%3D",
            "max_sections": 37,
            "name": "Hindu Marriage Act, 1955",
            "category": "Family Laws",
            "subcategory": "Personal Law",
            "source": "Legislative Department / India Code",
            "act_year": "1955",
        },
        "posh": {
            "pdf": "data/raw/womens_rights/posh_2013.pdf",
            "output": "data/raw/womens_rights/posh_sections.json",
            "url": "https://kwa.kerala.gov.in/wp-content/uploads/2023/08/THE-SEXUAL-HARASSMENT-OF-WOMEN-AT-WORKPLACE.pdf",
            "max_sections": 30,
            "name": "Sexual Harassment of Women at Workplace Act, 2013",
            "category": "Women's Rights",
            "subcategory": "Workplace Safety",
            "source": "The Gazette of India / Ministry of Law and Justice",
            "act_year": "2013",
        },
        "mva": {
            "pdf": "data/raw/traffic/mva_1988.pdf",
            "output": "data/raw/traffic/mva_sections.json",
            "url": "https://www.indiacode.nic.in/bitstream/123456789/9460/1/a1988-59.pdf",
            "max_sections": 223,
            "name": "Motor Vehicles Act, 1988",
            "category": "Traffic Laws",
            "subcategory": "Road & Traffic Law",
            "source": "India Code / Ministry of Road Transport and Highways",
            "act_year": "1988",
        },
        "tpa": {
            "pdf": "data/raw/property/tpa_1882.pdf",
            "output": "data/raw/property/tpa_sections.json",
            "url": "https://www.indiacode.nic.in/bitstream/123456789/2338/1/A1882-04.pdf",
            "max_sections": 148,
            "name": "Transfer of Property Act, 1882",
            "category": "Property Laws",
            "subcategory": "Property Rights",
            "source": "India Code / Legislative Department",
            "act_year": "1882",
        },
        "epa": {
            "pdf": "data/raw/environment/ep_act_1986.pdf",
            "output": "data/raw/environment/epa_sections.json",
            "url": "https://www.indiacode.nic.in/bitstream/123456789/4316/1/ep_act_1986.pdf",
            "max_sections": 26,
            "name": "Environment (Protection) Act, 1986",
            "category": "Environmental Laws",
            "subcategory": "Environmental Protection",
            "source": "India Code / Ministry of Environment, Forest and Climate Change",
            "act_year": "1986",
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
    elif args.act == "rti":
        records = extract_rti_pdf(pdf_path, source_url=config["url"], config=config)
    elif args.act == "lsa":
        records = extract_lsa_pdf(pdf_path, source_url=config["url"], config=config)
    elif args.act == "hma":
        records = extract_hma_pdf(pdf_path, source_url=config["url"], config=config)
    elif args.act == "posh":
        records = extract_posh_pdf(pdf_path, source_url=config["url"], config=config)
    elif args.act == "mva":
        records = extract_mva_pdf(pdf_path, source_url=config["url"], config=config)
    elif args.act == "tpa":
        records = extract_tpa_pdf(pdf_path, source_url=config["url"], config=config)
    elif args.act == "epa":
        records = extract_epa_pdf(pdf_path, source_url=config["url"], config=config)
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
