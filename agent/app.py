import streamlit as st
import uuid
import re
import base64
from pathlib import Path
from agent import run_agent
from crm import save_crm_ticket, update_crm_ticket, get_all_tickets, save_chat_message, load_chat_history, get_all_sessions
from tools import detect_language

st.set_page_config(
    page_title="Kayfa AI Sales Agent",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
.chat-msg {
    color: #1a1a1a !important;
    font-size: 15px;
    line-height: 1.7;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 6px 0;
    max-width: 80%;
    clear: both;
}
.chat-msg-user-ar {
    background: #DCF8C6;
    float: right;
    text-align: right;
    direction: rtl;
}
.chat-msg-user-en {
    background: #E3F2FD;
    float: left;
    text-align: left;
    direction: ltr;
}
.chat-msg-assistant-ar {
    background: #FFFFFF;
    border: 1px solid #e0e0e0;
    float: right;
    text-align: right;
    direction: rtl;
}
.chat-msg-assistant-en {
    background: #FFFFFF;
    border: 1px solid #e0e0e0;
    float: left;
    text-align: left;
    direction: ltr;
}
.clearfix { clear: both; }
.center-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}
.session-btn {
    font-size: 12px !important;
    text-align: left !important;
}
</style>
""", unsafe_allow_html=True)

BASE_DIR  = Path(__file__).parent
LOGO_PATH = BASE_DIR / "logo" / "logo.png"


def get_logo_base64() -> str:
    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""


def show_logo_sidebar(width: int = 100):
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=width)


def show_logo_with_title(title: str, width: int = 100):
    b64 = get_logo_base64()
    if b64:
        st.markdown(f"""
        <div class="center-block" style="margin-bottom:16px;">
            <img src="data:image/png;base64,{b64}" width="{width}" style="display:block;margin:0 auto;"/>
            <h2 style="margin-top:8px;">{title}</h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"<h2 style='text-align:center'>🎓 {title}</h2>", unsafe_allow_html=True)


def login_page():
    b64 = get_logo_base64()
    st.markdown(f"""
    <div class="center-block" style="margin-top:60px; margin-bottom:20px;">
        {"<img src='data:image/png;base64," + b64 + "' width='180' style='display:block;margin:0 auto;'/>" if b64 else "🎓"}
        <h2 style="margin-top:12px;">Kayfa AI Agent</h2>
        <p style="color:gray;">Please login to continue</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Incorrect password")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_page()
    st.stop()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history(st.session_state.session_id)
if "lead_status" not in st.session_state:
    st.session_state.lead_status = "cold"
if "intent" not in st.session_state:
    st.session_state.intent = "browsing"
if "collected_lead" not in st.session_state:
    st.session_state.collected_lead = False
if "lead_data_buffer" not in st.session_state:
    st.session_state.lead_data_buffer = {}
if "crm_ticket_id" not in st.session_state:
    st.session_state.crm_ticket_id = None
if "conversation_language" not in st.session_state:
    st.session_state.conversation_language = None


def parse_lead_signal(response: str) -> dict | None:
    match = re.search(r'\[LEAD_COLLECTED: ([^\]]+)\]', response)
    if not match:
        return None
    data = {}
    for part in match.group(1).split(","):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            data[k.strip()] = v.strip()
    return data


def clean_response(response: str) -> str:
    return re.sub(r'\[LEAD_COLLECTED: [^\]]+\]', '', response).strip()


def render_message(role: str, content: str):
    if role == "assistant" and st.session_state.conversation_language:
        is_arabic = st.session_state.conversation_language == "arabic"
    else:
        is_arabic = detect_language(content) == "arabic"

    if role == "user":
        css = "chat-msg chat-msg-user-ar" if is_arabic else "chat-msg chat-msg-user-en"
    else:
        css = "chat-msg chat-msg-assistant-ar" if is_arabic else "chat-msg chat-msg-assistant-en"

    direction = "rtl" if is_arabic else "ltr"
    st.markdown(f"""
    <div class="{css}" style="direction:{direction}">{content}</div>
    <div class="clearfix"></div>
    """, unsafe_allow_html=True)


def flush_crm(language: str):
    buf = st.session_state.lead_data_buffer
    if not buf:
        return
    summary = " | ".join([
        f"{m['role']}: {m['content'][:80]}"
        for m in st.session_state.messages[-8:]
    ])
    ticket = {
        "session_id":           st.session_state.session_id,
        "name":                 buf.get("name", "unknown"),
        "phone":                buf.get("phone", "unknown"),
        "email":                buf.get("email", "unknown"),
        "city":                 buf.get("city", "unknown"),
        "interest":             buf.get("interest", "unknown"),
        "level":                buf.get("level", "unknown"),
        "lead_status":          st.session_state.lead_status,
        "conversation_summary": summary,
        "next_action":          "Follow up within 24 hours via WhatsApp",
        "language":             language,
    }
    if st.session_state.crm_ticket_id:
        update_crm_ticket(st.session_state.crm_ticket_id, ticket)
    else:
        ticket_id = save_crm_ticket(ticket)
        st.session_state.crm_ticket_id = ticket_id


def load_session(session_id: str):
    """Load a past session into the current state."""
    if st.session_state.lead_data_buffer:
        flush_crm(st.session_state.conversation_language or "arabic")
    st.session_state.session_id            = session_id
    st.session_state.messages              = load_chat_history(session_id)
    st.session_state.lead_status           = "cold"
    st.session_state.intent                = "browsing"
    st.session_state.collected_lead        = False
    st.session_state.lead_data_buffer      = {}
    st.session_state.crm_ticket_id         = None
    st.session_state.conversation_language = None
    st.rerun()


# ── Sidebar ────────────────────────────────────────────
with st.sidebar:
    show_logo_sidebar(width=100)
    st.markdown("### Kayfa AI Agent")
    st.divider()

    # ── Past Chats ──────────────────────────────────────
    st.markdown("#### 💬 Chats")

    if st.button("🔄 New Chat", use_container_width=True):
        if st.session_state.lead_data_buffer:
            flush_crm(st.session_state.conversation_language or "arabic")
        st.session_state.messages              = []
        st.session_state.session_id            = str(uuid.uuid4())
        st.session_state.lead_status           = "cold"
        st.session_state.intent                = "browsing"
        st.session_state.collected_lead        = False
        st.session_state.lead_data_buffer      = {}
        st.session_state.crm_ticket_id         = None
        st.session_state.conversation_language = None
        st.rerun()

    sessions = get_all_sessions()
    for s in sessions:
        preview = s["first_msg"][:35] + "..." if len(s["first_msg"]) > 35 else s["first_msg"]
        is_active = s["_id"] == st.session_state.session_id
        icon = "▶ " if is_active else ""
        label = f"{icon}{preview}"
        btn_key = f"sess_{s['_id']}"
        if st.button(label, key=btn_key, use_container_width=True):
            if not is_active:
                load_session(s["_id"])

    st.divider()

    page = st.radio("Navigation", ["💬 Chat", "📋 CRM Tickets"], label_visibility="collapsed")
    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        if st.session_state.lead_data_buffer:
            flush_crm(st.session_state.conversation_language or "arabic")
        st.session_state.logged_in = False
        st.rerun()


# ══════════════════════════════════════════════════════
# PAGE 1: CHAT
# ══════════════════════════════════════════════════════
if page == "💬 Chat":
    show_logo_with_title("Kayfa AI Agent", width=100)

    if not st.session_state.messages:
        st.markdown("#### How can I help you today?")
        suggestions = [
            "I want to start learning AI",
            "What is the Data Science track?",
            "How much does the SOC diploma cost?",
            "Is there any free content?",
            "Compare Frontend vs Fullstack",
        ]
        cols = st.columns(len(suggestions))
        for i, col in enumerate(cols):
            with col:
                if st.button(suggestions[i], use_container_width=True, key=f"sug_{i}"):
                    st.session_state.pending_message = suggestions[i]
                    st.rerun()

    with st.container():
        for msg in st.session_state.messages:
            render_message(msg["role"], msg["content"])

    if "pending_message" in st.session_state:
        user_input = st.session_state.pop("pending_message")
    else:
        user_input = None

    typed = st.chat_input("Ask about Kayfa courses, diplomas, prices...")
    if typed:
        user_input = typed

    if user_input:
        detected_lang = detect_language(user_input)
        if st.session_state.conversation_language is None:
            st.session_state.conversation_language = detected_lang

        language = st.session_state.conversation_language

        st.session_state.messages.append({"role": "user", "content": user_input})
        save_chat_message(st.session_state.session_id, "user", user_input)

        with st.spinner("Kayfa Agent is typing..."):
            response, _, lead_temp, intent = run_agent(
                user_input,
                st.session_state.messages[:-1]
            )

        if lead_temp == "hot" or st.session_state.lead_status == "hot":
            st.session_state.lead_status = "hot"
        elif lead_temp == "warm" and st.session_state.lead_status == "cold":
            st.session_state.lead_status = "warm"
        st.session_state.intent = intent

        lead_data  = parse_lead_signal(response)
        clean_resp = clean_response(response)

        if lead_data:
            for k, v in lead_data.items():
                if v and v.lower() != "unknown":
                    st.session_state.lead_data_buffer[k] = v

        buf = st.session_state.lead_data_buffer

        if "interest" not in buf and intent in ["recommendation", "ready_to_buy", "price_inquiry"]:
            buf["interest"] = intent

        has_any = (
            buf.get("name", "unknown") != "unknown" or
            buf.get("phone", "unknown") != "unknown"
        )
        if has_any:
            flush_crm(language)

        if (
            buf.get("name", "unknown") != "unknown" and
            buf.get("phone", "unknown") != "unknown" and
            buf.get("interest", "unknown") != "unknown" and
            not st.session_state.collected_lead
        ):
            st.session_state.collected_lead = True
            st.session_state.lead_status    = "hot"
            st.success("✅ Lead captured and saved to CRM!")

        st.session_state.messages.append({"role": "assistant", "content": clean_resp})
        save_chat_message(st.session_state.session_id, "assistant", clean_resp)
        st.rerun()


# ══════════════════════════════════════════════════════
# PAGE 2: CRM
# ══════════════════════════════════════════════════════
elif page == "📋 CRM Tickets":
    show_logo_with_title("CRM Tickets Dashboard", width=80)

    tickets = get_all_tickets()

    if not tickets:
        st.info("No leads captured yet.")
    else:
        hot  = [t for t in tickets if t.get("lead_status") == "hot"]
        warm = [t for t in tickets if t.get("lead_status") == "warm"]
        cold = [t for t in tickets if t.get("lead_status") == "cold"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Leads", len(tickets))
        c2.metric("🔴 Hot",      len(hot))
        c3.metric("🟡 Warm",     len(warm))
        c4.metric("🔵 Cold",     len(cold))

        st.divider()

        col_f, col_s = st.columns(2)
        with col_f:
            filter_status = st.selectbox("Filter by status", ["All", "hot", "warm", "cold"])
        with col_s:
            search_term = st.text_input("Search by name or interest")

        filtered = tickets
        if filter_status != "All":
            filtered = [t for t in filtered if t.get("lead_status") == filter_status]
        if search_term:
            filtered = [
                t for t in filtered
                if search_term.lower() in t.get("name", "").lower()
                or search_term.lower() in t.get("interest", "").lower()
            ]

        st.markdown(f"Showing **{len(filtered)}** tickets")
        st.divider()

        icons = {"hot": "🔴", "warm": "🟡", "cold": "🔵"}
        for t in filtered:
            icon  = icons.get(t.get("lead_status"), "⚪")
            label = f"{icon} {t.get('name', 'Unknown')} — {t.get('interest', '')} | {str(t.get('created_at', ''))[:10]}"
            with st.expander(label):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Name:** {t.get('name', '-')}")
                    st.markdown(f"**Phone:** {t.get('phone', '-')}")
                    st.markdown(f"**Email:** {t.get('email', '-')}")
                    st.markdown(f"**City:** {t.get('city', '-')}")
                with c2:
                    st.markdown(f"**Interest:** {t.get('interest', '-')}")
                    st.markdown(f"**Level:** {t.get('level', '-')}")
                    st.markdown(f"**Lead Status:** {t.get('lead_status', '-').capitalize()}")
                    st.markdown(f"**Language:** {t.get('language', '-')}")
                st.markdown(f"**Summary:** {t.get('conversation_summary', '-')}")
                st.markdown(f"**Next Action:** {t.get('next_action', '-')}")
                st.markdown(f"**Created:** {t.get('created_at', '-')}")
                st.markdown(f"**Updated:** {t.get('updated_at', '-')}")
