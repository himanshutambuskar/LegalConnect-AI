#!/usr/bin/env python3
"""
Legal Chunk Validation Script & Content Preservation Tester
------------------------------------------------------------
Validates generated chunk JSON files against required schema rules, unique IDs,
metadata integrity, and performs a 100% Content Reconstruction Test against the
cleaned source dataset.
"""

import sys
import json
import argparse
import os
from collections import defaultdict

REQUIRED_CHUNK_FIELDS = [
    "chunk_id",
    "act",
    "category",
    "subcategory",
    "section",
    "title",
    "content",
    "source",
    "source_url",
    "document_type",
    "language",
    "parent_record_id",
    "chunk_index",
    "total_chunks_for_section"
]


def validate_chunk_json(chunk_file: str, source_file: str = None) -> dict:
    if not os.path.exists(chunk_file):
        print(f"Error: Chunk file not found at '{chunk_file}'")
        sys.exit(1)

    try:
        with open(chunk_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
    except Exception as e:
        print(f"Error loading chunk JSON file '{chunk_file}': {e}")
        sys.exit(1)

    if not isinstance(chunks, list):
        print(f"Error: Expected JSON list of chunks, got {type(chunks).__name__}")
        sys.exit(1)

    total_chunks = len(chunks)
    valid_chunks = 0
    invalid_chunks = 0
    empty_content_count = 0

    seen_chunk_ids = set()
    duplicate_ids = []

    # Group chunks by parent_record_id for reconstruction testing
    chunks_by_parent = defaultdict(list)

    for idx, chk in enumerate(chunks):
        chk_errors = []

        if not isinstance(chk, dict):
            chk_errors.append("Chunk is not a valid JSON dictionary")
            invalid_chunks += 1
            continue

        # Check required fields presence
        for field in REQUIRED_CHUNK_FIELDS:
            if field not in chk:
                chk_errors.append(f"Missing required field '{field}'")

        # Check chunk_id uniqueness
        cid = chk.get("chunk_id")
        if cid:
            if cid in seen_chunk_ids:
                duplicate_ids.append(cid)
                chk_errors.append(f"Duplicate chunk_id '{cid}'")
            else:
                seen_chunk_ids.add(cid)
        else:
            chk_errors.append("Missing chunk_id")

        # Check content non-empty & non-whitespace
        content = chk.get("content", "")
        if not content or not str(content).strip():
            empty_content_count += 1
            chk_errors.append("Empty or whitespace-only content")

        # Check parent_record_id
        pid = chk.get("parent_record_id")
        if not pid:
            chk_errors.append("Missing parent_record_id")
        else:
            chunks_by_parent[pid].append(chk)

        if chk_errors:
            invalid_chunks += 1
        else:
            valid_chunks += 1

    # Content Reconstruction Test (if source file provided)
    reconstruction_mismatches = 0
    total_parent_records_tested = 0

    if source_file and os.path.exists(source_file):
        with open(source_file, 'r', encoding='utf-8') as sf:
            source_records = json.load(sf)

        total_parent_records_tested = len(source_records)
        print("\nRunning Content Reconstruction Test...")

        for srec in source_records:
            pid = srec.get("id")
            original_text = srec.get("content", "").strip()

            parent_chunks = chunks_by_parent.get(pid, [])
            # Sort chunks by chunk_index
            parent_chunks_sorted = sorted(parent_chunks, key=lambda x: x.get("chunk_index", 1))

            reconstructed_text = '\n'.join([c.get("content", "") for c in parent_chunks_sorted]).strip()

            if reconstructed_text != original_text:
                reconstruction_mismatches += 1
                print(f"[RECONSTRUCTION FAIL] Parent ID: '{pid}'")

        if reconstruction_mismatches == 0:
            print(f"Content Reconstruction Test PASSED for all {total_parent_records_tested} records!")

    # Print Validation Report
    print("\n==================================================")
    print("LEGAL CHUNK VALIDATION REPORT")
    print("==================================================")
    print(f"Total chunks: {total_chunks}")
    print(f"Valid chunks: {valid_chunks}")
    print(f"Invalid chunks: {invalid_chunks}")
    print(f"Duplicate chunk IDs: {len(duplicate_ids)}")
    print(f"Empty/whitespace chunks: {empty_content_count}")
    if source_file:
        print(f"Reconstruction tested records: {total_parent_records_tested}")
        print(f"Reconstruction mismatches: {reconstruction_mismatches}")
    print("==================================================")

    return {
        "total": total_chunks,
        "valid": valid_chunks,
        "invalid": invalid_chunks,
        "duplicates": len(duplicate_ids),
        "empty": empty_content_count,
        "reconstruction_mismatches": reconstruction_mismatches
    }


def main():
    parser = argparse.ArgumentParser(description="Legal Chunk Validation Script")
    parser.add_argument("--file", type=str, default="data/processed_chunks/criminal/bns/bns_chunks.json", help="Chunk JSON file")
    parser.add_argument("--source-file", type=str, default="data/processed/criminal/bns/bns_cleaned.json", help="Cleaned source JSON file for reconstruction test")
    args = parser.parse_args()

    validate_chunk_json(args.file, args.source_file)


if __name__ == "__main__":
    main()
