from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scripts.legal_chat import (
    load_resources,
    build_prompt,
    generate_answer,
)

from scripts.retrieval_utils import retrieve_legal_chunks


app = FastAPI(
    title="LegalConnect API",
    description="Indian Legal Awareness RAG API",
    version="1.0.0",
)


# Load embedding model and ChromaDB once
embedding_model, collection = load_resources()


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "name": "LegalConnect API",
        "status": "running",
        "dataset": "Bharatiya Nyaya Sanhita, 2023",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model": "qwen3:4b",
        "vector_database": "ChromaDB",
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        # Run the existing Stage 6 retrieval pipeline
        retrieval_result = retrieve_legal_chunks(
            question,
            embedding_model,
            collection
        )

        # Check confidence
        if not retrieval_result["is_confident"]:
            return {
                "question": question,
                "answer": (
                    "I could not find sufficient information "
                    "in the retrieved legal sources to answer "
                    "this question."
                ),
                "sources": []
            }

        # Get final reranked chunks
        results = retrieval_result["reranked_results"]

        documents = [
            item["document"]
            for item in results
        ]

        metadatas = [
            item["metadata"]
            for item in results
        ]

        distances = [
            item["distance"]
            for item in results
        ]

        # Build grounded prompt
        prompt = build_prompt(
            question,
            documents,
            metadatas
        )

        # Generate answer using Qwen3
        answer = generate_answer(prompt)

        # Prepare sources
        sources = []

        for metadata, distance in zip(
            metadatas,
            distances
        ):
            sources.append({
                "act": metadata.get("act"),
                "section": metadata.get("section"),
                "title": metadata.get("title"),
                "source": metadata.get("source"),
                "source_url": metadata.get("source_url"),
                "distance": distance,
            })

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
