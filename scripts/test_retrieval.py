#!/usr/bin/env python3
"""
Legal Vector Retrieval & Evaluation Script
-------------------------------------------
Queries the ChromaDB vector database using dense embedding similarity and
metadata-aware boosting to retrieve the top K relevant legal sections.

Includes a combined BNS, BNSS, and BSA evaluation suite and generates
`data/vectorstore/combined_retrieval_test.json`.
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

# Ensure local script directory is in sys.path for retrieval_utils import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from retrieval_utils import (
    retrieve_legal_chunks,
    DEFAULT_CANDIDATE_POOL_SIZE,
    DEFAULT_FINAL_TOP_K,
    DEFAULT_CONFIDENCE_THRESHOLD
)

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RetrievalTester")

# Defaults
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_COLLECTION_NAME = "legal_bns_2023"
DEFAULT_PERSIST_DIR = "vectorstore/chroma"

BNS_ACT = "Bharatiya Nyaya Sanhita, 2023"
BNSS_ACT = "Bharatiya Nagarik Suraksha Sanhita, 2023"
BSA_ACT = "Bharatiya Sakshya Adhiniyam, 2023"
IT_ACT = "Information Technology Act, 2000"
CPA_ACT = "Consumer Protection Act, 2019"
CSS_ACT = "Code on Social Security, 2020"

BENCHMARK_TEST_QUERIES = [
    {
        "query": "What is the punishment for identity theft under IT Act?",
        "expected_section": "66C",
        "expected_act": IT_ACT,
    },
    {
        "query": "What does IT Act Section 43A say about compensation for failure to protect data?",
        "expected_section": "43A",
        "expected_act": IT_ACT,
    },
    {
        "query": "What is the penalty for publishing obscene information in electronic form?",
        "expected_section": "67",
        "expected_act": IT_ACT,
    },
    {
        "query": "What is the punishment for murder?",
        "expected_section": "103",
        "expected_act": BNS_ACT,
    },
    {
        "query": "What is defamation under BNS?",
        "expected_section": "356",
        "expected_act": BNS_ACT,
    },
    {
        "query": "What does BNS say about breach of contract to attend on and supply wants of helpless persons?",
        "expected_section": "357",
        "expected_act": BNS_ACT,
    },
    {
        "query": "What happens to the Indian Penal Code after BNS?",
        "expected_section": "358",
        "expected_act": BNS_ACT,
    },
    {
        "query": "what happens to IPC?",
        "expected_section": "358",
        "expected_act": BNS_ACT,
    },
    {
        "query": "IPC repeal",
        "expected_section": "358",
        "expected_act": BNS_ACT,
    },
    {
        "query": "What is defamation?",
        "expected_section": "356",
        "expected_act": BNS_ACT,
    },
    {
        "query": "punishment for murder",
        "expected_section": "103",
        "expected_act": BNS_ACT,
    },
    {
        "query": "What does Section 358 say?",
        "expected_section": "358",
        "expected_act": BNS_ACT,
    },
    {
        "query": "Whoever commits murder",
        "expected_section": "103",
        "expected_act": BNS_ACT,
    },
    {
        "query": "What does BNSS section 35 say?",
        "expected_section": "35",
        "expected_act": BNSS_ACT,
    },
    {
        "query": "When may police arrest without warrant under the Bharatiya Nagarik Suraksha Sanhita?",
        "expected_section": "35",
        "expected_act": BNSS_ACT,
    },
    {
        "query": "What is BNSS section 173 about?",
        "expected_section": "173",
        "expected_act": BNSS_ACT,
    },
    {
        "query": "How is information in cognizable cases handled under BNSS?",
        "expected_section": "173",
        "expected_act": BNSS_ACT,
    },
    {
        "query": "What is the maximum detention period for an undertrial prisoner under BNSS?",
        "expected_section": "479",
        "expected_act": BNSS_ACT,
    },
    {
        "query": "What happens to the Code of Criminal Procedure under BNSS section 531?",
        "expected_section": "531",
        "expected_act": BNSS_ACT,
    },
    {
        "query": "What does BSA section 63 say?",
        "expected_section": "63",
        "expected_act": BSA_ACT,
    },
    {
        "query": "Are electronic records admissible as evidence under the Bharatiya Sakshya Adhiniyam?",
        "expected_section": "63",
        "expected_act": BSA_ACT,
    },
    {
        "query": "What does BSA section 26 cover?",
        "expected_section": "26",
        "expected_act": BSA_ACT,
    },
    {
        "query": "When is a statement by a person who is dead or cannot be found relevant under BSA?",
        "expected_section": "26",
        "expected_act": BSA_ACT,
    },
    {
        "query": "What facts may a Court presume under BSA section 119?",
        "expected_section": "119",
        "expected_act": BSA_ACT,
    },
    {
        "query": "What does BSA say about repeal of the Indian Evidence Act?",
        "expected_section": "170",
        "expected_act": BSA_ACT,
    },
    {
        "query": "What does Consumer Protection Act Section 83 say about product liability action?",
        "expected_section": "83",
        "expected_act": CPA_ACT,
    },
    {
        "query": "What is the penalty for false or misleading advertisement under CPA section 21?",
        "expected_section": "21",
        "expected_act": CPA_ACT,
    },
    {
        "query": "What is the Central Consumer Protection Authority under CPA section 10?",
        "expected_section": "10",
        "expected_act": CPA_ACT,
    },
    {
        "query": "What happens to the Consumer Protection Act 1986 under CPA section 107?",
        "expected_section": "107",
        "expected_act": CPA_ACT,
    },
    {
        "query": "What does Code on Social Security section 53 say about maternity benefit?",
        "expected_section": "53",
        "expected_act": CSS_ACT,
    },
    {
        "query": "What does Section 55 of Code on Social Security say about nursing breaks?",
        "expected_section": "55",
        "expected_act": CSS_ACT,
    },
    {
        "query": "What is the Social Security Fund for unorganised workers under CSS section 109?",
        "expected_section": "109",
        "expected_act": CSS_ACT,
    },
    {
        "query": "What does Section 164 of the Code on Social Security say about repeal and savings?",
        "expected_section": "164",
        "expected_act": CSS_ACT,
    }
]


def print_debug_search(query_text: str, retrieval_result: Dict[str, Any]):
    """Print detailed debug trace for retrieval steps."""
    orig_q = retrieval_result["original_query"]
    search_q = retrieval_result["search_query"]
    all_candidates = retrieval_result["candidates_retrieved"]
    final_results = retrieval_result["reranked_results"]
    is_conf = retrieval_result["is_confident"]
    top_score = retrieval_result["top_score"]
    thresh = retrieval_result["confidence_threshold"]

    print("\n" + "=" * 70)
    print("RETRIEVAL DEBUG TRACE")
    print("=" * 70)
    print(f"Original Query:                  \"{orig_q}\"")
    print(f"Normalized/Expanded Search Query: \"{search_q}\"")
    print(f"Confidence Evaluation:           {'CONFIDENT' if is_conf else 'LOW CONFIDENCE'} (Top Score: {top_score:.4f}, Threshold: {thresh:.4f})")
    print(f"Candidate Pool Retrieved:        {len(all_candidates)} candidates")
    print("=" * 70)

    print("\n--- CANDIDATE POOL (BEFORE DEDUPLICATION & FINAL RANKING) ---")
    for i, cand in enumerate(all_candidates[:10], start=1):
        cid = cand["chunk_id"]
        meta = cand["metadata"]
        sec_num = meta.get("section_number", meta.get("section", "N/A"))
        title = meta.get("title", "N/A")
        sim = cand["semantic_similarity"]
        boost = cand["metadata_boost"]
        final_score = cand["final_score"]
        reasons = "; ".join(cand["boost_reasons"]) if cand["boost_reasons"] else "None"

        print(f"\nCandidate {i:2d} | Chunk: {cid}")
        print(f"  Section: {sec_num} | Title: {title}")
        print(f"  Semantic Similarity: {sim:.4f} | Metadata Boost: {boost:.4f} | Final Score: {final_score:.4f}")
        print(f"  Boost Reasons: {reasons}")

    print("\n" + "=" * 70)
    print("FINAL TOP RERANKED RESULTS (AFTER DEDUPLICATION)")
    print("=" * 70)
    for rank, res in enumerate(final_results, start=1):
        cid = res["chunk_id"]
        meta = res["metadata"]
        doc_text = res["document"]
        sec_num = meta.get("section_number", meta.get("section", "N/A"))
        title = meta.get("title", "N/A")
        act = meta.get("act", "N/A")
        sim = res["semantic_similarity"]
        boost = res["metadata_boost"]
        final_score = res["final_score"]
        preview = doc_text.replace("\n", " ")[:150]

        print(f"\nRANK {rank}")
        print("-" * 50)
        print(f"Chunk ID:            {cid}")
        print(f"Act:                 {act}")
        print(f"Section:             {sec_num}")
        print(f"Title:               {title}")
        print(f"Semantic Similarity: {sim:.4f}")
        print(f"Metadata Boost:      {boost:.4f}")
        print(f"Final Rerank Score:  {final_score:.4f}")
        print(f"Content Preview:     {preview}...")

    print("=" * 70 + "\n")


def print_search_results(query_text: str, retrieval_result: Dict[str, Any]):
    """Print standard search results summary to stdout."""
    final_results = retrieval_result["reranked_results"]
    orig_q = retrieval_result["original_query"]

    print("\n==================================================")
    print(f"QUERY: \"{orig_q}\"")
    print("==================================================")

    for rank, res in enumerate(final_results, start=1):
        cid = res["chunk_id"]
        meta = res["metadata"]
        doc_text = res["document"]
        sec_num = meta.get("section_number", meta.get("section", "N/A"))
        title = meta.get("title", "N/A")
        act = meta.get("act", "N/A")
        source = meta.get("source", "N/A")
        sim = res["semantic_similarity"]
        final_score = res["final_score"]
        preview = doc_text.replace("\n", " ")[:150]

        print(f"\nRESULT {rank}")
        print("-" * 50)
        print(f"Chunk ID: {cid}")
        print(f"Act: {act}")
        print(f"Section: {sec_num}")
        print(f"Title: {title}")
        print(f"Similarity Score: {sim:.4f} | Rerank Score: {final_score:.4f}")
        print(f"Source: {source}")
        print(f"Content Preview:\n{preview}...")

    print("==================================================\n")


def run_benchmark_evaluation(
    collection,
    model: SentenceTransformer,
    top_k: int = DEFAULT_FINAL_TOP_K,
    report_file: str = "data/vectorstore/combined_retrieval_test.json"
) -> dict:
    """Run evaluation benchmark queries against ChromaDB and calculate Hit Rate@1/3/5 & MRR."""
    logger.info(f"Running retrieval evaluation suite on {len(BENCHMARK_TEST_QUERIES)} benchmark queries...")

    eval_results = []
    hit_1_count = 0
    hit_3_count = 0
    hit_5_count = 0
    reciprocal_ranks = []

    for item in BENCHMARK_TEST_QUERIES:
        qtext = item["query"]
        exp_sec = str(item["expected_section"])
        exp_act = item.get("expected_act")

        res_info = retrieve_legal_chunks(
            query_text=qtext,
            embedding_model=model,
            collection=collection,
            candidate_pool_size=DEFAULT_CANDIDATE_POOL_SIZE,
            final_top_k=top_k
        )

        reranked_metas = [r["metadata"] for r in res_info["reranked_results"]]
        retrieved_sections = [str(m.get("section_number", m.get("section", ""))) for m in reranked_metas]
        retrieved_acts = [m.get("act", "") for m in reranked_metas]

        rank = None
        for idx, (section, act) in enumerate(zip(retrieved_sections, retrieved_acts), start=1):
            if section == exp_sec and (not exp_act or act == exp_act):
                rank = idx
                break
        rr = 1.0 / rank if rank else 0.0

        reciprocal_ranks.append(rr)

        hit_1 = (rank == 1)
        hit_3 = (rank is not None and rank <= 3)
        hit_5 = (rank is not None and rank <= 5)

        if hit_1:
            hit_1_count += 1
        if hit_3:
            hit_3_count += 1
        if hit_5:
            hit_5_count += 1

        top_match = res_info["reranked_results"][0] if res_info["reranked_results"] else None
        top_sim = top_match["semantic_similarity"] if top_match else 0.0
        top_final = top_match["final_score"] if top_match else 0.0

        status_str = f"Rank {rank}" if rank else "NOT FOUND"
        logger.info(f"Query: '{qtext[:45]:<45}' -> Expected: {exp_act} s.{exp_sec} | Retrieved: {str(list(zip(retrieved_acts, retrieved_sections))):<25} | {status_str}")

        eval_results.append({
            "query": qtext,
            "expected_section": exp_sec,
            "expected_act": exp_act,
            "retrieved_sections": retrieved_sections,
            "retrieved_acts": retrieved_acts,
            "expected_rank": rank,
            "top_similarity_score": round(top_sim, 4),
            "top_final_score": round(top_final, 4),
            "hit_at_1": hit_1,
            "hit_at_3": hit_3,
            "hit_at_5": hit_5
        })

    total_queries = len(BENCHMARK_TEST_QUERIES)
    hit_rate_1 = round(hit_1_count / total_queries, 4) if total_queries > 0 else 0.0
    hit_rate_3 = round(hit_3_count / total_queries, 4) if total_queries > 0 else 0.0
    hit_rate_5 = round(hit_5_count / total_queries, 4) if total_queries > 0 else 0.0
    mrr = round(sum(reciprocal_ranks) / total_queries, 4) if total_queries > 0 else 0.0

    report = {
        "embedding_model": DEFAULT_EMBEDDING_MODEL,
        "collection": DEFAULT_COLLECTION_NAME,
        "top_k": top_k,
        "total_test_queries": total_queries,
        "hit_rate_at_1": hit_rate_1,
        "hit_rate_at_3": hit_rate_3,
        "hit_rate_at_5": hit_rate_5,
        "mrr": mrr,
        "tests": eval_results
    }

    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("BENCHMARK EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Total Test Queries: {total_queries}")
    print(f"Hit Rate@1:         {hit_rate_1 * 100:.1f}% ({hit_1_count}/{total_queries})")
    print(f"Hit Rate@3:         {hit_rate_3 * 100:.1f}% ({hit_3_count}/{total_queries})")
    print(f"Hit Rate@5:         {hit_rate_5 * 100:.1f}% ({hit_5_count}/{total_queries})")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.4f}")
    print("=" * 70)
    logger.info(f"Evaluation report saved -> {report_file}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Legal Vector Retrieval & Benchmark Tester")
    parser.add_argument("--query", type=str, help="Natural language legal query")
    parser.add_argument("--top-k", type=int, default=DEFAULT_FINAL_TOP_K, help="Number of top results to return")
    parser.add_argument("--eval", action="store_true", help="Run benchmark evaluation suite")
    parser.add_argument("--debug", action="store_true", help="Enable retrieval debug mode")
    parser.add_argument("--persist-dir", type=str, default=DEFAULT_PERSIST_DIR, help="ChromaDB persistence directory")
    parser.add_argument("--collection", type=str, default=DEFAULT_COLLECTION_NAME, help="ChromaDB collection name")
    parser.add_argument("--model", type=str, default=DEFAULT_EMBEDDING_MODEL, help="SentenceTransformer model name")

    args = parser.parse_args()

    if not os.path.exists(args.persist_dir):
        print(f"Error: ChromaDB directory '{args.persist_dir}' does not exist.")
        sys.exit(1)

    logger.info(f"Loading embedding model '{args.model}'...")
    model = SentenceTransformer(args.model)

    chroma_client = chromadb.PersistentClient(path=args.persist_dir)
    collection = chroma_client.get_collection(name=args.collection)

    if args.eval or not args.query:
        run_benchmark_evaluation(collection, model, top_k=args.top_k)

    if args.query:
        retrieval_res = retrieve_legal_chunks(
            query_text=args.query,
            embedding_model=model,
            collection=collection,
            candidate_pool_size=DEFAULT_CANDIDATE_POOL_SIZE,
            final_top_k=args.top_k
        )
        if args.debug:
            print_debug_search(args.query, retrieval_res)
        else:
            print_search_results(args.query, retrieval_res)


if __name__ == "__main__":
    main()
