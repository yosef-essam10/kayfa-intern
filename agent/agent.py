import time
from groq import Groq
from tools import (
    tool_search_all,
    tool_search_policy,
    tool_search_courses,
    tool_search_tracks,
    tool_search_instructors,
    tool_read_courses_file,
    tool_read_roadmaps_file,
    tool_read_policy_file,
    tool_read_instructors_file,
    tool_read_free_content_file,
    tool_read_company_file,
    tool_read_specific_diploma,
    detect_language,
    detect_lead_temperature,
    detect_intent,
    detect_diploma,
    detect_course_topic,
)
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are the Kayfa AI Agent, an expert AI Sales Consultant for Kayfa — a leading Arabic educational platform.
You are not a chatbot. You are a professional sales consultant who genuinely helps people find the right learning path.

════════════════════════════════════════
IDENTITY & PERSONALITY
════════════════════════════════════════
- Your name is "Kayfa Agent".
- Never say you are an AI or a bot — say you are a Kayfa consultant.
- GREETING RULE — CRITICAL:
  → Only in the VERY FIRST message (no conversation history at all):
    - "السلام عليكم" → "عليكم السلام"
    - "مساء الخير" → "مساء النور"
    - "صباح الخير" → "صباح النور"
    - "hi" / "hello" / "hey" → "Hi!"
    - Any other opener → natural warm response.
  → Then: introduce yourself ONCE + ask name ONLY IF not already given.
  → Arabic: "أنا مساعد كيفا الذكي، إيه اسمك؟"
  → English: "I'm Kayfa's AI consultant! What's your name?"
  → If user gave their name in the SAME message → acknowledge it, do NOT ask again.
  → In ALL subsequent messages → NEVER greet again. NEVER say "أنا مساعد كيفا". Answer directly.

════════════════════════════════════════
MEMORY — ABSOLUTELY CRITICAL
════════════════════════════════════════
Read the FULL conversation history before every response.
Extract and remember:
- NAME: anything after "اسمي", "أنا", "انا", "my name is", "i am", "i'm"
- LEVEL: "مبتدئ"/"beginner", "متوسط"/"intermediate", "متقدم"/"advanced"
- PHONE: any 11-digit number starting with 010/011/012/015
- EMAIL: any text matching x@x.xx format
- CITY: any Egyptian city mentioned
- INTEREST: the course/track they asked about

RULES:
- If NAME is already in history → NEVER ask for name again.
- If LEVEL is already in history → NEVER ask for level again.
- If PHONE is already in history → NEVER ask for phone again.
- If EMAIL is already in history → NEVER ask for email again.
- If CITY is already in history → NEVER ask for city again.
- If INTEREST is clear → NEVER ask what they're interested in again.
- Violating this rule = critical failure. The user will lose trust.

════════════════════════════════════════
LANGUAGE RULES — ABSOLUTE
════════════════════════════════════════
- Arabic message → 100% Arabic. Zero English except technical terms.
- English message → 100% English. Zero Arabic.
- NEVER mix. NEVER insert Chinese, Korean, or any other language characters.
- Respond in the SAME language and dialect as the current user message.
- Technical terms in English always: AI, SQL, SOC, Python, React, Node.js, Power BI, MLOps, NLP, Docker, Machine Learning, Data Science, Excel

════════════════════════════════════════
COURSE NAME RECOGNITION
════════════════════════════════════════
- فول استاك / فول ستاك → Fullstack Diploma
- ماشيين ليرنينج / داتا ساينس / داتا → Data Science Diploma
- ذكاء اصطناعي → AI Diploma
- سوك / امن سيبراني → SOC Diploma
- اختراق / بينتست → PenTest Diploma
- فرونت اند → Frontend Track
- باك اند → Backend Track
- تحليل بيانات → Data Analysis Track

════════════════════════════════════════
ANSWER DIRECTLY
════════════════════════════════════════
- Direct answer in FIRST sentence always.
- NEVER say "لم أجد معلومات" if info is in knowledge base.
- NEVER repeat "أنا مساعد كيفا الذكي" after the first message.
- Read the FULL knowledge base before answering.
- Do NOT invent instructor names — only use names from the knowledge base.

════════════════════════════════════════
RECOMMENDATION RULE
════════════════════════════════════════
- Once you recommend a product and the user shows interest → STICK WITH IT.
- Do NOT switch recommendations unless the user explicitly asks.
- If user asks "how do I register" → guide them to register for the product already discussed.

════════════════════════════════════════
LEAD COLLECTION — CRITICAL
════════════════════════════════════════
BEFORE asking for any field → scan conversation history.
If already provided → skip it, move to next missing field.

COLLECTION ORDER: name → level → phone OR email → city

- name: extract from intro messages automatically.
- level: ask once if not mentioned. Accept: مبتدئ/beginner, متوسط/intermediate, متقدم/advanced.
- phone OR email: accept either. Validate format. Do NOT ask for both.
- city: any Egyptian city.

EMIT [LEAD_COLLECTED] when you have:
name + level + (phone OR email) + city + interest — ALL valid.

[LEAD_COLLECTED: name=X, phone=X, email=X, city=X, interest=X, level=X]
- Use "unknown" for the field not provided (phone or email).
- Add silently at end of message — user must NOT see it.
- Re-emit on every update with new info.
- NEVER emit if name=unknown or level=unknown.

PHONE VALIDATION:
→ Egyptian mobile: 010/011/012/015 + 11 digits total.
→ Invalid: "الرقم ده مش صحيح، لازم يبدأ بـ 010/011/012/015 ويكون 11 رقم."

EMAIL VALIDATION:
→ Format: name@domain.com
→ Invalid: "الإيميل ده مش صحيح، زي مثلاً name@gmail.com"

════════════════════════════════════════
SALES STAGES
════════════════════════════════════════
1. GREETING: Once. Intro once. Ask name if not given.
2. DISCOVERY: Goal, background, level. One question at a time.
3. RECOMMENDATION: ONE best product. Reasons + price + duration + certificate.
4. OBJECTION HANDLING: price/time/experience/trust.
5. LEAD QUALIFICATION: detect hot/warm signals.
6. CONTACT: level → phone OR email → city.

════════════════════════════════════════
SMART RECOMMENDATIONS
════════════════════════════════════════
- Finance/Accounting → Data Analysis ($180)
- Network/IT/Security → SOC ($250) or PenTest
- Wants freelancing → Fullstack or Data Science
- Wants abroad → AI or Data Science
- Fast job → SOC (44h) or Data Analysis
- Budget <$100 → Frontend ($100), Backend ($100), AI Fundamentals ($65)
- Budget $100-200 → Data Analysis ($180), Web Dev ($200)
- Budget $200+ → Data Science ($250), SOC ($250), or Diploma
- Beginner → suggest free content first, then paid track

════════════════════════════════════════
GROUNDING RULES
════════════════════════════════════════
- All facts from RELEVANT KNOWLEDGE BASE only.
- Unknown → refer to info@kayfa.io
- NEVER invent instructor names, prices, or durations.
- Contacts: info@kayfa.io | support@kayfa.io | +201055023774 | kayfa.io
"""

KNOWLEDGE_TRIGGERS = [
    "course", "track", "diploma", "price", "cost", "duration", "hours",
    "refund", "policy", "certificate", "instructor", "teacher", "trainer",
    "register", "enroll", "free", "discount", "payment", "accreditation",
    "who teach", "who is", "about", "kayfa", "fullstack", "full stack",
    "pentest", "pen test", "soc", "ai", "كورس", "تراك", "دبلومه", "دبلوما",
    "دبلوم", "كيفا", "فول استاك", "فول ستاك", "فولستاك", "بينتست",
    "سعر", "ساعات", "شهادة", "مدرب", "مدربين", "سجل", "اشترك", "مجاني",
    "خصم", "دفع", "اعتماد", "مستوى", "المنهج", "بيشرح", "مين بيشرح",
    "انستراكتور", "انستراكتورز", "data science", "machine learning", "ml",
    "ماشيين ليرنينج", "داتا ساينس", "داتا", "ذكاء", "اختراق", "امن",
    "python", "sql", "power bi", "react", "node", "javascript", "typescript",
    "html", "css", "linux", "splunk", "qradar", "excel", "cybersecurity",
    "فرونت اند", "باك اند", "تحليل بيانات", "تعلم الاله", "deep learning",
    "nlp", "computer vision", "mlops", "hacking", "penetration",
    "roadmap", "curriculum", "what track", "what course", "recommend",
    "network", "security", "شبكات", "امن معلومات", "ابدا", "انسب",
]


def needs_knowledge(message: str) -> bool:
    msg = message.lower()
    return any(t in msg for t in KNOWLEDGE_TRIGGERS)


def build_context_summary(history: list[dict]) -> str:
    """Build a summary of what we already know about the user from history."""
    if not history:
        return ""

    known = {}
    for msg in history:
        if msg["role"] == "user":
            text = msg["content"].lower()
            # name
            import re
            for pat in [
                r"(?:اسمي|أنا|انا)\s+([\u0600-\u06FF\s]{2,30}?)(?:\s+و|\s+ك|\s+عايز|$)",
                r"(?:my name is|i am|i'm)\s+([a-zA-Z\s]{2,40}?)(?:\s+and|\s+i|$)",
            ]:
                m = re.search(pat, msg["content"], re.IGNORECASE)
                if m and "name" not in known:
                    known["name"] = m.group(1).strip()

            # level
            if any(w in text for w in ["مبتدئ", "مبتدا", "beginner", "من الصفر", "from scratch"]):
                known["level"] = "beginner"
            elif any(w in text for w in ["متوسط", "intermediate", "شوية خبرة"]):
                known["level"] = "intermediate"
            elif any(w in text for w in ["متقدم", "advanced", "خبرة كبيرة"]):
                known["level"] = "advanced"

            # phone
            phone_match = re.search(r'\b(01[0125]\d{8})\b', msg["content"])
            if phone_match:
                known["phone"] = phone_match.group(1)

            # email
            email_match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w{2,}\b', msg["content"])
            if email_match:
                known["email"] = email_match.group(0)

    if not known:
        return ""

    lines = ["ALREADY KNOWN FROM CONVERSATION:"]
    for k, v in known.items():
        lines.append(f"- {k}: {v}")
    lines.append("DO NOT ask for any of the above fields again.")
    return "\n".join(lines)


def build_prompt(user_message: str, history: list[dict], intent: str):
    context    = ""
    msg_lower  = user_message.lower()

    is_instructor_q = any(w in msg_lower for w in [
        "instructor", "teacher", "trainer", "who teach", "مدرب", "مدربين",
        "بيشرح", "مين بيشرح", "مين المدرب", "انستراكتور", "انستراكتورز",
        "مين بيدرس", "who is the instructor",
    ])

    tool_calls_log = []
    sources_log    = []

    if needs_knowledge(user_message):
        diploma = detect_diploma(user_message)
        topic   = detect_course_topic(user_message) if not diploma else diploma

        if is_instructor_q:
            raw = tool_read_instructors_file()
            tool_calls_log.append({"tool": "tool_read_instructors_file", "args": {}})
            sources_log.append("kayfa_instructor_network.md")
            if topic:
                raw += "\n\n---\n\n" + tool_read_specific_diploma(topic)
                tool_calls_log.append({"tool": "tool_read_specific_diploma", "args": {"diploma": topic}})
                sources_log.append(f"diploma:{topic}")
        elif intent == "policy":
            raw = tool_read_policy_file()
            tool_calls_log.append({"tool": "tool_read_policy_file", "args": {}})
            sources_log.append("kayfa_policies_and_faqs.md")
        elif intent == "free_content":
            raw = tool_read_free_content_file()
            tool_calls_log.append({"tool": "tool_read_free_content_file", "args": {}})
            sources_log.append("kayfa_free_educational_content.md")
        elif intent == "company":
            raw = tool_read_company_file()
            tool_calls_log.append({"tool": "tool_read_company_file", "args": {}})
            sources_log.append("kayfa_company_overview.md")
        elif topic:
            raw = tool_read_specific_diploma(topic) + "\n\n---\n\n" + tool_read_instructors_file()
            tool_calls_log.append({"tool": "tool_read_specific_diploma", "args": {"diploma": topic}})
            tool_calls_log.append({"tool": "tool_read_instructors_file", "args": {}})
            sources_log.append(f"diploma:{topic}")
            sources_log.append("kayfa_instructor_network.md")
        elif intent in ("price_inquiry", "recommendation", "comparing", "ready_to_buy"):
            raw = tool_read_courses_file()
            tool_calls_log.append({"tool": "tool_read_courses_file", "args": {}})
            sources_log.append("kayfa_paid_educational_tracks.md")
        else:
            raw = tool_read_courses_file()
            tool_calls_log.append({"tool": "tool_read_courses_file", "args": {}})
            sources_log.append("kayfa_paid_educational_tracks.md")

        context = (
            f"\n\nRELEVANT KNOWLEDGE BASE:\n{raw}\n\n"
            f"IMPORTANT: Base your answer strictly on the above. "
            f"Read ALL sections carefully. "
            f"Do not say 'not found' if info exists above. "
            f"Do not invent instructor names."
        )

    # Build context summary from history
    context_summary = build_context_summary(history)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        for msg in history[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = user_message
    extras = []
    if context_summary:
        extras.append(context_summary)
    if context:
        extras.append(context)
    if extras:
        user_content = user_message + "\n\n" + "\n\n".join(extras)

    messages.append({"role": "user", "content": user_content})

    return messages, tool_calls_log, sources_log


def run_agent(user_message: str, history: list[dict]) -> dict:
    language  = detect_language(user_message)
    lead_temp = detect_lead_temperature(user_message)
    intent    = detect_intent(user_message)

    messages, tool_calls_log, sources_log = build_prompt(user_message, history, intent)

    t0 = time.time()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )
    latency_ms = (time.time() - t0) * 1000

    content       = response.choices[0].message.content
    prompt_tokens = response.usage.prompt_tokens
    comp_tokens   = response.usage.completion_tokens

    return {
        "content":       content,
        "language":      language,
        "lead_temp":     lead_temp,
        "intent":        intent,
        "prompt_tokens": prompt_tokens,
        "comp_tokens":   comp_tokens,
        "latency_ms":    latency_ms,
        "tool_calls":    tool_calls_log,
        "sources":       sources_log,
    }