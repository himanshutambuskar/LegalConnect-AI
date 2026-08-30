#!/usr/bin/env python3
"""
Universal Legal Data Cleaning Pipeline
--------------------------------------
Reusable, category-agnostic cleaning pipeline for official Indian legal text datasets.

Performs safe formatting normalization without altering legal wording:
- Trim leading/trailing whitespace
- Normalize accidental excessive horizontal whitespace
- Normalize excessive blank lines (max 2 consecutive newlines)
- Strip non-printable ASCII/PDF control artifacts
- Preserve paragraphs, subsection markers, punctuation, and legal terms

Supports single-file processing and batch directory structure processing.
Generates structured cleaning quality reports alongside processed JSON files.
"""

import os
import sys
import json
import re
import argparse
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("UniversalLegalCleaner")


def sanitize_text(text: str) -> str:
    """Apply safe formatting normalization to legal text."""
    if not isinstance(text, str):
        return text

    # 1. Remove non-printable control characters (keep tabs \t and newlines \n)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # 2. Normalize accidental excessive horizontal whitespace (preserve newlines)
    # Replaces 2 or more spaces/tabs on a single line with a single space
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line_trimmed = line.strip()
        line_norm = re.sub(r'[ \t]{2,}', ' ', line_trimmed)
        cleaned_lines.append(line_norm)

    # 3. Normalize excessive vertical blank lines (max 2 consecutive newlines)
    text_norm = '\n'.join(cleaned_lines)
    text_norm = re.sub(r'\n{3,}', '\n\n', text_norm)

    return text_norm.strip()


def clean_record(record: dict) -> dict:
    """Clean all string fields of a single legal record."""
    cleaned = {}
    for key, val in record.items():
        if isinstance(val, str):
            if key == "content":
                cleaned[key] = sanitize_text(val)
            else:
                # Normal string fields (titles, ids, names, etc.)
                cleaned[key] = re.sub(r'\s+', ' ', val).strip()
        else:
            cleaned[key] = val
    return cleaned


def process_dataset(input_file: str, output_file: str, report_file: str = None) -> dict:
    """Process and clean a single legal JSON dataset."""
    logger.info(f"Processing dataset: {input_file}")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            records = json.load(f)
        except Exception as e:
            logger.error(f"Invalid JSON file {input_file}: {e}")
            raise

    if not isinstance(records, list):
        raise ValueError(f"Expected a JSON list of records in {input_file}, got {type(records).__name__}")

    records_before = len(records)
    cleaned_records = []

    seen_ids = set()
    seen_sections = set()

    empty_content_count = 0
    duplicate_ids_count = 0
    duplicate_sections_count = 0
    flagged_records = []

    for idx, rec in enumerate(records):
        if not isinstance(rec, dict):
            flagged_records.append({
                "index": idx,
                "reason": "Record is not a valid JSON dictionary"
            })
            continue

        cleaned_rec = clean_record(rec)
        cleaned_records.append(cleaned_rec)

        rec_id = cleaned_rec.get("id")
        content = cleaned_rec.get("content", "")
        sec_num = cleaned_rec.get("section_number")
        source = cleaned_rec.get("source")
        source_url = cleaned_rec.get("source_url")
        doc_type = cleaned_rec.get("document_type", "Act")

        flags = []

        # Check empty content
        if not content:
            empty_content_count += 1
            flags.append("Empty content")
        elif len(content) < 20:
            flags.append(f"Suspiciously short content ({len(content)} chars)")
        elif len(content) > 100000:
            flags.append(f"Suspiciously long content ({len(content)} chars)")

        # Check duplicate ID
        if rec_id:
            if rec_id in seen_ids:
                duplicate_ids_count += 1
                flags.append(f"Duplicate ID '{rec_id}'")
            else:
                seen_ids.add(rec_id)
        else:
            flags.append("Missing 'id' field")

        # Check section number (if applicable for Acts)
        if doc_type in ["Act", "Rule"] and sec_num:
            if sec_num in seen_sections:
                duplicate_sections_count += 1
                flags.append(f"Duplicate section_number '{sec_num}'")
            else:
                seen_sections.add(sec_num)

        # Check missing source / source URL
        if not source:
            flags.append("Missing 'source' field")
        if not source_url:
            flags.append("Missing 'source_url' field")

        if flags:
            flagged_records.append({
                "index": idx,
                "id": rec_id,
                "section": cleaned_rec.get("section"),
                "flags": flags
            })

    records_after = len(cleaned_records)
    status = "passed" if (records_before == records_after and empty_content_count == 0 and duplicate_ids_count == 0) else "warning"

    report = {
        "source_file": input_file,
        "output_file": output_file,
        "records_before": records_before,
        "records_after": records_after,
        "empty_content": empty_content_count,
        "duplicate_ids": duplicate_ids_count,
        "duplicate_sections": duplicate_sections_count,
        "flagged_records": flagged_records,
        "status": status
    }

    # Save cleaned records
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_records, f, indent=4, ensure_ascii=False)

    # Save report
    if not report_file:
        dir_name = os.path.dirname(output_file)
        base_name = os.path.basename(output_file)
        if base_name.endswith("_cleaned.json"):
            report_name = base_name.replace("_cleaned.json", "_cleaning_report.json")
        elif base_name.endswith(".json"):
            report_name = base_name[:-5] + "_cleaning_report.json"
        else:
            report_name = base_name + "_report.json"
        report_file = os.path.join(dir_name, report_name)

    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    logger.info(f"Cleaned {records_after}/{records_before} records -> {output_file}")
    logger.info(f"Report saved -> {report_file} (Status: {status})")

    return report


def process_directory(input_dir: str, output_dir: str):
    """Recursively process all JSON files under input_dir into output_dir."""
    logger.info(f"Processing directory: '{input_dir}' -> '{output_dir}'")

    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    total_files = 0
    successful_files = 0
    failed_files = 0

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".json") and not file.endswith("_report.json"):
                total_files += 1
                full_input_path = os.path.join(root, file)

                # Determine relative path from input_dir
                rel_path = os.path.relpath(full_input_path, input_dir)

                # Generate output filename
                if file.endswith("_sections.json"):
                    out_filename = file.replace("_sections.json", "_cleaned.json")
                elif not file.endswith("_cleaned.json"):
                    out_filename = os.path.splitext(file)[0] + "_cleaned.json"
                else:
                    out_filename = file

                rel_dir = os.path.dirname(rel_path)
                full_output_dir = os.path.join(output_dir, rel_dir)
                full_output_path = os.path.join(full_output_dir, out_filename)

                try:
                    process_dataset(full_input_path, full_output_path)
                    successful_files += 1
                except Exception as e:
                    logger.error(f"Failed to process dataset '{full_input_path}': {e}")
                    failed_files += 1

    logger.info(f"Directory batch processing completed: {successful_files}/{total_files} succeeded, {failed_files} failed.")


def main():
    parser = argparse.ArgumentParser(description="Universal Legal Data Cleaning Script")
    parser.add_argument("--input", type=str, help="Input raw JSON file path")
    parser.add_argument("--output", type=str, help="Output processed JSON file path")
    parser.add_argument("--report", type=str, help="Optional output report JSON file path")
    parser.add_argument("--input-dir", type=str, help="Input raw directory path for batch processing")
    parser.add_argument("--output-dir", type=str, help="Output processed directory path for batch processing")

    args = parser.parse_args()

    if args.input_dir and args.output_dir:
        process_directory(args.input_dir, args.output_dir)
    elif args.input and args.output:
        process_dataset(args.input, args.output, args.report)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
