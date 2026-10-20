#!/usr/bin/env python3
"""
LegalConnect Retrieval Utilities Module
----------------------------------------
Implements:
1. Deterministic Legal Query Expansion / Normalization
2. Metadata-Aware Score Boosting (Section number, title, act, alias matches)
3. Candidate Reranking & Section-Level Deduplication
4. Retrieval Confidence / Relevance Verification
"""

import os
import re
import time
from typing import List, Dict, Any, Tuple, Optional

# Configure offline mode only when explicitly requested in environment
if os.environ.get("HF_HUB_OFFLINE") in ("1", "true", "yes"):
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Legal Alias Mapping (Deterministic)
LEGAL_ALIASES = {
    "ipc": "Indian Penal Code",
    "bns": "Bharatiya Nyaya Sanhita",
    "bnss": "Bharatiya Nagarik Suraksha Sanhita",
    "bsa": "Bharatiya Sakshya Adhiniyam",
    "cpa": "Consumer Protection Act",
    "it": "Information Technology Act",
    "css": "Code on Social Security",
    "pwdva": "Protection of Women from Domestic Violence Act",
    "rti": "Right to Information Act",
    "lsa": "Legal Services Authorities Act",
    "nalsa": "National Legal Services Authority",
    "salsa": "State Legal Services Authority",
    "dlsa": "District Legal Services Authority",
    "tlsc": "Taluk Legal Services Committee",
    "hma": "Hindu Marriage Act",
    "hindu marriage": "Hindu Marriage Act",
    "posh": "Sexual Harassment of Women at Workplace Act",
    "icc": "Internal Complaints Committee",
    "lcc": "Local Complaints Committee",
    "mva": "Motor Vehicles Act",
    "motor vehicles": "Motor Vehicles Act",
    "traffic": "Motor Vehicles Act",
    "tpa": "Transfer of Property Act",
    "transfer of property": "Transfer of Property Act",
    "property law": "Transfer of Property Act",
    "epa": "Environment Protection Act",
    "environment": "Environment Protection Act",
    "coi": "The Constitution of India",
    "constitution": "The Constitution of India",
    "constitution of india": "The Constitution of India",
    "indian constitution": "The Constitution of India",
    "pm-kisan": "Government Welfare Schemes",
    "pm kisan": "Government Welfare Schemes",
    "pm-jay": "Government Welfare Schemes",
    "pm jay": "Government Welfare Schemes",
    "ayushman bharat": "Government Welfare Schemes",
    "pmay": "Government Welfare Schemes",
    "awas yojana": "Government Welfare Schemes",
    "sukanya samriddhi": "Government Welfare Schemes",
    "ssy": "Government Welfare Schemes"
}

LEGAL_ACT_PATTERNS = {
    "Government Welfare Schemes": [
        r"\b(?:pm-?kisan|kisan\s+samman\s+nidhi)\b",
        r"\b(?:pm-?jay|ayushman\s+bharat|jan\s+arogya\s+yojana)\b",
        r"\b(?:pmay|pradhan\s+mantri\s+awas\s+yojana|awas\s+yojana)\b",
        r"\b(?:sukanya\s+samriddhi|ssy)\b",
        r"\b(?:welfare\s+scheme|government\s+scheme|myscheme)\b"
    ],
    "The Constitution of India": [
        r"\bthe\s+constitution\s+of\s+india\b",
        r"\bconstitution\s+of\s+india\b",
        r"\bindian\s+constitution\b",
        r"\bconstitution\b",
        r"\bcoi\b"
    ],
    "Bharatiya Nyaya Sanhita, 2023": [r"\bbns\b", r"\bbharatiya\s+nyaya\s+sanhita\b", r"\bipc\b", r"\bindian\s+penal\s+code\b"],
    "Bharatiya Nagarik Suraksha Sanhita, 2023": [r"\bbnss\b", r"\bbharatiya\s+nagarik\s+suraksha\s+sanhita\b", r"\bcrpc\b", r"\bcode\s+of\s+criminal\s+procedure\b"],
    "Bharatiya Sakshya Adhiniyam, 2023": [r"\bbsa\b", r"\bbharatiya\s+sakshya\s+adhiniyam\b", r"\bindian\s+evidence\s+act\b", r"\bevidence\s+act\b"],
    "Information Technology Act, 2000": [r"\bit\s+act\b", r"\binformation\s+technology\s+act\b", r"\bcyber\s+law\b", r"\bcyber\s+crime\b", r"\bcyber\s+act\b"],
    "Consumer Protection Act, 2019": [r"\bcpa\b", r"\bconsumer\s+protection\s+act\b"],
    "Code on Social Security, 2020": [r"\bcss\b", r"\bcode\s+on\s+social\s+security\b", r"\bsocial\s+security\s+code\b"],
    "Protection of Women from Domestic Violence Act, 2005": [r"\bpwdva\b", r"\bdomestic\s+violence\s+act\b", r"\bprotection\s+of\s+women\s+from\s+domestic\s+violence\b"],
    "Right to Information Act, 2005": [r"\brti\b", r"\bright\s+to\s+information\b", r"\bright\s+to\s+information\s+act\b"],
    "Legal Services Authorities Act, 1987": [r"\blsa\b", r"\blegal\s+services\s+authorities\s+act\b", r"\blegal\s+services\s+act\b", r"\bnalsa\b", r"\bls\s+act\b"],
    "Hindu Marriage Act, 1955": [r"\bhma\b", r"\bhindu\s+marriage\s+act\b", r"\bhindu\s+marriage\b"],
    "Sexual Harassment of Women at Workplace Act, 2013": [
        r"\bposh\b",
        r"\bsexual\s+harassment\s+(?:of\s+women\s+at\s+workplace(?:\s+act)?)\b",
        r"\bworkplace\s+sexual\s+harassment\b",
        r"\bposh\s+act\b",
        r"\binternal\s+complaints?\s+committee\b",
        r"\blocal\s+complaints?\s+committee\b",
    ],
    "Motor Vehicles Act, 1988": [
        r"\bmva\b",
        r"\bmotor\s+vehicles?\s+act\b",
        r"\bmotor\s+vehicle\b",
        r"\btraffic\s+rules?\b",
        r"\btraffic\s+act\b",
        r"\bdriving\s+licen[cs]e\b",
        r"\bdrunk(?:en)?\s+driving\b",
    ],
    "Transfer of Property Act, 1882": [
        r"\btpa\b",
        r"\btransfer\s+of\s+property\s+act\b",
        r"\btransfer\s+of\s+property\b",
        r"\bproperty\s+act\b",
        r"\blis\s+pendens\b",
        r"\bpart\s+performance\b",
        r"\bmortgage\s+(?:deed|rights?|redemption)\b",
    ],
    "Environment (Protection) Act, 1986": [
        r"\bepa\b",
        r"\benvironment\s+protection\s+act\b",
        r"\benvironment\s+\(protection\)\s+act\b",
        r"\benvironmental\s+protection\b",
        r"\benvironmental\s+pollut(?:ant|ion)\b",
        r"\bhazardous\s+substances?\b",
    ]
}

DEFAULT_CANDIDATE_POOL_SIZE = 45
DEFAULT_FINAL_TOP_K = 5
DEFAULT_CONFIDENCE_THRESHOLD = 0.35
MAX_CHUNKS_PER_SECTION = 2
MIN_TITLE_TOPIC_OVERLAP = 2

TOPIC_STOP_WORDS = {
    "what", "is", "the", "a", "an", "for", "of", "to", "in", "and", "or",
    "under", "does", "say", "about", "when", "may", "how", "are", "as",
    "with", "by", "from", "on", "at", "it", "this", "that", "be",
    "bharatiya", "nyaya", "nagarik", "suraksha", "sakshya", "adhiniyam", "sanhita",
    "bns", "bnss", "bsa", "cpa", "consumer", "protection", "act", "css", "social", "security", "code",
    "pwdva", "domestic", "women", "violence", "rti", "information",
    "lsa", "nalsa", "salsa", "dlsa",
    "hma", "hindu", "marriage",
    "posh", "harassment",
    "mva", "vehicle", "motor",
    "tpa", "epa", "article", "articles", "art", "constitution", "preamble"
}


# Natural Problem Domain Concepts for Colloquial Queries
NATURAL_PROBLEM_CONCEPTS = [
    (r"\b(instagram|facebook|twitter|whatsapp|social media|fake account|fake profile|fake id|impersonat\w*)\b", "Information Technology Act identity theft cheating by personation computer resource section 66c section 66d"),
    (r"\b(using\s+my\s+name|account\s+using\s+my\s+name|personal\s+(?:details|information)|without\s+my\s+permission|photo\w*\s+online|stolen\s+identity|identity\s+theft)\b", "Information Technology Act identity theft cheating by personation computer resource section 66c section 66d"),
    (r"\b(hacked|hacking|cyber\s*crime|phishing|otp fraud|online fraud)\b", "Information Technology Act hacking computer system electronic"),
    (r"\b(phone|laptop|product|item|goods|appliance|device)\b.*\b(not working|stopped working|defect\w*|faulty|replace|refund|shopkeeper|seller|refuses?\s+to\s+help)\b", "Consumer Protection Act defective product product liability liability of product sellers section 84 section 85 section 86 consumer rights"),
    (r"\b(defect\w* product|damaged\s+product|damaged\s+when\s+it\s+arrived|product\s+(?:that\s+)?was\s+damaged|refus\w* to refund|refund my money|seller\s+refuses?\s+to\s+help|isn'?t\s+their\s+responsibility)\b", "Consumer Protection Act defective product product liability liability of product sellers section 84 section 85 section 86 consumer rights"),
    (r"\b(seller\s+liability|liability\s+of\s+(?:product\s+)?seller|defect\w*\s+product\s+from\s+seller|compensation.*product.*seller)\b", "Consumer Protection Act liability of product sellers section 85 product liability compensation"),
    (r"\b(salary|wages|unpaid|delay\w* pay\w*|not paid|withheld pay|withholding salary|paid my salary)\b", "Code on Social Security payment wages compensation default"),
    (r"\b(husband|spouse|in-laws|partner|wife)\b.*\b(threat\w*|worried\s+about\s+my\s+safety|scared|safety|physic\w*\s*violen\w*|beat\w*|abuse|abusing|harass\w*)\b", "Protection of Women from Domestic Violence Act domestic violence protection orders section 3 section 12 section 18"),
    (r"\bprotection\s+orders?\b", "Protection of Women from Domestic Violence Act protection orders section 18 magistrate"),
    (r"\b(rti|right\s+to\s+information|public\s+information\s+officer|pio|first\s+appeal|second\s+appeal|information\s+commission|cic|sic|public\s+authority|obtain\s+copies.*public\s+authority)\b", "Right to Information Act request for obtaining information public authority disposal of request section 3 section 6"),
    (r"\b(free\s+legal\s+aid|free\s+lawyer|cannot\s+afford\s+a\s+(?:lawyer|advocate)|can'?t\s+afford\s+a\s+(?:lawyer|advocate)|legal\s+aid|free\s+legal\s+representation|lok\s+adalat|permanent\s+lok\s+adalat|nalsa)\b", "Legal Services Authorities Act criteria for giving legal services entitlement free legal aid Lok Adalats section 12"),
    (r"\b(living\s+separately|separated\s+from\s+(?:my\s+)?(?:spouse|husband|wife)|stopped\s+living\s+with\s+me|withdrawn\s+from\s+(?:my\s+)?society|desert\w*)\b", "Hindu Marriage Act restitution of conjugal rights judicial separation divorce living separately"),
    (r"\b(grounds\s+for\s+divorce|divorce\s+grounds|file\s+for\s+divorce|apply\s+for\s+divorce)\b", "Hindu Marriage Act divorce grounds for divorce judicial separation"),
    (r"\b(mutual\s+consent\s+divorce|divorce\s+by\s+mutual\s+consent|mutual\s+divorce)\b", "Hindu Marriage Act divorce by mutual consent section 13b living separately"),
    (r"\b(mutually\s+agreed|mutual\s+agreement)\b.*\b(?:separate|divorce)\b|\bdivorce\b.*\b(?:mutually\s+agreed|mutual\s+consent)\b", "Hindu Marriage Act divorce by mutual consent section 13b living separately"),
    (r"\b(void\s+marriage|voidable\s+marriage|declare\s+(?:a\s+)?marriage\s+void|nullity\s+of\s+marriage|annulment|annul\s+marriage)\b", "Hindu Marriage Act void marriages voidable marriages conditions for Hindu marriage"),
    (r"\b(restitution\s+of\s+conjugal\s+rights|conjugal\s+rights)\b", "Hindu Marriage Act restitution of conjugal rights section 9"),
    (r"\b(alimony|maintenance\s+pendente\s+lite|permanent\s+alimony)\b", "Hindu Marriage Act maintenance pendente lite permanent alimony expenses of proceedings"),
    (r"\b(sexual\s+harassment|harass\w*\s+at\s+(?:work|office|workplace)|inappropriate\s+touching\s+at\s+work|sexual\s+favors?|unwelcome\s+(?:sexual\s+)?conduct)\b", "Sexual Harassment of Women at Workplace Act prevention Internal Complaints Committee section 4 complaint of sexual harassment section 9 employer duties"),
    (r"\b(internal\s+complaints?\s+committee|icc\s+complaint|local\s+complaints?\s+committee|lcc|posh\s+complaint)\b", "Sexual Harassment of Women at Workplace Act constitution of Internal Complaints Committee section 4 complaint of sexual harassment section 9 inquiry into complaint duties of employer"),
    (r"\b(?:what\s+)?committee\s+handles\b|\bworkplace\s+(?:harassment|sexual\s+harassment)\b.*\bcommittee\b|\binternal\s+committee\s+complaint\b", "Sexual Harassment of Women at Workplace Act constitution of Internal Complaints Committee section 4 complaint of sexual harassment section 9"),
    (r"\b(employer\s+duties\s+posh|posh\s+policy|workplace\s+harassment\s+committee|duties\s+of\s+employer\s+under\s+posh)\b", "Sexual Harassment of Women at Workplace Act duties of employer Internal Complaints Committee annual report"),
    (r"\b(drunk\s+driving|drunken\s+driving|driving\s+under\s+the\s+influence|dui|drink\s+and\s+drive|alcohol\s+(?:while\s+)?driving)\b", "Motor Vehicles Act driving by drunken person under influence of drugs section 185 breath test breath analyser penalty imprisonment"),
    (r"\b(driving\s+without\s+(?:a\s+)?(?:valid\s+)?(?:driving\s+)?licen[cs]e|no\s+driving\s+licen[cs]e|without\s+(?:valid\s+)?licen[cs]e|expired\s+licen[cs]e)\b", "Motor Vehicles Act necessity for driving licence driving without licence section 3 section 181 penalty"),
    (r"\b(without\s+(?:a\s+)?helmet|not\s+wearing\s+(?:a\s+)?helmet|pillion\s+rider\s+helmet|protective\s+headgear|seat\s*belt)\b", "Motor Vehicles Act wearing of protective headgear helmet section 129 safety measures pillion riders penalty"),
    (r"\b(overspeeding|speed\s+limit|speeding\s+fine|rash\s+driving|driving\s+dangerously|dangerous\s+driving)\b", "Motor Vehicles Act limits of speed driving dangerously section 112 section 183 section 184 penalty"),
    (r"\b(hit\s+and\s+run|car\s+accident|road\s+accident|duty\s+of\s+driver\s+in\s+accident|accident\s+victim)\b", "Motor Vehicles Act duty of driver in case of accident medical attendance section 134 hit and run special compensation"),
    (r"\b(motor\s+accident\s+claim|claims\s+tribunal|compensation\s+for\s+accident|accident\s+compensation|mact)\b", "Motor Vehicles Act Claims Tribunal application for compensation section 165 section 166"),
    (r"\b(driving\s+without\s+insurance|vehicle\s+insurance|third\s+party\s+insurance|uninsured\s+vehicle)\b", "Motor Vehicles Act necessity for insurance against third party risk section 146 driving uninsured vehicle section 196 penalty"),
    (r"\b(transfer\s+of\s+property|sale\s+of\s+(?:immovable\s+)?property|contract\s+for\s+sale\s+of\s+land|sale\s+deed|buy\w*\s+land|sell\w*\s+land|seller\s+and\s+buyer\s+of\s+property)\b", "Transfer of Property Act sale defined sale how made contract for sale section 54 rights and liabilities of buyer and seller"),
    (r"\b(mortgage|mortgagor|mortgagee|equity\s+of\s+redemption|right\s+to\s+redeem|simple\s+mortgage|usufructuary\s+mortgage|english\s+mortgage)\b", "Transfer of Property Act mortgage defined section 58 right of mortgagor to redeem section 60"),
    (r"\b(lease\s+of\s+(?:immovable\s+)?property|tenant\s+eviction|notice\s+to\s+quit|landlord\s+and\s+tenant|termination\s+of\s+lease|determination\s+of\s+lease|duration\s+of\s+lease)\b", "Transfer of Property Act lease defined section 105 duration of lease notice to quit section 106 rights and liabilities of lessor and lessee determination of lease section 111"),
    (r"\b(gift\s+of\s+(?:immovable\s+)?property|gift\s+deed|transfer\s+by\s+gift|revocation\s+of\s+gift|property\s+(?:be\s+)?gifted|gifted\s+verbally)\b", "Transfer of Property Act gift defined section 122 transfer how effected section 123 suspension or revocation of gift"),
    (r"\b(property\s+dispute\s+in\s+court|selling\s+property\s+during\s+lawsuit|pending\s+suit\s+property|lis\s+pendens)\b", "Transfer of Property Act transfer of property pending suit lis pendens section 52"),
    (r"\b(part\s+performance|possession\s+under\s+contract|agreement\s+to\s+sell\s+possession)\b", "Transfer of Property Act part performance section 53A"),
    (r"\b(fraudulent\s+transfer\s+of\s+property|transfer\s+to\s+defeat\s+creditors)\b", "Transfer of Property Act fraudulent transfer section 53"),
    (r"\b(fir|first\s+information\s+report|zero\s+fir|police\s+complaint|police\s+refuses?\s+to\s+(?:register|file|take)\s+(?:an?\s+)?fir)\b", "Bharatiya Nagarik Suraksha Sanhita first information report FIR information in cognizable cases police officer refusal section 173"),
    (r"\b(anticipatory\s+bail|grant\s+of\s+bail|regular\s+bail|bail\s+application)\b", "Bharatiya Nagarik Suraksha Sanhita bail direction for grant of bail section 480 section 482"),
    (r"\b(dowry|dowry\s+harassment|cruelty\s+by\s+husband)\b", "Bharatiya Nyaya Sanhita cruelty by husband or relatives dowry death section 85 section 86"),
    (r"\b(cheque\s+bounce|bounced\s+cheque|dishonour\s+of\s+cheque)\b", "cheque bounce dishonour of cheque financial fraud complaint"),
    (r"\b(?:replaces?|in\s+place\s+of)\s+section\s+154\b|\b(?:crpc|code\s+of\s+criminal\s+procedure)\b.*\b(?:section\s+154|fir)\b", "Bharatiya Nagarik Suraksha Sanhita information in cognizable cases first information report FIR section 173"),
    (r"\b(?:replaces?|in\s+place\s+of)\s+section\s+302\b|\b(?:ipc|indian\s+penal\s+code)\b.*\b(?:section\s+302|murder)\b|\bsection\s+302\b.*\b(?:ipc|indian\s+penal\s+code)\b", "Bharatiya Nyaya Sanhita punishment for murder section 103 repeal and savings section 358"),
    (r"\b(?:replaces?|in\s+place\s+of)\s+section\s+65b\b|\b(?:evidence\s+act|indian\s+evidence\s+act)\b.*\b65b\b|\belectronic\s+evidence\b.*\bbharatiya\s+sakshya\b", "Bharatiya Sakshya Adhiniyam electronic records admissibility section 61 section 63"),
    (r"\b(discharge|emission|excess\s+emission|environmental\s+pollutant|handling\s+hazardous\s+substances?|closure\s+of\s+industry|stoppage\s+of\s+electricity|pollution\s+from\s+factory)\b", "Environment (Protection) Act power of Central Government power to give directions section 5 persons carrying on industry not to allow emission section 7 hazardous substances section 8 penalties section 15"),
    (r"\b(environmental\s+laborator\w*|government\s+analyst|samples?\s+of\s+air\s+water\s+soil)\b", "Environment (Protection) Act power to take sample section 11 environmental laboratories section 12 Government Analysts section 13"),
    (r"\b(fundamental\s+rights?|right\s+to\s+equality|equality\s+before\s+law|equal\s+protection\s+of\s+laws?)\b", "The Constitution of India Article 14 equality before law fundamental rights"),
    (r"\b(right\s+to\s+life|personal\s+liberty|life\s+and\s+personal\s+liberty|privacy|right\s+to\s+privacy)\b", "The Constitution of India Article 21 protection of life and personal liberty fundamental rights"),
    (r"\b(right\s+to\s+education|free\s+and\s+compulsory\s+education)\b", "The Constitution of India Article 21A right to education fundamental rights"),
    (r"\b(freedom\s+of\s+speech|freedom\s+of\s+expression|peaceful\s+assembly)\b", "The Constitution of India Article 19 protection of certain rights regarding freedom of speech fundamental rights"),
    (r"\b(constitutional\s+remedies?|writ|writs|habeas\s+corpus|mandamus|prohibition|certiorari|quo\s+warranto)\b", "The Constitution of India Article 32 Article 226 remedies for enforcement of fundamental rights writs"),
    (r"\b(directive\s+principles|dpsp|directive\s+principles\s+of\s+state\s+policy)\b", "The Constitution of India Part IV Directive Principles of State Policy"),
    (r"\b(amendment\s+of\s+the\s+constitution|power\s+of\s+parliament\s+to\s+amend)\b", "The Constitution of India Article 368 power of Parliament to amend the Constitution"),
    (r"\b(preamble\s+to\s+the\s+constitution|sovereign\s+socialist\s+secular\s+democratic\s+republic)\b", "The Constitution of India Preamble sovereign socialist secular democratic republic"),
    (r"\b(fundamental\s+duties)\b", "The Constitution of India Article 51A Fundamental duties Part IVA"),
    (r"\b(pm-?kisan|kisan\s+samman\s+nidhi|financial\s+assistance\s+for\s+farmers?|farmer\s+subsidy|6000\s+(?:rupees|per\s+year).*farmer)\b", "Government Welfare Schemes Pradhan Mantri Kisan Samman Nidhi PM-KISAN 6000 per year installment DBT eligibility farmer"),
    (r"\b(ayushman\s+bharat|pm-?jay|jan\s+arogya\s+yojana|health\s+insurance\s+scheme|5\s+lakh\s+health\s+cover|free\s+hospitalization\s+card|ayushman\s+card)\b", "Government Welfare Schemes Ayushman Bharat Pradhan Mantri Jan Arogya Yojana PM-JAY 5 lakh health insurance cover cashless hospitalization golden card"),
    (r"\b(pmay|pradhan\s+mantri\s+awas\s+yojana|awas\s+yojana|housing\s+scheme|pucca\s+house\s+subsidy|financial\s+assistance.*house\s+construction)\b", "Government Welfare Schemes Pradhan Mantri Awas Yojana PMAY pucca house subsidy housing for all"),
    (r"\b(sukanya\s+samriddhi|ssy|scheme\s+for\s+girl\s+child|saving\s+for\s+daughter|girl\s+child\s+post\s+office\s+account)\b", "Government Welfare Schemes Sukanya Samriddhi Yojana SSY girl child interest rate tax free Section 80C"),
]

COMMON_LEGAL_TYPOS = [
    (r"\bdrunkn\b", "drunken"),
    (r"\bdrivng\b", "driving"),
    (r"\bmorgage\b", "mortgage"),
    (r"\bmorgaged\b", "mortgaged"),
    (r"\bdivorse\b", "divorce"),
    (r"\bdevorce\b", "divorce"),
    (r"\btenent\b", "tenant"),
    (r"\btanent\b", "tenant"),
    (r"\bharasment\b", "harassment"),
    (r"\bharrasment\b", "harassment"),
    (r"\bcommitee\b", "committee"),
    (r"\bcomittee\b", "committee"),
    (r"\bdefectiv\b", "defective"),
    (r"\bseparatly\b", "separately"),
    (r"\bmaintanance\b", "maintenance"),
    (r"\bmaintainance\b", "maintenance"),
    (r"\bcompansation\b", "compensation"),
    (r"\bcompensasion\b", "compensation"),
    (r"\bcomplent\b", "complaint"),
    (r"\binshurance\b", "insurance"),
    (r"\binsurence\b", "insurance"),
    (r"\bpropety\b", "property"),
    (r"\bevictin\b", "eviction"),
    (r"\bagreament\b", "agreement"),
    (r"\breponsibility\b", "responsibility"),
]


VAGUE_QUERY_PATTERNS = [
    (
        r"^(my\s+)?(company|employer|boss|workplace|manager)\s+(is\s+)?(troubling|harassing|causing\s+problems?|bothering)\s*(me)?\.?$",
        "I can help with that. Could you tell me what is happening—for example, unpaid salary, wrongful termination, workplace harassment, or something else?"
    ),
    (
        r"^(my\s+)?(husband|spouse|partner|in-laws|family)\s+(is\s+)?(causing\s+problems?|troubling|harassing|bothering)\s*(me)?\.?$",
        "Could you tell me a little more about what is happening—for example, threats, physical violence, financial control, or another issue?"
    ),
    (
        r"^(someone|somebody)\s+(is\s+)?(troubling|bothering|harassing)\s*(me)?\.?$",
        "I can help explain your legal options. Could you provide a few more details about what happened—for example, online harassment, threats, financial fraud, or something else?"
    ),
]


def detect_vague_query(query: str) -> Optional[str]:
    """Returns a tailored clarification question if query is overly vague."""
    q = query.strip().lower()
    for pattern, clarification in VAGUE_QUERY_PATTERNS:
        if re.match(pattern, q):
            return clarification
    return None


def normalize_query(query: str) -> Tuple[str, str]:
    """
    Normalizes and expands user query deterministically.
    Returns tuple of (original_query, expanded_search_query).
    """
    original = query.strip()
    query_lower = original.lower()

    # Clean common phonetic/spelling typos in Indian legal English
    corrected = original
    for typo_pat, correction in COMMON_LEGAL_TYPOS:
        query_lower = re.sub(typo_pat, correction, query_lower)
        corrected = re.sub(typo_pat, correction, corrected, flags=re.IGNORECASE)

    expansions = []
    for alias, full_name in LEGAL_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', query_lower):
            expansions.append(full_name)

    for pattern, concept in NATURAL_PROBLEM_CONCEPTS:
        if re.search(pattern, query_lower):
            expansions.append(concept)

    base = corrected if corrected.lower() != original.lower() else original
    if expansions:
        expanded_search_query = f"{base} {' '.join(expansions)}"
    else:
        expanded_search_query = base

    return original, expanded_search_query


def extract_mentioned_sections(query: str) -> List[str]:
    """
    Extracts explicit section numbers mentioned in the query text,
    excluding old repealed sections that the user asks what replaces them or
    sections explicitly belonging to old statutes (IPC, CrPC, Indian Evidence Act).
    E.g. 'Section 358', 'sec 358', 's. 358', '358'
    """
    old_statute_patterns = [
        r'\b(?:section|sec\.?|s\.?)\s*(\d+[a-z]?)\s+(?:of\s+(?:the\s+)?)?(?:indian\s+penal\s+code|ipc|code\s+of\s+criminal\s+procedure|crpc|indian\s+evidence\s+act|evidence\s+act)\b',
        r'\b(?:indian\s+penal\s+code|ipc|code\s+of\s+criminal\s+procedure|crpc|indian\s+evidence\s+act|evidence\s+act)\s+(?:section|sec\.?|s\.?)\s*(\d+[a-z]?)\b',
        r'\b(?:instead\s+of|in\s+place\s+of|replaces?|repealing)\s+(?:section|sec\.?|s\.?)?\s*(\d+[a-z]?)\b',
        r'\b(?:section|sec\.?|s\.?)\s*(\d+[a-z]?)\b.*?\b(?:has\s+been\s+replaced|still\s+apply|repealed)\b',
    ]
    excluded_secs = set()
    for pat in old_statute_patterns:
        for m in re.findall(pat, query, re.IGNORECASE):
            excluded_secs.add(m.lower())

    matches = re.findall(r'\b(?:section|sec\.?|s\.?|article|art\.?)\s*(\d+[a-z]?|preamble)\b', query, re.IGNORECASE)
    valid_matches = [m.lower() for m in matches if m.lower() not in excluded_secs]
    if valid_matches:
        return valid_matches

    query_lower = query.lower()
    num_matches = re.findall(r'\b(\d+[a-z]?)\b', query_lower)
    if ("section" in query_lower or "sec" in query_lower or "article" in query_lower or "art" in query_lower) and num_matches:
        return [n.lower() for n in num_matches if n.lower() not in excluded_secs]

    if "preamble" in query_lower:
        return ["preamble"]

    return []


def extract_mentioned_acts(query: str) -> List[str]:
    """Return canonical Act names explicitly named by a query."""
    query_lower = query.lower()
    return [
        act_name
        for act_name, patterns in LEGAL_ACT_PATTERNS.items()
        if any(re.search(pattern, query_lower) for pattern in patterns)
    ]


def lookup_exact_section_candidates(
    collection,
    query_original: str,
    query_expanded: str,
    sections: List[str],
    acts: List[str],
) -> List[Dict[str, Any]]:
    """Fetch chunks by exact section metadata, optionally constrained to named Acts."""
    exact_candidates = []
    seen_ids = set()
    target_acts = acts or [None]

    for section in sections:
        sec_variants = list(dict.fromkeys([section, section.upper(), section.lower(), section.capitalize()]))
        for sec_var in sec_variants:
            for act in target_acts:
                where = {"section_number": {"$eq": sec_var}}
                if act:
                    where = {"$and": [{"act": {"$eq": act}}, where]}

                result = collection.get(
                    where=where,
                    include=["documents", "metadatas"],
                )
            for chunk_id, document, metadata in zip(
                result.get("ids", []),
                result.get("documents", []),
                result.get("metadatas", []),
            ):
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                score_info = calculate_candidate_score(
                    query_original,
                    query_expanded,
                    document,
                    metadata,
                    distance=0.0,
                    target_acts=acts,
                )
                exact_candidates.append({
                    "chunk_id": chunk_id,
                    "document": document,
                    "metadata": metadata,
                    "distance": 0.0,
                    "semantic_similarity": score_info["semantic_similarity"],
                    "metadata_boost": score_info["metadata_boost"],
                    "final_score": score_info["final_score"],
                    "boost_reasons": score_info["boost_reasons"] + ["Exact Act/section metadata lookup"],
                    "is_exact_metadata_match": True,
                })

    return sorted(exact_candidates, key=lambda candidate: candidate["chunk_id"])


# def lookup_act_title_candidates(
#     collection,
#     query_original: str,
#     acts: List[str],
# ) -> List[Dict[str, Any]]:
#     """Add a strong Act-scoped title match when dense retrieval misses its section."""
#     query_terms = set(re.findall(r"\w+", query_original.lower())) - TOPIC_STOP_WORDS
#     if not query_terms:
#         return []

#     best_match = None
#     for act in acts:
#         result = collection.get(
#             where={"act": {"$eq": act}},
#             include=["documents", "metadatas"],
#         )
#         for chunk_id, document, metadata in zip(
#             result.get("ids", []),
#             result.get("documents", []),
#             result.get("metadatas", []),
#         ):
#             title_terms = set(re.findall(r"\w+", str(metadata.get("title", "")).lower()))
#             overlap = len(query_terms.intersection(title_terms))
#             candidate_key = (overlap, -int(metadata.get("chunk_index", 1)), chunk_id)
#             if overlap >= MIN_TITLE_TOPIC_OVERLAP and (
#                 best_match is None or candidate_key > best_match[0]
#             ):
#                 best_match = (candidate_key, chunk_id, document, metadata, overlap)

#     if not best_match:
#         return []

#     _, chunk_id, document, metadata, overlap = best_match
#     return [{
#         "chunk_id": chunk_id,
#         "document": document,
#         "metadata": metadata,
#         "distance": 0.0,
#         "semantic_similarity": 0.0,
#         "metadata_boost": float(overlap),
#         "final_score": float(overlap),
#         "boost_reasons": [f"Act-scoped title topic match ({overlap} terms)"],
#         "is_exact_metadata_match": False,
#         "is_title_metadata_match": True,
#     }]

def lookup_act_title_candidates(
    collection,
    query_original: str,
    acts: List[str],
) -> List[Dict[str, Any]]:
    """Find the best Act-scoped title match using topic overlap."""

    query_terms = set(
        re.findall(r"\w+", query_original.lower())
    ) - TOPIC_STOP_WORDS

    if not query_terms:
        return []

    candidates = []

    for act in acts:
        result = collection.get(
            where={"act": {"$eq": act}},
            include=["documents", "metadatas"],
        )

        for chunk_id, document, metadata in zip(
            result.get("ids", []),
            result.get("documents", []),
            result.get("metadatas", []),
        ):
            title = str(metadata.get("title", "")).lower()
            title_terms = set(re.findall(r"\w+", title))

            overlap = query_terms.intersection(title_terms)

            if len(overlap) < MIN_TITLE_TOPIC_OVERLAP:
                continue

            # Base score from important topic-term overlap.
            score = len(overlap) * 1.0

            # Prefer titles whose wording is directly aligned
            # with the user's query.
            query_clean = " ".join(
                re.findall(r"\w+", query_original.lower())
            )

            title_clean = " ".join(
                re.findall(r"\w+", title)
            )

            query_tokens = query_clean.split()

            # Reward meaningful multi-word phrases appearing
            # directly in the legal title.
            for n in (5, 4, 3, 2):
                for i in range(len(query_tokens) - n + 1):
                    phrase = " ".join(query_tokens[i:i + n])

                    if len(phrase.split()) >= 2 and phrase in title_clean:
                        score += 0.10 * n
                        break

            candidates.append({
                "chunk_id": chunk_id,
                "document": document,
                "metadata": metadata,
                "distance": 0.0,
                "semantic_similarity": 0.0,
                "metadata_boost": score,
                "final_score": score,
                "boost_reasons": [
                    f"Act-scoped title topic match ({len(overlap)} terms)"
                ],
                "is_exact_metadata_match": False,
                "is_title_metadata_match": True,
            })

    if not candidates:
        return []

    candidates.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return candidates[:3]

def normalize_legal_term(word: str) -> str:
    """Normalize word to base singular / non-inflected form for legal title matching."""
    w = word.strip().lower()
    if len(w) <= 3:
        return w
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    if w.endswith("ing") and len(w) > 5:
        return w[:-3]
    if w.endswith("ed") and len(w) > 4:
        return w[:-2]
    return w


def calculate_candidate_score(
    query_original: str,
    query_expanded: str,
    doc_text: str,
    metadata: Dict[str, Any],
    distance: float,
    target_acts: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculates composite score based on semantic distance and metadata/keyword boosting.
    """
    # Cosine similarity calculation: similarity = 1.0 - distance
    sim_score = max(0.0, 1.0 - float(distance))

    meta_boost = 0.0
    boost_reasons = []

    query_orig_lower = query_original.lower()
    query_exp_lower = query_expanded.lower()

    sec_num_str = str(metadata.get("section_number", "")).strip().lower()
    sec_str = str(metadata.get("section", "")).strip().lower()
    title_str = str(metadata.get("title", "")).strip().lower()
    act_str = str(metadata.get("act", "")).strip().lower()
    doc_lower = doc_text.lower()

    # 0. Act Alignment Boost (Prioritize the Act explicitly requested by the user)
    if target_acts:
        for tact in target_acts:
            if tact and tact.lower() in act_str:
                meta_boost += 0.30
                boost_reasons.append(f"Act alignment match ({tact}): +0.30")
                break

    # 1. Explicit Section Number Boost
    mentioned_secs = extract_mentioned_sections(query_original)
    if not mentioned_secs and query_expanded != query_original:
        exp_secs = extract_mentioned_sections(query_expanded)
        if exp_secs:
            mentioned_secs = exp_secs

    if sec_num_str and any(sec_num_str == ms for ms in mentioned_secs):
        meta_boost += 0.35
        boost_reasons.append(f"Section match ({sec_num_str}): +0.35")
    elif sec_str and any(ms in sec_str for ms in mentioned_secs):
        meta_boost += 0.35
        boost_reasons.append(f"Section match ({sec_str}): +0.35")

    # 2. Title Keyword Boost (with stemming / plural normalization)
    stop_words = {
        "what", "is", "the", "a", "an", "for", "of", "to", "in", "and", "or",
        "under", "does", "say", "about", "after", "happen", "happens", "commits",
        "persons", "code", "act", "law", "my", "me", "can", "how", "do", "we", "i", "you"
    }
    query_words = set(re.findall(r'\w+', query_orig_lower)) - stop_words
    title_words = set(re.findall(r'\w+', title_str))

    query_stemmed = {normalize_legal_term(w): w for w in query_words}
    title_stemmed = {normalize_legal_term(w): w for w in title_words}
    common_stems = set(query_stemmed.keys()).intersection(set(title_stemmed.keys()))

    if common_stems:
        matched_words = [query_stemmed[s] for s in common_stems]
        boost_val = min(0.30, 0.15 * len(common_stems))
        meta_boost += boost_val
        boost_reasons.append(f"Title keyword match ({', '.join(matched_words)}): +{boost_val:.2f}")

    # Exact Title Phrase Match Boost (e.g. 'punishment for murder' == 'punishment for murder')
    clean_title = re.sub(r'^\d+\s*[\.\-]?\s*', '', title_str).strip()
    if clean_title:
        if clean_title == query_orig_lower.strip():
            meta_boost += 0.30
            boost_reasons.append(f"Exact title equality match ('{clean_title}'): +0.30")
        elif clean_title in query_orig_lower or query_orig_lower in clean_title:
            meta_boost += 0.15
            boost_reasons.append(f"Exact title substring match ('{clean_title}'): +0.15")

    # 3. Act / Alias Match Boost
    if "ipc" in query_orig_lower or "indian penal code" in query_orig_lower:
        if "repeal" in title_str or "repeal" in doc_lower or "savings" in title_str or "indian penal code" in doc_lower:
            meta_boost += 0.20
            boost_reasons.append("IPC alias match in text/title: +0.20")

    # 4. Content Keyword Boost
    common_content_words = query_words.intersection(set(re.findall(r'\w+', doc_lower)))
    if common_content_words and not common_stems:
        boost_val = min(0.10, 0.03 * len(common_content_words))
        meta_boost += boost_val
        boost_reasons.append(f"Content keyword match ({', '.join(list(common_content_words)[:3])}): +{boost_val:.2f}")

    # 5. Definitions Section Deprioritization for Actionable Queries
    is_definition_chunk = (sec_num_str in ("2", "3") or sec_str in ("section 2", "section 3")) and "definition" in title_str
    action_terms = {"committee", "complaint", "file", "procedure", "penalty", "compensation", "seller", "evict", "order", "harassment", "divorce", "notice"}
    if is_definition_chunk and bool(query_words.intersection(action_terms)):
        meta_boost = max(0.0, meta_boost - 0.20)
        boost_reasons.append("Definitions section deprioritized for actionable query: -0.20")

    final_score = sim_score + meta_boost

    return {
        "semantic_similarity": sim_score,
        "metadata_boost": meta_boost,
        "final_score": final_score,
        "boost_reasons": boost_reasons
    }


def rerank_and_deduplicate(
    candidates: List[Dict[str, Any]],
    top_k: int = DEFAULT_FINAL_TOP_K,
    max_per_section: int = MAX_CHUNKS_PER_SECTION
) -> List[Dict[str, Any]]:
    """
    Reranks candidates by final score and applies section-level diversity rules.
    """
    sorted_candidates = sorted(
        candidates,
        key=lambda x: (
            not x.get("is_exact_metadata_match", False),
            not x.get("is_title_metadata_match", False),
            -x["final_score"],
        ),
    )

    selected = []
    section_counts = {}
    unselected_fallback = []

    for cand in sorted_candidates:
        act = str(cand["metadata"].get("act", "unknown"))
        sec = str(cand["metadata"].get("section_number", cand["metadata"].get("section", "unknown")))
        section_key = (act, sec)
        curr_count = section_counts.get(section_key, 0)
        if curr_count < max_per_section:
            selected.append(cand)
            section_counts[section_key] = curr_count + 1
        else:
            unselected_fallback.append(cand)

        if len(selected) == top_k:
            break

    if len(selected) < top_k:
        needed = top_k - len(selected)
        selected.extend(unselected_fallback[:needed])

    return selected


def retrieve_legal_chunks(
    query_text: str,
    embedding_model,
    collection,
    candidate_pool_size: int = DEFAULT_CANDIDATE_POOL_SIZE,
    final_top_k: int = DEFAULT_FINAL_TOP_K,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    max_per_section: int = MAX_CHUNKS_PER_SECTION
) -> Dict[str, Any]:
    """
    Full legal retrieval pipeline:
    1. Query normalization & legal alias expansion
    2. Candidate retrieval from ChromaDB (top candidate_pool_size)
    3. Metadata-aware score calculation & boosting
    4. Section deduplication / diversity selection (top final_top_k)
    5. Confidence threshold check
    """
    t_retrieval_start = time.perf_counter()
    orig_query, search_query = normalize_query(query_text)
    mentioned_sections = extract_mentioned_sections(orig_query)
    if not mentioned_sections and search_query != orig_query:
        mentioned_sections = extract_mentioned_sections(search_query)

    mentioned_acts = extract_mentioned_acts(orig_query)
    if not mentioned_acts and search_query != orig_query:
        mentioned_acts = extract_mentioned_acts(search_query)

    t_emb_start = time.perf_counter()
    query_embedding = embedding_model.encode(
        [search_query],
        normalize_embeddings=True
    ).tolist()
    t_emb_end = time.perf_counter()

    t_chroma_start = time.perf_counter()
    raw_res = collection.query(
        query_embeddings=query_embedding,
        n_results=candidate_pool_size,
        include=["documents", "metadatas", "distances"]
    )
    t_chroma_end = time.perf_counter()

    doc_list = raw_res["documents"][0] if raw_res.get("documents") else []
    meta_list = raw_res["metadatas"][0] if raw_res.get("metadatas") else []
    dist_list = raw_res["distances"][0] if raw_res.get("distances") else []
    id_list = raw_res["ids"][0] if raw_res.get("ids") else []

    semantic_candidates = []
    for cid, doc, meta, dist in zip(id_list, doc_list, meta_list, dist_list):
        score_info = calculate_candidate_score(
            orig_query,
            search_query,
            doc,
            meta,
            dist,
            target_acts=mentioned_acts,
        )
        semantic_candidates.append({
            "chunk_id": cid,
            "document": doc,
            "metadata": meta,
            "distance": dist,
            "semantic_similarity": score_info["semantic_similarity"],
            "metadata_boost": score_info["metadata_boost"],
            "final_score": score_info["final_score"],
            "boost_reasons": score_info["boost_reasons"],
            "is_exact_metadata_match": False,
            "is_title_metadata_match": False,
        })

    t_exact_start = time.perf_counter()
    exact_candidates = lookup_exact_section_candidates(
        collection,
        orig_query,
        search_query,
        mentioned_sections,
        mentioned_acts,
    ) if mentioned_sections else []
    t_exact_end = time.perf_counter()

    t_title_start = time.perf_counter()
    title_candidates = lookup_act_title_candidates(
        collection,
        orig_query,
        mentioned_acts,
    ) if (mentioned_acts and not exact_candidates) else []
    t_title_end = time.perf_counter()

    prioritized_ids = {
        candidate["chunk_id"] for candidate in exact_candidates + title_candidates
    }
    candidates = exact_candidates + title_candidates + [
        candidate for candidate in semantic_candidates
        if candidate["chunk_id"] not in prioritized_ids
    ]

    sorted_all_candidates = sorted(
        candidates,
        key=lambda x: (
            not x.get("is_exact_metadata_match", False),
            not x.get("is_title_metadata_match", False),
            -x["final_score"],
        ),
    )
    t_rerank_start = time.perf_counter()
    reranked_top_k = rerank_and_deduplicate(candidates, top_k=final_top_k, max_per_section=max_per_section)
    t_rerank_end = time.perf_counter()

    top_score = sorted_all_candidates[0]["final_score"] if sorted_all_candidates else 0.0
    is_confident = top_score >= confidence_threshold

    # Gating for explicit foreign jurisdictions with no Indian statutory relevance
    foreign_oos_pats = [
        r"\b(uspto|united\s+states|u\.s\.a?|european\s+union|eu\s+regulation|singapore|uk\s+court|english\s+law|german\s+law|foreign\s+jurisdiction)\b",
    ]
    is_foreign_oos = any(re.search(pat, orig_query.lower()) for pat in foreign_oos_pats)
    has_indian_act = bool(mentioned_acts) or any(
        re.search(r'\b' + re.escape(alias) + r'\b', orig_query.lower())
        for alias in LEGAL_ALIASES
    )
    if is_foreign_oos and not has_indian_act:
        is_confident = False
    t_retrieval_end = time.perf_counter()

    timing = {
        "query_embedding_time_ms": round((t_emb_end - t_emb_start) * 1000, 2),
        "chromadb_search_time_ms": round((t_chroma_end - t_chroma_start) * 1000, 2),
        "exact_metadata_lookup_time_ms": round((t_exact_end - t_exact_start) * 1000, 2),
        "act_title_lookup_time_ms": round((t_title_end - t_title_start) * 1000, 2),
        "reranking_time_ms": round((t_rerank_end - t_rerank_start) * 1000, 2),
        "total_retrieval_time_ms": round((t_retrieval_end - t_retrieval_start) * 1000, 2),
    }

    return {
        "original_query": orig_query,
        "search_query": search_query,
        "candidates_retrieved": sorted_all_candidates,
        "reranked_results": reranked_top_k,
        "top_score": top_score,
        "is_confident": is_confident,
        "confidence_threshold": confidence_threshold,
        "timing": timing,
    }
