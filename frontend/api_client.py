"""HTTP client for the existing LegalConnect FastAPI backend."""

from __future__ import annotations

import requests

API_BASE_URL = "http://127.0.0.1:8000"
ASK_ENDPOINT = f"{API_BASE_URL}/ask"
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


def ask_question(question: str) -> dict:
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
            json={"question": clean_query},
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

        return {
            "ok": False,
            "error": "The legal assistant ran into a server problem. Please try again in a moment.",
            "answer": None,
            "sources": [],
        }

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "error": (
                f"The request timed out after {TIMEOUT_SECONDS} seconds. "
                "Please try a shorter question or try again shortly."
            ),
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
            "error": "Something went wrong while reaching the legal assistant. Please try again.",
            "answer": None,
            "sources": [],
        }
