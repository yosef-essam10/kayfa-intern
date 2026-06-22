import streamlit as st

MONGO_URI = st.secrets["MONGO_URI"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
APP_PASSWORD = st.secrets["APP_PASSWORD"]

DB_NAME = "Aiagent"
KNOWLEDGE_COLLECTION = "knowledge"
CHAT_HISTORY_COLLECTION = "chat_history"
CRM_COLLECTION = "crm_tickets"

EMBEDDING_MODEL = "BAAI/bge-m3"
TOP_K_RESULTS = 3