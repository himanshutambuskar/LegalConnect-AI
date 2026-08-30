# Indian Legal Awareness Chatbot - Data Pipeline

A modular, reusable, and category-agnostic legal data extraction, cleaning, and chunking pipeline for official Indian legal content across 13 categories.

---

## 1. Pipeline Overview
The data preparation framework consists of three sequential stages:
1. **Stage 1 — Legal Data Extraction**: Downloads official `.pdf`/`.html` files from government portals (`.gov.in` / `.nic.in`) and extracts section-level JSON records.
2. **Stage 2 — Universal Legal Data Cleaning**: Normalizes whitespace, removes extraction artifacts, flags data quality anomalies, and saves clean JSON records and quality reports into `data/processed/`.
3. **Stage 3 — Legal-Aware Chunking & Data Preparation**: Splits cleaned legal documents into retrieval-ready chunks while strictly prioritizing legal boundaries over arbitrary character counts.

> [!IMPORTANT]
> Legal text is **never invented, summarized, paraphrased, or modified**. Exact legal wording, punctuation, and structure are strictly preserved throughout all stages.

---

## 2. Stage 3 — Legal-Aware Chunking & Data Preparation

### Why Legal Documents Are Not Blindly Split
Standard fixed-character chunking (e.g. 500 or 1000 characters) frequently cuts off legal definitions, penal clauses, or exception conditions mid-sentence. In legal retrieval systems, preserving the **entire legal section or subsection** as a cohesive semantic unit is paramount to maintaining legal meaning and providing accurate citations.

### Chunking Principles
- **Legal Structure Priority**: Splitting respects legal hierarchy: `Act` $\rightarrow$ `Chapter` $\rightarrow$ `Section` $\rightarrow$ `Subsection` $\rightarrow$ `Clause`.
- **Intact Sections**: Sections within guideline limits (`TARGET_CHUNK_SIZE = 1200`, `MAX_CHUNK_SIZE = 1800`) are preserved as single intact chunks.
- **Subsection-Aware Splitting**: Extremely long sections (e.g. Section 2 definitions) are split at subsection (`(1)`, `(2)`), sub-clause (`(a)`, `(b)`), or paragraph boundaries.
- **Metadata Preservation**: Every chunk retains full context (`act`, `category`, `subcategory`, `chapter`, `section`, `section_number`, `title`, `subsection`, `source`, `source_url`, `document_type`, `page`).
- **Parent-Child Traceability**: Every chunk contains `parent_record_id` pointing directly to its parent record in `data/processed/`, allowing 100% trace-back from vector chunks to raw source documents.
- **Content Reconstruction Validation**: The pipeline includes an automated test (`validate_chunks.py`) that reconstructs 100% of original cleaned text from generated chunks to guarantee zero loss of text.

---

## 3. Directory Layout & Storage

```
legal-awareness-chatbot/
│
├── data/
│   ├── raw/                           <-- SOURCE OF TRUTH (READ-ONLY)
│   │   └── criminal/
│   │       └── bns/
│   │           ├── bns_2023.pdf
│   │           └── bns_sections.json
│   │
│   ├── processed/                     <-- CLEANED DATA & REPORTS
│   │   └── criminal/
│   │       └── bns/
│   │           ├── bns_cleaned.json
│   │           └── bns_cleaning_report.json
│   │
│   ├── processed_chunks/              <-- RETRIEVAL-READY CHUNKS & REPORTS
│   │   └── criminal/
│   │       └── bns/
│   │           ├── bns_chunks.json
│   │           └── bns_chunking_report.json
│   │
│   └── metadata/
│       └── sources.json
│
├── scripts/
│   ├── extract_data.py
│   ├── clean_data.py
│   ├── chunk_data.py
│   ├── validate_data.py
│   └── validate_chunks.py
│
├── requirements.txt
└── README.md
```

---

## 4. Chunk JSON Schema

```json
{
    "chunk_id": "BNS-2023-SECTION-103-CHUNK-1",
    "act": "Bharatiya Nyaya Sanhita, 2023",
    "category": "Criminal Laws",
    "subcategory": "Criminal Law",
    "chapter": "",
    "section": "Section 103",
    "section_number": "103",
    "title": "Punishment for murder",
    "subsection": "(1)",
    "content": "103. (1) Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine. ...",
    "source": "India Code / BPRD",
    "source_url": "https://bprd.nic.in/uploads/pdf/1706692028_eeccb6a2701f4c13ac9b.pdf",
    "document_type": "Act",
    "page": 33,
    "language": "English",
    "parent_record_id": "BNS-2023-SECTION-103",
    "chunk_index": 1,
    "total_chunks_for_section": 1
}
```

---

## 5. Pipeline Commands

### Stage 1: Extraction
```bash
python3 scripts/extract_data.py --act bns
```

### Stage 2: Universal Cleaning
```bash
# Single File
python3 scripts/clean_data.py \
    --input data/raw/criminal/bns/bns_sections.json \
    --output data/processed/criminal/bns/bns_cleaned.json

# Batch Directory
python3 scripts/clean_data.py --input-dir data/raw/ --output-dir data/processed/
```

### Stage 3: Legal-Aware Chunking
```bash
# Single File
python3 scripts/chunk_data.py \
    --input data/processed/criminal/bns/bns_cleaned.json \
    --output data/processed_chunks/criminal/bns/bns_chunks.json

# Batch Directory
python3 scripts/chunk_data.py --input-dir data/processed/ --output-dir data/processed_chunks/
```

### Chunk Validation & Content Reconstruction Test
```bash
python3 scripts/validate_chunks.py \
    --file data/processed_chunks/criminal/bns/bns_chunks.json \
    --source-file data/processed/criminal/bns/bns_cleaned.json
```

---

## 6. Current Implementation Disclaimer

> [!NOTE]
> Embeddings, ChromaDB, vector database, retrieval, semantic search, FastAPI, LLM integration, chatbot UI, and deployment have **NOT** yet been implemented.
