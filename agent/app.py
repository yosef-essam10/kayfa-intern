import streamlit as st
import uuid
import re
import base64
from pathlib import Path
from agent import run_agent
from crm import (
    save_crm_ticket, update_crm_ticket, get_all_tickets,
    save_chat_message, load_chat_history, get_all_sessions,
    generate_summary, delete_session
)
from monitor import log_usage
from tools import detect_language, validate_phone, validate_email
from config import ADMIN_PASSWORD
from admin import show_admin_dashboard

st.set_page_config(
    page_title="Kayfa AI Sales Agent",
    page_icon="🎓",
    layout="wide"
)

st.markdown("""
<style>
.msg-user-ar {
    background: #DCF8C6;
    color: #1a1a1a;
    padding: 10px 14px;
    border-radius: 12px 12px 2px 12px;
    margin: 4px 0 4px auto;
    max-width: 75%;
    text-align: right;
    direction: rtl;
    display: block;
    width: fit-content;
    margin-left: auto;
}
.msg-user-en {
    background: #E3F2FD;
    color: #1a1a1a;
    padding: 10px 14px;
    border-radius: 12px 12px 12px 2px;
    margin: 4px auto 4px 0;
    max-width: 75%;
    text-align: left;
    direction: ltr;
    display: block;
    width: fit-content;
}
.msg-assistant-ar {
    background: #FFFFFF;
    color: #1a1a1a;
    border: 1px solid #e0e0e0;
    padding: 10px 14px;
    border-radius: 12px 12px 2px 12px;
    max-width: 75%;
    text-align: right;
    direction: rtl;
    display: block;
    width: fit-content;
}
.msg-assistant-en {
    background: #FFFFFF;
    color: #1a1a1a;
    border: 1px solid #e0e0e0;
    padding: 10px 14px;
    border-radius: 12px 12px 12px 2px;
    max-width: 75%;
    text-align: left;
    direction: ltr;
    display: block;
    width: fit-content;
}
.clearfix { clear: both; }
.center-block {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
}
</style>

<script>
const observer = new MutationObserver(() => {
    const textarea = document.querySelector('[data-testid="stChatInput"] textarea');
    if (textarea) {
        textarea.addEventListener('input', function() {
            const text = this.value;
            if (!text) return;
            const arabicChars = (text.match(/[\u0600-\u06FF]/g) || []).length;
            const isArabic = arabicChars / text.length > 0.3;
            this.style.direction = isArabic ? 'rtl' : 'ltr';
            this.style.textAlign = isArabic ? 'right' : 'left';
        });
        observer.disconnect();
    }
});
observer.observe(document.body, { childList: true, subtree: true });
</script>
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
        if "login_tab" not in st.session_state:
            st.session_state.login_tab = "User"

        tab_col1, tab_col2 = st.columns(2)
        with tab_col1:
            if st.button("👤 User", use_container_width=True,
                         type="primary" if st.session_state.login_tab == "User" else "secondary"):
                st.session_state.login_tab = "User"
                st.rerun()
        with tab_col2:
            if st.button("🛡️ Admin", use_container_width=True,
                         type="primary" if st.session_state.login_tab == "Admin" else "secondary"):
                st.session_state.login_tab = "Admin"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True):
            if st.session_state.login_tab == "Admin" and password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.is_admin  = True
                st.session_state.user_id   = "admin"
                st.rerun()
            elif st.session_state.login_tab == "User" and password == st.secrets["APP_PASSWORD"]:
                st.session_state.logged_in = True
                st.session_state.is_admin  = False
                st.session_state.user_id   = str(uuid.uuid4())
                st.rerun()
            else:
                st.error("Incorrect password")


# ── Session State ────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ── Admin Route ──────────────────────────────────────
if st.session_state.is_admin:
    with st.sidebar:
        show_logo_sidebar(width=100)
        st.markdown("### 🛡️ Admin Panel")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.is_admin  = False
            st.rerun()
    show_admin_dashboard()
    st.stop()

# ── User Session State ───────────────────────────────
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
if "current_page" not in st.session_state:
    st.session_state.current_page = "chat"


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


def extract_info_from_message(message: str, buf: dict):
    """Extract name, phone, email, level, city from user message and update buffer."""

    # Name — Arabic
    ar_name = re.search(
        r'(?:اسمي|أنا|انا)\s+([\u0600-\u06FFa-zA-Z][^\n،,]{1,30}?)(?:\s+(?:و|ك|عايز|محتاج|من|في)|$)',
        message, re.IGNORECASE
    )
    # Name — English
    en_name = re.search(
        r'(?:my name is|i am|i\'m|name is)\s+([A-Za-z][a-zA-Z\s]{1,40}?)(?:\s+(?:and|i|from)|[,.]|$)',
        message, re.IGNORECASE
    )
    if buf.get("name", "unknown") in ("unknown", ""):
        if ar_name:
            name = ar_name.group(1).strip().rstrip("،,. ")
            if len(name) > 1:
                buf["name"] = name
        elif en_name:
            name = en_name.group(1).strip().rstrip(".,")
            if len(name) > 1:
                buf["name"] = name

    # Phone
    if buf.get("phone", "unknown") in ("unknown", ""):
        phone = re.search(r'\b(01[0125]\d{8})\b', message)
        if phone:
            buf["phone"] = phone.group(1)

    # Email
    if buf.get("email", "unknown") in ("unknown", ""):
        email = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b', message)
        if email:
            buf["email"] = email.group(0)

    # Level
    if buf.get("level", "unknown") in ("unknown", ""):
        msg_l = message.lower()
        if any(w in msg_l for w in ["مبتدئ", "مبتدا", "beginner", "من الصفر", "from scratch", "zero"]):
            buf["level"] = "beginner"
        elif any(w in msg_l for w in ["متوسط", "intermediate", "شوية خبرة", "some experience"]):
            buf["level"] = "intermediate"
        elif any(w in msg_l for w in ["متقدم", "advanced", "خبير", "expert"]):
            buf["level"] = "advanced"

    # City — common Egyptian cities
    if buf.get("city", "unknown") in ("unknown", ""):
        cities = [
            "cairo", "القاهرة", "giza", "الجيزة", "alexandria", "الإسكندرية", "اسكندرية",
            "mansoura", "المنصورة", "tanta", "طنطا", "aswan", "أسوان", "luxor", "الأقصر",
            "suez", "السويس", "ismailia", "الإسماعيلية", "zagazig", "الزقازيق",
            "qalyubia", "القليوبية", "القليوبيه", "banha", "بنها", "shubra", "شبرا",
            "helwan", "حلوان", "6th october", "السادس من أكتوبر", "nasr city", "مدينة نصر",
            "maadi", "المعادي", "dokki", "الدقي", "zamalek", "الزمالك",
            "port said", "بورسعيد", "damietta", "دمياط", "fayoum", "الفيوم",
            "minya", "المنيا", "assiut", "أسيوط", "sohag", "سوهاج", "qena", "قنا",
            "hurghada", "الغردقة", "sharm", "شرم الشيخ", "obour", "العبور",
            "shorouk", "الشروق", "new cairo", "القاهرة الجديدة", "10th ramadan", "العاشر من رمضان",
        ]
        msg_l = message.lower()
        for city in cities:
            if city in msg_l:
                buf["city"] = city
                break


def is_lead_valid(buf: dict) -> bool:
    has_name     = buf.get("name",     "unknown") not in ("unknown", "")
    has_level    = buf.get("level",    "unknown") not in ("unknown", "")
    has_city     = buf.get("city",     "unknown") not in ("unknown", "")
    has_interest = buf.get("interest", "unknown") not in ("unknown", "")
    has_phone    = buf.get("phone",    "unknown") not in ("unknown", "")
    has_email    = buf.get("email",    "unknown") not in ("unknown", "")
    has_contact  = has_phone or has_email

    if has_phone and not validate_phone(buf["phone"]):
        return False
    if has_email and not validate_email(buf["email"]):
        return False

    return has_name and has_level and has_contact and has_city and has_interest


def render_message(role: str, content: str):
    is_arabic = detect_language(content) == "arabic"
    if role == "user":
        css = "msg-user-ar" if is_arabic else "msg-user-en"
        st.markdown(
            f'<div class="{css}">{content}</div><div class="clearfix"></div>',
            unsafe_allow_html=True
        )
    else:
        css = "msg-assistant-ar" if is_arabic else "msg-assistant-en"
        b64 = get_logo_base64()
        if b64:
            avatar = f'<img src="data:image/png;base64,{b64}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;flex-shrink:0;"/>'
        else:
            avatar = '<div style="width:32px;height:32px;border-radius:50%;background:#3b3f8c;display:flex;align-items:center;justify-content:center;color:white;font-size:14px;flex-shrink:0;">K</div>'
        flex_dir = "row-reverse" if is_arabic else "row"
        st.markdown(f'''
        <div style="display:flex;flex-direction:{flex_dir};align-items:flex-end;gap:8px;margin:4px 0;">
            {avatar}
            <div class="{css}" style="margin:0;">{content}</div>
        </div>
        <div class="clearfix"></div>
        ''', unsafe_allow_html=True)


def flush_crm(language: str):
    buf = st.session_state.lead_data_buffer
    if not buf:
        return
    summary = generate_summary(st.session_state.messages, language)
    ticket = {
        "session_id":           st.session_state.session_id,
        "name":                 buf.get("name",     "unknown"),
        "phone":                buf.get("phone",    "unknown"),
        "email":                buf.get("email",    "unknown"),
        "city":                 buf.get("city",     "unknown"),
        "interest":             buf.get("interest", "unknown"),
        "level":                buf.get("level",    "unknown"),
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


def get_session_label(session: dict) -> str:
    preview  = session["first_msg"][:25].strip()
    if len(session["first_msg"]) > 25:
        preview += "..."
    time_str = session["last_time"][11:16] if len(session["last_time"]) > 16 else ""
    date_str = session["last_time"][:10]   if len(session["last_time"]) > 10 else ""
    return f"{preview} · {date_str} {time_str}"


def load_session(session_id: str):
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


def reset_to_new_chat():
    st.session_state.messages              = []
    st.session_state.session_id            = str(uuid.uuid4())
    st.session_state.lead_status           = "cold"
    st.session_state.intent                = "browsing"
    st.session_state.collected_lead        = False
    st.session_state.lead_data_buffer      = {}
    st.session_state.crm_ticket_id         = None
    st.session_state.conversation_language = None
    st.session_state.current_page          = "chat"


# ── Sidebar ──────────────────────────────────────────
with st.sidebar:
    show_logo_sidebar(width=100)
    st.markdown("### Kayfa AI Agent")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 Chat", use_container_width=True,
                     type="primary" if st.session_state.current_page == "chat" else "secondary"):
            st.session_state.current_page = "chat"
            st.rerun()
    with col2:
        if st.button("📋 CRM", use_container_width=True,
                     type="primary" if st.session_state.current_page == "crm" else "secondary"):
            st.session_state.current_page = "crm"
            st.rerun()

    st.divider()

    if st.button("🔄 New Chat", use_container_width=True):
        if st.session_state.lead_data_buffer:
            flush_crm(st.session_state.conversation_language or "arabic")
        reset_to_new_chat()
        st.rerun()

    st.markdown("#### 💬 Past Chats")
    sessions = get_all_sessions()
    for s in sessions:
        label     = get_session_label(s)
        is_active = s["_id"] == st.session_state.session_id
        icon      = "▶ " if is_active else ""

        col_chat, col_del = st.columns([5, 1])
        with col_chat:
            if st.button(f"{icon}{label}", key=f"sess_{s['_id']}", use_container_width=True):
                if not is_active:
                    load_session(s["_id"])
        with col_del:
            if st.button("🗑", key=f"del_{s['_id']}"):
                delete_session(s["_id"])
                if is_active:
                    reset_to_new_chat()
                st.rerun()

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        if st.session_state.lead_data_buffer:
            flush_crm(st.session_state.conversation_language or "arabic")
        st.session_state.logged_in = False
        st.rerun()


# ══════════════════════════════════════════════════════
# PAGE 1: CHAT
# ══════════════════════════════════════════════════════
if st.session_state.current_page == "chat":
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
        language = detect_language(user_input)
        st.session_state.conversation_language = language

        buf = st.session_state.lead_data_buffer

        # ── Extract info from user message directly ──
        extract_info_from_message(user_input, buf)

        st.session_state.messages.append({"role": "user", "content": user_input})
        save_chat_message(st.session_state.session_id, "user", user_input)

        with st.spinner("Kayfa Agent is typing..."):
            result = run_agent(user_input, st.session_state.messages[:-1])

        content    = result["content"]
        lead_temp  = result["lead_temp"]
        intent     = result["intent"]
        clean_resp = clean_response(content)

        # ── Log usage ────────────────────────────────
        try:
            log_usage(
                session_id        = st.session_state.session_id,
                user_id           = st.session_state.user_id,
                message_id        = str(uuid.uuid4()),
                prompt_tokens     = result["prompt_tokens"],
                completion_tokens = result["comp_tokens"],
                embedding_tokens  = 0,
                latency_ms        = result["latency_ms"],
                tool_calls        = result["tool_calls"],
                sources           = result["sources"],
                user_prompt       = user_input,
                final_response    = clean_resp,
                intent            = intent,
            )
        except Exception:
            pass

        if lead_temp == "hot" or st.session_state.lead_status == "hot":
            st.session_state.lead_status = "hot"
        elif lead_temp == "warm" and st.session_state.lead_status == "cold":
            st.session_state.lead_status = "warm"
        st.session_state.intent = intent

        # ── Parse lead signal from agent ─────────────
        lead_data = parse_lead_signal(content)
        if lead_data:
            for k, v in lead_data.items():
                if v and v.lower() not in ("unknown", ""):
                    if k == "name" and buf.get("name", "unknown") not in ("unknown", ""):
                        continue
                    buf[k] = v

        # ── Set interest from intent if missing ───────
        if buf.get("interest", "unknown") in ("unknown", ""):
            if intent in ["recommendation", "ready_to_buy", "price_inquiry"]:
                buf["interest"] = intent

        # ── Save to CRM ───────────────────────────────
        has_name    = buf.get("name",  "unknown") not in ("unknown", "")
        has_phone   = buf.get("phone", "unknown") not in ("unknown", "")
        has_email   = buf.get("email", "unknown") not in ("unknown", "")
        has_contact = has_phone or has_email

        if has_name and has_contact:
            flush_crm(language)
            if is_lead_valid(buf) and not st.session_state.collected_lead:
                st.session_state.collected_lead = True
                st.session_state.lead_status    = "hot"
                st.success("✅ Lead captured and saved to CRM!")

        st.session_state.messages.append({"role": "assistant", "content": clean_resp})
        save_chat_message(st.session_state.session_id, "assistant", clean_resp)
        st.rerun()


# ══════════════════════════════════════════════════════
# PAGE 2: CRM
# ══════════════════════════════════════════════════════
elif st.session_state.current_page == "crm":
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