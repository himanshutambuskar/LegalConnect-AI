#!/usr/bin/env python3
"""
Vectorstore Inspection Script
------------------------------
Displays summary statistics and metadata samples for ChromaDB collections
without printing raw embedding arrays.
"""

import sys
import json
import argparse
import os

import chromadb

DEFAULT_COLLECTION_NAME = "legal_bns_2023"
DEFAULT_PERSIST_DIR = "vectorstore/chroma"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def inspect_collection(
    persist_dir: str = DEFAULT_PERSIST_DIR,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    model_name: str = DEFAULT_EMBEDDING_MODEL
):
    if not os.path.exists(persist_dir):
        print(f"Error: Vectorstore directory '{persist_dir}' not found.")
        sys.exit(1)

    chroma_client = chromadb.PersistentClient(path=persist_dir)
    
    try:
        collection = chroma_client.get_collection(name=collection_name)
    except Exception as e:
        print(f"Error getting collection '{collection_name}': {e}")
        sys.exit(1)

    doc_count = collection.count()
    sample = collection.peek(limit=5)

    print("\n==================================================")
    print("VECTORSTORE INSPECTION SUMMARY")
    print("==================================================")
    print(f"Collection Name: {collection_name}")
    print(f"Persistence Directory: {persist_dir}")
    print(f"Embedding Model: {model_name}")
    print(f"Stored Document Count: {doc_count}")
    print("==================================================")

    print("\n--- SAMPLE DOCUMENT IDs (First 5) ---")
    for i, cid in enumerate(sample.get("ids", []), start=1):
        print(f" {i}. {cid}")

    print("\n--- SAMPLE METADATA (First 2) ---")
    for i, meta in enumerate(sample.get("metadatas", [])[:2], start=1):
        print(f"\nSample {i} ({sample['ids'][i-1]}):")
        for k, v in meta.items():
            print(f"  - {k}: {v}")

    print("\n--- SAMPLE DOCUMENT CONTENT PREVIEW (First 2) ---")
    for i, doc_text in enumerate(sample.get("documents", [])[:2], start=1):
        preview = doc_text.replace("\n", " ")[:150]
        print(f"Sample {i}: \"{preview}...\"\n")
    print("==================================================\n")


def main():
    parser = argparse.ArgumentParser(description="ChromaDB Vectorstore Inspector")
    parser.add_argument("--persist-dir", type=str, default=DEFAULT_PERSIST_DIR, help="ChromaDB persistence directory")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION_NAME, help="ChromaDB collection name")
    parser.add_argument("--model", type=str, default=DEFAULT_EMBEDDING_MODEL, help="Embedding model name")

    args = parser.parse_args()
    inspect_collection(args.persist_dir, args.collection, args.model)


if __name__ == "__main__":
    main()
