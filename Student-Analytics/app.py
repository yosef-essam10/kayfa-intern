import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import hashlib, base64
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kayfa Student Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme tokens ──────────────────────────────────────────────────────────────
BG      = "#0D0F2B"
PANEL   = "#141736"
BORDER  = "#1E2250"
BLUE    = "#4B7BFF"
PURPLE  = "#7B5EFF"
GREEN   = "#00C896"
RED     = "#FF4B6E"
YELLOW  = "#FFB700"
TEXT    = "#E8EAFF"
MUTED   = "#6B7280"
GRID    = "#1E2250"
ORANGE  = "#FF8C42"

SEG_COLORS = {
    "High Achiever":      GREEN,
    "At Risk":            RED,
    "Self-Directed":      BLUE,
    "Struggling Engaged": ORANGE,
    "Average":            PURPLE,
    "Disengaged":         MUTED,
}

INSIGHT_MAP = {
    "High Achiever":
        "High grades <strong>and</strong> high attendance <strong>and</strong> active logins — "
        "the star students. Keep them challenged with advanced material.",
    "At Risk":
        "Low grades <strong>and</strong> low attendance — need <strong>immediate instructor contact</strong>. "
        "Every week of delay reduces recovery probability.",
    "Self-Directed":
        "Good grades despite <strong>below-average attendance</strong> — independent learners who study "
        "on their own. Low-touch, but worth a check-in to confirm they're not falling through the cracks.",
    "Struggling Engaged":
        "High login count but grades are <strong>below average</strong> — effort without results. "
        "These students need targeted academic support, not just motivation.",
    "Average":
        "Middle-of-the-road across all metrics — stable but with clear room to grow. "
        "A single structured nudge (study plan, peer group) can move them up.",
    "Disengaged":
        "Low logins and low engagement — students who have <strong>mentally checked out</strong>. "
        "Outreach before the next term is critical.",
}

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {BG};
    color: {TEXT};
}}
.stApp {{ background-color: {BG}; }}

section[data-testid="stSidebar"] {{
    background-color: {PANEL};
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}

.top-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 32px 14px 32px;
    background: linear-gradient(135deg, {PANEL} 0%, #0D1240 100%);
    border-bottom: 1px solid {BORDER};
    margin: -1rem -1rem 2rem -1rem;
}}
.top-bar-left {{ display: flex; flex-direction: column; gap: 2px; }}
.top-bar-eyebrow {{
    font-size: 10px; font-weight: 600; letter-spacing: 2px;
    color: {MUTED}; text-transform: uppercase;
}}
.top-bar-title {{ font-size: 22px; font-weight: 700; color: {TEXT}; }}
.top-bar-sub   {{ font-size: 13px; color: {BLUE}; font-weight: 500; }}
.top-bar-logo img {{ height: 44px; }}

.kpi-row {{ display: flex; gap: 16px; margin-bottom: 28px; flex-wrap: wrap; }}
.kpi-card {{
    flex: 1; min-width: 140px;
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px 20px;
}}
.kpi-label {{ font-size: 10px; font-weight: 600; letter-spacing: 1.5px;
              text-transform: uppercase; color: {MUTED}; margin-bottom: 6px; }}
.kpi-value {{ font-size: 28px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
.kpi-sub   {{ font-size: 11px; color: {MUTED}; margin-top: 4px; }}
.kpi-blue   {{ color: {BLUE}; }}
.kpi-green  {{ color: {GREEN}; }}
.kpi-red    {{ color: {RED}; }}
.kpi-yellow {{ color: {YELLOW}; }}
.kpi-purple {{ color: {PURPLE}; }}

.section-title {{
    font-size: 13px; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; color: {MUTED};
    border-left: 3px solid {BLUE}; padding-left: 10px;
    margin: 28px 0 16px 0;
}}

.insight-box {{
    background: linear-gradient(135deg, rgba(75,123,255,0.08), rgba(123,94,255,0.08));
    border: 1px solid rgba(75,123,255,0.25);
    border-radius: 10px; padding: 14px 18px; margin-top: 10px;
    font-size: 13px; line-height: 1.8; color: {TEXT};
}}
.insight-box strong {{ color: {BLUE}; }}

.badge-high   {{ background: rgba(255,75,110,0.15); color: {RED};
                 border: 1px solid {RED}; border-radius: 6px;
                 padding: 2px 10px; font-size: 11px; font-weight: 600; }}
.badge-medium {{ background: rgba(255,183,0,0.15); color: {YELLOW};
                 border: 1px solid {YELLOW}; border-radius: 6px;
                 padding: 2px 10px; font-size: 11px; font-weight: 600; }}
.badge-low    {{ background: rgba(0,200,150,0.15); color: {GREEN};
                 border: 1px solid {GREEN}; border-radius: 6px;
                 padding: 2px 10px; font-size: 11px; font-weight: 600; }}

div[data-baseweb="select"] > div {{
    background-color: {PANEL} !important;
    border-color: {BORDER} !important;
    color: {TEXT} !important;
}}
.stTextInput > div > div > input {{
    background-color: {PANEL}; border: 1px solid {BORDER}; color: {TEXT};
}}
.stButton > button {{
    background: linear-gradient(135deg, {BLUE}, {PURPLE});
    color: white; border: none; border-radius: 8px;
    padding: 10px 28px; font-weight: 600; width: 100%;
}}

/* Active nav button highlight */
div[data-testid="stSidebar"] .stButton > button[aria-pressed="true"],
div[data-testid="stSidebar"] .stButton > button:focus {{
    background: rgba(75,123,255,0.2) !important;
    border: 1px solid {BLUE} !important;
    color: {TEXT} !important;
}}
div[data-testid="stSidebar"] .stButton > button {{
    background: transparent !important;
    border: 1px solid transparent !important;
    color: {TEXT} !important;
    text-align: left !important;
    font-weight: 400 !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    width: 100% !important;
}}
</style>
""", unsafe_allow_html=True)

# ── MongoDB ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    uri = st.secrets["MONGO_URI"]
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client["elearning_platform"]

@st.cache_data(ttl=300)
def load(collection, query=None, projection=None):
    db = get_db()
    cursor = db[collection].find(query or {}, projection or {"_id": 0})
    return pd.DataFrame(list(cursor))

# ── Sidebar filters ───────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_group_track_map():
    groups  = load("group_summaries", projection={"_id": 0, "group_id": 1, "group_name": 1, "course_id": 1})
    courses = load("courses",         projection={"_id": 0, "course_id": 1, "course_name": 1})
    if groups.empty:
        return pd.DataFrame(columns=["group_id", "group_name", "course_id", "course_name"])
    if not courses.empty and "course_id" in groups.columns:
        groups = groups.merge(courses, on="course_id", how="left")
    if "course_name" not in groups.columns:
        groups["course_name"] = groups.get("course_id")
    return groups

def filter_sidebar():
    gt_map = get_group_track_map()
    with st.sidebar:
        st.markdown(f'<div style="font-size:10px;color:{MUTED};letter-spacing:1.5px;'
                    f'text-transform:uppercase;padding:16px 0 8px 4px;">Filters</div>',
                    unsafe_allow_html=True)
        track_options  = sorted(gt_map["course_name"].dropna().unique().tolist()) if not gt_map.empty else []
        selected_tracks = st.multiselect("Track", track_options, default=[], key="filter_tracks")

        group_pool    = gt_map[gt_map["course_name"].isin(selected_tracks)] if selected_tracks and not gt_map.empty else gt_map
        group_options = sorted(group_pool["group_name"].dropna().unique().tolist()) if not group_pool.empty else []
        selected_groups = st.multiselect("Group", group_options, default=[], key="filter_groups")

    selected_gids = []
    if not gt_map.empty:
        pool = gt_map.copy()
        if selected_tracks:
            pool = pool[pool["course_name"].isin(selected_tracks)]
        if selected_groups:
            pool = pool[pool["group_name"].isin(selected_groups)]
        if selected_tracks or selected_groups:
            selected_gids = pool["group_id"].dropna().unique().tolist()
    return selected_gids

def apply_group_filter(df, gids):
    if gids and not df.empty and "group_id" in df.columns:
        return df[df["group_id"].isin(gids)]
    return df

# ── Helpers ───────────────────────────────────────────────────────────────────
def apply_theme(fig, title="", xlab="", ylab="", height=400):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT, family="Inter"),
                   x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter", size=11),
        xaxis=dict(gridcolor=GRID, linecolor=BORDER, title=xlab, tickfont=dict(color=MUTED)),
        yaxis=dict(gridcolor=GRID, linecolor=BORDER, title=ylab, tickfont=dict(color=MUTED)),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, font=dict(color=TEXT)),
        margin=dict(t=50, b=40, l=40, r=20),
        height=height,
    )
    return fig

def kpi(label, value, color_class="kpi-blue", sub=""):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {color_class}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""

def insight(text):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def cosine_sim(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if (na == 0 or nb == 0) else float(np.dot(a, b) / (na * nb))

# ── Header ────────────────────────────────────────────────────────────────────
def render_header():
    logo_path = Path(__file__).parent / "logo.png"
    logo_html = ""
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}">'
    st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-left">
            <div class="top-bar-eyebrow">KAYFA — كيف · MONTH 1 · WEEK 2 · DATA ANALYTICS TRACK</div>
            <div class="top-bar-title">Student Analytics Dashboard</div>
            <div class="top-bar-sub">Multi-source data · Real insight · Actionable decisions</div>
        </div>
        <div class="top-bar-logo">{logo_html}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Sidebar nav ───────────────────────────────────────────────────────────────
PAGES = {
    "📊  Overview":    "overview",
    "🎓  Performance": "performance",
    "⚡  Engagement":  "engagement",
    "🧠  Concepts":    "concepts",
    "🚨  At-Risk":     "risk",
    "🔵  Segments":    "segments",
    "👥  Groups":      "groups",
}

def sidebar():
    with st.sidebar:
        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<div style="text-align:center;padding:16px 0 24px;">'
                f'<img src="data:image/png;base64,{b64}" style="height:40px;"></div>',
                unsafe_allow_html=True
            )

        st.markdown(f'<div style="font-size:10px;color:{MUTED};letter-spacing:1.5px;'
                    f'text-transform:uppercase;padding:0 0 8px 4px;">Navigation</div>',
                    unsafe_allow_html=True)

        if "page" not in st.session_state:
            st.session_state["page"] = "overview"

        for label, key in PAGES.items():
            active = st.session_state["page"] == key
            # Highlight active tab with colored background
            btn_bg    = f"rgba(75,123,255,0.18)" if active else "transparent"
            btn_border = BLUE if active else "transparent"
            btn_color  = TEXT
            st.markdown(f"""
            <div style="margin-bottom:4px;">
                <div onclick="" style="
                    background:{btn_bg};
                    border:1px solid {btn_border};
                    border-radius:8px;
                    padding:9px 14px;
                    font-size:13px;
                    color:{btn_color};
                    cursor:pointer;
                    font-weight:{'600' if active else '400'};
                    display:flex; align-items:center; gap:8px;
                ">{label}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state["page"] = key
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        user = st.session_state.get("user", {})
        st.markdown(f"""
        <div style="border-top:1px solid {BORDER};padding-top:16px;font-size:11px;color:{MUTED};">
            <span style="color:{TEXT};font-weight:600;">{user.get('username','—')}</span>
            <span style="color:{BLUE};"> · {user.get('role','')}</span>
        </div>
        """, unsafe_allow_html=True)

    return st.session_state.get("page", "overview")

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGES
# ═══════════════════════════════════════════════════════════════════════════════

def page_overview():
    section("PLATFORM OVERVIEW")
    students = load("students")
    groups   = load("group_summaries")
    risk     = load("at_risk_ranking")
    concepts = load("concept_failure_table")

    n_students  = len(students)
    n_groups    = len(groups)
    avg_att     = groups["attendance_rate"].mean() * 100 if not groups.empty else 0
    high_risk_n = (risk["risk_level"] == "High Risk").sum() if "risk_level" in risk.columns else 0
    top_fail    = concepts.nsmallest(1, "avg_score").iloc[0] if not concepts.empty else {}

    st.markdown(
        '<div class="kpi-row">'
        + kpi("Total Students",       f"{n_students:,}", "kpi-blue",   "enrolled")
        + kpi("Active Groups",         str(n_groups),    "kpi-purple",  "this term")
        + kpi("Platform Attendance",   f"{avg_att:.1f}%","kpi-green",  "avg across groups")
        + kpi("High Risk Students",    str(high_risk_n), "kpi-red",    "need contact")
        + kpi("Weakest Concept",
              top_fail.get("concept_name", "—")[:18], "kpi-yellow",
              f"{top_fail.get('fail_rate', 0):.0f}% fail rate")
        + '</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)

    with c1:
        section("Q1 — ATTENDANCE RATE PER GROUP")
        if not groups.empty:
            gf  = groups.sort_values("attendance_rate")
            avg = groups["attendance_rate"].mean()
            fig = go.Figure(go.Bar(
                x=(gf["attendance_rate"] * 100).round(1),
                y=gf["group_id"],
                orientation="h",
                marker_color=[RED if v < avg else GREEN for v in gf["attendance_rate"]],
                text=(gf["attendance_rate"] * 100).round(1).astype(str) + "%",
                textposition="inside",
                insidetextanchor="middle",
            ))
            fig.add_vline(x=avg * 100, line_dash="dash", line_color=MUTED,
                          annotation_text=f"Platform avg  {avg*100:.1f}%",
                          annotation_font_color=MUTED)
            apply_theme(fig, "", "Attendance Rate (%)", "", 360)
            fig.update_xaxes(range=[0, 110])
            st.plotly_chart(fig, use_container_width=True)
            below = gf[gf["attendance_rate"] < avg]
            worst = gf.iloc[0]
            insight(
                f"<strong>{len(below)} group(s)</strong> sit below the platform average of "
                f"<strong>{avg*100:.1f}%</strong>. "
                f"Group <strong>{worst['group_id']}</strong> is the lowest at "
                f"<strong>{worst['attendance_rate']*100:.1f}%</strong> — "
                f"flag for instructor review this week before the gap widens further."
            )

    with c2:
        section("Q15 — GROUP GRADE TRENDS OVER THE TERM")
        trends = load("grade_trends_by_group")
        if not trends.empty:
            palette = [BLUE, GREEN, RED, YELLOW, PURPLE, "#00D4FF", "#FF6B35", "#A8FF3E", "#FF3EA8", "#3EFFDC"]
            fig2 = go.Figure()
            for i, gid in enumerate(trends["group_id"].unique()):
                sub = trends[trends["group_id"] == gid].sort_values("month")
                fig2.add_trace(go.Scatter(
                    x=sub["month"], y=sub["avg_score"],
                    mode="lines+markers", name=str(gid),
                    line=dict(color=palette[i % len(palette)], width=2),
                    marker=dict(size=5)
                ))
            apply_theme(fig2, "", "Month", "Avg Score", 360)
            st.plotly_chart(fig2, use_container_width=True)
            insight(
                "Groups whose line <strong>slopes down after mid-term</strong> signal a pacing issue — "
                "difficulty ramps faster than students can absorb. "
                "Cross-reference these groups with the at-risk ranking to identify students who need early contact."
            )


def page_performance():
    section("Q2 — SCORE DISTRIBUTION BY ASSESSMENT TYPE")
    ass    = load("assessment_type_stats")
    grades = load("grades", projection={"_id": 0, "type": 1, "score": 1})

    if not grades.empty and not ass.empty:
        type_order  = ass.sort_values("mean", ascending=False)["type"].tolist()
        colors_map  = {"quiz": BLUE, "assignment": GREEN, "practical": YELLOW, "exam": RED}
        fig = go.Figure()
        for t in type_order:
            vals = grades[grades["type"] == t]["score"].dropna()
            fig.add_trace(go.Violin(
                y=vals, name=t, box_visible=True, meanline_visible=True,
                points="outliers", opacity=0.75,
                marker_color=colors_map.get(t, PURPLE),
                line_color=colors_map.get(t, PURPLE),
                fillcolor=colors_map.get(t, PURPLE),
            ))
        apply_theme(fig, "", "Assessment Type", "Score", 420)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Derive actual insight from data
        widest = ass.loc[ass["std"].idxmax(), "type"] if "std" in ass.columns else "exam"
        most_consistent = ass.loc[ass["std"].idxmin(), "type"] if "std" in ass.columns else "quiz"
        insight(
            f"<strong>{widest.capitalize()}s</strong> show the widest score spread — "
            "polarised outcomes between top and bottom performers indicate high variance in preparation. "
            f"<strong>{most_consistent.capitalize()}s</strong> are the most consistent predictor of overall grade, "
            "making them the best early warning signal for at-risk identification."
        )

    section("Q3 — BEST & WORST COURSE BY AVERAGE GRADE")
    grades_full = load("grades",   projection={"_id": 0, "course_id": 1, "score": 1})
    courses     = load("courses",  projection={"_id": 0, "course_id": 1, "course_name": 1})
    if not grades_full.empty and not courses.empty:
        merged     = grades_full.merge(courses, on="course_id", how="left")
        course_avg = merged.groupby("course_name")["score"].agg(avg="mean", std="std").reset_index().sort_values("avg", ascending=False)
        bar_colors = [GREEN] + [BLUE] * (len(course_avg) - 2) + [RED]
        fig3 = go.Figure(go.Bar(
            x=course_avg["course_name"],
            y=course_avg["avg"].round(1),
            error_y=dict(type="data", array=course_avg["std"].round(1), visible=True, color=MUTED),
            marker_color=bar_colors,
            text=course_avg["avg"].round(1),
            textposition="inside",
            insidetextanchor="middle",
        ))
        fig3.add_hline(y=course_avg["avg"].mean(), line_dash="dot",
                       line_color=MUTED, annotation_text="Platform avg",
                       annotation_font_color=MUTED)
        apply_theme(fig3, "", "", "Avg Score", 380)
        fig3.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig3, use_container_width=True)
        best  = course_avg.iloc[0]
        worst = course_avg.iloc[-1]
        gap   = best["avg"] - worst["avg"]
        insight(
            f"<strong>{best['course_name']}</strong> leads at <strong>{best['avg']:.1f} pts</strong>. "
            f"<strong>{worst['course_name']}</strong> trails at <strong>{worst['avg']:.1f} pts</strong> — "
            f"a <strong>{gap:.1f}-point gap</strong> that warrants a curriculum review. "
            "High standard deviation in the worst course suggests inconsistent delivery, not just student difficulty."
        )


def page_engagement():
    gids = st.session_state.get("selected_gids", [])

    section("Q4 — ATTENDANCE RATE VS AVERAGE GRADE")
    sf = load("student_profiles")
    sf = apply_group_filter(sf, gids)
    if not sf.empty:
        q4   = sf[["attendance_rate", "avg_grade"]].dropna()
        corr = q4["attendance_rate"].corr(q4["avg_grade"])

        fig = px.scatter(
            sf, x="attendance_rate", y="avg_grade",
            color="group_id", opacity=0.65,
            color_discrete_sequence=[BLUE, GREEN, RED, YELLOW, PURPLE, "#00D4FF", "#FF6B35", "#A8FF3E"],
            labels={"attendance_rate": "Attendance Rate", "avg_grade": "Avg Grade", "group_id": "Group"},
            hover_data=["full_name", "group_id"]
        )
        slope, intercept = np.polyfit(q4["attendance_rate"], q4["avg_grade"], 1)
        xl = [float(q4["attendance_rate"].min()), float(q4["attendance_rate"].max())]
        fig.add_trace(go.Scatter(
            x=xl, y=[slope * x + intercept for x in xl],
            mode="lines", line=dict(color=YELLOW, width=2.5),
            name="Trend line", showlegend=False
        ))
        apply_theme(fig, f"Each dot = one student  ·  Trend line shows overall direction  ·  Pearson r = {corr:.3f}", "Attendance Rate", "Avg Grade", 420)
        fig.update_xaxes(tickformat=".0%")
        fig.update_traces(marker=dict(size=5), selector=dict(mode="markers"))
        st.plotly_chart(fig, use_container_width=True)

        # Attendance band bar
        q4b = q4.copy()
        q4b["attendance_band"] = pd.cut(
            q4b["attendance_rate"],
            bins=[0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            labels=["<50%", "50–60%", "60–70%", "70–80%", "80–90%", "90–100%"]
        )
        band_stats = q4b.groupby("attendance_band", observed=True)["avg_grade"].mean().reset_index()
        fig_band = go.Figure(go.Bar(
            x=band_stats["attendance_band"].astype(str),
            y=band_stats["avg_grade"].round(1),
            marker_color=BLUE,
            text=band_stats["avg_grade"].round(1),
            textposition="inside",
            insidetextanchor="middle",
        ))
        apply_theme(fig_band, "Average Grade Rises with Attendance Band", "Attendance Band", "Avg Grade", 320)
        fig_band.update_yaxes(range=[0, band_stats["avg_grade"].max() + 15])
        st.plotly_chart(fig_band, use_container_width=True)

        low_att  = sf[sf["attendance_rate"] < 0.5]["avg_grade"].mean()
        high_att = sf[sf["attendance_rate"] >= 0.8]["avg_grade"].mean()
        insight(
            f"Pearson r = <strong>{corr:.3f}</strong> — a moderate positive relationship between attendance and grades. "
            f"Students attending <strong>80%+</strong> average <strong>{high_att:.1f} pts</strong>, "
            f"versus <strong>{low_att:.1f} pts</strong> for those below 50% — "
            f"a <strong>{high_att - low_att:.1f}-point advantage</strong>. "
            "Attendance alone doesn't guarantee high grades, but low attendance almost always predicts lower performance."
        )

    section("Q5 — ENGAGEMENT VS ACADEMIC PERFORMANCE")
    if not sf.empty:
        c1, c2 = st.columns(2)
        for col, xcol, xlab, color, x_fmt in [
            (c1, "login_count",      "Login Count",      BLUE,   None),
            (c2, "total_watch_time", "Watch Time (sec)", PURPLE, None),
        ]:
            with col:
                q5  = sf[[xcol, "avg_grade"]].dropna()
                r   = q5[xcol].corr(q5["avg_grade"])
                fig_e = go.Figure()
                fig_e.add_trace(go.Scatter(
                    x=q5[xcol], y=q5["avg_grade"],
                    mode="markers",
                    marker=dict(color=color, size=4, opacity=0.55),
                    showlegend=False,
                ))
                s, b = np.polyfit(q5[xcol], q5["avg_grade"], 1)
                xl   = [float(q5[xcol].min()), float(q5[xcol].max())]
                fig_e.add_trace(go.Scatter(
                    x=xl, y=[s * x + b for x in xl],
                    mode="lines", line=dict(color=YELLOW, width=2),
                    name="Trend", showlegend=False
                ))
                direction = "positive" if r > 0 else "negative"
                strength  = "strong" if abs(r) > 0.5 else ("moderate" if abs(r) > 0.3 else "weak")
                apply_theme(fig_e,
                    f"{xlab} vs Grade  ·  {strength.capitalize()} {direction} correlation  (r = {r:.3f})",
                    xlab, "Avg Grade", 340)
                st.plotly_chart(fig_e, use_container_width=True)

        r_login = sf["login_count"].corr(sf["avg_grade"])
        r_watch = sf["total_watch_time"].corr(sf["avg_grade"]) if "total_watch_time" in sf.columns else 0
        insight(
            f"Login count (r = <strong>{r_login:.3f}</strong>) and watch time (r = <strong>{r_watch:.3f}</strong>) "
            "both show a positive link with grades — but the relationship is weaker than attendance or concept mastery. "
            "<strong>Passive consumption (watching videos) doesn't replace active practice.</strong> "
            "Students who log in frequently but still fail concepts are the 'Struggling Engaged' segment — "
            "effort without the right strategy."
        )

    section("Q9 — ATTENDANCE & ENGAGEMENT TRENDS OVER THE TERM")
    ts_att = load("time_series_attendance")
    ts_eng = load("time_series_engagement")
    if not ts_att.empty and not ts_eng.empty:
        merged = ts_att.merge(ts_eng, on="month", how="outer").sort_values("month")
        fig9   = make_subplots(specs=[[{"secondary_y": True}]])
        fig9.add_trace(go.Scatter(
            x=merged["month"], y=merged["attendance_pct"],
            mode="lines+markers", name="Attendance %",
            line=dict(color=BLUE, width=2.5),
            fill="tozeroy", fillcolor="rgba(75,123,255,0.08)"
        ), secondary_y=False)
        fig9.add_trace(go.Bar(
            x=merged["month"], y=merged["event_count"],
            name="Engagement Events", marker_color="rgba(255,183,0,0.4)"
        ), secondary_y=True)
        apply_theme(fig9, "Blue = Attendance %  ·  Bars = Total Engagement Events per Month", "Month", "", 380)
        fig9.update_yaxes(title_text="Attendance (%)", secondary_y=False, range=[0, 100])
        fig9.update_yaxes(title_text="Events", secondary_y=True)
        st.plotly_chart(fig9, use_container_width=True)
        insight(
            "When both the blue line <strong>and</strong> the yellow bars dip in the same month, "
            "that signals a <strong>cohort-wide event</strong> — not individual disengagement. "
            "Cross-reference with the academic calendar: holidays, midterms, or platform outages are the usual culprits. "
            "A solo dip in attendance without an engagement drop suggests students are studying independently but skipping sessions."
        )


def page_concepts():
    section("Q6 — CONCEPTS WITH HIGHEST FAILURE RATE")
    cf = load("concept_failure_table")
    if not cf.empty:
        top12 = cf.nlargest(12, "fail_rate")
        fig = go.Figure(go.Bar(
            x=top12["fail_rate"],
            y=top12["concept_name"] + "  ·  " + top12["course_name"].str[:18],
            orientation="h",
            marker=dict(
                color=top12["avg_score"],
                colorscale=[[0, RED], [0.5, YELLOW], [1, GREEN]],
                cmin=30, cmax=80,
                colorbar=dict(title=dict(text="Avg Score %", font=dict(color=TEXT)),
                              tickfont=dict(color=TEXT))
            ),
            text=top12["fail_rate"].round(1).astype(str) + "%",
            textposition="inside",
            insidetextanchor="end",
        ))
        fig.add_vline(x=40, line_dash="dash", line_color=MUTED,
                      annotation_text="40% failure threshold", annotation_font_color=MUTED)
        apply_theme(fig, "Bar length = Fail Rate  ·  Color = Avg Score (red = low, green = high)", "Fail Rate (%)", "", 480)
        fig.update_xaxes(range=[0, 110])
        fig.update_layout(margin=dict(l=260))
        st.plotly_chart(fig, use_container_width=True)

        above_thresh = (top12["fail_rate"] > 40).sum()
        worst        = cf.loc[cf["avg_score"].idxmin()]
        insight(
            f"<strong>{above_thresh} concepts</strong> exceed the 40% failure threshold — "
            "these are structural curriculum weaknesses, not individual student failures. "
            f"The single worst concept is <strong>{worst['concept_name']}</strong> "
            f"in {worst['course_name']} — only <strong>{worst['avg_score']:.1f}% avg score</strong> "
            f"with a <strong>{worst['fail_rate']:.1f}% fail rate</strong>. "
            "Targeted remedial sessions on the bottom 3 concepts would have the highest ROI per hour of instructor time."
        )

    section("Q7 — MASTERY TREND FOR THE WEAKEST CONCEPT")
    concepts_raw = load("concepts", projection={"_id": 0, "concept_name": 1,
                                                  "course_id": 1, "score_pct": 1,
                                                  "mastery_status": 1, "timestamp": 1})
    if not concepts_raw.empty and not cf.empty:
        worst_name   = cf.loc[cf["avg_score"].idxmin(), "concept_name"]
        worst_course = cf.loc[cf["avg_score"].idxmin(), "course_id"]
        q7 = concepts_raw[
            (concepts_raw["concept_name"] == worst_name) &
            (concepts_raw["course_id"]    == worst_course)
        ].copy()
        q7["month"] = pd.to_datetime(q7["timestamp"]).dt.to_period("M").astype(str)
        monthly = q7.groupby("month").agg(
            avg_score=("score_pct",      "mean"),
            pass_rate=("mastery_status", lambda x: (x == "passed").mean() * 100),
            n=("score_pct",              "count")
        ).reset_index()

        fig7 = make_subplots(specs=[[{"secondary_y": True}]])
        fig7.add_trace(go.Bar(x=monthly["month"], y=monthly["n"],
            name="Attempt Count", marker_color="rgba(75,123,255,0.2)"), secondary_y=True)
        fig7.add_trace(go.Scatter(x=monthly["month"], y=monthly["avg_score"],
            mode="lines+markers", name="Avg Score %",
            line=dict(color=BLUE, width=3), marker=dict(size=8)), secondary_y=False)
        fig7.add_trace(go.Scatter(x=monthly["month"], y=monthly["pass_rate"],
            mode="lines+markers", name="Pass Rate %",
            line=dict(color=GREEN, width=3, dash="dot"),
            marker=dict(size=8, symbol="diamond")), secondary_y=False)
        fig7.add_hline(y=60, line_dash="dash", line_color=RED,
                       annotation_text="Pass threshold 60%", annotation_font_color=RED)
        apply_theme(fig7, f"Monthly mastery for  '{worst_name}'  —  Blue = avg score  ·  Green = pass rate  ·  Bars = attempts", "Month", "", 380)
        fig7.update_yaxes(title_text="Score / Pass Rate (%)", range=[0, 100], secondary_y=False)
        fig7.update_yaxes(title_text="Attempt Count", secondary_y=True)
        st.plotly_chart(fig7, use_container_width=True)

        if len(monthly) >= 2:
            slope = monthly["avg_score"].iloc[-1] - monthly["avg_score"].iloc[0]
            if slope > 2:
                trend_txt = f"improving (+{slope:.1f} pts over the term) — interventions are working"
                trend_action = "Maintain current support and document what changed."
            elif slope < -2:
                trend_txt = f"declining ({slope:.1f} pts over the term) — students are not self-correcting"
                trend_action = "This concept needs a full redesign in the next term, not just extra practice."
            else:
                trend_txt = "flat — no improvement despite repeated exposure"
                trend_action = "A flat trend means the issue is structural. Review how this concept is taught, not just how much."
            insight(
                f"Mastery trend is <strong>{trend_txt}</strong>. "
                f"<strong>{trend_action}</strong> "
                f"Current pass rate: <strong>{monthly['pass_rate'].iloc[-1]:.1f}%</strong> "
                f"vs the 60% threshold — "
                f"{'above threshold ✓' if monthly['pass_rate'].iloc[-1] >= 60 else 'still below threshold — action required'}."
            )


def page_risk():
    gids = st.session_state.get("selected_gids", [])

    section("Q14 — AT-RISK STUDENT RANKING")
    risk = load("at_risk_ranking")
    risk = apply_group_filter(risk, gids)

    if not risk.empty:
        top10      = risk.nlargest(10, "risk_score")
        risk_color = {"High Risk": RED, "Medium Risk": YELLOW, "Low Risk": GREEN}

        dist = risk["risk_level"].value_counts().reset_index()
        dist.columns = ["level", "count"]

        c1, c2 = st.columns([2, 1])
        with c1:
            fig = go.Figure(go.Bar(
                x=top10["risk_score"].round(3),
                y=top10["full_name"],
                orientation="h",
                marker_color=[risk_color.get(str(r), BLUE) for r in top10["risk_level"]],
                text=[
                    f"att {a:.0%}  grade {g:.0f}  failed {f:.0f}"
                    for a, g, f in zip(top10["attendance_rate"],
                                       top10["avg_grade"],
                                       top10["failed_concepts"])
                ],
                textposition="inside",
                insidetextanchor="end",
            ))
            apply_theme(fig, "Top 10 students to contact first — sorted by composite risk score", "Risk Score (0–1)", "", 400)
            fig.update_xaxes(range=[0, 0.95])
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig_pie = go.Figure(go.Pie(
                labels=dist["level"], values=dist["count"],
                marker_colors=[risk_color.get(str(l), BLUE) for l in dist["level"]],
                textinfo="label+percent", hole=0.45,
                textfont=dict(color=TEXT)
            ))
            apply_theme(fig_pie, "Risk Distribution", height=400)
            st.plotly_chart(fig_pie, use_container_width=True)

        high_n = (risk["risk_level"] == "High Risk").sum()
        high_att_mean  = risk[risk["risk_level"] == "High Risk"]["attendance_rate"].mean()
        high_grade_mean = risk[risk["risk_level"] == "High Risk"]["avg_grade"].mean()
        insight(
            f"<strong>{high_n} students</strong> are flagged as High Risk. "
            f"On average they attend <strong>{high_att_mean:.0%}</strong> of sessions "
            f"and score <strong>{high_grade_mean:.1f} pts</strong>. "
            "These students share low attendance, low grades, and high failed concepts — "
            "a combination that rarely self-corrects without direct instructor contact. "
            "<strong>Do not send automated emails — a personal call in the first week of next term "
            "has the highest recovery rate.</strong>"
        )

        section("Q8 — LATE SUBMISSION EFFECT ON GRADES")
        subs       = load("submissions", projection={"_id": 0, "student_id": 1, "course_id": 1, "is_late": 1})
        grades_raw = load("grades",      projection={"_id": 0, "student_id": 1, "course_id": 1, "score": 1})
        if not subs.empty and not grades_raw.empty:
            avg_g = grades_raw.groupby(["student_id", "course_id"])["score"].mean().reset_index()
            q8    = subs.merge(avg_g, on=["student_id", "course_id"], how="left").dropna(subset=["score"])
            q8["status"] = q8["is_late"].map({True: "Late", False: "On Time"})

            fig8 = go.Figure()
            for status, color in [("On Time", GREEN), ("Late", RED)]:
                vals = q8[q8["status"] == status]["score"]
                fig8.add_trace(go.Box(y=vals, name=status, marker_color=color,
                                      boxmean=True, boxpoints="outliers"))
            apply_theme(fig8, "On-time vs Late submissions — grade distribution comparison", "Submission Status", "Avg Grade", 360)
            st.plotly_chart(fig8, use_container_width=True)

            stats8 = q8.groupby("status")["score"].mean()
            if "On Time" in stats8.index and "Late" in stats8.index:
                gap = stats8["On Time"] - stats8["Late"]
                insight(
                    f"On-time submitters score <strong>{gap:.1f} pts higher</strong> on average "
                    f"(<strong>{stats8['On Time']:.1f}</strong> vs <strong>{stats8['Late']:.1f}</strong>). "
                    "This gap is likely causal — students who submit late are also the ones least prepared. "
                    "A 48-hour deadline reminder notification could close most of this gap with minimal effort."
                )

        subs_full   = load("submissions", projection={"_id": 0, "student_id": 1, "assessment_id": 1,
                                                       "deadline": 1, "submitted_at": 1})
        grades_score = load("grades", projection={"_id": 0, "assessment_id": 1, "student_id": 1, "score": 1})
        if not subs_full.empty and not grades_score.empty:
            subs_full["deadline"]     = pd.to_datetime(subs_full["deadline"],     errors="coerce")
            subs_full["submitted_at"] = pd.to_datetime(subs_full["submitted_at"], errors="coerce")
            subs_scored = subs_full.merge(grades_score, on=["assessment_id", "student_id"], how="left").dropna(subset=["score"])
            subs_scored["days_before"] = (subs_scored["deadline"] - subs_scored["submitted_at"]).dt.total_seconds() / 86400
            subs_scored["timing"] = pd.cut(
                subs_scored["days_before"],
                bins=[-999, 0, 1, 3, 999],
                labels=["Late", "Same day", "1–3 days early", ">3 days early"]
            )
            bucket = subs_scored.groupby("timing", observed=True)["score"].mean().round(1).reset_index()
            color_map = {"Late": RED, "Same day": YELLOW, "1–3 days early": BLUE, ">3 days early": GREEN}
            fig8b = go.Figure(go.Bar(
                x=bucket["timing"].astype(str),
                y=bucket["score"],
                marker_color=[color_map.get(t, BLUE) for t in bucket["timing"].astype(str)],
                text=bucket["score"],
                textposition="inside",
                insidetextanchor="middle",
                width=0.5
            ))
            apply_theme(fig8b, "Avg Grade by Submission Timing — earlier submissions score higher", "Submission Timing", "Avg Score", 360)
            fig8b.update_yaxes(range=[0, bucket["score"].max() + 15])
            st.plotly_chart(fig8b, use_container_width=True)


def page_segments():
    gids = st.session_state.get("selected_gids", [])

    section("Q11 — STUDENT SEGMENTATION")

    # The KMeans clustering + persona mapping is already computed in the notebook
    # (Q11) and stored in MongoDB as `cluster_assignments`. The dashboard reads
    # that precomputed result directly instead of re-running clustering live —
    # this is what was crashing the page before (a homemade KMeans/silhouette
    # implementation that broke whenever a sidebar filter left fewer students
    # than the number of clusters being tried, which also meant every section
    # AFTER segments — including the Q10 Age Bands block below — never rendered).
    seg_df = load("cluster_assignments")
    seg_df = apply_group_filter(seg_df, gids)

    if seg_df.empty:
        insight(
            "No segmentation data found yet in <strong>cluster_assignments</strong>. "
            "Re-run the notebook's MongoDB storage step (Part 13) to populate it."
        )
    else:
        seg_df = seg_df.rename(columns={"cluster_label": "segment"})

        # keep a stable, meaningful order (falls back to whatever is present)
        seg_order = [s for s in SEG_COLORS if s in seg_df["segment"].unique()]
        if not seg_order:
            seg_order = sorted(seg_df["segment"].dropna().unique())

        seg_counts = seg_df["segment"].value_counts().reindex(seg_order).reset_index()
        seg_counts.columns = ["segment", "n"]
        seg_counts["pct"] = (seg_counts["n"] / len(seg_df) * 100).round(1)

        fig_donut = go.Figure(go.Pie(
            labels=seg_counts["segment"],
            values=seg_counts["n"],
            text=seg_counts["pct"].astype(str) + "%",
            textinfo="label+text",
            hole=0.5,
            marker=dict(colors=[SEG_COLORS.get(s, MUTED) for s in seg_counts["segment"]]),
            textfont=dict(size=12),
            sort=False,
        ))
        fig_donut.update_layout(
            title=dict(text="Segment Distribution", font=dict(size=14, color=TEXT, family="Inter"),
                       x=0, xanchor="left"),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT, family="Inter", size=12),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, font=dict(color=TEXT)),
            margin=dict(t=50, b=20, l=0, r=0),
            height=440,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

        # ── Bubble scatter: the actual cluster view (grade vs attendance) ──
        section("Q11 — GRADE VS ATTENDANCE  (CLUSTER VIEW)")
        plot_df = seg_df.copy()
        plot_df["att_pct"] = plot_df["attendance_rate"] * 100
        fig_scat = go.Figure()
        for seg in seg_order:
            sub = plot_df[plot_df["segment"] == seg]
            if sub.empty:
                continue
            lc = sub["login_count"].clip(upper=sub["login_count"].quantile(0.95)) if len(sub) > 1 else sub["login_count"]
            fig_scat.add_trace(go.Scatter(
                x=sub["att_pct"], y=sub["avg_grade"],
                mode="markers",
                name=seg,
                marker=dict(
                    color=SEG_COLORS.get(seg, MUTED),
                    size=lc, sizemode="area", sizeref=0.15,
                    opacity=0.75,
                    line=dict(width=0.5, color="rgba(255,255,255,0.3)"),
                ),
                text=sub["full_name"] if "full_name" in sub.columns else None,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Attendance: %{x:.1f}%<br>"
                    "Grade: %{y:.1f}<br>"
                    f"Segment: {seg}<extra></extra>"
                ),
            ))
        fig_scat.update_layout(
            title=dict(text="Each dot = one student  ·  Bubble size = Login Count  ·  Color = Segment",
                       font=dict(size=13, color=TEXT, family="Inter"), x=0, xanchor="left"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=BG,
            font=dict(color=TEXT, family="Inter", size=11),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, font=dict(color=TEXT)),
            margin=dict(t=50, b=40, l=40, r=20),
            xaxis=dict(title="Attendance %", gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED)),
            yaxis=dict(title="Avg Grade",    gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED)),
            height=440,
        )
        st.plotly_chart(fig_scat, use_container_width=True)
        insight(
            "Each bubble is one student, colored by segment and sized by login count. "
            "<strong>High Achievers</strong> sit top-right (high grade, high attendance); "
            "<strong>At Risk</strong> students cluster bottom-left — these are the names on the Q14 contact list. "
            "Blue/purple bubbles sitting further left than the green cluster but still scoring well are the "
            "<strong>Self-Directed</strong> pattern showing up visually, not just in the averages table."
        )

        # ── Per-segment insights ────────────────────────────────────────────
        section("SEGMENT INSIGHTS")
        FEATS       = ["avg_grade", "attendance_rate", "login_count", "failed_concepts"]
        feats_avail = [f for f in FEATS if f in seg_df.columns]
        for seg in seg_order:
            sub = seg_df[seg_df["segment"] == seg]
            if sub.empty:
                continue
            means = sub[feats_avail].mean()
            color = SEG_COLORS.get(seg, MUTED)
            pct   = len(sub) / len(seg_df) * 100
            grade_v = means.get("avg_grade", float("nan"))
            att_v   = means.get("attendance_rate", float("nan")) * 100
            login_v = means.get("login_count", float("nan"))
            fail_v  = means.get("failed_concepts", float("nan"))
            st.markdown(f"""
            <div class="insight-box" style="border-color:{color}33;margin-bottom:10px;">
                <span style="color:{color};font-weight:700;font-size:14px;">● {seg}</span>
                <span style="color:{MUTED};font-size:12px;margin-left:10px;">{len(sub)} students · {pct:.1f}%</span><br>
                <span style="font-size:12px;color:{MUTED};">
                    Grade <strong style="color:{TEXT};">{grade_v:.1f}</strong> ·
                    Attendance <strong style="color:{TEXT};">{att_v:.0f}%</strong> ·
                    Logins <strong style="color:{TEXT};">{login_v:.0f}</strong> ·
                    Failed concepts <strong style="color:{TEXT};">{fail_v:.1f}</strong>
                </span><br>
                <span style="font-size:13px;">{INSIGHT_MAP.get(seg, '')}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Q10 Age Bands ─────────────────────────────────────────────────────────
    section("Q10 — AGE BANDS VS OUTCOMES")
    sf = load("student_profiles")
    sf = apply_group_filter(sf, gids)
    if not sf.empty and "age" in sf.columns:
        sf["age_band"] = pd.cut(sf["age"], bins=[0, 20, 25, 30, 40],
                                 labels=["≤20", "21–25", "26–30", "31–40"])
        age_stats = sf.groupby("age_band", observed=True).agg(
            avg_grade=("avg_grade",     "mean"),
            att_pct=("attendance_rate", lambda x: x.mean() * 100),
            logins=("login_count",      "mean"),
            n=("student_id",            "count")
        ).reset_index().dropna(subset=["avg_grade"])

        fig_age = go.Figure()
        fig_age.add_trace(go.Bar(
            name="Avg Grade",    x=age_stats["age_band"].astype(str),
            y=age_stats["avg_grade"].round(1), marker_color=BLUE,
            text=age_stats["avg_grade"].round(1),
            textposition="inside", insidetextanchor="middle",
        ))
        fig_age.add_trace(go.Bar(
            name="Attendance %", x=age_stats["age_band"].astype(str),
            y=age_stats["att_pct"].round(1), marker_color=GREEN,
            text=age_stats["att_pct"].round(1),
            textposition="inside", insidetextanchor="middle",
        ))
        apply_theme(fig_age, "Avg Grade and Attendance % by Age Band", "Age Band", "", 360)
        fig_age.update_layout(barmode="group")
        st.plotly_chart(fig_age, use_container_width=True)

        best_band  = age_stats.loc[age_stats["avg_grade"].idxmax(), "age_band"]
        best_grade = age_stats["avg_grade"].max()
        low_att    = age_stats.loc[age_stats["att_pct"].idxmin(), "age_band"]
        insight(
            f"The <strong>{best_band}</strong> age group has the highest average grade "
            f"(<strong>{best_grade:.1f} pts</strong>) — likely full-time learners with fewer competing priorities. "
            f"The <strong>{low_att}</strong> band has the lowest attendance, "
            "consistent with working adults managing study alongside jobs and family. "
            "Despite lower attendance, their grades remain comparable — indicating <strong>self-directed efficiency</strong>."
        )

        BANDS = ["≤20", "21–25", "26–30", "31–40"]
        fig_box = make_subplots(rows=1, cols=3,
            subplot_titles=["Grade Distribution", "Attendance Rate (%)", "Login Count"])
        for col_idx, (ycol, color, scale) in enumerate([
            ("avg_grade", BLUE, 1), ("attendance_rate", GREEN, 100), ("login_count", PURPLE, 1)
        ], 1):
            for band in BANDS:
                subset = sf[sf["age_band"] == band][ycol].dropna() * scale
                if len(subset) == 0:
                    continue
                fig_box.add_trace(go.Box(
                    y=subset, name=band, marker_color=color,
                    boxmean=True, showlegend=(col_idx == 1), legendgroup=band,
                ), row=1, col=col_idx)
        fig_box.update_layout(
            title=dict(text="Outcomes by Age Band  —  Box = spread  ·  Dot = mean",
                       font=dict(size=13, color=TEXT, family="Inter"), x=0, xanchor="left"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=BG,
            font=dict(color=TEXT, family="Inter", size=11),
            margin=dict(t=60, b=40), boxmode="group", height=400,
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, font=dict(color=TEXT)),
        )
        fig_box.update_xaxes(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED))
        fig_box.update_yaxes(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED))
        st.plotly_chart(fig_box, use_container_width=True)


def page_groups():
    section("Q12 — STATED VS ACTUAL GROUP SIZES")
    groups     = load("group_summaries")
    groups_raw = load("groups")
    if not groups.empty and not groups_raw.empty and "stated_num_students" in groups_raw.columns:
        q12 = groups_raw[["group_id", "group_name", "stated_num_students"]].merge(
            groups[["group_id", "num_students"]], on="group_id", how="left"
        )
        q12["discrepancy"] = q12["num_students"] - q12["stated_num_students"]

        fig = make_subplots(rows=2, cols=1,
            subplot_titles=("Stated vs Actual student count per group",
                            "Discrepancy  (positive = more than stated, negative = fewer)"),
            row_heights=[0.6, 0.4], shared_xaxes=True)
        fig.add_trace(go.Bar(x=q12["group_id"], y=q12["stated_num_students"],
            name="Stated", marker_color=f"rgba(75,123,255,0.4)"), row=1, col=1)
        fig.add_trace(go.Bar(x=q12["group_id"], y=q12["num_students"],
            name="Actual", marker_color=BLUE,
            text=q12["num_students"], textposition="inside", insidetextanchor="middle"), row=1, col=1)
        flagged_mask = q12["discrepancy"].abs() > 2
        fig.add_trace(go.Bar(
            x=q12.loc[~flagged_mask, "group_id"], y=q12.loc[~flagged_mask, "discrepancy"],
            name="Within tolerance (≤2)",
            marker_color=GREEN,
            text=q12.loc[~flagged_mask, "discrepancy"].astype(str),
            textposition="inside", insidetextanchor="middle",
        ), row=2, col=1)
        fig.add_trace(go.Bar(
            x=q12.loc[flagged_mask, "group_id"], y=q12.loc[flagged_mask, "discrepancy"],
            name="Flagged (>2 students off)",
            marker_color=RED,
            text=q12.loc[flagged_mask, "discrepancy"].astype(str),
            textposition="inside", insidetextanchor="middle",
        ), row=2, col=1)
        fig.add_hline(y=0, line_color=MUTED, row=2, col=1)
        apply_theme(fig, "", "", "", 480)
        fig.update_layout(barmode="group")
        st.plotly_chart(fig, use_container_width=True)
        flagged = q12[q12["discrepancy"].abs() > 2]
        insight(
            f"<strong>{len(flagged)} group(s)</strong> have a discrepancy larger than 2 students. "
            "This indicates either unrecorded dropouts, manual data entry errors, or students who enrolled but never attended. "
            "Audit these groups before finalising term records — discrepancies above 5 should be escalated."
        )
    else:
        insight("Run the notebook to store group data in MongoDB, then refresh.")

    section("Q13 — NON-VIABLE GROUP IDENTIFICATION & MERGE RECOMMENDATION")
    if not groups.empty:
        smallest = groups.nsmallest(1, "num_students").iloc[0]
        st.markdown(f"""
        <div class="insight-box" style="border-color:{RED}44;">
            <span style="color:{RED};font-weight:700;">Non-viable group: {smallest['group_id']}</span>
            — only <strong>{int(smallest['num_students'])}</strong> enrolled student(s).<br>
            No peer interaction, disproportionate instructor overhead, and statistically unreliable metrics.
            Closest match by concept profile should absorb this group.
            <strong>Recommendation: merge into the nearest group on the same course track.</strong>
        </div>
        """, unsafe_allow_html=True)

        concepts_raw = load("concepts")
        students_raw = load("students")
        if not concepts_raw.empty and not students_raw.empty:
            target_gid  = smallest["group_id"]
            target_name = smallest.get("group_name", target_gid)

            concept_pivot = (
                concepts_raw.groupby(["student_id", "concept_name"])["score_pct"]
                .mean().unstack(fill_value=0)
            )
            stu_group_map = students_raw.set_index("student_id")["group_id"]
            concept_pivot = concept_pivot.join(stu_group_map, how="left")

            def group_profile(gid):
                rows = concept_pivot[concept_pivot["group_id"] == gid].drop(columns="group_id")
                return rows.mean() if len(rows) > 0 else None

            target_vec   = group_profile(target_gid)
            other_groups = groups[groups["group_id"] != target_gid]

            sims = {}
            for _, row in other_groups.iterrows():
                v = group_profile(row["group_id"])
                if v is not None and target_vec is not None:
                    sims[row.get("group_name", row["group_id"])] = round(
                        cosine_sim(target_vec.fillna(0).values, v.fillna(0).values), 4
                    )

            sim_df = pd.Series(sims).sort_values(ascending=False).reset_index()
            sim_df.columns = ["group_name", "similarity"]
            top4 = sim_df[sim_df["similarity"] > 0].head(4)
            if top4.empty:
                top4 = sim_df.head(4)

            c1, c2 = st.columns([1, 1.4])
            with c1:
                fig = px.bar(
                    top4.sort_values("similarity"),
                    x="similarity", y="group_name", orientation="h",
                    color="similarity",
                    color_continuous_scale=[[0, RED], [0.5, YELLOW], [1, GREEN]],
                    text=top4.sort_values("similarity")["similarity"].round(3),
                    labels={"similarity": "Cosine Similarity", "group_name": "Group"},
                )
                fig.update_traces(textposition="inside", insidetextanchor="end")
                fig.update_layout(xaxis_range=[0, 1.05], coloraxis_showscale=False)
                apply_theme(fig, f"Concept similarity — top matches for  {target_name}",
                            "Cosine Similarity", "", 360)
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                all_gids   = groups["group_id"].tolist()
                all_gnames = [groups.loc[groups["group_id"] == g, "group_name"].values[0]
                              if "group_name" in groups.columns else g for g in all_gids]
                n   = len(all_gids)
                mat = np.zeros((n, n))
                for i, gi in enumerate(all_gids):
                    vi = group_profile(gi)
                    for j, gj in enumerate(all_gids):
                        vj = group_profile(gj)
                        if vi is not None and vj is not None:
                            mat[i, j] = round(cosine_sim(vi.fillna(0).values, vj.fillna(0).values), 3)

                fig_hm = go.Figure(go.Heatmap(
                    z=mat, x=all_gnames, y=all_gnames,
                    colorscale=[[0, BG], [0.5, BLUE], [1, GREEN]],
                    zmin=0, zmax=1,
                    text=np.round(mat, 2), texttemplate="%{text}",
                    textfont=dict(size=9),
                    colorbar=dict(title="Similarity", tickfont=dict(color=TEXT)),
                ))
                apply_theme(fig_hm, "Full group-to-group concept similarity matrix", "", "", 360)
                fig_hm.update_layout(margin=dict(t=50, b=80, l=80, r=20),
                    xaxis=dict(tickangle=-45, gridcolor=GRID),
                    yaxis=dict(gridcolor=GRID))
                st.plotly_chart(fig_hm, use_container_width=True)

            if not sim_df.empty:
                closest = sim_df.iloc[0]
                insight(
                    f"Best merge target: <strong>{closest['group_name']}</strong> "
                    f"with a concept similarity of <strong>{closest['similarity']:.4f}</strong>. "
                    "High similarity means students in both groups have covered the same concepts at comparable levels — "
                    "the merged group won't have knowledge gaps between cohorts. "
                    "Verify they share the same course track and instructor availability before confirming."
                )

                # ── Q13b — what actually drove that similarity score ─────────
                # The bar/heatmap above are similarity numbers; this shows the
                # underlying per-concept mastery scores (concept_pivot) that the
                # cosine similarity was computed on, for the target vs its best match.
                match_rows = groups.loc[groups["group_name"] == closest["group_name"], "group_id"]
                match_gid  = match_rows.values[0] if len(match_rows) else None
                match_vec  = group_profile(match_gid) if match_gid is not None else None

                if target_vec is not None and match_vec is not None:
                    concept_compare = pd.DataFrame({
                        target_name:           target_vec,
                        closest["group_name"]: match_vec,
                    }).fillna(0)
                    concept_compare["abs_diff"] = (
                        concept_compare[target_name] - concept_compare[closest["group_name"]]
                    ).abs()

                    active = concept_compare[
                        (concept_compare[target_name] > 0) | (concept_compare[closest["group_name"]] > 0)
                    ]
                    top_concepts = active.sort_values("abs_diff", ascending=False).head(12).sort_values(target_name)

                    if not top_concepts.empty:
                        section(f"Q13 — CONCEPT MASTERY PROFILE  (actual similarity basis, cos={closest['similarity']:.4f})")
                        fig_concepts = go.Figure()
                        fig_concepts.add_trace(go.Bar(
                            y=top_concepts.index, x=top_concepts[target_name],
                            name=target_name, orientation="h", marker_color=BLUE,
                        ))
                        fig_concepts.add_trace(go.Bar(
                            y=top_concepts.index, x=top_concepts[closest["group_name"]],
                            name=closest["group_name"], orientation="h", marker_color=GREEN,
                        ))
                        fig_concepts.update_layout(barmode="group")
                        apply_theme(fig_concepts, "", "Mean score_pct", "", 420)
                        fig_concepts.update_layout(margin=dict(t=50, b=40, l=190, r=20))
                        st.plotly_chart(fig_concepts, use_container_width=True)
                        insight(
                            f"The {closest['similarity']:.4f} similarity score was computed on per-concept mastery scores, "
                            "not the operational metrics above — this chart shows the concepts that actually drove the match. "
                            "Where the bars are close, both groups learned that concept at the same pace; "
                            "the widest gaps flag exactly what the merged group's catch-up plan needs to cover first."
                        )


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if "user" not in st.session_state:
        st.session_state["user"] = {"username": "guest", "role": "viewer"}

    render_header()
    page = sidebar()
    st.session_state["selected_gids"] = filter_sidebar()

    dispatch = {
        "overview":    page_overview,
        "performance": page_performance,
        "engagement":  page_engagement,
        "concepts":    page_concepts,
        "risk":        page_risk,
        "segments":    page_segments,
        "groups":      page_groups,
    }
    dispatch.get(page, page_overview)()

if __name__ == "__main__":
    main()
