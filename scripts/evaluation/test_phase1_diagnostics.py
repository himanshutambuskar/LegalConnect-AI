#!/usr/bin/env python3
"""
LegalConnect — Phase 1 Test Suite: Output Token Ceiling, Finish Reason & Telemetry
----------------------------------------------------------------------------------
Validates:
1. Configurable LLM_MAX_TOKENS (default 1500, respects custom int, handles invalid values).
2. Normal complete responses (finish_reason="stop", truncated=False).
3. Token limit truncation handling (finish_reason="length", truncated=True, truncation note).
4. Streaming token truncation handling (stream_finish_reason="length").
5. Empty model responses (graceful user-facing notice, no silent failures).
6. Early stream termination handling.
7. HTTP 429 (Rate Limit) and HTTP 503 (Unavailable/Overloaded) error handling.
8. Full response schema backwards compatibility for frontend and external consumers.
"""

import os
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.legal_chat import (
    get_max_tokens,
    get_llm_config,
    generate_answer,
    generate_answer_stream,
)
from backend.main import app
from fastapi.testclient import TestClient


class TestPhase1Diagnostics(unittest.TestCase):
    """Validation test suite for Phase 1 objectives."""

    # 1. Configurable LLM_MAX_TOKENS
    def test_01_llm_max_tokens_configuration(self):
        # Default when unset
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_max_tokens(), 1500)

        # Custom valid integer
        with patch.dict(os.environ, {"LLM_MAX_TOKENS": "2500"}, clear=True):
            self.assertEqual(get_max_tokens(), 2500)

        # Invalid string falls back to 1500
        with patch.dict(os.environ, {"LLM_MAX_TOKENS": "not-a-number"}, clear=True):
            self.assertEqual(get_max_tokens(), 1500)

        # Non-positive integer falls back to 1500
        with patch.dict(os.environ, {"LLM_MAX_TOKENS": "-50"}, clear=True):
            self.assertEqual(get_max_tokens(), 1500)

    # 2. Normal complete response (finish_reason="stop")
    @patch("requests.post")
    def test_02_normal_complete_response(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Under Section 185, driving under influence is punishable."},
                    "finish_reason": "stop"
                }
            ]
        }
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            ans, timing = generate_answer("Prompt", return_timing=True, allowed_sections={"185"})
            self.assertEqual(ans, "Under Section 185, driving under influence is punishable.")
            self.assertFalse(timing["truncated"])
            self.assertEqual(timing["finish_reason"], "stop")
            self.assertEqual(timing["provider"], "openai_compatible")
            # Verify payload used max_tokens=1500
            sent_payload = mock_post.call_args[1]["json"]
            self.assertEqual(sent_payload["max_tokens"], 1500)

    # 3. Truncated non-streaming response (finish_reason="length")
    @patch("requests.post")
    def test_03_truncated_response_non_streaming(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Under Section 185, penalties include imprisonment and"},
                    "finish_reason": "length"
                }
            ]
        }
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            ans, timing = generate_answer("Prompt", return_timing=True, allowed_sections={"185"})
            # Verify explicit truncation note appended
            self.assertIn("Under Section 185, penalties include imprisonment and...", ans)
            self.assertIn("Response reached the maximum output token limit", ans)
            self.assertTrue(timing["truncated"])
            self.assertEqual(timing["finish_reason"], "length")

    # 4. Truncated streaming response (finish_reason="length")
    @patch("requests.post")
    def test_04_truncated_response_streaming(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        sse_lines = [
            b'data: {"choices": [{"delta": {"content": "Under Section 185, fines "}, "finish_reason": null}]}',
            b'data: {"choices": [{"delta": {"content": "apply to the "}, "finish_reason": null}]}',
            b'data: {"choices": [{"delta": {}, "finish_reason": "length"}]}',
            b'data: [DONE]'
        ]
        mock_resp.iter_lines.return_value = sse_lines
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            stream_timing = {}
            def cb(t):
                stream_timing.update(t)

            tokens = list(generate_answer_stream("Prompt", return_timing_callback=cb, allowed_sections={"185"}))
            full_text = "".join(tokens)
            self.assertIn("Under Section 185, fines apply to the", full_text)
            self.assertIn("Response reached the maximum output token limit", full_text)
            self.assertTrue(stream_timing["truncated"])
            self.assertEqual(stream_timing["finish_reason"], "length")

    # 5. Empty model responses
    @patch("requests.post")
    def test_05_empty_model_response(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": []}
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            # Non-streaming empty handling
            ans, timing = generate_answer("Prompt", return_timing=True)
            self.assertIn("couldn't generate a response", ans)

            # Streaming empty handling (now raises RuntimeError)
            mock_resp.iter_lines.return_value = [b'data: [DONE]']
            with self.assertRaises(RuntimeError) as ctx:
                list(generate_answer_stream("Prompt"))
            self.assertIn("couldn't generate a response", str(ctx.exception))

    # 6. HTTP 429 (Rate Limit) and Gateway Errors (502, 503, 504)
    @patch("requests.post")
    def test_06_http_429_and_gateway_errors_handling(self, mock_post):
        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            # HTTP 429 Rate Limit
            mock_429 = MagicMock()
            mock_429.status_code = 429
            mock_post.return_value = mock_429
            with self.assertRaises(RuntimeError) as ctx_429:
                generate_answer("Prompt")
            self.assertIn("Rate limit", str(ctx_429.exception))

            # HTTP 502, 503, 504 Gateway Errors
            import requests as req
            for status in (502, 503, 504):
                mock_gw = MagicMock()
                mock_gw.status_code = status
                mock_post.return_value = mock_gw
                with self.assertRaises(req.exceptions.ConnectionError) as ctx_gw:
                    generate_answer("Prompt")
                self.assertIn("temporarily unavailable", str(ctx_gw.exception))

    # 7. Response Schema Compatibility in FastAPI /ask and /ask/stream
    @patch("backend.main.generate_answer_stream")
    @patch("backend.main.generate_answer")
    @patch("backend.main.retrieve_legal_chunks")
    def test_07_fastapi_telemetry_schema(self, mock_retrieve, mock_gen, mock_stream):
        client = TestClient(app)

        mock_retrieve.return_value = {
            "is_confident": True,
            "reranked_results": [
                {
                    "document": "Section 185 penalties",
                    "metadata": {"act": "Motor Vehicles Act, 1988", "section_number": "185", "title": "Drunk driving"},
                    "distance": 0.1
                }
            ],
            "timing": {
                "query_embedding_time_ms": 15.0,
                "chromadb_search_time_ms": 25.0,
                "exact_metadata_lookup_time_ms": 2.0,
                "act_title_lookup_time_ms": 3.0,
                "reranking_time_ms": 5.0,
                "total_retrieval_time_ms": 50.0,
                "rag_context_construction_time_ms": 1.0,
            }
        }

        mock_gen.return_value = (
            "Under Section 185, penalties apply.",
            {
                "llm_request_start_ms": 200.0,
                "total_llm_generation_time_ms": 1200.0,
                "time_to_first_token_ms": 0.0,
                "ttft_applicable": False,
                "finish_reason": "stop",
                "truncated": False,
                "provider": "openai_compatible",
                "ollama_request_start_ms": 200.0,
                "total_ollama_generation_time_ms": 1200.0,
            }
        )

        resp = client.post("/ask", json={"question": "What is drunken driving penalty?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        timing = data["timing"]

        # 1. Verify provider-agnostic telemetry
        self.assertEqual(timing["llm_provider"], "openai_compatible")
        self.assertEqual(timing["llm_request_start_time_ms"], 200.0)
        self.assertEqual(timing["total_llm_generation_time_ms"], 1200.0)
        self.assertFalse(timing["ttft_applicable"])
        self.assertEqual(timing["finish_reason"], "stop")
        self.assertFalse(timing["truncated"])

        # 2. Verify legacy keys preserved
        self.assertEqual(timing["ollama_request_start_time_ms"], 200.0)
        self.assertEqual(timing["total_ollama_generation_time_ms"], 1200.0)
        self.assertEqual(timing["time_to_first_token_ms"], 0.0)
        self.assertIn("total_request_time_ms", timing)

        # 3. Verify streaming telemetry includes ttft_applicable=True
        def fake_stream(prompt, return_timing_callback=None, allowed_sections=None):
            if return_timing_callback:
                return_timing_callback({
                    "llm_request_start_ms": 150.0,
                    "total_llm_generation_time_ms": 800.0,
                    "time_to_first_token_ms": 250.0,
                    "ttft_applicable": True,
                    "finish_reason": "stop",
                    "truncated": False,
                    "provider": "openai_compatible",
                    "ollama_request_start_ms": 150.0,
                    "total_ollama_generation_time_ms": 800.0,
                })
            yield "Under Section 185, penalties apply."

        mock_stream.side_effect = fake_stream
        stream_resp = client.post("/ask/stream", json={"question": "What is drunken driving penalty?"})
        self.assertEqual(stream_resp.status_code, 200)
        events = [json.loads(line) for line in stream_resp.text.strip().split("\n") if line.strip()]
        timing_events = [e for e in events if e.get("type") == "timing"]
        self.assertEqual(len(timing_events), 1)
        s_timing = timing_events[0]["timing"]
        self.assertTrue(s_timing["ttft_applicable"])
        self.assertEqual(s_timing["llm_provider"], "openai_compatible")

    # 8. Ollama Truncation (done_reason="length")
    @patch("requests.post")
    def test_08_ollama_truncation(self, mock_post):
        # A. Ollama Non-Streaming with done_reason="length"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": "Under Section 185 of Motor Vehicles Act, fines and"},
            "done": True,
            "done_reason": "length"
        }
        mock_post.return_value = mock_resp

        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            ans, timing = generate_answer("Prompt", return_timing=True, allowed_sections={"185"})
            self.assertIn("Under Section 185 of Motor Vehicles Act, fines and...", ans)
            self.assertIn("Response reached the maximum output token limit", ans)
            self.assertTrue(timing["truncated"])
            self.assertEqual(timing["finish_reason"], "length")

        # B. Ollama Streaming with done_reason="length"
        mock_stream_resp = MagicMock()
        mock_stream_resp.status_code = 200
        lines = [
            json.dumps({"message": {"content": "Under Section 185, "}, "done": False}).encode("utf-8"),
            json.dumps({"message": {"content": "penalties apply "}, "done": False}).encode("utf-8"),
            json.dumps({"done": True, "done_reason": "length"}).encode("utf-8"),
        ]
        mock_stream_resp.iter_lines.return_value = lines
        mock_post.return_value = mock_stream_resp

        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            s_timing = {}
            def cb(t):
                s_timing.update(t)

            tokens = list(generate_answer_stream("Prompt", return_timing_callback=cb, allowed_sections={"185"}))
            full_text = "".join(tokens)
            self.assertIn("Under Section 185, penalties apply", full_text)
            self.assertIn("Response reached the maximum output token limit", full_text)
            self.assertTrue(s_timing["truncated"])
            self.assertEqual(s_timing["finish_reason"], "length")

    # 9. Top-Level Provider Error in Streaming
    @patch("requests.post")
    def test_09_streaming_top_level_provider_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            b'data: {"error": {"message": "Service unavailable upstream", "code": 503}}'
        ]
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            s_timing = {}
            def cb(t):
                s_timing.update(t)

            with self.assertRaises(RuntimeError) as ctx:
                list(generate_answer_stream("Prompt", return_timing_callback=cb))
            self.assertIn("upstream issue", str(ctx.exception).lower())
            self.assertFalse(s_timing["ttft_applicable"])
            self.assertEqual(s_timing["time_to_first_token_ms"], 0.0)

    # 10. Choice-Level Provider Error in Streaming
    @patch("requests.post")
    def test_10_streaming_choice_level_provider_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {}, "error": {"message": "Model generation timeout"}}]}'
        ]
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            s_timing = {}
            def cb(t):
                s_timing.update(t)

            with self.assertRaises(RuntimeError) as ctx:
                list(generate_answer_stream("Prompt", return_timing_callback=cb))
            self.assertIn("upstream issue", str(ctx.exception).lower())
            self.assertFalse(s_timing["ttft_applicable"])
            self.assertEqual(s_timing["time_to_first_token_ms"], 0.0)

    # 11. finish_reason="error" Treated as Upstream Failure and Failed-Stream TTFT
    @patch("backend.main.retrieve_legal_chunks")
    @patch("requests.post")
    def test_11_streaming_finish_reason_error_handling(self, mock_post, mock_retrieval):
        mock_retrieval.return_value = {
            "is_confident": True,
            "reranked_results": [
                {
                    "document": "Causing death by negligence",
                    "metadata": {"act": "Bharatiya Nyaya Sanhita, 2023", "section_number": "106", "title": "Section 106"},
                    "distance": 0.1,
                }
            ],
            "timing": {
                "query_embedding_time_ms": 10.0,
                "chromadb_search_time_ms": 20.0,
                "exact_metadata_lookup_time_ms": 1.0,
                "act_title_lookup_time_ms": 2.0,
                "reranking_time_ms": 3.0,
                "total_retrieval_time_ms": 36.0,
                "rag_context_construction_time_ms": 1.0,
            },
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Simulates OpenRouter chunk with finish_reason="error" and empty delta
        mock_resp.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {}, "finish_reason": "error"}]}',
            b'data: [DONE]'
        ]
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            # A. Test direct generate_answer_stream raises RuntimeError and records failed TTFT
            s_timing = {}
            def cb(t):
                s_timing.update(t)

            with self.assertRaises(RuntimeError):
                list(generate_answer_stream("Prompt", return_timing_callback=cb))
            self.assertFalse(s_timing["ttft_applicable"])
            self.assertEqual(s_timing["time_to_first_token_ms"], 0.0)
            self.assertEqual(s_timing["finish_reason"], "error")

            # B. Test FastAPI /ask/stream yields structured {"type":"error"} and NO generic token
            client = TestClient(app)
            resp = client.post("/ask/stream", json={"question": "What is Section 106 BNS?"})
            self.assertEqual(resp.status_code, 200)
            events = [json.loads(line) for line in resp.text.strip().split("\n") if line.strip()]

            # Must contain meta and error event
            types = [e.get("type") for e in events]
            self.assertIn("meta", types)
            self.assertIn("error", types)

            # Must NOT emit generic failure message as normal token
            token_events = [e for e in events if e.get("type") == "token"]
            self.assertEqual(len(token_events), 0)

            # Error event message must be clean and safe
            error_event = next(e for e in events if e.get("type") == "error")
            self.assertIn("upstream issue", error_event["error"].lower())
            self.assertNotIn("sk-test-key", error_event["error"])

    # 12. Successful Streaming Telemetry and Genuine TTFT Preservation
    @patch("backend.main.retrieve_legal_chunks")
    @patch("requests.post")
    def test_12_successful_streaming_telemetry(self, mock_post, mock_retrieval):
        mock_retrieval.return_value = {
            "is_confident": True,
            "reranked_results": [
                {
                    "document": "Drunken driving penalties",
                    "metadata": {"act": "Motor Vehicles Act, 1988", "section_number": "185", "title": "Section 185"},
                    "distance": 0.1,
                }
            ],
            "timing": {
                "query_embedding_time_ms": 10.0,
                "chromadb_search_time_ms": 20.0,
                "exact_metadata_lookup_time_ms": 1.0,
                "act_title_lookup_time_ms": 2.0,
                "reranking_time_ms": 3.0,
                "total_retrieval_time_ms": 36.0,
                "rag_context_construction_time_ms": 1.0,
            },
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "Under Section 185, "}, "finish_reason": null}]}',
            b'data: {"choices": [{"delta": {"content": "penalties apply."}, "finish_reason": null}]}',
            b'data: {"choices": [{"delta": {}, "finish_reason": "stop"}]}',
            b'data: [DONE]'
        ]
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            client = TestClient(app)
            resp = client.post("/ask/stream", json={"question": "What is Section 185?"})
            self.assertEqual(resp.status_code, 200)
            events = [json.loads(line) for line in resp.text.strip().split("\n") if line.strip()]

            # Must contain meta, token, and timing events
            types = [e.get("type") for e in events]
            self.assertIn("meta", types)
            self.assertIn("token", types)
            self.assertIn("timing", types)

            token_text = "".join(e.get("token", "") for e in events if e.get("type") == "token")
            self.assertIn("Under Section 185, penalties apply.", token_text)

            timing_event = next(e for e in events if e.get("type") == "timing")
            t_data = timing_event["timing"]
            self.assertTrue(t_data["ttft_applicable"])
            self.assertGreater(t_data["time_to_first_token_ms"], 0.0)
            self.assertEqual(t_data["finish_reason"], "stop")
            self.assertFalse(t_data["truncated"])

    # 13. Empty Stream FastAPI Error Event and Failed TTFT
    @patch("backend.main.retrieve_legal_chunks")
    @patch("requests.post")
    def test_13_empty_stream_fastapi_handling(self, mock_post, mock_retrieval):
        mock_retrieval.return_value = {
            "is_confident": True,
            "reranked_results": [
                {
                    "document": "Section 185 penalties",
                    "metadata": {"act": "Motor Vehicles Act, 1988", "section_number": "185", "title": "Drunk driving"},
                    "distance": 0.1,
                }
            ],
            "timing": {
                "query_embedding_time_ms": 10.0,
                "chromadb_search_time_ms": 20.0,
                "exact_metadata_lookup_time_ms": 1.0,
                "act_title_lookup_time_ms": 2.0,
                "reranking_time_ms": 3.0,
                "total_retrieval_time_ms": 36.0,
                "rag_context_construction_time_ms": 1.0,
            },
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [b'data: [DONE]']
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            client = TestClient(app)
            resp = client.post("/ask/stream", json={"question": "What is Section 185?"})
            self.assertEqual(resp.status_code, 200)
            events = [json.loads(line) for line in resp.text.strip().split("\n") if line.strip()]

            types = [e.get("type") for e in events]
            self.assertIn("meta", types)
            self.assertIn("error", types)

            # Ensure empty stream produces 0 token events
            token_events = [e for e in events if e.get("type") == "token"]
            self.assertEqual(len(token_events), 0)

            error_event = next(e for e in events if e.get("type") == "error")
            self.assertIn("couldn't generate a response", error_event["error"])

    # 14. Legitimate Answer Matching Former Fallback Sentence
    @patch("backend.main.retrieve_legal_chunks")
    @patch("requests.post")
    def test_14_legitimate_answer_matching_former_fallback_sentence(self, mock_post, mock_retrieval):
        mock_retrieval.return_value = {
            "is_confident": True,
            "reranked_results": [
                {
                    "document": "Statutory definitions",
                    "metadata": {"act": "Motor Vehicles Act, 1988", "section_number": "185", "title": "Section 185"},
                    "distance": 0.1,
                }
            ],
            "timing": {
                "query_embedding_time_ms": 10.0,
                "chromadb_search_time_ms": 20.0,
                "exact_metadata_lookup_time_ms": 1.0,
                "act_title_lookup_time_ms": 2.0,
                "reranking_time_ms": 3.0,
                "total_retrieval_time_ms": 36.0,
                "rag_context_construction_time_ms": 1.0,
            },
        }

        # Model generates text that matches the former fallback sentence
        former_fallback = "I couldn't generate a response for this legal query. Please try rephrasing your question."
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = [
            f'data: {{"choices": [{{"delta": {{"content": "{former_fallback}"}}, "finish_reason": null}}]}}'.encode("utf-8"),
            b'data: {"choices": [{"delta": {}, "finish_reason": "stop"}]}',
            b'data: [DONE]'
        ]
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            client = TestClient(app)
            resp = client.post("/ask/stream", json={"question": "What happens if no response is possible?"})
            self.assertEqual(resp.status_code, 200)
            events = [json.loads(line) for line in resp.text.strip().split("\n") if line.strip()]

            types = [e.get("type") for e in events]
            self.assertIn("meta", types)
            self.assertIn("token", types)
            self.assertIn("timing", types)

            # Must NOT be classified as an error
            self.assertNotIn("error", types)

            # Token content must preserve the legitimate answer
            token_events = [e for e in events if e.get("type") == "token"]
            self.assertEqual(len(token_events), 1)
            self.assertEqual(token_events[0]["token"], former_fallback)

            timing_event = next(e for e in events if e.get("type") == "timing")
            self.assertTrue(timing_event["timing"]["ttft_applicable"])
            self.assertGreater(timing_event["timing"]["time_to_first_token_ms"], 0.0)

    # 15. Non-Streaming TTFT Zero and Generation Time Preservation
    @patch("backend.main.retrieve_legal_chunks")
    @patch("requests.post")
    def test_15_non_streaming_ttft_zero_and_generation_time_preserved(self, mock_post, mock_retrieval):
        mock_retrieval.return_value = {
            "is_confident": True,
            "reranked_results": [
                {
                    "document": "Section 185 penalties",
                    "metadata": {"act": "Motor Vehicles Act, 1988", "section_number": "185", "title": "Section 185"},
                    "distance": 0.1,
                }
            ],
            "timing": {
                "query_embedding_time_ms": 10.0,
                "chromadb_search_time_ms": 20.0,
                "exact_metadata_lookup_time_ms": 1.0,
                "act_title_lookup_time_ms": 2.0,
                "reranking_time_ms": 3.0,
                "total_retrieval_time_ms": 36.0,
                "rag_context_construction_time_ms": 1.0,
            },
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Under Section 185, penalties apply."},
                    "finish_reason": "stop"
                }
            ]
        }
        mock_post.return_value = mock_resp

        env = {
            "LLM_PROVIDER": "openai_compatible",
            "LLM_BASE_URL": "https://openrouter.ai/api/v1",
            "LLM_API_KEY": "sk-test-key",
            "LLM_MODEL": "cohere/north-mini-code:free",
        }
        with patch.dict(os.environ, env, clear=True):
            # A. Test direct generate_answer telemetry
            _, gen_timing = generate_answer("Prompt", return_timing=True, allowed_sections={"185"})
            self.assertFalse(gen_timing["ttft_applicable"])
            self.assertEqual(gen_timing["time_to_first_token_ms"], 0.0)
            self.assertGreater(gen_timing["total_llm_generation_time_ms"], 0.0)

            # B. Test FastAPI POST /ask response telemetry
            client = TestClient(app)
            resp = client.post("/ask", json={"question": "What is Section 185?"})
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            timing = data["timing"]

            # Confirm TTFT is not applicable and reported as 0.0
            self.assertFalse(timing["ttft_applicable"])
            self.assertEqual(timing["time_to_first_token_ms"], 0.0)

            # Confirm generation duration and total request duration are preserved (> 0.0)
            self.assertGreater(timing["total_llm_generation_time_ms"], 0.0)
            self.assertGreater(timing["total_request_time_ms"], 0.0)


def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase1Diagnostics)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    return res.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
