from datetime import datetime
from pymongo import MongoClient
from retriever import get_mongo_client
from config import (
    DB_NAME, USAGE_LOGS_COLLECTION,
    GROQ_INPUT_COST_PER_1M, GROQ_OUTPUT_COST_PER_1M,
    EMBEDDING_COST_PER_1M
)


def calc_cost(prompt_tokens: int, completion_tokens: int, embedding_tokens: int = 0) -> dict:
    input_cost     = (prompt_tokens     / 1_000_000) * GROQ_INPUT_COST_PER_1M
    output_cost    = (completion_tokens / 1_000_000) * GROQ_OUTPUT_COST_PER_1M
    embedding_cost = (embedding_tokens  / 1_000_000) * EMBEDDING_COST_PER_1M
    total_cost     = input_cost + output_cost + embedding_cost
    return {
        "input_cost":     round(input_cost,     8),
        "output_cost":    round(output_cost,    8),
        "embedding_cost": round(embedding_cost, 8),
        "total_cost":     round(total_cost,     8),
    }


def log_usage(
    session_id:        str,
    user_id:           str,
    message_id:        str,
    prompt_tokens:     int,
    completion_tokens: int,
    embedding_tokens:  int,
    latency_ms:        float,
    tool_calls:        list,
    sources:           list,
    user_prompt:       str,
    final_response:    str,
    intent:            str = "",
):
    costs = calc_cost(prompt_tokens, completion_tokens, embedding_tokens)
    doc = {
        "session_id":        session_id,
        "user_id":           user_id,
        "message_id":        message_id,
        "provider":          "Groq",
        "model":             "llama-3.3-70b-versatile",
        "prompt_tokens":     prompt_tokens,
        "completion_tokens": completion_tokens,
        "embedding_tokens":  embedding_tokens,
        "input_cost":        costs["input_cost"],
        "output_cost":       costs["output_cost"],
        "embedding_cost":    costs["embedding_cost"],
        "total_cost":        costs["total_cost"],
        "latency_ms":        round(latency_ms, 2),
        "tool_calls":        tool_calls,
        "sources":           sources,
        "user_prompt":       user_prompt,
        "final_response":    final_response,
        "intent":            intent,
        "timestamp":         datetime.utcnow().isoformat(),
    }
    client = get_mongo_client()
    client[DB_NAME][USAGE_LOGS_COLLECTION].insert_one(doc)


# ── Aggregation helpers ──────────────────────────────

def get_all_users_cost() -> list[dict]:
    client = get_mongo_client()
    col    = client[DB_NAME][USAGE_LOGS_COLLECTION]
    pipeline = [
        {"$group": {
            "_id":               "$user_id",
            "total_cost":        {"$sum": "$total_cost"},
            "total_messages":    {"$sum": 1},
            "total_sessions":    {"$addToSet": "$session_id"},
            "prompt_tokens":     {"$sum": "$prompt_tokens"},
            "completion_tokens": {"$sum": "$completion_tokens"},
        }},
        {"$project": {
            "user_id":           "$_id",
            "total_cost":        1,
            "total_messages":    1,
            "total_sessions":    {"$size": "$total_sessions"},
            "prompt_tokens":     1,
            "completion_tokens": 1,
        }},
        {"$sort": {"total_cost": -1}},
    ]
    return list(col.aggregate(pipeline))


def get_user_conversations_cost(user_id: str) -> list[dict]:
    client = get_mongo_client()
    col    = client[DB_NAME][USAGE_LOGS_COLLECTION]
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id":            "$session_id",
            "total_cost":     {"$sum": "$total_cost"},
            "total_messages": {"$sum": 1},
            "last_time":      {"$max": "$timestamp"},
        }},
        {"$sort": {"last_time": -1}},
    ]
    return list(col.aggregate(pipeline))


def get_conversation_messages_cost(session_id: str) -> list[dict]:
    client = get_mongo_client()
    col    = client[DB_NAME][USAGE_LOGS_COLLECTION]
    return list(col.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1))


def get_total_stats() -> dict:
    client = get_mongo_client()
    col    = client[DB_NAME][USAGE_LOGS_COLLECTION]
    pipeline = [
        {"$group": {
            "_id":               None,
            "total_cost":        {"$sum": "$total_cost"},
            "total_messages":    {"$sum": 1},
            "prompt_tokens":     {"$sum": "$prompt_tokens"},
            "completion_tokens": {"$sum": "$completion_tokens"},
            "embedding_tokens":  {"$sum": "$embedding_tokens"},
            "avg_latency":       {"$avg": "$latency_ms"},
        }}
    ]
    result = list(col.aggregate(pipeline))
    return result[0] if result else {}