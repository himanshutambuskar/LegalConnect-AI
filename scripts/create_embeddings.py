#!/usr/bin/env python3
"""
Legal Embedding Generation & ChromaDB Ingestion Engine
-------------------------------------------------------
Generates dense vector embeddings for legal chunks using SentenceTransformers
and stores them in a persistent local ChromaDB vector database.

Features:
- Configurable embedding model (default: sentence-transformers/all-MiniLM-L6-v2)
- Idempotent upsert by deterministic chunk ID (prevents duplicate ingestion)
- Batch processing (default BATCH_SIZE = 32)
- Safe primitive metadata serialization
- Data integrity verification and report generation
"""

import os
import sys
import json
import argparse
import logging
from typing import List, Dict, Any

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import chromadb
from sentence_transformers import SentenceTransformer

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EmbeddingPipeline")

# Global Configurable Defaults
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 32
DEFAULT_COLLECTION_NAME = "legal_bns_2023"
DEFAULT_PERSIST_DIR = "vectorstore/chroma"


def sanitize_metadata_for_chroma(meta_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert metadata dictionary values into ChromaDB-compatible primitive types."""
    clean_meta = {}
    for k, v in meta_dict.items():
        if v is None:
            clean_meta[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            clean_meta[k] = v
        else:
            clean_meta[k] = str(v)
    return clean_meta


def ingest_chunks_to_chroma(
    input_file: str,
    persist_dir: str = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = DEFAULT_BATCH_SIZE,
    report_file: str = "data/vectorstore/bns_embedding_report.json"
) -> dict:
    """Ingest legal chunk JSON into ChromaDB vector database."""
    logger.info(f"Loading chunk dataset from: {input_file}")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input chunk file not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    if not isinstance(chunks, list):
        raise ValueError(f"Expected a list of chunks in {input_file}")

    source_chunk_count = len(chunks)
    logger.info(f"Loaded {source_chunk_count} chunks. Performing pre-ingestion data integrity check...")

    # Data Integrity Pre-checks
    seen_ids = set()
    duplicate_count = 0
    empty_content_count = 0

    valid_chunks = []
    for idx, chk in enumerate(chunks):
        cid = chk.get("chunk_id")
        content = chk.get("content", "")

        if not cid:
            logger.error(f"Chunk at index {idx} missing 'chunk_id'. Skipping.")
            continue
        if not content or not content.strip():
            empty_content_count += 1
            logger.error(f"Chunk '{cid}' has empty content. Skipping.")
            continue
        if cid in seen_ids:
            duplicate_count += 1
            logger.warning(f"Duplicate chunk_id '{cid}' detected.")

        seen_ids.add(cid)
        valid_chunks.append(chk)

    logger.info(f"Pre-check complete: {len(valid_chunks)} valid chunks ready for embedding.")

    # Load SentenceTransformer Model
    logger.info(f"Loading SentenceTransformer embedding model: '{model_name}'...")
    model = SentenceTransformer(model_name)
    embedding_dim = model.get_sentence_embedding_dimension()
    logger.info(f"Embedding model loaded successfully. Vector dimension: {embedding_dim}")

    # Initialize ChromaDB Client
    os.makedirs(persist_dir, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    logger.info(f"Connected to ChromaDB collection '{collection_name}' at '{persist_dir}'.")

    # Ingest in Batches
    logger.info(f"Ingesting {len(valid_chunks)} chunks in batches of {batch_size}...")

    failed_records = 0
    for i in range(0, len(valid_chunks), batch_size):
        batch = valid_chunks[i:i + batch_size]
        batch_ids = [c["chunk_id"] for c in batch]
        batch_texts = [c["content"] for c in batch]
        batch_metas = [sanitize_metadata_for_chroma(c) for c in batch]

        try:
            batch_embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()
            collection.upsert(
                ids=batch_ids,
                documents=batch_texts,
                embeddings=batch_embeddings,
                metadatas=batch_metas
            )
            logger.info(f"Ingested batch {i // batch_size + 1}/{(len(valid_chunks) + batch_size - 1) // batch_size} ({len(batch)} items)")
        except Exception as e:
            logger.error(f"Failed to ingest batch starting at index {i}: {e}")
            failed_records += len(batch)

    # Post-Ingestion Verification
    stored_document_count = collection.count()
    logger.info(f"ChromaDB Ingestion Complete. Total documents in collection '{collection_name}': {stored_document_count}")

    if stored_document_count != source_chunk_count:
        logger.warning(f"Mismatch: Source chunks ({source_chunk_count}) != Stored documents ({stored_document_count})")
        status = "warning"
    else:
        logger.info("Integrity Verification Passed: Stored document count perfectly matches source chunk count!")
        status = "passed"

    report = {
        "source_file": input_file,
        "collection": collection_name,
        "embedding_model": model_name,
        "source_chunks": source_chunk_count,
        "stored_documents": stored_document_count,
        "embedding_dimension": embedding_dim,
        "batch_size": batch_size,
        "duplicate_ids": duplicate_count,
        "failed_records": failed_records,
        "status": status
    }

    # Save report
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    logger.info(f"Embedding report saved -> {report_file}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Legal Data Embedding Generation & Ingestion Script")
    parser.add_argument("--input", type=str, default="data/processed_chunks/criminal/bns/bns_chunks.json", help="Input chunk JSON file")
    parser.add_argument("--persist-dir", type=str, default=DEFAULT_PERSIST_DIR, help="ChromaDB persistence directory")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION_NAME, help="ChromaDB collection name")
    parser.add_argument("--model", type=str, default=DEFAULT_EMBEDDING_MODEL, help="SentenceTransformer model name")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size for embedding generation")
    parser.add_argument("--report", type=str, default="data/vectorstore/bns_embedding_report.json", help="Output embedding report JSON file")

    args = parser.parse_args()

    ingest_chunks_to_chroma(
        input_file=args.input,
        persist_dir=args.persist_dir,
        collection_name=args.collection,
        model_name=args.model,
        batch_size=args.batch_size,
        report_file=args.report
    )


if __name__ == "__main__":
    main()
