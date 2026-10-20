"""HTTP client for the existing LegalConnect FastAPI backend."""

from __future__ import annotations

import os
import json
import requests

API_BASE_URL = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8000").rstrip("/")
ASK_ENDPOINT = f"{API_BASE_URL}/ask"
ASK_STREAM_ENDPOINT = f"{API_BASE_URL}/ask/stream"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
TIMEOUT_SECONDS = 180


def check_health(timeout: float = 3.0) -> dict:
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return {"ok": True, "data": data}
        return {
            "ok": False,
            "error": "The legal assistant is currently unavailable. Please try again shortly.",
        }
    except requests.exceptions.RequestException:
        return {
            "ok": False,
            "error": "LegalConnect backend is currently unavailable. Please make sure the FastAPI server is running.",
        }


def ask_question(question: str, history: list[dict] | None = None) -> dict:
    """POST a question to /ask. Returns a normalized result dict (never raises)."""
    clean_query = (question or "").strip()
    if not clean_query:
        return {
            "ok": False,
            "error": "Please enter a legal question before sending.",
            "answer": None,
            "sources": [],
        }

    try:
        response = requests.post(
            ASK_ENDPOINT,
            json={"question": clean_query, "history": history or []},
            timeout=TIMEOUT_SECONDS,
        )

        if response.status_code == 200:
            try:
                res_data = response.json()
            except ValueError:
                return {
                    "ok": False,
                    "error": "The assistant returned an unreadable response. Please try again.",
                    "answer": None,
                    "sources": [],
                }

            answer = res_data.get("answer")
            sources = res_data.get("sources") or []
            if not isinstance(sources, list):
                sources = []
            if not answer:
                return {
                    "ok": False,
                    "error": "The assistant could not generate an answer for this question.",
                    "answer": None,
                    "sources": sources,
                }
            return {"ok": True, "answer": answer, "sources": sources, "error": None}

        if response.status_code == 400:
            try:
                detail = response.json().get("detail", "Invalid request parameters.")
            except ValueError:
                detail = "Invalid request parameters."
            return {
                "ok": False,
                "error": f"We could not process that question. {detail}",
                "answer": None,
                "sources": [],
            }

        if response.status_code in (500, 502, 503, 504):
            try:
                detail = response.json().get("detail", "")
            except Exception:
                detail = ""
            if detail and not any(t in detail.lower() for t in ["httpconnection", "traceback", "errno"]):
                err_msg = detail
            elif response.status_code == 503 or "ollama" in detail.lower():
                err_msg = "LegalConnect could not connect to the local AI service. Please make sure Ollama is running."
            else:
                err_msg = "I couldn't generate a response right now. Please try again."
            return {
                "ok": False,
                "error": err_msg,
                "answer": None,
                "sources": [],
            }

        return {
            "ok": False,
            "error": "I couldn't generate a response right now. Please try again.",
            "answer": None,
            "sources": [],
        }

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "error": "The request timed out. Please try a shorter question or try again shortly.",
            "answer": None,
            "sources": [],
        }
    except requests.exceptions.ConnectionError:
        return {
            "ok": False,
            "error": "LegalConnect backend is currently unavailable. Please make sure the FastAPI server is running.",
            "answer": None,
            "sources": [],
        }
    except Exception:
        return {
            "ok": False,
            "error": "I couldn't generate a response right now. Please try again.",
            "answer": None,
            "sources": [],
        }


def ask_question_stream(question: str, history: list[dict] | None = None):
    """
    POST a question to /ask/stream. Yields events:
    {"type": "meta", "is_confident": bool, "sources": list}
    {"type": "token", "token": str}
    {"type": "error", "error": str}
    """
    clean_query = (question or "").strip()
    if not clean_query:
        yield {"type": "error", "error": "Please enter a legal question before sending."}
        return

    try:
        response = requests.post(
            ASK_STREAM_ENDPOINT,
            json={"question": clean_query, "history": history or []},
            stream=True,
            timeout=TIMEOUT_SECONDS,
        )

        if response.status_code != 200:
            try:
                err_data = response.json()
                detail = err_data.get("detail", "")
            except Exception:
                detail = ""
            if detail and not any(t in detail.lower() for t in ["httpconnection", "traceback", "errno"]):
                yield {"type": "error", "error": detail}
            elif response.status_code == 503 or "ollama" in detail.lower():
                yield {
                    "type": "error",
                    "error": "LegalConnect could not connect to the local AI service. Please make sure Ollama is running.",
                }
            else:
                yield {"type": "error", "error": "I couldn't generate a response right now. Please try again."}
            return

        for line in response.iter_lines():
            if not line:
                continue
            try:
                event = json.loads(line.decode("utf-8"))
                yield event
            except Exception:
                continue

    except requests.exceptions.Timeout:
        yield {
            "type": "error",
            "error": "The request timed out. Please try again.",
        }
    except requests.exceptions.ConnectionError:
        yield {
            "type": "error",
            "error": "LegalConnect backend is currently unavailable. Please make sure the FastAPI server is running.",
        }
    except Exception:
        yield {"type": "error", "error": "I couldn't generate a response right now. Please try again."}
