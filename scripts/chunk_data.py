#!/usr/bin/env python3
"""
Legal-Aware Chunking Engine
---------------------------
Converts cleaned legal JSON records into retrieval-ready chunks while prioritizing
legal structure over raw character count.

Preserves legal hierarchy:
Act -> Chapter -> Section -> Subsection -> Clause

Includes metadata context, parent-child traceability, and deterministic chunk IDs.
Outputs chunk JSON files and chunking reports.
"""

import os
import sys
import json
import re
import argparse
import logging
from typing import List, Dict, Tuple, Optional

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("LegalChunker")

# Configurable Chunking Size Guidelines
TARGET_CHUNK_SIZE = 1200
MAX_CHUNK_SIZE = 1800
MIN_CHUNK_SIZE = 200


def generate_deterministic_chunk_id(record_id: str, chunk_index: int) -> str:
    """Generate a deterministic, unique chunk ID based on the parent record ID."""
    clean_id = record_id.strip()
    return f"{clean_id}-CHUNK-{chunk_index}"


def split_text_by_lines(text: str, sub: Optional[str], max_size: int) -> List[Tuple[Optional[str], str]]:
    """Split a single large block of text by paragraph or line boundaries if it exceeds max_size."""
    lines = text.split('\n')
    chunks = []
    curr_lines = []
    curr_len = 0

    for line in lines:
        if curr_len + len(line) > max_size and curr_lines:
            chunks.append((sub, '\n'.join(curr_lines)))
            curr_lines = [line]
            curr_len = len(line)
        else:
            curr_lines.append(line)
            curr_len += len(line) + 1

    if curr_lines:
        chunks.append((sub, '\n'.join(curr_lines)))

    return chunks


def chunk_record_content(content: str, max_size: int = MAX_CHUNK_SIZE) -> List[Tuple[Optional[str], str]]:
    """
    Split legal record content into structural units (subsections, explanations, illustrations, clauses).
    Preserves exact wording without modification.
    """
    if len(content) <= max_size:
        return [(None, content)]

    lines = content.split('\n')
    blocks = []
    curr_sub = None
    curr_lines = []

    # 1. Identify subsection and structural boundaries
    for line in lines:
        m = re.match(r'^\s*(\(\d+\)|Explanation(?:\s+\d+)?\.\-\-?|Illustration[s]?\.\-\-?|\([a-z]\))\s*', line)
        if m and curr_lines:
            blocks.append((curr_sub, '\n'.join(curr_lines)))
            curr_lines = [line]
            curr_sub = m.group(1)
        else:
            if not curr_lines and m:
                curr_sub = m.group(1)
            curr_lines.append(line)

    if curr_lines:
        blocks.append((curr_sub, '\n'.join(curr_lines)))

    # 2. Ensure no single block exceeds max_size
    sized_blocks = []
    for sub, btxt in blocks:
        if len(btxt) > max_size:
            sub_chunks = split_text_by_lines(btxt, sub, max_size)
            sized_blocks.extend(sub_chunks)
        else:
            sized_blocks.append((sub, btxt))

    # 3. Combine adjacent small blocks up to max_size
    combined_chunks = []
    c_sub = None
    c_lines = []
    c_len = 0

    for sub, txt in sized_blocks:
        if c_len + len(txt) > max_size and c_lines:
            combined_chunks.append((c_sub, '\n'.join(c_lines)))
            c_sub = sub
            c_lines = [txt]
            c_len = len(txt)
        else:
            if not c_sub:
                c_sub = sub
            c_lines.append(txt)
            c_len += len(txt) + 1

    if c_lines:
        combined_chunks.append((c_sub, '\n'.join(c_lines)))

    return combined_chunks


def chunk_dataset(input_file: str, output_file: str, report_file: str = None) -> dict:
    """Process a cleaned legal JSON file and generate structured chunks."""
    logger.info(f"Chunking dataset: {input_file}")

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError(f"Expected a JSON list in {input_file}")

    chunks_created = []
    sections_split_count = 0
    chunk_lengths = []

    seen_chunk_ids = set()
    duplicate_chunk_ids_count = 0
    empty_chunks_count = 0
    flagged_chunks = []

    for rec in records:
        rec_id = rec.get("id", "UNKNOWN-ID")
        content = rec.get("content", "")

        raw_chunks = chunk_record_content(content, max_size=MAX_CHUNK_SIZE)
        total_chunks_for_section = len(raw_chunks)

        if total_chunks_for_section > 1:
            sections_split_count += 1

        for idx, (sub_unit, chunk_text) in enumerate(raw_chunks, start=1):
            chunk_id = generate_deterministic_chunk_id(rec_id, idx)
            c_len = len(chunk_text)
            chunk_lengths.append(c_len)

            if c_len == 0:
                empty_chunks_count += 1

            if chunk_id in seen_chunk_ids:
                duplicate_chunk_ids_count += 1
            else:
                seen_chunk_ids.add(chunk_id)

            chunk_obj = {
                "chunk_id": chunk_id,
                "act": rec.get("act", ""),
                "category": rec.get("category", ""),
                "subcategory": rec.get("subcategory", ""),
                "chapter": rec.get("chapter", ""),
                "section": rec.get("section", ""),
                "section_number": rec.get("section_number"),
                "title": rec.get("title", ""),
                "subsection": sub_unit,
                "content": chunk_text,
                "source": rec.get("source", ""),
                "source_url": rec.get("source_url", ""),
                "document_type": rec.get("document_type", "Act"),
                "page": rec.get("page"),
                "language": rec.get("language", "English"),
                "parent_record_id": rec_id,
                "chunk_index": idx,
                "total_chunks_for_section": total_chunks_for_section
            }
            chunks_created.append(chunk_obj)

    records_before = len(records)
    total_chunks = len(chunks_created)
    avg_size = round(sum(chunk_lengths) / total_chunks, 1) if total_chunks > 0 else 0
    min_size = min(chunk_lengths) if total_chunks > 0 else 0
    max_size = max(chunk_lengths) if total_chunks > 0 else 0

    status = "passed" if (empty_chunks_count == 0 and duplicate_chunk_ids_count == 0) else "warning"

    report = {
        "source_file": input_file,
        "output_file": output_file,
        "records_before": records_before,
        "chunks_created": total_chunks,
        "sections_split": sections_split_count,
        "average_chunk_size": avg_size,
        "min_chunk_size": min_size,
        "max_chunk_size": max_size,
        "empty_chunks": empty_chunks_count,
        "duplicate_chunk_ids": duplicate_chunk_ids_count,
        "flagged_chunks": flagged_chunks,
        "status": status
    }

    # Write chunk JSON file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(chunks_created, f, indent=4, ensure_ascii=False)

    # Write report file
    if not report_file:
        dir_name = os.path.dirname(output_file)
        base_name = os.path.basename(output_file)
        if base_name.endswith("_chunks.json"):
            report_name = base_name.replace("_chunks.json", "_chunking_report.json")
        elif base_name.endswith(".json"):
            report_name = base_name[:-5] + "_chunking_report.json"
        else:
            report_name = base_name + "_report.json"
        report_file = os.path.join(dir_name, report_name)

    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    logger.info(f"Generated {total_chunks} chunks ({sections_split_count} sections split) -> {output_file}")
    logger.info(f"Report saved -> {report_file} (Avg size: {avg_size} chars)")

    return report


def process_directory(input_dir: str, output_dir: str):
    """Recursively process all cleaned JSON files under input_dir into output_dir."""
    logger.info(f"Processing chunking directory: '{input_dir}' -> '{output_dir}'")

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

                rel_path = os.path.relpath(full_input_path, input_dir)
                if file.endswith("_cleaned.json"):
                    out_filename = file.replace("_cleaned.json", "_chunks.json")
                elif not file.endswith("_chunks.json"):
                    out_filename = os.path.splitext(file)[0] + "_chunks.json"
                else:
                    out_filename = file

                rel_dir = os.path.dirname(rel_path)
                full_output_dir = os.path.join(output_dir, rel_dir)
                full_output_path = os.path.join(full_output_dir, out_filename)

                try:
                    chunk_dataset(full_input_path, full_output_path)
                    successful_files += 1
                except Exception as e:
                    logger.error(f"Failed to chunk dataset '{full_input_path}': {e}")
                    failed_files += 1

    logger.info(f"Directory chunking completed: {successful_files}/{total_files} succeeded, {failed_files} failed.")


def main():
    parser = argparse.ArgumentParser(description="Legal-Aware Chunking Script")
    parser.add_argument("--input", type=str, help="Input cleaned JSON file path")
    parser.add_argument("--output", type=str, help="Output chunk JSON file path")
    parser.add_argument("--report", type=str, help="Optional output report JSON file path")
    parser.add_argument("--input-dir", type=str, help="Input cleaned directory path for batch processing")
    parser.add_argument("--output-dir", type=str, help="Output chunks directory path for batch processing")

    args = parser.parse_args()

    if args.input_dir and args.output_dir:
        process_directory(args.input_dir, args.output_dir)
    elif args.input and args.output:
        chunk_dataset(args.input, args.output, args.report)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
