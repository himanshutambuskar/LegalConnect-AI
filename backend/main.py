import os
import json
import time
import requests
# Configure offline mode only when explicitly requested in environment
if os.environ.get("HF_HUB_OFFLINE") in ("1", "true", "yes"):
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from scripts.legal_chat import (
    load_resources,
    build_prompt,
    generate_answer,
    generate_answer_stream,
    extract_allowed_section_numbers,
    sanitize_unsupported_citations,
    get_llm_config,
    OLLAMA_BASE_URL,
    LLM_MODEL
)

from scripts.retrieval_utils import retrieve_legal_chunks, detect_vague_query


app = FastAPI(
    title="LegalConnect API",
    description="Indian Legal Awareness RAG API",
    version="1.2.0",
)

# Configurable CORS for secure API consumption
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Load embedding model and ChromaDB once
embedding_model, collection = load_resources()


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    history: Optional[List[Dict[str, str]]] = []


@app.get("/")
def root():
    return {
        "name": "LegalConnect API",
        "status": "running",
        "knowledge_base": "The Constitution of India, 14 Statutory Acts (BNS, BNSS, BSA, IT Act, CPA, Code on Social Security, PWDVA, RTI Act, LSA Act, HMA, POSH Act, MVA, TPA, EPA 1986), and National Government Welfare Schemes (myScheme)",
        "total_sources": 16,
    }


@app.get("/health")
def health():
    llm_status = "disconnected"
    model_ready = False
    provider = "ollama"
    model_name = "qwen3:4b"

    try:
        config = get_llm_config()
        provider = config.get("provider", "ollama")
        model_name = config.get("model", "qwen3:4b")

        if provider == "ollama":
            base_url = config.get("base_url") or OLLAMA_BASE_URL
            resp = requests.get(f"{base_url}/api/tags", timeout=1.5)
            if resp.status_code == 200:
                llm_status = "connected"
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                model_ready = any(model_name in (m or "") for m in models)
        else:
            # Hosted OpenAI-compatible provider: lightweight reachability check
            base_url = config.get("base_url", "").rstrip("/")
            api_key = config.get("api_key", "")
            headers = {"Authorization": f"Bearer {api_key}"}
            resp = requests.get(f"{base_url}/models", headers=headers, timeout=1.5)
            if resp.status_code == 200:
                llm_status = "connected"
                model_ready = True
            elif resp.status_code in (401, 403):
                llm_status = "unauthorized"
                model_ready = False
            elif resp.status_code in (404, 405):
                # Provider reached, but /models route disabled on endpoint
                llm_status = "connected"
                model_ready = True
            else:
                llm_status = "degraded"
                model_ready = False
    except ValueError:
        llm_status = "misconfigured"
        model_ready = False
    except Exception:
        llm_status = "disconnected"
        model_ready = False

    vector_db_count = 0
    vector_db_status = "unknown"
    try:
        vector_db_count = collection.count()
        vector_db_status = "connected"
    except Exception:
        vector_db_status = "error"

    overall_status = "healthy" if (llm_status == "connected" and vector_db_status == "connected") else "degraded"

    return {
        "status": overall_status,
        "provider": provider,
        "model": model_name,
        "model_ready": model_ready,
        "ollama": llm_status if provider == "ollama" else "n/a",
        "llm_status": llm_status,
        "vector_database": "ChromaDB",
        "vector_db_status": vector_db_status,
        "total_vectors": vector_db_count,
    }


def prepare_retrieval_and_prompt(question: str, history: List[Dict[str, str]]):
    # 1. Handle overly vague questions with a direct, helpful clarification (Task 5)
    vague_clarification = detect_vague_query(question)
    if vague_clarification:
        return {
            "is_confident": False,
            "answer": vague_clarification,
            "sources": [],
            "prompt": None,
            "timing": {}
        }

    # 2. Maintain conversational thread context for follow-up turns (Task 4)
    search_query = question
    if history:
        user_turns = [turn["content"].strip() for turn in history if turn.get("role") == "user" and turn.get("content")]
        if user_turns:
            root_problem = user_turns[0]
            last_user_query = user_turns[-1]
            q_lower = question.lower().strip()

            is_continuation = (
                len(question.split()) <= 12
                or any(q_lower.startswith(prefix) for prefix in [
                    "what should i", "what can i", "how do i", "can i", "what about",
                    "where do i", "who can", "what is next", "is there", "and ", "how to",
                    "which section", "what section", "what if", "if he", "if they", "if the seller",
                    "if my employer", "why"
                ])
                or any(keyword in q_lower for keyword in [
                    "first", "then", "next", "online", "procedure", "penalty",
                    "time limit", "limitation", "appeal", "compensation", "fir", "police",
                    "refuses", "refusal", "applies", "section"
                ])
            )
            if is_continuation:
                if len(user_turns) > 1 and last_user_query != root_problem:
                    search_query = f"{root_problem} {last_user_query} {question}"
                else:
                    search_query = f"{root_problem} {question}"

    retrieval_result = retrieve_legal_chunks(
        search_query,
        embedding_model,
        collection
    )

    if not retrieval_result["is_confident"]:
        return {
            "is_confident": False,
            "answer": (
                "I couldn't find sufficiently relevant statutory material in the current legal sources "
                "to answer this reliably. Could you provide a little more detail about your situation?\n\n"
                "*Disclaimer: This information is for legal awareness only and does not constitute formal legal advice. "
                "For case-specific guidance, please consult a qualified advocate or legal aid service.*"
            ),
            "sources": [],
            "prompt": None,
            "timing": retrieval_result.get("timing", {})
        }

    results = retrieval_result["reranked_results"]
    documents = [item["document"] for item in results]
    metadatas = [item["metadata"] for item in results]
    distances = [item["distance"] for item in results]

    # Deduplicate sources by (act, section, title)
    sources = []
    seen = set()
    for metadata, distance in zip(metadatas, distances):
        act = metadata.get("act")
        section = metadata.get("section", metadata.get("section_number"))
        title = metadata.get("title")
        key = (act, section, title)
        if key not in seen:
            seen.add(key)
            sources.append({
                "act": act,
                "section": section,
                "title": title,
                "source": metadata.get("source"),
                "source_url": metadata.get("source_url"),
                "distance": distance,
            })

    t_prompt_start = time.perf_counter()
    prompt = build_prompt(question, documents, metadatas, history=history)
    t_prompt_end = time.perf_counter()

    timing = dict(retrieval_result.get("timing", {}))
    timing["rag_context_construction_time_ms"] = round((t_prompt_end - t_prompt_start) * 1000, 2)

    return {
        "is_confident": True,
        "answer": None,
        "sources": sources,
        "prompt": prompt,
        "timing": timing
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    t_req_start = time.perf_counter()
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        prep = prepare_retrieval_and_prompt(question, request.history or [])
        if not prep["is_confident"]:
            t_req_end = time.perf_counter()
            return {
                "question": question,
                "answer": prep["answer"],
                "sources": [],
                "timing": {
                    "total_request_time_ms": round((t_req_end - t_req_start) * 1000, 2)
                }
            }

        allowed_sections = extract_allowed_section_numbers(prep["sources"])
        answer, gen_timing = generate_answer(
            prep["prompt"],
            return_timing=True,
            allowed_sections=allowed_sections
        )
        t_req_end = time.perf_counter()
        total_request_time_ms = round((t_req_end - t_req_start) * 1000, 2)

        init_timing = getattr(embedding_model, "_init_timing", {})

        full_timing = {
            "request_handling_time_ms": total_request_time_ms,
            "embedding_model_init_time_ms": init_timing.get("embedding_init_time_ms", 0.0),
            "chromadb_init_time_ms": init_timing.get("chroma_init_time_ms", 0.0),
            "query_embedding_generation_time_ms": prep["timing"].get("query_embedding_time_ms", 0.0),
            "chromadb_search_time_ms": prep["timing"].get("chromadb_search_time_ms", 0.0),
            "exact_metadata_lookup_time_ms": prep["timing"].get("exact_metadata_lookup_time_ms", 0.0),
            "act_title_candidate_lookup_time_ms": prep["timing"].get("act_title_lookup_time_ms", 0.0),
            "retrieval_reranking_time_ms": prep["timing"].get("reranking_time_ms", 0.0),
            "total_retrieval_time_ms": prep["timing"].get("total_retrieval_time_ms", 0.0),
            "rag_context_construction_time_ms": prep["timing"].get("rag_context_construction_time_ms", 0.0),
            # Standardized provider-agnostic telemetry
            "llm_provider": gen_timing.get("provider", "unknown"),
            "llm_request_start_time_ms": gen_timing.get("llm_request_start_ms", gen_timing.get("ollama_request_start_ms", 0.0)),
            "total_llm_generation_time_ms": gen_timing.get("total_llm_generation_time_ms", gen_timing.get("total_ollama_generation_time_ms", 0.0)),
            "ttft_applicable": False,
            "finish_reason": gen_timing.get("finish_reason", "stop"),
            "truncated": gen_timing.get("truncated", False),
            # Legacy telemetry fields (preserved for backwards compatibility)
            "ollama_request_start_time_ms": gen_timing.get("ollama_request_start_ms", 0.0),
            "time_to_first_token_ms": gen_timing.get("time_to_first_token_ms", 0.0),
            "total_ollama_generation_time_ms": gen_timing.get("total_ollama_generation_time_ms", 0.0),
            "total_request_time_ms": total_request_time_ms,
        }

        return {
            "question": question,
            "answer": answer,
            "sources": prep["sources"],
            "timing": full_timing
        }
    except requests.exceptions.ConnectionError:
        provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
        detail = (
            "LegalConnect could not connect to the local AI service. Please make sure Ollama is running."
            if provider == "ollama"
            else "LegalConnect could not connect to the hosted AI service. Please check provider reachability."
        )
        raise HTTPException(status_code=503, detail=detail)
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="The AI service timed out while generating a response. Please try again."
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="I couldn't generate a response right now. Please try again."
        )


@app.post("/ask/stream")
def ask_question_stream(request: QuestionRequest):
    t_req_start = time.perf_counter()
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        prep = prepare_retrieval_and_prompt(question, request.history or [])

        def event_stream():
            if not prep["is_confident"]:
                yield json.dumps({
                    "type": "meta",
                    "is_confident": False,
                    "sources": []
                }) + "\n"
                yield json.dumps({
                    "type": "token",
                    "token": prep["answer"]
                }) + "\n"
                return

            yield json.dumps({
                "type": "meta",
                "is_confident": True,
                "sources": prep["sources"]
            }) + "\n"

            stream_timing = {}

            def timing_cb(t_dict):
                nonlocal stream_timing
                stream_timing = t_dict

            allowed_sections = extract_allowed_section_numbers(prep["sources"])
            try:
                for token in generate_answer_stream(
                    prep["prompt"],
                    return_timing_callback=timing_cb,
                    allowed_sections=allowed_sections
                ):
                    yield json.dumps({
                        "type": "token",
                        "token": token
                    }) + "\n"
            except requests.exceptions.ConnectionError:
                provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
                detail = (
                    "LegalConnect could not connect to the local AI service. Please make sure Ollama is running."
                    if provider == "ollama"
                    else "LegalConnect could not connect to the hosted AI service. Please check provider reachability."
                )
                yield json.dumps({
                    "type": "error",
                    "error": detail
                }) + "\n"
                return
            except requests.exceptions.Timeout:
                yield json.dumps({
                    "type": "error",
                    "error": "The AI service timed out while generating a response. Please try again."
                }) + "\n"
                return
            except (PermissionError, RuntimeError, ValueError) as e:
                yield json.dumps({
                    "type": "error",
                    "error": str(e)
                }) + "\n"
                return
            except Exception:
                yield json.dumps({
                    "type": "error",
                    "error": "I couldn't generate a response right now. Please try again."
                }) + "\n"
                return

            t_req_end = time.perf_counter()
            total_request_time_ms = round((t_req_end - t_req_start) * 1000, 2)
            init_timing = getattr(embedding_model, "_init_timing", {})

            full_timing = {
                "request_handling_time_ms": total_request_time_ms,
                "embedding_model_init_time_ms": init_timing.get("embedding_init_time_ms", 0.0),
                "chromadb_init_time_ms": init_timing.get("chroma_init_time_ms", 0.0),
                "query_embedding_generation_time_ms": prep["timing"].get("query_embedding_time_ms", 0.0),
                "chromadb_search_time_ms": prep["timing"].get("chromadb_search_time_ms", 0.0),
                "exact_metadata_lookup_time_ms": prep["timing"].get("exact_metadata_lookup_time_ms", 0.0),
                "act_title_candidate_lookup_time_ms": prep["timing"].get("act_title_lookup_time_ms", 0.0),
                "retrieval_reranking_time_ms": prep["timing"].get("reranking_time_ms", 0.0),
                "total_retrieval_time_ms": prep["timing"].get("total_retrieval_time_ms", 0.0),
                "rag_context_construction_time_ms": prep["timing"].get("rag_context_construction_time_ms", 0.0),
                # Standardized provider-agnostic telemetry
                "llm_provider": stream_timing.get("provider", "unknown"),
                "llm_request_start_time_ms": stream_timing.get("llm_request_start_ms", stream_timing.get("ollama_request_start_ms", 0.0)),
                "total_llm_generation_time_ms": stream_timing.get("total_llm_generation_time_ms", stream_timing.get("total_ollama_generation_time_ms", 0.0)),
                "ttft_applicable": True,
                "finish_reason": stream_timing.get("finish_reason", "stop"),
                "truncated": stream_timing.get("truncated", False),
                # Legacy telemetry fields (preserved for backwards compatibility)
                "ollama_request_start_time_ms": stream_timing.get("ollama_request_start_ms", 0.0),
                "time_to_first_token_ms": round(prep["timing"].get("total_retrieval_time_ms", 0.0) + prep["timing"].get("rag_context_construction_time_ms", 0.0) + stream_timing.get("time_to_first_token_ms", 0.0), 2),
                "total_ollama_generation_time_ms": stream_timing.get("total_ollama_generation_time_ms", 0.0),
                "total_request_time_ms": total_request_time_ms,
            }

            yield json.dumps({
                "type": "timing",
                "timing": full_timing
            }) + "\n"

        return StreamingResponse(
            event_stream(),
            media_type="application/x-ndjson"
        )
    except requests.exceptions.ConnectionError:
        provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
        detail = (
            "LegalConnect could not connect to the local AI service. Please make sure Ollama is running."
            if provider == "ollama"
            else "LegalConnect could not connect to the hosted AI service. Please check provider reachability."
        )
        raise HTTPException(status_code=503, detail=detail)
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="The AI service timed out while generating a response. Please try again."
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="I couldn't generate a response right now. Please try again."
        )
