from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from config import MONGO_URI, DB_NAME, CRM_COLLECTION
from retriever import get_mongo_client
from groq import Groq
from config import GROQ_API_KEY

groq_client = Groq(api_key=GROQ_API_KEY)


def generate_summary(messages: list[dict], language: str) -> str:
    if not messages:
        return "No conversation."
    history = "\n".join([
        f"{'User' if m['role'] == 'user' else 'Agent'}: {m['content']}"
        for m in messages[-12:]
    ])
    prompt = f"""Summarize this sales conversation in 2-3 sentences.
Mention: what the user is interested in, their level, and their decision status.
Reply in {'Arabic' if language == 'arabic' else 'English'}.
Conversation:
{history}"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def save_crm_ticket(ticket: dict) -> str:
    client = get_mongo_client()
    col = client[DB_NAME][CRM_COLLECTION]
    ticket["created_at"] = datetime.utcnow().isoformat()
    ticket["updated_at"] = datetime.utcnow().isoformat()
    result = col.insert_one(ticket)
    return str(result.inserted_id)


def update_crm_ticket(ticket_id: str, ticket: dict) -> None:
    client = get_mongo_client()
    col = client[DB_NAME][CRM_COLLECTION]
    ticket["updated_at"] = datetime.utcnow().isoformat()
    col.update_one(
        {"_id": ObjectId(ticket_id)},
        {"$set": ticket}
    )


def get_all_tickets() -> list[dict]:
    client = get_mongo_client()
    col = client[DB_NAME][CRM_COLLECTION]
    tickets = list(col.find({}, {"_id": 0}).sort("created_at", -1))
    return tickets


def save_chat_message(session_id: str, role: str, content: str):
    client = get_mongo_client()
    col = client[DB_NAME]["chat_history"]
    col.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })


def load_chat_history(session_id: str) -> list[dict]:
    client = get_mongo_client()
    col = client[DB_NAME]["chat_history"]
    messages = list(col.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "content": 1}
    ).sort("timestamp", 1))
    return messages


def delete_session(session_id: str) -> None:
    client = get_mongo_client()
    client[DB_NAME]["chat_history"].delete_many({"session_id": session_id})
    client[DB_NAME][CRM_COLLECTION].delete_many({"session_id": session_id})


def get_all_sessions() -> list[dict]:
    client = get_mongo_client()
    col = client[DB_NAME]["chat_history"]
    pipeline = [
        {"$sort": {"timestamp": 1}},
        {"$group": {
            "_id": "$session_id",
            "first_msg": {"$first": "$content"},
            "first_role": {"$first": "$role"},
            "last_time": {"$last": "$timestamp"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"last_time": -1}},
        {"$limit": 30}
    ]
    return list(col.aggregate(pipeline))