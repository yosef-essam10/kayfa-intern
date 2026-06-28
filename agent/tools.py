from retriever import search_knowledge, format_context
import re
import json
import os

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "knowledge")


def read_file(filename: str) -> str:
    path = os.path.join(KNOWLEDGE_DIR, filename)
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_json(filename: str) -> list:
    content = read_file(filename)
    if not content:
        return []
    try:
        return json.loads(content)
    except Exception:
        return []


def tool_read_courses_file() -> str:
    parts = []
    parts.append(read_file("kayfa_paid_educational_tracks.md"))
    parts.append(read_file("kayfa_paid_individual_courses.md"))
    return "\n\n---\n\n".join(p for p in parts if p)


def tool_read_specific_diploma(diploma: str) -> str:
    mapping = {
        "ai":        "kayfa_ai_diploma.md",
        "data":      "kayfa_data_science_diploma.md",
        "soc":       "kayfa_soc_diploma.md",
        "fullstack": "Kayfa_Fullstack_Diploma.md",
        "pentest":   "Kayfa_PenTest_Diploma.md",
    }
    filename = mapping.get(diploma)
    if not filename:
        return tool_read_courses_file()
    content = read_file(filename)
    tracks  = read_file("kayfa_paid_educational_tracks.md")
    return f"{content}\n\n---\n\n{tracks}"


def tool_read_roadmaps_file() -> str:
    parts = []
    roadmaps = read_json("kayfa_roadmaps.json")
    if roadmaps:
        lines = []
        for r in roadmaps:
            lines.append(
                f"Track/Diploma: {r.get('name','')}\n"
                f"Summary: {r.get('summary','')}\n"
                f"Duration: {r.get('duration','')}\n"
                f"Price: {r.get('price','')}\n"
                f"Courses Count: {r.get('courses_count','')}\n"
                f"Link: {r.get('link','')}\n"
                f"---"
            )
        parts.append("\n".join(lines))
    parts.append(read_file("kayfa_paid_educational_tracks.md"))
    return "\n\n---\n\n".join(p for p in parts if p)


def tool_read_policy_file() -> str:
    return read_file("kayfa_policies_and_faqs.md")


def tool_read_instructors_file() -> str:
    return read_file("kayfa_instructor_network.md")


def tool_read_free_content_file() -> str:
    return read_file("kayfa_free_educational_content.md")


def tool_read_company_file() -> str:
    return read_file("kayfa_company_overview.md")


def tool_read_all_files() -> str:
    parts = [
        tool_read_company_file(),
        tool_read_roadmaps_file(),
        tool_read_free_content_file(),
        tool_read_instructors_file(),
    ]
    return "\n\n===\n\n".join(p for p in parts if p)


def tool_search_courses(query: str, intent: str = None) -> str:
    results = search_knowledge(query, top_k=3, filter_type="course", intent=intent)
    return format_context(results)


def tool_search_tracks(query: str, intent: str = None) -> str:
    results = search_knowledge(query, top_k=3, filter_type="roadmap", intent=intent)
    return format_context(results)


def tool_search_policy(query: str) -> str:
    results = search_knowledge(query, top_k=3, filter_type="markdown", intent="policy")
    return format_context(results)


def tool_search_instructors(query: str) -> str:
    results = search_knowledge(query, top_k=3, filter_type="markdown")
    if not results or results[0].get("score", 0) < 0.65:
        results = search_knowledge("instructor network " + query, top_k=3)
    return format_context(results)


def tool_search_all(query: str, intent: str = None) -> str:
    results = search_knowledge(query, top_k=4, intent=intent)
    return format_context(results)


def detect_language(text: str) -> str:
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    total = len(text.strip())
    if total == 0:
        return "english"
    return "arabic" if arabic_chars / total > 0.2 else "english"


def detect_lead_temperature(message: str) -> str:
    msg = message.lower()
    hot_signals = [
        "register", "enroll", "sign up", "pay", "payment", "buy", "purchase",
        "start now", "how to join", "whatsapp", "call me", "contact",
        "عايز اسجل", "عايز اشترك", "الدفع", "ادفع", "اشتري", "سجلني",
        "كلمني", "واتساب", "هسجل", "i want to register", "i want to enroll",
    ]
    warm_signals = [
        "price", "cost", "how much", "discount", "offer", "compare",
        "difference", "which is better", "recommend",
        "السعر", "كام", "خصم", "عرض", "الفرق", "انسب", "افضل",
    ]
    for s in hot_signals:
        if s in msg:
            return "hot"
    for s in warm_signals:
        if s in msg:
            return "warm"
    return "cold"


def detect_intent(message: str) -> str:
    msg = message.lower()
    if any(w in msg for w in ["price", "cost", "how much", "السعر", "كام", "بكام", "سعره", "بكد", "سعر"]):
        return "price_inquiry"
    if any(w in msg for w in ["refund", "cancel", "policy", "policies", "استرداد", "الغاء", "سياسة", "الشروط", "privacy"]):
        return "policy"
    if any(w in msg for w in ["instructor", "teacher", "trainer", "who teach", "مدرب", "مدربين",
                               "بيشرح", "مين بيشرح", "مين المدرب", "انستراكتور", "انستراكتورز",
                               "مين بيدرس", "who is the instructor"]):
        return "instructor"
    if any(w in msg for w in ["register", "enroll", "sign up", "سجل", "اشترك", "هسجل", "عايز اسجل"]):
        return "ready_to_buy"
    if any(w in msg for w in ["compare", "difference", "vs", "الفرق", "ولا", "ام", "احسن", "افضل"]):
        return "comparing"
    if any(w in msg for w in ["recommend", "suggest", "best", "رشح", "انسب", "ابدأ بإيه",
                               "ابدا بايه", "من فين ابدا", "ايه المناسب"]):
        return "recommendation"
    if any(w in msg for w in ["free", "مجاني", "بلاش", "مجانية", "مجانا"]):
        return "free_content"
    if any(w in msg for w in ["who", "about", "kayfa", "كيفا", "مين", "عن"]):
        return "company"
    return "browsing"


def detect_diploma(message: str) -> str | None:
    msg = message.lower()

    if any(w in msg for w in [
        "fullstack", "full stack", "full-stack",
        "فول استاك", "فول ستاك", "فولستاك", "فل استاك", "فل ستاك",
    ]):
        return "fullstack"

    if any(w in msg for w in [
        "pentest", "pen test", "pen-test", "penetration", "ethical hacking", "hacking",
        "بينتست", "بن تست", "اختراق", "الاختراق", "هاكينج",
    ]):
        return "pentest"

    if any(w in msg for w in [
        "soc diploma", "soc bootcamp", "soc track",
        "دبلومة soc", "دبلومه soc", "دبلوم soc", "سوك", "مركز عمليات",
    ]):
        return "soc"

    if any(w in msg for w in [
        "data science diploma", "data science bootcamp",
        "دبلومة data science", "دبلومه data science",
        "دبلومة داتا", "دبلومه داتا", "دبلوم داتا",
        "داتا ساينس دبلوم", "ماشيين ليرنينج", "machine learning",
        "machine learning diploma", "ml diploma",
        "دبلومه ماشيين", "دبلومة ماشيين", "دبلوم ماشيين",
        "دبلومة تعلم", "دبلومه تعلم",
    ]):
        return "data"

    if any(w in msg for w in [
        "ai diploma", "ai bootcamp", "ai track diploma",
        "دبلومة ai", "دبلومه ai", "دبلوم ai",
        "دبلومة الذكاء", "دبلومه الذكاء", "دبلوم الذكاء",
        "دبلومة ذكاء", "ذكاء اصطناعي دبلوم",
    ]):
        return "ai"

    return None


def detect_course_topic(message: str) -> str | None:
    msg = message.lower()

    fullstack_kw = [
        "fullstack", "full stack", "فول استاك", "فول ستاك", "فولستاك",
        "react", "node", "nodejs", "next.js", "nextjs",
        "frontend", "backend", "فرونت اند", "باك اند",
    ]
    pentest_kw = [
        "pentest", "pen test", "penetration", "hacking", "ethical",
        "اختراق", "هاكينج", "بينتست", "nmap", "burp", "wireshark",
    ]
    soc_kw = [
        "soc", "splunk", "qradar", "siem", "incident response",
        "threat hunting", "سوك", "امن سيبراني", "cyber",
    ]
    data_kw = [
        "data science", "machine learning", "ml", "داتا ساينس",
        "ماشيين ليرنينج", "تعلم الاله", "power bi", "pandas", "numpy",
        "داتا", "data analysis", "تحليل بيانات",
    ]
    ai_kw = [
        "ai", "artificial intelligence", "deep learning", "nlp",
        "computer vision", "ذكاء اصطناعي", "تعلم عميق",
        "gpt", "llm", "generative", "rag", "mlops",
    ]

    if any(w in msg for w in fullstack_kw):
        return "fullstack"
    if any(w in msg for w in pentest_kw):
        return "pentest"
    if any(w in msg for w in soc_kw):
        return "soc"
    if any(w in msg for w in data_kw):
        return "data"
    if any(w in msg for w in ai_kw):
        return "ai"

    return None


def validate_phone(text: str) -> bool:
    digits = re.sub(r'[\s\-\+]', '', text)
    return bool(re.match(r'^(\+?20|0)?1[0125]\d{8}$', digits))


def validate_email(text: str) -> bool:
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', text.strip()))