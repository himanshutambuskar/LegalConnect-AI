import argparse
import logging
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# =========================
# Configuration
# =========================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHROMA_PATH = PROJECT_ROOT / "vectorstore" / "chroma"

COLLECTION_NAME = "legal_bns_2023"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

DEFAULT_TOP_K = 5


# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


# =========================
# Load resources
# =========================

def load_resources():
    if not CHROMA_PATH.exists():
        raise FileNotFoundError(
            f"ChromaDB directory not found: {CHROMA_PATH}"
        )

    logging.info(
        f"Loading embedding model: {EMBEDDING_MODEL}"
    )

    model = SentenceTransformer(EMBEDDING_MODEL)

    logging.info(
        f"Opening ChromaDB: {CHROMA_PATH}"
    )

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    try:
        collection = client.get_collection(
            name=COLLECTION_NAME
        )
    except Exception as e:
        raise RuntimeError(
            f"ChromaDB collection '{COLLECTION_NAME}' "
            f"was not found.\nError: {e}"
        )

    return model, collection


# =========================
# Retrieve chunks
# =========================

def retrieve(question, model, collection, top_k=DEFAULT_TOP_K):

    if not question.strip():
        print("Please enter a question.")
        return

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # Convert question into embedding
    query_embedding = model.encode(
        question,
        normalize_embeddings=True
    ).tolist()

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]

    if not documents:
        print("\nNo relevant legal chunks were found.\n")
        return

    print("\n")
    print("=" * 70)
    print("LEGAL CHUNK RETRIEVAL")
    print("=" * 70)

    print(f"\nQuestion:\n{question}")

    for i, document in enumerate(documents):

        metadata = metadatas[i] if i < len(metadatas) else {}
        distance = distances[i] if i < len(distances) else None
        chunk_id = ids[i] if i < len(ids) else "Unknown"

        print("\n")
        print("-" * 70)
        print(f"RESULT {i + 1}")
        print("-" * 70)

        print(f"Chunk ID: {chunk_id}")

        print(
            f"Act: "
            f"{metadata.get('act', 'N/A')}"
        )

        print(
            f"Category: "
            f"{metadata.get('category', 'N/A')}"
        )

        print(
            f"Section: "
            f"{metadata.get('section', 'N/A')}"
        )

        print(
            f"Section Number: "
            f"{metadata.get('section_number', 'N/A')}"
        )

        print(
            f"Title: "
            f"{metadata.get('title', 'N/A')}"
        )

        print(
            f"Source: "
            f"{metadata.get('source', 'N/A')}"
        )

        print(
            f"Source URL: "
            f"{metadata.get('source_url', 'N/A')}"
        )

        print(
            f"Distance: "
            f"{distance if distance is not None else 'N/A'}"
        )

        print("\nContent:")
        print(document)

    print("\n")
    print("=" * 70)
    print(f"Retrieved {len(documents)} legal chunks.")
    print("=" * 70)
    print()


# =========================
# Interactive mode
# =========================

def interactive_mode(model, collection, top_k):

    print("\n")
    print("=" * 70)
    print("LEGALCONNECT — LEGAL CHUNK RETRIEVER")
    print("=" * 70)

    print("\nDataset: Bharatiya Nyaya Sanhita, 2023")
    print(f"Top K: {top_k}")

    print("\nAsk a legal question.")
    print("Type 'exit' or 'quit' to stop.")

    while True:

        try:
            question = input("\nLegalConnect > ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if question.lower() in {"exit", "quit"}:
            print("Exiting.")
            break

        if not question:
            continue

        try:
            retrieve(
                question,
                model,
                collection,
                top_k
            )

        except Exception as e:
            print(f"\nRetrieval error: {e}\n")


# =========================
# Main
# =========================

def main():

    parser = argparse.ArgumentParser(
        description="Retrieve relevant legal chunks from ChromaDB."
    )

    parser.add_argument(
        "--query",
        type=str,
        help="Legal question to search."
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="Number of chunks to retrieve."
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive question mode."
    )

    args = parser.parse_args()

    try:
        model, collection = load_resources()

        if args.interactive:
            interactive_mode(
                model,
                collection,
                args.top_k
            )

        elif args.query:
            retrieve(
                args.query,
                model,
                collection,
                args.top_k
            )

        else:
            interactive_mode(
                model,
                collection,
                args.top_k
            )

    except Exception as e:
        logging.error(str(e))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
