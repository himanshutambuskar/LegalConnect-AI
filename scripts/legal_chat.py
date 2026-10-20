import os
import sys
import re
import json
import time
import argparse
from pathlib import Path
import requests
import chromadb
from sentence_transformers import SentenceTransformer

# Configure offline mode only when explicitly requested in environment
if os.environ.get("HF_HUB_OFFLINE") in ("1", "true", "yes"):
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
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from frontend.citation_utils import (
        extract_allowed_section_numbers,
        sanitize_unsupported_citations,
        create_citation_stream_filter,
    )
except ImportError:
    from citation_utils import (
        extract_allowed_section_numbers,
        sanitize_unsupported_citations,
        create_citation_stream_filter,
    )

CHROMA_PATH = Path(os.environ.get("CHROMA_PERSIST_DIR", str(PROJECT_ROOT / "vectorstore" / "chroma")))
COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "legal_bns_2023")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3:4b")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama").lower().strip()
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "").strip()


def get_llm_config() -> dict:
    """
    Retrieve and validate LLM provider configuration from environment variables.
    Supported providers: 'ollama' (default), 'openai_compatible'.
    """
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower().strip()
    if provider not in ("ollama", "openai_compatible"):
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{provider}'. Supported providers are: 'ollama', 'openai_compatible'."
        )

    if provider == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.environ.get("LLM_MODEL", "qwen3:4b").strip()
        if not model:
            raise ValueError("LLM_MODEL environment variable must not be empty.")
        return {
            "provider": "ollama",
            "base_url": base_url,
            "api_key": "",
            "model": model,
        }

    # provider == "openai_compatible"
    base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    if not base_url:
        raise ValueError("LLM_BASE_URL environment variable is required when LLM_PROVIDER=openai_compatible.")

    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable is required when LLM_PROVIDER=openai_compatible.")

    model = os.environ.get("LLM_MODEL", "").strip()
    if not model:
        raise ValueError("LLM_MODEL environment variable is required when LLM_PROVIDER=openai_compatible.")

    return {
        "provider": "openai_compatible",
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    }


# =========================
# Resource Initialization & Vectorstore Readiness
# =========================

_CACHED_RESOURCES = None


def load_embedding_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    """
    Load SentenceTransformer embedding model.
    Tries offline loading from cache first to avoid unnecessary network calls.
    Falls back to downloading once if cache is missing and offline mode is not enforced.
    """
    offline_env = os.environ.get("HF_HUB_OFFLINE", "").strip().lower()
    explicit_offline = offline_env in ("1", "true", "yes")

    # 1. Attempt offline load from local cache first
    try:
        return SentenceTransformer(model_name, device="cpu", local_files_only=True)
    except Exception as e:
        if explicit_offline:
            raise FileNotFoundError(
                f"Embedding model '{model_name}' not found in local cache and HF_HUB_OFFLINE=1 is set. "
                "To allow initial download in a fresh cloud environment, set HF_HUB_OFFLINE=0."
            ) from e

        # 2. In fresh cloud environment with no cache, download once into local cache
        print(f"Embedding model '{model_name}' not found in local cache. Downloading once for cloud deployment...")
        return SentenceTransformer(model_name, device="cpu", local_files_only=False)


def ensure_vectorstore_ready(chroma_path: Path, collection_name: str = COLLECTION_NAME) -> Path:
    """
    Verify ChromaDB persistent index directory and collection exist before connecting.
    If an index archive is provided (CHROMA_ARCHIVE_PATH or CHROMA_ARCHIVE_URL),
    safely unpacks it into chroma_path without modifying any other data.
    Fails safely if index is missing; NEVER resets or re-indexes.
    """
    sqlite_file = chroma_path / "chroma.sqlite3"
    if sqlite_file.is_file() and sqlite_file.stat().st_size > 0:
        return chroma_path

    # Check for local archive in CHROMA_ARCHIVE_PATH or directory-relative location
    archive_env = os.environ.get("CHROMA_ARCHIVE_PATH")
    archive_candidates = []
    if archive_env:
        archive_candidates.append(Path(archive_env))
    archive_candidates.extend([
        chroma_path.parent / "chroma.tar.gz",
        chroma_path.parent / f"{chroma_path.name}.tar.gz",
    ])

    for archive in archive_candidates:
        if archive.is_file():
            print(f"Unpacking pre-packaged ChromaDB index from {archive} to {chroma_path.parent}...")
            import tarfile
            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(path=chroma_path.parent)
            if sqlite_file.is_file():
                return chroma_path

    # Check for remote archive URL
    archive_url = os.environ.get("CHROMA_ARCHIVE_URL", "").strip()
    if archive_url:
        print(f"Downloading pre-packaged ChromaDB index from {archive_url}...")
        import urllib.request
        import tarfile
        temp_tar = chroma_path.parent / "temp_chroma_download.tar.gz"
        chroma_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            urllib.request.urlretrieve(archive_url, temp_tar)
            with tarfile.open(temp_tar, "r:gz") as tar:
                tar.extractall(path=chroma_path.parent)
            if temp_tar.is_file():
                temp_tar.unlink()
            if sqlite_file.is_file():
                return chroma_path
        except Exception as e:
            if temp_tar.is_file():
                temp_tar.unlink()
            raise RuntimeError(f"Failed to download ChromaDB index archive from {archive_url}: {e}") from e

    raise FileNotFoundError(
        f"ChromaDB index not found at '{chroma_path}' (missing 'chroma.sqlite3'). "
        f"Cannot open collection '{collection_name}'. "
        "To deploy LegalConnect in the cloud, ensure the existing 3,209-vector index is provided "
        "at CHROMA_PERSIST_DIR or specify a deployment artifact via CHROMA_ARCHIVE_PATH / CHROMA_ARCHIVE_URL. "
        "Automatic database reset or re-indexing is disabled to protect data integrity."
    )


def load_resources(force_reload: bool = False):
    """
    Load embedding model and connect to ChromaDB collection.
    Reuses cached resources to prevent loading models multiple times into memory.
    """
    global _CACHED_RESOURCES
    if _CACHED_RESOURCES is not None and not force_reload:
        return _CACHED_RESOURCES

    t0 = time.perf_counter()
    print("Loading embedding model...")
    t_emb0 = time.perf_counter()
    embedding_model = load_embedding_model(EMBEDDING_MODEL)
    t_emb1 = time.perf_counter()

    print("Connecting to ChromaDB...")
    t_chroma0 = time.perf_counter()
    persist_dir = ensure_vectorstore_ready(CHROMA_PATH, COLLECTION_NAME)
    client = chromadb.PersistentClient(path=str(persist_dir))
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        raise RuntimeError(
            f"ChromaDB collection '{COLLECTION_NAME}' could not be opened in '{persist_dir}'. "
            "Automatic re-indexing is disabled to protect existing vector data."
        ) from e
    t_chroma1 = time.perf_counter()

    init_timing = {
        "embedding_init_time_ms": round((t_emb1 - t_emb0) * 1000, 2),
        "chroma_init_time_ms": round((t_chroma1 - t_chroma0) * 1000, 2),
        "total_init_time_ms": round((t_chroma1 - t0) * 1000, 2),
    }
    setattr(embedding_model, "_init_timing", init_timing)
    setattr(embedding_model, "_instance_id", id(embedding_model))
    setattr(collection, "_instance_id", id(collection))
    _CACHED_RESOURCES = (embedding_model, collection)
    return embedding_model, collection


# =========================
# Build RAG prompt
# =========================




def build_prompt(question, documents, metadatas, history=None):
    context_parts = []
    allowed_list = []
    seen_allowed = set()

    for i, (document, metadata) in enumerate(zip(documents, metadatas), start=1):
        source = metadata.get("source", "Unknown")
        section = metadata.get("section", metadata.get("section_number", "Unknown"))
        title = metadata.get("title", "Unknown")
        act = metadata.get("act", "Unknown")

        context_parts.append(
            f"""
LEGAL SOURCE {i}
Act: {act}
Section: {section}
Title: {title}
Source: {source}
Legal Text:
{document}
"""
        )

        key = (act, section)
        if key not in seen_allowed:
            seen_allowed.add(key)
            doc_type = metadata.get("document_type", "")
            if doc_type == "Government Scheme" or act == "Government Welfare Schemes":
                sec_str = f"Scheme: {section}"
            elif str(section).lower().startswith("article") or str(section).lower().startswith("preamble"):
                sec_str = str(section)
            elif not str(section).lower().startswith("section"):
                sec_str = f"Section {section}"
            else:
                sec_str = str(section)
            t_str = f" ({title})" if title and title != section else ""
            allowed_list.append(f"- {act}: {sec_str}{t_str}")

    context = "\n".join(context_parts)
    allowed_citations_text = "\n".join(allowed_list) if allowed_list else "None specified."

    history_text = ""
    if history:
        # Keep a compact recent-history window (last 6 turns) to support multi-turn threads
        recent_history = history[-6:]
        formatted_turns = []
        for turn in recent_history:
            role = "User" if turn.get("role") == "user" else "Assistant"
            content = turn.get("content", "").strip()
            if content:
                # Keep assistant turns concise to conserve context tokens
                if role == "Assistant" and len(content) > 350:
                    content = content[:350].rsplit(" ", 1)[0] + "..."
                formatted_turns.append(f"{role}: {content}")
        if formatted_turns:
            history_text = "\nPREVIOUS CONVERSATION CONTEXT:\n" + "\n".join(formatted_turns) + "\n"

    prompt = f"""You are LegalConnect, an objective, conversational, and legally grounded legal awareness assistant for India.
Your goal is to explain citizens' legal rights, statutory provisions, and practical next steps when they describe real-life situations in natural language.

Answer the user's question ONLY using the retrieved official Indian legal sources provided below.

{history_text}
ALLOWED CITATIONS IN RETRIEVED SOURCES (STRICT RULE: YOU MAY ONLY CITE THESE SECTIONS):
{allowed_citations_text}

RETRIEVED LEGAL SOURCES:
{context}

USER QUESTION:
{question}

CRITICAL RESPONSE GUIDELINES:
1. Conversational & Direct Opening:
   Start with a natural opening sentence addressing the user's specific problem (e.g., "That may give you a consumer-related remedy, especially if the product is defective...", or "Under Indian law, delayed or withheld salary is governed by statutory provisions...").

2. Strict Grounding & Citation Rules:
   - You may ONLY cite the section numbers explicitly listed under ALLOWED CITATIONS above.
   - NEVER mention, cite, or invent any other section numbers (e.g. do NOT cite Section 84, Section 85, Section 39, etc. unless explicitly listed in ALLOWED CITATIONS above).
   - If explaining a concept whose specific section was not retrieved, refer to it simply as "the Act" or "statutory provisions" without guessing a section number.
   - DO NOT invent specific deadlines, time limits (e.g. do not state 'within 14 days' or 'within 30 days' unless explicitly written in the legal text above), percentages (e.g. do not invent '50% damages'), penalties, websites, or procedures not directly found in the text. Describe remedies qualitatively.

3. Distinguish Law from Practical Guidance:
   Clearly separate what the law strictly says from practical advice:
   - Use measured, objective phrasing: "Based on the retrieved provision...", "This may be relevant because...", "The Act provides...", "If your situation falls within this provision...".
   - NEVER make overconfident promises such as "You definitely have a case", "You will win", or "You will definitely get compensation".
   - Never present your own practical inference as if it were directly written in the statute.

4. Response Structure (Use these Markdown headings when appropriate for structured problems):
   ### What this means
   Explain the user's situation and the core legal concept in clear, simple language.

   ### What the law says
   Explain the relevant statutory provisions, citing ONLY the Act name and Section number(s) from ALLOWED CITATIONS.

   ### What you can consider doing
   Provide practical, general legal-awareness steps based ONLY on the retrieved sources (e.g., preserving bills/invoices/evidence, issuing a written notice, approaching the designated authority).

   ### Important
   Note key statutory limitations, exceptions, time limits, or when consultation with a qualified advocate or police authority is necessary.

5. Multi-Turn Context & Follow-Ups:
   If the user asks a follow-up question (such as "What should I do first?", "What if he refuses?", or "Which section applies?"):
   - Maintain full continuity with the previous turns in the conversation.
   - Answer directly by referring back to the specific statutory section, remedy, or situation discussed earlier.
   - Do not make the user repeat their problem statement.

6. Avoid Redundancy & Word Budget:
   - Do not repeat the same legal explanation across sections.
   - Target 250–450 visible words for normal questions. Keep it clear, concise, and focused.
   - End your response with this standard notice:
   *Disclaimer: This information is for legal awareness only and does not constitute formal legal advice.*
"""
    return prompt



# =========================
# LLM Generation (Ollama & Hosted Providers)
# =========================

def generate_answer(prompt, return_timing=False, allowed_sections=None):
    config = get_llm_config()
    t_gen_start = time.perf_counter()
    t_post_start = time.perf_counter()

    if config["provider"] == "ollama":
        prefill = "<think>\nDirect response.\n</think>\n\n"
        messages = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": prefill}
        ]
        url = f"{config['base_url']}/api/chat"
        response = requests.post(
            url,
            json={
                "model": config["model"],
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 650,
                    "keep_alive": "30m"
                }
            },
            timeout=300
        )
        t_post_end = time.perf_counter()
        response.raise_for_status()
        data = response.json()
        raw_response = data.get("message", {}).get("content", "")
    else:
        # Hosted OpenAI-compatible provider
        url = f"{config['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        }
        payload = {
            "model": config["model"],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 800,
            "stream": False,
        }
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        t_post_end = time.perf_counter()
        if response.status_code == 401:
            raise PermissionError("Authentication failed with the hosted AI service. Please verify LLM_API_KEY.")
        if response.status_code == 429:
            raise RuntimeError("Rate limit exceeded for the hosted AI service. Please try again shortly.")
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raw_response = ""
        else:
            raw_response = choices[0].get("message", {}).get("content", "")

    if "</think>" in raw_response:
        cleaned = raw_response.split("</think>")[-1].strip()
    else:
        cleaned = raw_response.strip()
    cleaned = cleaned.replace("<think>", "").strip()
    if allowed_sections is not None:
        cleaned = sanitize_unsupported_citations(cleaned, allowed_sections)
    t_gen_end = time.perf_counter()

    gen_timing = {
        "ollama_request_start_ms": round((t_post_end - t_post_start) * 1000, 2),
        "total_ollama_generation_time_ms": round((t_gen_end - t_gen_start) * 1000, 2),
        "time_to_first_token_ms": round((t_gen_end - t_gen_start) * 1000, 2),
    }

    if return_timing:
        return cleaned.strip(), gen_timing
    return cleaned.strip()


def generate_answer_stream(prompt, return_timing_callback=None, allowed_sections=None):
    """
    Yields response tokens with real-time streaming,
    supporting local Ollama and hosted OpenAI-compatible providers,
    passing each token chunk through citation safety filtering.
    """
    config = get_llm_config()
    t_gen_start = time.perf_counter()
    t_post_start = time.perf_counter()

    process_token, flush_stream = create_citation_stream_filter(allowed_sections)

    if config["provider"] == "ollama":
        prefill = "<think>\nDirect response.\n</think>\n\n"
        messages = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": prefill}
        ]
        url = f"{config['base_url']}/api/chat"
        response = requests.post(
            url,
            json={
                "model": config["model"],
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 650,
                    "keep_alive": "30m"
                }
            },
            stream=True,
            timeout=300
        )
        t_post_end = time.perf_counter()
        request_start_ms = round((t_post_end - t_post_start) * 1000, 2)
        response.raise_for_status()

        first_token_time_ms = None
        in_think_block = False

        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8"))
                chunk = data.get("message", {}).get("content", "")
                if not chunk:
                    continue

                if "<think>" in chunk:
                    in_think_block = True
                if in_think_block:
                    if "</think>" in chunk:
                        chunk = chunk.split("</think>")[-1]
                        in_think_block = False
                    else:
                        continue

                if "</think>" in chunk:
                    chunk = chunk.split("</think>")[-1]

                if chunk:
                    if first_token_time_ms is None:
                        first_token_time_ms = round((time.perf_counter() - t_gen_start) * 1000, 2)
                    filtered = process_token(chunk)
                    if filtered:
                        yield filtered
            except Exception:
                continue

    else:
        # Hosted OpenAI-compatible streaming
        url = f"{config['base_url']}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        }
        payload = {
            "model": config["model"],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 800,
            "stream": True,
        }
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=120)
        t_post_end = time.perf_counter()
        request_start_ms = round((t_post_end - t_post_start) * 1000, 2)
        if response.status_code == 401:
            raise PermissionError("Authentication failed with the hosted AI service. Please verify LLM_API_KEY.")
        if response.status_code == 429:
            raise RuntimeError("Rate limit exceeded for the hosted AI service. Please try again shortly.")
        response.raise_for_status()

        first_token_time_ms = None
        in_think_block = False

        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8").strip()
            if not line_str or line_str.startswith(":"):
                continue
            if line_str.startswith("data: "):
                data_str = line_str[6:].strip()
            elif line_str.startswith("data:"):
                data_str = line_str[5:].strip()
            else:
                continue

            if data_str == "[DONE]":
                break

            try:
                data = json.loads(data_str)
                choices = data.get("choices", [])
                if not choices:
                    continue
                chunk = choices[0].get("delta", {}).get("content", "")
                if not chunk:
                    continue

                if "<think>" in chunk:
                    in_think_block = True
                if in_think_block:
                    if "</think>" in chunk:
                        chunk = chunk.split("</think>")[-1]
                        in_think_block = False
                    else:
                        continue

                if "</think>" in chunk:
                    chunk = chunk.split("</think>")[-1]

                if chunk:
                    if first_token_time_ms is None:
                        first_token_time_ms = round((time.perf_counter() - t_gen_start) * 1000, 2)
                    filtered = process_token(chunk)
                    if filtered:
                        yield filtered
            except Exception:
                continue

    remaining = flush_stream()
    if remaining:
        yield remaining

    t_gen_end = time.perf_counter()
    total_generation_time_ms = round((t_gen_end - t_gen_start) * 1000, 2)
    if first_token_time_ms is None:
        first_token_time_ms = total_generation_time_ms

    if return_timing_callback:
        return_timing_callback({
            "ollama_request_start_ms": request_start_ms,
            "time_to_first_token_ms": first_token_time_ms,
            "total_ollama_generation_time_ms": total_generation_time_ms
        })


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
