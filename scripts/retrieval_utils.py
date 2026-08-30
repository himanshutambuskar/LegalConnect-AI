#!/usr/bin/env python3
"""
LegalConnect Retrieval Utilities Module
----------------------------------------
Implements:
1. Deterministic Legal Query Expansion / Normalization
2. Metadata-Aware Score Boosting (Section number, title, act, alias matches)
3. Candidate Reranking & Section-Level Deduplication
4. Retrieval Confidence / Relevance Verification
"""

import os
import re
from typing import List, Dict, Any, Tuple

# Ensure offline execution for HuggingFace / Transformers models
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Legal Alias Mapping (Deterministic)
LEGAL_ALIASES = {
    "ipc": "Indian Penal Code",
    "bns": "Bharatiya Nyaya Sanhita",
    "bnss": "Bharatiya Nagarik Suraksha Sanhita",
    "bsa": "Bharatiya Sakshya Adhiniyam"
}

LEGAL_ACT_PATTERNS = {
    "Bharatiya Nyaya Sanhita, 2023": [r"\bbns\b", r"\bbharatiya\s+nyaya\s+sanhita\b"],
    "Bharatiya Nagarik Suraksha Sanhita, 2023": [r"\bbnss\b", r"\bbharatiya\s+nagarik\s+suraksha\s+sanhita\b"],
    "Bharatiya Sakshya Adhiniyam, 2023": [r"\bbsa\b", r"\bbharatiya\s+sakshya\s+adhiniyam\b"],
}

DEFAULT_CANDIDATE_POOL_SIZE = 20
DEFAULT_FINAL_TOP_K = 5
DEFAULT_CONFIDENCE_THRESHOLD = 0.35
MAX_CHUNKS_PER_SECTION = 2
MIN_TITLE_TOPIC_OVERLAP = 2

TOPIC_STOP_WORDS = {
    "what", "is", "the", "a", "an", "for", "of", "to", "in", "and", "or",
    "under", "does", "say", "about", "when", "may", "how", "are", "as",
    "with", "by", "from", "on", "at", "it", "this", "that", "be",
    "bharatiya", "nyaya", "nagarik", "suraksha", "sakshya", "adhiniyam", "sanhita",
    "bns", "bnss", "bsa",
}


def normalize_query(query: str) -> Tuple[str, str]:
    """
    Normalizes and expands user query deterministically.
    Returns tuple of (original_query, expanded_search_query).
    """
    original = query.strip()
    query_lower = original.lower()
    
    expansions = []
    for alias, full_name in LEGAL_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', query_lower):
            expansions.append(full_name)
            
    if expansions:
        expanded_search_query = f"{original} {' '.join(expansions)}"
    else:
        expanded_search_query = original
        
    return original, expanded_search_query


def extract_mentioned_sections(query: str) -> List[str]:
    """
    Extracts explicit section numbers mentioned in the query text.
    E.g. 'Section 358', 'sec 358', 's. 358', '358'
    """
    matches = re.findall(r'\b(?:section|sec\.?|s\.?)\s*(\d+[a-z]?)\b', query, re.IGNORECASE)
    if matches:
        return [m.lower() for m in matches]
    
    query_lower = query.lower()
    num_matches = re.findall(r'\b(\d+[a-z]?)\b', query_lower)
    if ("section" in query_lower or "sec" in query_lower) and num_matches:
        return [n.lower() for n in num_matches]
        
    return []


def extract_mentioned_acts(query: str) -> List[str]:
    """Return canonical Act names explicitly named by a query."""
    query_lower = query.lower()
    return [
        act_name
        for act_name, patterns in LEGAL_ACT_PATTERNS.items()
        if any(re.search(pattern, query_lower) for pattern in patterns)
    ]


def lookup_exact_section_candidates(
    collection,
    query_original: str,
    query_expanded: str,
    sections: List[str],
    acts: List[str],
) -> List[Dict[str, Any]]:
    """Fetch chunks by exact section metadata, optionally constrained to named Acts."""
    exact_candidates = []
    seen_ids = set()
    target_acts = acts or [None]

    for section in sections:
        for act in target_acts:
            where = {"section_number": {"$eq": section}}
            if act:
                where = {"$and": [{"act": {"$eq": act}}, where]}

            result = collection.get(
                where=where,
                include=["documents", "metadatas"],
            )
            for chunk_id, document, metadata in zip(
                result.get("ids", []),
                result.get("documents", []),
                result.get("metadatas", []),
            ):
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                score_info = calculate_candidate_score(
                    query_original,
                    query_expanded,
                    document,
                    metadata,
                    distance=0.0,
                )
                exact_candidates.append({
                    "chunk_id": chunk_id,
                    "document": document,
                    "metadata": metadata,
                    "distance": 0.0,
                    "semantic_similarity": score_info["semantic_similarity"],
                    "metadata_boost": score_info["metadata_boost"],
                    "final_score": score_info["final_score"],
                    "boost_reasons": score_info["boost_reasons"] + ["Exact Act/section metadata lookup"],
                    "is_exact_metadata_match": True,
                })

    return sorted(exact_candidates, key=lambda candidate: candidate["chunk_id"])


# def lookup_act_title_candidates(
#     collection,
#     query_original: str,
#     acts: List[str],
# ) -> List[Dict[str, Any]]:
#     """Add a strong Act-scoped title match when dense retrieval misses its section."""
#     query_terms = set(re.findall(r"\w+", query_original.lower())) - TOPIC_STOP_WORDS
#     if not query_terms:
#         return []

#     best_match = None
#     for act in acts:
#         result = collection.get(
#             where={"act": {"$eq": act}},
#             include=["documents", "metadatas"],
#         )
#         for chunk_id, document, metadata in zip(
#             result.get("ids", []),
#             result.get("documents", []),
#             result.get("metadatas", []),
#         ):
#             title_terms = set(re.findall(r"\w+", str(metadata.get("title", "")).lower()))
#             overlap = len(query_terms.intersection(title_terms))
#             candidate_key = (overlap, -int(metadata.get("chunk_index", 1)), chunk_id)
#             if overlap >= MIN_TITLE_TOPIC_OVERLAP and (
#                 best_match is None or candidate_key > best_match[0]
#             ):
#                 best_match = (candidate_key, chunk_id, document, metadata, overlap)

#     if not best_match:
#         return []

#     _, chunk_id, document, metadata, overlap = best_match
#     return [{
#         "chunk_id": chunk_id,
#         "document": document,
#         "metadata": metadata,
#         "distance": 0.0,
#         "semantic_similarity": 0.0,
#         "metadata_boost": float(overlap),
#         "final_score": float(overlap),
#         "boost_reasons": [f"Act-scoped title topic match ({overlap} terms)"],
#         "is_exact_metadata_match": False,
#         "is_title_metadata_match": True,
#     }]

def lookup_act_title_candidates(
    collection,
    query_original: str,
    acts: List[str],
) -> List[Dict[str, Any]]:
    """Find the best Act-scoped title match using topic overlap."""

    query_terms = set(
        re.findall(r"\w+", query_original.lower())
    ) - TOPIC_STOP_WORDS

    if not query_terms:
        return []

    candidates = []

    for act in acts:
        result = collection.get(
            where={"act": {"$eq": act}},
            include=["documents", "metadatas"],
        )

        for chunk_id, document, metadata in zip(
            result.get("ids", []),
            result.get("documents", []),
            result.get("metadatas", []),
        ):
            title = str(metadata.get("title", "")).lower()
            title_terms = set(re.findall(r"\w+", title))

            overlap = query_terms.intersection(title_terms)

            if len(overlap) < MIN_TITLE_TOPIC_OVERLAP:
                continue

            # Base score from important topic-term overlap.
            score = len(overlap) * 1.0

            # Prefer titles whose wording is directly aligned
            # with the user's query.
            query_clean = " ".join(
                re.findall(r"\w+", query_original.lower())
            )

            title_clean = " ".join(
                re.findall(r"\w+", title)
            )

            query_tokens = query_clean.split()

            # Reward meaningful multi-word phrases appearing
            # directly in the legal title.
            for n in (5, 4, 3, 2):
                for i in range(len(query_tokens) - n + 1):
                    phrase = " ".join(query_tokens[i:i + n])

                    if len(phrase.split()) >= 2 and phrase in title_clean:
                        score += 0.10 * n
                        break

            candidates.append({
                "chunk_id": chunk_id,
                "document": document,
                "metadata": metadata,
                "distance": 0.0,
                "semantic_similarity": 0.0,
                "metadata_boost": score,
                "final_score": score,
                "boost_reasons": [
                    f"Act-scoped title topic match ({len(overlap)} terms)"
                ],
                "is_exact_metadata_match": False,
                "is_title_metadata_match": True,
            })

    if not candidates:
        return []

    candidates.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    return candidates[:3]

def calculate_candidate_score(
    query_original: str,
    query_expanded: str,
    doc_text: str,
    metadata: Dict[str, Any],
    distance: float
) -> Dict[str, Any]:
    """
    Calculates composite score based on semantic distance and metadata/keyword boosting.
    """
    # Cosine similarity calculation: similarity = 1.0 - distance
    sim_score = max(0.0, 1.0 - float(distance))
    
    meta_boost = 0.0
    boost_reasons = []
    
    query_orig_lower = query_original.lower()
    query_exp_lower = query_expanded.lower()
    
    sec_num_str = str(metadata.get("section_number", "")).strip().lower()
    sec_str = str(metadata.get("section", "")).strip().lower()
    title_str = str(metadata.get("title", "")).strip().lower()
    act_str = str(metadata.get("act", "")).strip().lower()
    doc_lower = doc_text.lower()
    
    # 1. Explicit Section Number Boost
    mentioned_secs = extract_mentioned_sections(query_original)
    if sec_num_str and any(sec_num_str == ms for ms in mentioned_secs):
        meta_boost += 0.35
        boost_reasons.append(f"Section match ({sec_num_str}): +0.35")
    elif sec_str and any(ms in sec_str for ms in mentioned_secs):
        meta_boost += 0.35
        boost_reasons.append(f"Section match ({sec_str}): +0.35")
        
    # 2. Title Keyword Boost
    stop_words = {
        "what", "is", "the", "a", "an", "for", "of", "to", "in", "and", "or", 
        "under", "does", "say", "about", "after", "happen", "happens", "commits", 
        "persons", "code", "act", "law"
    }
    query_words = set(re.findall(r'\w+', query_orig_lower)) - stop_words
    
    title_words = set(re.findall(r'\w+', title_str))
    common_title_words = query_words.intersection(title_words)
    if common_title_words:
        boost_val = min(0.25, 0.12 * len(common_title_words))
        meta_boost += boost_val
        boost_reasons.append(f"Title keyword match ({', '.join(common_title_words)}): +{boost_val:.2f}")

    # Exact Title Phrase Match Boost (e.g. 'punishment for murder' == 'punishment for murder')
    clean_title = re.sub(r'^\d+\s*[\.\-]?\s*', '', title_str).strip()
    if clean_title:
        if clean_title == query_orig_lower.strip():
            meta_boost += 0.30
            boost_reasons.append(f"Exact title equality match ('{clean_title}'): +0.30")
        elif clean_title in query_orig_lower or query_orig_lower in clean_title:
            meta_boost += 0.15
            boost_reasons.append(f"Exact title substring match ('{clean_title}'): +0.15")

    # 3. Act / Alias Match Boost
    if "ipc" in query_orig_lower or "indian penal code" in query_orig_lower:
        if "repeal" in title_str or "repeal" in doc_lower or "savings" in title_str or "indian penal code" in doc_lower:
            meta_boost += 0.20
            boost_reasons.append("IPC alias match in text/title: +0.20")

    # 4. Content Keyword Boost
    common_content_words = query_words.intersection(set(re.findall(r'\w+', doc_lower)))
    if common_content_words and not common_title_words:
        boost_val = min(0.10, 0.03 * len(common_content_words))
        meta_boost += boost_val
        boost_reasons.append(f"Content keyword match ({', '.join(list(common_content_words)[:3])}): +{boost_val:.2f}")
        
    final_score = sim_score + meta_boost
    
    return {
        "semantic_similarity": sim_score,
        "metadata_boost": meta_boost,
        "final_score": final_score,
        "boost_reasons": boost_reasons
    }


def rerank_and_deduplicate(
    candidates: List[Dict[str, Any]],
    top_k: int = DEFAULT_FINAL_TOP_K,
    max_per_section: int = MAX_CHUNKS_PER_SECTION
) -> List[Dict[str, Any]]:
    """
    Reranks candidates by final score and applies section-level diversity rules.
    """
    sorted_candidates = sorted(
        candidates,
        key=lambda x: (
            not x.get("is_exact_metadata_match", False),
            not x.get("is_title_metadata_match", False),
            -x["final_score"],
        ),
    )
    
    selected = []
    section_counts = {}
    unselected_fallback = []
    
    for cand in sorted_candidates:
        act = str(cand["metadata"].get("act", "unknown"))
        sec = str(cand["metadata"].get("section_number", cand["metadata"].get("section", "unknown")))
        section_key = (act, sec)
        curr_count = section_counts.get(section_key, 0)
        if curr_count < max_per_section:
            selected.append(cand)
            section_counts[section_key] = curr_count + 1
        else:
            unselected_fallback.append(cand)
            
        if len(selected) == top_k:
            break
            
    if len(selected) < top_k:
        needed = top_k - len(selected)
        selected.extend(unselected_fallback[:needed])
        
    return selected


def retrieve_legal_chunks(
    query_text: str,
    embedding_model,
    collection,
    candidate_pool_size: int = DEFAULT_CANDIDATE_POOL_SIZE,
    final_top_k: int = DEFAULT_FINAL_TOP_K,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    max_per_section: int = MAX_CHUNKS_PER_SECTION
) -> Dict[str, Any]:
    """
    Full legal retrieval pipeline:
    1. Query normalization & legal alias expansion
    2. Candidate retrieval from ChromaDB (top candidate_pool_size)
    3. Metadata-aware score calculation & boosting
    4. Section deduplication / diversity selection (top final_top_k)
    5. Confidence threshold check
    """
    orig_query, search_query = normalize_query(query_text)
    mentioned_sections = extract_mentioned_sections(orig_query)
    mentioned_acts = extract_mentioned_acts(orig_query)
    
    query_embedding = embedding_model.encode(
        [search_query],
        normalize_embeddings=True
    ).tolist()
    
    raw_res = collection.query(
        query_embeddings=query_embedding,
        n_results=candidate_pool_size,
        include=["documents", "metadatas", "distances"]
    )
    
    doc_list = raw_res["documents"][0] if raw_res.get("documents") else []
    meta_list = raw_res["metadatas"][0] if raw_res.get("metadatas") else []
    dist_list = raw_res["distances"][0] if raw_res.get("distances") else []
    id_list = raw_res["ids"][0] if raw_res.get("ids") else []
    
    semantic_candidates = []
    for cid, doc, meta, dist in zip(id_list, doc_list, meta_list, dist_list):
        score_info = calculate_candidate_score(orig_query, search_query, doc, meta, dist)
        semantic_candidates.append({
            "chunk_id": cid,
            "document": doc,
            "metadata": meta,
            "distance": dist,
            "semantic_similarity": score_info["semantic_similarity"],
            "metadata_boost": score_info["metadata_boost"],
            "final_score": score_info["final_score"],
            "boost_reasons": score_info["boost_reasons"],
            "is_exact_metadata_match": False,
            "is_title_metadata_match": False,
        })

    exact_candidates = lookup_exact_section_candidates(
        collection,
        orig_query,
        search_query,
        mentioned_sections,
        mentioned_acts,
    ) if mentioned_sections else []
    title_candidates = lookup_act_title_candidates(
        collection,
        orig_query,
        mentioned_acts,
    ) if mentioned_acts and not mentioned_sections else []
    prioritized_ids = {
        candidate["chunk_id"] for candidate in exact_candidates + title_candidates
    }
    candidates = exact_candidates + title_candidates + [
        candidate for candidate in semantic_candidates
        if candidate["chunk_id"] not in prioritized_ids
    ]

    sorted_all_candidates = sorted(
        candidates,
        key=lambda x: (
            not x.get("is_exact_metadata_match", False),
            not x.get("is_title_metadata_match", False),
            -x["final_score"],
        ),
    )
    reranked_top_k = rerank_and_deduplicate(candidates, top_k=final_top_k, max_per_section=max_per_section)
    
    top_score = sorted_all_candidates[0]["final_score"] if sorted_all_candidates else 0.0
    is_confident = top_score >= confidence_threshold
    
    return {
        "original_query": orig_query,
        "search_query": search_query,
        "candidates_retrieved": sorted_all_candidates,
        "reranked_results": reranked_top_k,
        "top_score": top_score,
        "is_confident": is_confident,
        "confidence_threshold": confidence_threshold
    }
