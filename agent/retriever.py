from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from config import MONGO_URI, DB_NAME, KNOWLEDGE_COLLECTION, EMBEDDING_MODEL
import streamlit as st

@st.cache_resource
def get_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)

@st.cache_resource
def get_mongo_client():
    return MongoClient(MONGO_URI)

def get_embedding(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()

INTENT_TYPE_MAP = {
    "price_inquiry":  ["roadmap", "markdown"],
    "policy":         ["markdown"],
    "free_content":   ["course", "markdown"],
    "recommendation": ["course", "roadmap"],
    "comparing":      ["roadmap"],
    "ready_to_buy":   ["roadmap", "markdown"],
    "browsing":       None,
}

def search_knowledge(
    query: str,
    top_k: int = 3,
    filter_type: str = None,
    intent: str = None
) -> list[dict]:
    client = get_mongo_client()
    col = client[DB_NAME][KNOWLEDGE_COLLECTION]
    query_embedding = get_embedding(query)

    vector_search = {
        "index": "default",
        "path": "embedding",
        "queryVector": query_embedding,
        "numCandidates": 80,
        "limit": top_k * 4,
    }

    if filter_type:
        vector_search["filter"] = {"type": {"$eq": filter_type}}

    pipeline = [
        {"$vectorSearch": vector_search},
        {
            "$project": {
                "text": 1,
                "type": 1,
                "name": 1,
                "source": 1,
                "metadata": 1,
                "score": {"$meta": "vectorSearchScore"},
                "_id": 0,
            }
        },
    ]

    results = list(col.aggregate(pipeline))

    allowed_types = None
    if intent and intent in INTENT_TYPE_MAP:
        allowed_types = INTENT_TYPE_MAP[intent]

    if allowed_types:
        filtered = [r for r in results if r.get("type") in allowed_types]
        if len(filtered) >= 2:
            results = filtered

    # Lower threshold to catch instructors/policies
    results = [r for r in results if r.get("score", 0) >= 0.60]

    seen = set()
    deduped = []
    for r in results:
        preview = r.get("text", "")[:80]
        if preview not in seen:
            seen.add(preview)
            deduped.append(r)

    return deduped[:top_k]

def format_context(results: list[dict]) -> str:
    if not results:
        return "No relevant information found."
    parts = []
    for r in results:
        label = f"[{r.get('type', '').upper()}] {r.get('name') or r.get('source', '')}"
        parts.append(f"{label}\n{r.get('text', '')}")
    return "\n\n---\n\n".join(parts)