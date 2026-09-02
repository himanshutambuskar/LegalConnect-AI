# LegalConnect Setup Guide

## Prerequisites

- Python 3.10+
- Git
- Ollama
- Required Python dependencies

## Start the Backend

From the LegalConnect project root:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
