import os
import sys
import argparse
from pathlib import Path
import requests
import chromadb
from sentence_transformers import SentenceTransformer

# Set offline environment variables
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieval_utils import (
    retrieve_legal_chunks,
    DEFAULT_CANDIDATE_POOL_SIZE,
    DEFAULT_FINAL_TOP_K,
    DEFAULT_CONFIDENCE_THRESHOLD
)

# =========================
# Configuration
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_PATH = PROJECT_ROOT / "vectorstore" / "chroma"
COLLECTION_NAME = "legal_bns_2023"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
LLM_MODEL = "qwen3:4b"


# =========================
# Load resources
# =========================

def load_resources():
    print("Loading embedding model...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_collection(name=COLLECTION_NAME)
    return embedding_model, collection


# =========================
# Build RAG prompt
# =========================

def build_prompt(question, documents, metadatas):
    context_parts = []

    for i, (document, metadata) in enumerate(zip(documents, metadatas), start=1):
        source = metadata.get("source", "Unknown")
        section = metadata.get("section", metadata.get("section_number", "Unknown"))
        title = metadata.get("title", "Unknown")
        act = metadata.get("act", "Unknown")

        context_parts.append(
            f"""
LEGAL SOURCE {i}

Act:
{act}

Section:
{section}

Title:
{title}

Source:
{source}

Legal Text:
{document}
"""
        )

    context = "\n".join(context_parts)

    prompt = f"""
You are a legal awareness assistant for India.

Answer the user's question ONLY using the legal sources
provided below.

IMPORTANT RULES:

1. Do not use outside knowledge.
2. Do not invent legal sections, punishments, procedures,
   dates, or facts.
3. Do not make assumptions when the sources do not provide
   enough information.
4. If the provided sources are insufficient, clearly say:
   "I could not find sufficient information in the retrieved
   legal sources to answer this question."
5. Preserve the meaning of the legal text.
6. Explain the information in simple language.
7. Mention the relevant Act and section when available.
8. This is legal awareness information, not a substitute
   for advice from a qualified legal professional.

USER QUESTION:

{question}

RETRIEVED LEGAL SOURCES:

{context}

Now answer the user's question using ONLY the retrieved
legal sources.
"""
    return prompt


# =========================
# Ask Qwen3 through Ollama
# =========================

def generate_answer(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    response.raise_for_status()
    data = response.json()
    return data["response"]


# =========================
# Display sources
# =========================

def display_sources(metadatas, distances):
    print("\n")
    print("=" * 70)
    print("SOURCES USED")
    print("=" * 70)

    for i, metadata in enumerate(metadatas, start=1):
        print(f"\nSource {i}")
        print(f"Act: {metadata.get('act', 'N/A')}")
        print(f"Section: {metadata.get('section', metadata.get('section_number', 'N/A'))}")
        print(f"Title: {metadata.get('title', 'N/A')}")
        print(f"Source: {metadata.get('source', 'N/A')}")
        print(f"Source URL: {metadata.get('source_url', 'N/A')}")
        if i <= len(distances):
            print(f"Distance: {distances[i - 1]}")


# =========================
# Main question handler
# =========================

def ask_question(question, embedding_model, collection):
    print("\nSearching legal sources...")

    retrieval_info = retrieve_legal_chunks(
        query_text=question,
        embedding_model=embedding_model,
        collection=collection,
        candidate_pool_size=DEFAULT_CANDIDATE_POOL_SIZE,
        final_top_k=DEFAULT_FINAL_TOP_K,
        confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD
    )

    if not retrieval_info["is_confident"] or not retrieval_info["reranked_results"]:
        print("\nI could not find sufficient information in the retrieved legal sources to answer this question.")
        return

    documents = [r["document"] for r in retrieval_info["reranked_results"]]
    metadatas = [r["metadata"] for r in retrieval_info["reranked_results"]]
    distances = [r["distance"] for r in retrieval_info["reranked_results"]]

    print("Generating answer using retrieved legal sources...")

    prompt = build_prompt(question, documents, metadatas)
    answer = generate_answer(prompt)

    print("\n")
    print("=" * 70)
    print("LEGALCONNECT ANSWER")
    print("=" * 70)

    print(answer)

    display_sources(metadatas, distances)

    print("\n")
    print("=" * 70)


# =========================
# Interactive mode
# =========================

def interactive_mode(embedding_model, collection):
    print("\n")
    print("=" * 70)
    print("LEGALCONNECT — LEGAL AWARENESS CHATBOT")
    print("=" * 70)

    print("\nDataset: Bharatiya Nyaya Sanhita, 2023")
    print("\nAsk a legal question.")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        try:
            question = input("\nLegalConnect > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if question.lower() in {"exit", "quit"}:
            print("Exiting.")
            break

        if not question:
            continue

        try:
            ask_question(question, embedding_model, collection)
        except Exception as e:
            print(f"\nError: {e}")


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, help="Ask one legal question.")
    args = parser.parse_args()

    try:
        embedding_model, collection = load_resources()
        if args.query:
            ask_question(args.query, embedding_model, collection)
        else:
            interactive_mode(embedding_model, collection)
    except Exception as e:
        print(f"\nStartup error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
