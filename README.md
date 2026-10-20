---
title: LegalConnect
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---

# LegalConnect — AI-Powered Indian Legal Awareness System

LegalConnect is an AI-powered, citizen-focused Indian legal awareness and RAG (Retrieval-Augmented Generation) system. It pairs dense vector retrieval over ChromaDB with localized Ollama inference (`qwen3:4b`), providing grounded legal explanations, statutory citations, constitutional article lookups, and government welfare scheme information.

---

## 1. System Architecture & Knowledge Base

### 1.1 Complete Legal Knowledge Base (3,209 Chunks)
LegalConnect indexes **16 distinct legal sources** spanning statutory enactments, constitutional law, and national welfare schemes:

1. **The Constitution of India** (Preamble + Articles 1 to 395, up to 106th Amendment Act, 2023) — *578 chunks*
2. **Bharatiya Nyaya Sanhita, 2023 (BNS)** — *430 chunks*
3. **Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)** — *679 chunks*
4. **Bharatiya Sakshya Adhiniyam, 2023 (BSA)** — *192 chunks*
5. **Consumer Protection Act, 2019 (CPA)** — *134 chunks*
6. **Information Technology Act, 2000 (IT Act)** — *131 chunks*
7. **Protection of Women from Domestic Violence Act, 2005 (PWDVA)** — *46 chunks*
8. **Sexual Harassment of Women at Workplace Act, 2013 (POSH)** — *43 chunks*
9. **Code on Social Security, 2020** — *248 chunks*
10. **Hindu Marriage Act, 1955** — *39 chunks*
11. **Motor Vehicles Act, 1988 (MVA)** — *321 chunks*
12. **Transfer of Property Act, 1882 (TPA)** — *177 chunks*
13. **Right to Information Act, 2005 (RTI)** — *47 chunks*
14. **Legal Services Authorities Act, 1987 (LSA)** — *43 chunks*
15. **Environment (Protection) Act, 1986 (EPA)** — *33 chunks*
16. **National Government Welfare Schemes (myScheme)** — *7 chunks*
    - *Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)*
    - *Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB-PMJAY)*
    - *Pradhan Mantri Awas Yojana (PMAY - Urban & Gramin)*
    - *Sukanya Samriddhi Account / Sukanya Samriddhi Yojana (SSY)*

### 1.2 RAG Engine Specifications
- **Vector Database**: Local Persistent ChromaDB (`vectorstore/chroma`, collection: `legal_bns_2023`)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, cosine distance)
- **Local LLM**: Local Ollama running `qwen3:4b` (262k context length, GGUF Q4_K_M)
- **Retrieval Pipeline**: Hybrid metadata boosting (explicit Act/Section/Article matching), typo correction, semantic re-ranking, and diversity de-duplication.
- **Citation Guardrails**: Runtime citation whitelist filtering and streaming token-boundary verification to prevent legal hallucination.

---

## 2. Directory Structure

```
LegalConnect/
├── backend/
│   └── main.py                        # FastAPI application with CORS & health checks
├── frontend/
│   ├── app.py                         # Streamlit UI application
│   ├── api_client.py                  # Environment-aware backend API client
│   ├── chrome.py                      # UI sidebar & navigation components
│   ├── views.py                       # Chat and citation render views
│   └── styles.css                     # Premium styling
├── data/
│   ├── raw/                           # Official source PDF & raw extracted JSON
│   ├── processed/                     # Cleaned JSON datasets & quality reports
│   ├── processed_chunks/              # Validated chunks & chunking reports
│   └── metadata/
│       └── sources.json               # Canonical source registry & tracking
├── reports/                           # Automated RAG evaluation & audit reports
├── scripts/
│   ├── extract_data.py                # Source extraction pipeline
│   ├── clean_data.py                  # Universal legal text cleaning engine
│   ├── chunk_data.py                  # Legal-aware structural chunking engine
│   ├── validate_chunks.py             # 100% Content Reconstruction validator
│   ├── create_embeddings.py           # Incremental ChromaDB embedding engine
│   ├── retrieval_utils.py             # Query normalization, boosting & reranking
│   ├── legal_chat.py                  # Prompt engineering & LLM streaming
│   ├── evaluate_rag.py                # RAG evaluation engine (Hit@k, MRR)
│   └── evaluation/
│       ├── legal_test_cases.json      # 60 verified statutory benchmark cases
│       ├── legal_test_cases_extended.json # 70 verified benchmark cases
│       ├── test_citations.py          # Citation unit tests
│       └── test_regression.py         # Failure regression & robustness test suite
├── Dockerfile                         # Production multi-stage Docker container
├── docker-compose.yml                 # Multi-service composition (Backend + Frontend)
├── .env.example                       # Environment template
├── requirements.txt                   # Production Python dependencies
└── README.md
```

---

## 3. Quick Start & Execution

### 3.1 Local Environment Setup
```bash
# 1. Clone repository and navigate to directory
cd LegalConnect

# 2. Activate Python 3.10 virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment configuration
cp .env.example .env
```

### 3.2 Starting Local Services
```bash
# Terminal 1: Ensure Ollama is running with qwen3:4b
ollama serve
ollama pull qwen3:4b

# Terminal 2: Start FastAPI Backend
uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 3: Start Streamlit Frontend
streamlit run frontend/app.py --server.port 8501
```

Access the web interface at: `http://localhost:8501`
Access the backend OpenAPI docs at: `http://localhost:8000/docs`
Backend health status: `http://localhost:8000/health`

---

## 4. Docker Deployment

LegalConnect provides full Docker support with volume persistence:

```bash
# Build and run backend and frontend services
docker-compose up --build
```

> **Note on Ollama in Docker:**
> When running the backend container, it connects to host Ollama via `http://host.docker.internal:11434` (pre-configured in `docker-compose.yml`). Ensure Ollama on the host allows requests or run `OLLAMA_HOST=0.0.0.0:11434 ollama serve`.

---

## 5. RAG Evaluation & Regression Benchmark

### 5.1 Verification Commands
All test suites can be executed with `.venv/bin/python`:

```bash
# 1. Run Baseline Retrieval Evaluation (60 Test Cases)
python3 scripts/evaluate_rag.py --retrieval-only

# 2. Run Extended Cross-Domain Evaluation (70 Test Cases: Acts + Constitution + Schemes)
python3 scripts/evaluate_rag.py \
    --dataset scripts/evaluation/legal_test_cases_extended.json \
    --report reports/rag_evaluation_extended_70.json \
    --retrieval-only

# 3. Run Citation Grounding & Filter Safety Tests
python3 -m unittest scripts/evaluation/test_citations.py

# 4. Run System Regression & Vectorstore Integrity Tests
python3 scripts/evaluation/test_regression.py
```

### 5.2 Latest Verified Benchmark Metrics

| Metric | Baseline Suite (60 Cases) | Extended Suite (70 Cases) | Status |
| :--- | :--- | :--- | :--- |
| **Total Test Cases** | 60 | 70 | Verified |
| **Overall Pass Rate** | **100.0%** | **100.0%** | Passed |
| **Hit@1** | **100.0%** | **100.0%** | Top-rank accuracy |
| **Hit@3** | **100.0%** | **100.0%** | Top-3 recall |
| **Hit@5** | **100.0%** | **100.0%** | Top-5 recall |
| **MRR (Mean Reciprocal Rank)** | **1.0000** | **1.0000** | Perfect reciprocal rank |
| **Expected Act Accuracy** | **100.0%** | **100.0%** | Zero cross-statute confusion |
| **Expected Section Accuracy** | **95.0%** | **95.71%** | Ground truth match* |
| **Citation Unit Tests** | **8/8 Passed** | **8/8 Passed** | Zero hallucinations |
| **Regression Tests** | **10/10 Passed** | **10/10 Passed** | Zero regressions |

*\* Note: The remaining ~4.3% in Expected Section Accuracy represents intentional non-statutory / `insufficient_context` test cases where `expected_sections = []`.*

---

## 6. Security & Safe Legal AI Principles

1. **Non-Destructive Ingestion Safeguards**: Incremental upserts and strict ID validation protect existing vectors from loss or unnecessary re-embedding.
2. **Statutory Citations Whitelist**: The assistant is strictly constrained to cite only sections and articles present in retrieved chunks. Any unsupported section numbers are automatically qualified before user presentation.
3. **Legal Disclaimer**: LegalConnect is designed solely for public legal awareness and information retrieval. It does not provide formal legal advice and is not a substitute for a licensed advocate or judicial authority.
