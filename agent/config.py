import streamlit as st

MONGO_URI    = st.secrets["MONGO_URI"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")

DB_NAME                  = "Aiagent"
KNOWLEDGE_COLLECTION     = "knowledge"
CHAT_HISTORY_COLLECTION  = "chat_history"
CRM_COLLECTION           = "crm_tickets"
USAGE_LOGS_COLLECTION    = "usage_logs"

EMBEDDING_MODEL = "BAAI/bge-m3"
TOP_K_RESULTS   = 3

# ── Pricing (per 1M tokens) ──────────────────────────
GROQ_INPUT_COST_PER_1M    = 0.59   # llama-3.3-70b-versatile input
GROQ_OUTPUT_COST_PER_1M   = 0.79   # llama-3.3-70b-versatile output
EMBEDDING_COST_PER_1M     = 0.13   # BAAI/bge-m3 via HuggingFace estimate