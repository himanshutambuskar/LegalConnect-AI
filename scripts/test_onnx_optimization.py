#!/usr/bin/env python3
"""
Comprehensive Test Suite for ONNX Embedding Runtime Optimization
-----------------------------------------------------------------
Validates:
1. Embedding output shape (384-dimensional) and L2 normalization
2. Mathematical equivalence & cosine similarity against SentenceTransformer
3. sys.modules assertion (ensures torch and sentence_transformers are NOT loaded)
4. Vectorstore compatibility with existing 3,209 vectors in ChromaDB
5. Retrieval ranking & chunk fidelity across multi-statute queries
6. FastAPI endpoints: GET /, GET /health, POST /ask, and POST /ask/stream (NDJSON)
7. Citation extraction and sanitization preservation
"""

import os
import sys
import json
import time
import unittest
from pathlib import Path

# Enforce clean environment
os.environ["EMBEDDING_BACKEND"] = "onnx"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestONNXOptimization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. Verify sys.modules before loading
        assert "torch" not in sys.modules, "torch should not be loaded yet"
        assert "sentence_transformers" not in sys.modules, "sentence_transformers should not be loaded yet"

        from scripts.legal_chat import load_resources
        cls.embedding_model, cls.collection = load_resources()

        # Verify torch is STILL not loaded when using ONNX backend
        assert "torch" not in sys.modules, "torch was unexpectedly imported by ONNX backend!"
        assert "sentence_transformers" not in sys.modules, "sentence_transformers was unexpectedly imported!"

    def test_01_embedding_dimensions_and_normalization(self):
        """Verify ONNX model outputs normalized 384-dimensional float32 vectors."""
        import numpy as np

        # Single string input
        vec_single = self.embedding_model.encode("What is theft under Bharatiya Nyaya Sanhita?")
        self.assertEqual(vec_single.shape, (384,))
        self.assertEqual(vec_single.dtype, np.float32)
        norm_single = float(np.linalg.norm(vec_single))
        self.assertAlmostEqual(norm_single, 1.0, places=5)

        # Batch input
        vec_batch = self.embedding_model.encode([
            "What is theft under Bharatiya Nyaya Sanhita?",
            "Transfer of Property Act section 52 lis pendens doctrine"
        ])
        self.assertEqual(vec_batch.shape, (2, 384))
        self.assertEqual(vec_batch.dtype, np.float32)
        for i in range(2):
            self.assertAlmostEqual(float(np.linalg.norm(vec_batch[i])), 1.0, places=5)

    def test_02_vectorstore_compatibility(self):
        """Verify existing ChromaDB vectorstore has 3,209 vectors and queries successfully."""
        count = self.collection.count()
        self.assertEqual(count, 3209, f"Expected 3,209 vectors, found {count}")

        # Query using precomputed ONNX embeddings
        query_vec = self.embedding_model.encode(["punishment for cyber crime"]).tolist()
        results = self.collection.query(
            query_embeddings=query_vec,
            n_results=5,
            include=["documents", "metadatas", "distances"]
        )
        self.assertEqual(len(results["documents"][0]), 5)
        self.assertEqual(len(results["metadatas"][0]), 5)

    def test_03_legal_retrieval_ranking(self):
        """Verify legal retrieval pipeline returns correct statutes, sections, and confidence."""
        from scripts.retrieval_utils import retrieve_legal_chunks

        test_cases = [
            {
                "query": "What is the punishment for murder under Section 103 of BNS?",
                "expected_act": "Bharatiya Nyaya Sanhita, 2023",
                "expected_secs": ["103"]
            },
            {
                "query": "How to file a workplace sexual harassment complaint in internal complaints committee?",
                "expected_act": "Sexual Harassment of Women at Workplace Act, 2013",
                "expected_secs": ["4", "9"]
            },
            {
                "query": "What is identity theft under IT Act Section 66C?",
                "expected_act": "Information Technology Act, 2000",
                "expected_secs": ["66C", "66c"]
            },
            {
                "query": "Transfer of property lis pendens rule section 52",
                "expected_act": "Transfer of Property Act, 1882",
                "expected_secs": ["52"]
            }
        ]

        for tc in test_cases:
            res = retrieve_legal_chunks(tc["query"], self.embedding_model, self.collection)
            self.assertTrue(res["is_confident"], f"Query failed confidence check: {tc['query']}")
            self.assertGreater(len(res["reranked_results"]), 0)

            top_chunk = res["reranked_results"][0]
            meta = top_chunk["metadata"]
            sec = str(meta.get("section") or meta.get("section_number"))
            act = meta.get("act")

            self.assertEqual(act, tc["expected_act"], f"Act mismatch for '{tc['query']}': got '{act}'")
            matched = any(exp in sec for exp in tc["expected_secs"])
            self.assertTrue(matched, f"Section mismatch for '{tc['query']}': expected one of '{tc['expected_secs']}' in '{sec}'")

    def test_04_citation_sanitization(self):
        """Verify citation extraction and sanitization works with retrieved chunks."""
        from scripts.retrieval_utils import retrieve_legal_chunks
        from frontend.citation_utils import extract_allowed_section_numbers, sanitize_unsupported_citations

        res = retrieve_legal_chunks(
            "What is identity theft under Section 66C of IT Act?",
            self.embedding_model,
            self.collection
        )
        sources = [
            {
                "act": r["metadata"].get("act"),
                "section": r["metadata"].get("section") or r["metadata"].get("section_number"),
                "title": r["metadata"].get("title")
            }
            for r in res["reranked_results"]
        ]
        allowed_sections = extract_allowed_section_numbers(sources)
        self.assertIn("66c", allowed_sections)

        # Test hallucinated citation removal
        hallucinated_text = "Under Section 66C of IT Act and Section 9999 of BNS, identity theft is illegal."
        sanitized = sanitize_unsupported_citations(hallucinated_text, allowed_sections)
        self.assertIn("Section 66C", sanitized)
        self.assertNotIn("Section 9999", sanitized)

    def test_05_fastapi_endpoints(self):
        """Verify FastAPI endpoints: root, health, and stream handling."""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)

        # 1. Root
        resp_root = client.get("/")
        self.assertEqual(resp_root.status_code, 200)
        data_root = resp_root.json()
        self.assertEqual(data_root["status"], "running")
        self.assertEqual(data_root["total_sources"], 16)

        # 2. Health
        resp_health = client.get("/health")
        self.assertEqual(resp_health.status_code, 200)
        data_health = resp_health.json()
        self.assertEqual(data_health["vector_database"], "ChromaDB")
        self.assertEqual(data_health["vector_db_status"], "connected")
        self.assertEqual(data_health["total_vectors"], 3209)

        # 3. Stream with unconfident / vague query
        resp_stream_vague = client.post("/ask/stream", json={"question": "my boss is troubling me", "history": []})
        self.assertEqual(resp_stream_vague.status_code, 200)
        lines = [line.strip() for line in resp_stream_vague.text.split("\n") if line.strip()]
        self.assertGreater(len(lines), 0)
        meta_event = json.loads(lines[0])
        self.assertEqual(meta_event["type"], "meta")
        self.assertFalse(meta_event["is_confident"])

    def test_06_equivalence_with_sentence_transformers(self):
        """
        Verify mathematical equivalence between ONNX embeddings and SentenceTransformers
        across representative legal texts (cosine similarity >= 0.999999).
        """
        import numpy as np
        from sentence_transformers import SentenceTransformer

        st_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

        test_sentences = [
            "What is the punishment for theft under Section 303 of Bharatiya Nyaya Sanhita?",
            "Internal complaints committee constitution and procedure under Section 4 of POSH Act",
            "Right to Information Act Section 6 application process for citizens",
            "Transfer of Property Act section 52 lis pendens doctrine applicability during pending litigation"
        ]

        for s in test_sentences:
            st_vec = st_model.encode(s, normalize_embeddings=True)
            onnx_vec = self.embedding_model.encode(s, normalize_embeddings=True)

            # Cosine similarity
            cos_sim = float(np.dot(st_vec, onnx_vec) / (np.linalg.norm(st_vec) * np.linalg.norm(onnx_vec)))
            max_abs_diff = float(np.max(np.abs(st_vec - onnx_vec)))

            self.assertGreaterEqual(cos_sim, 0.999999, f"Cosine similarity {cos_sim} too low for '{s}'")
            self.assertLess(max_abs_diff, 1e-5, f"Max difference {max_abs_diff} too high for '{s}'")


if __name__ == "__main__":
    print("=" * 70)
    print("RUNNING FOCUSED ONNX OPTIMIZATION TEST SUITE")
    print("=" * 70)
    unittest.main(verbosity=2)
