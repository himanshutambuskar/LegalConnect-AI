#!/usr/bin/env python3
"""
Legal Data Validation Script
----------------------------
Validates extracted legal section JSON files against the required schema
and data integrity rules.
"""

import sys
import json
import argparse
import os

REQUIRED_FIELDS = [
    "id",
    "act",
    "category",
    "subcategory",
    "section",
    "section_number",
    "title",
    "content",
    "source",
    "source_url",
    "document_type",
    "language",
    "retrieved_date"
]


def validate_legal_json(file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file '{file_path}': {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print(f"Error: Expected JSON root to be a list of records, got {type(data).__name__}")
        sys.exit(1)

    total_records = len(data)
    valid_records = 0
    invalid_records = 0
    duplicate_records = 0

    seen_ids = set()
    seen_section_numbers = set()

    duplicate_ids = []
    duplicate_sec_nums = []
    empty_records = []

    for idx, rec in enumerate(data):
        record_errors = []

        if not isinstance(rec, dict):
            record_errors.append("Record is not a JSON object")
            invalid_records += 1
            continue

        # Check required fields presence & non-emptiness
        for field in REQUIRED_FIELDS:
            if field not in rec:
                record_errors.append(f"Missing required field '{field}'")
            elif rec[field] is None or (isinstance(rec[field], str) and not rec[field].strip()):
                # Title may be empty in some laws, but content/section_number/act/category/id/source_url must not be empty
                if field not in ["title", "subcategory", "page"]:
                    record_errors.append(f"Field '{field}' is empty or null")

        # Check empty content
        content = rec.get("content", "")
        if not content or not str(content).strip():
            empty_records.append(rec.get("id", f"Record index {idx}"))

        # Check duplicate ID
        rec_id = rec.get("id")
        if rec_id:
            if rec_id in seen_ids:
                duplicate_ids.append(rec_id)
            else:
                seen_ids.add(rec_id)

        # Check duplicate section number
        sec_num = rec.get("section_number")
        if sec_num:
            if sec_num in seen_section_numbers:
                duplicate_sec_nums.append(sec_num)
            else:
                seen_section_numbers.add(sec_num)

        if record_errors:
            invalid_records += 1
        else:
            valid_records += 1

    duplicate_records = len(duplicate_ids)

    # Output Validation Report
    print("\n==================================================")
    print("LEGAL DATA VALIDATION REPORT")
    print("==================================================")
    print(f"Total records: {total_records}")
    print(f"Valid records: {valid_records}")
    print(f"Invalid records: {invalid_records}")
    print(f"Duplicate records: {duplicate_records}")
    print("==================================================")
    print(f"Number of sections extracted: {total_records}")
    print(f"Number of empty records: {len(empty_records)}")
    print(f"Number of duplicate section numbers: {len(duplicate_sec_nums)}")
    print("==================================================")

    # Print First 3 Records
    print("\n--- FIRST 3 RECORDS ---")
    for r in data[:3]:
        snippet = r.get('content', '').replace('\n', ' ')[:100]
        print(f"ID: {r.get('id')} | Act: {r.get('act')} | Section: {r.get('section')} | Title: \"{r.get('title')}\"")
        print(f"Snippet: {snippet}...\n")

    # Print Last 3 Records
    print("--- LAST 3 RECORDS ---")
    for r in data[-3:]:
        snippet = r.get('content', '').replace('\n', ' ')[:100]
        print(f"ID: {r.get('id')} | Act: {r.get('act')} | Section: {r.get('section')} | Title: \"{r.get('title')}\"")
        print(f"Snippet: {snippet}...\n")

    return {
        "total": total_records,
        "valid": valid_records,
        "invalid": invalid_records,
        "duplicates": duplicate_records,
        "empty_count": len(empty_records),
        "duplicate_sec_count": len(duplicate_sec_nums)
    }


def main():
    parser = argparse.ArgumentParser(description="Legal Data Validation Script")
    parser.add_argument("--file", type=str, default="data/raw/criminal/bns/bns_sections.json", help="JSON file to validate")
    args = parser.parse_args()

    validate_legal_json(args.file)


if __name__ == "__main__":
    main()
