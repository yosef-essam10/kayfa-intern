from retriever import search_knowledge, format_context

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
    # also try without filter for broader results
    if not results or results[0].get("score", 0) < 0.65:
        results = search_knowledge("instructor network " + query, top_k=3)
    return format_context(results)

def tool_search_all(query: str, intent: str = None) -> str:
    results = search_knowledge(query, top_k=4, intent=intent)
    return format_context(results)

def detect_language(text: str) -> str:
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    return "arabic" if arabic_chars > len(text) * 0.3 else "english"

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
    if any(w in msg for w in ["price", "cost", "how much", "السعر", "كام", "بكام", "سعره"]):
        return "price_inquiry"
    if any(w in msg for w in ["refund", "cancel", "policy", "policies", "استرداد", "الغاء", "سياسة", "الشروط"]):
        return "policy"
    if any(w in msg for w in ["instructor", "teacher", "trainer", "who teach", "مدرب", "مدربين", "بيشرح", "مين بيشرح"]):
        return "instructor"
    if any(w in msg for w in ["register", "enroll", "sign up", "سجل", "اشترك", "هسجل"]):
        return "ready_to_buy"
    if any(w in msg for w in ["compare", "difference", "vs", "الفرق", "ولا", "ام", "احسن"]):
        return "comparing"
    if any(w in msg for w in ["recommend", "suggest", "best", "رشح", "انسب", "افضل", "ابدأ بإيه", "ابدا بايه"]):
        return "recommendation"
    if any(w in msg for w in ["free", "مجاني", "بلاش", "مجانية"]):
        return "free_content"
    return "browsing"