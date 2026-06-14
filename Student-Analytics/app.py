import streamlit as st
from pymongo import MongoClient
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import hashlib, base64, os
from pathlib import Path

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kayfa Student Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme tokens ─────────────────────────────────────────────────────────────
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

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    background-color: {BG};
    color: {TEXT};
}}
.stApp {{ background-color: {BG}; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: {PANEL};
    border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}

/* Header bar */
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
.top-bar-title {{
    font-size: 22px; font-weight: 700; color: {TEXT};
}}
.top-bar-sub {{ font-size: 13px; color: {BLUE}; font-weight: 500; }}
.top-bar-logo img {{ height: 44px; }}

/* KPI cards */
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

/* Section title */
.section-title {{
    font-size: 13px; font-weight: 600; letter-spacing: 1.5px;
    text-transform: uppercase; color: {MUTED};
    border-left: 3px solid {BLUE}; padding-left: 10px;
    margin: 28px 0 16px 0;
}}

/* Insight box */
.insight-box {{
    background: linear-gradient(135deg, rgba(75,123,255,0.08), rgba(123,94,255,0.08));
    border: 1px solid rgba(75,123,255,0.25);
    border-radius: 10px; padding: 14px 18px; margin-top: 10px;
    font-size: 13px; line-height: 1.7; color: {TEXT};
}}
.insight-box strong {{ color: {BLUE}; }}

/* Risk badges */
.badge-high   {{ background: rgba(255,75,110,0.15); color: {RED};
                 border: 1px solid {RED}; border-radius: 6px;
                 padding: 2px 10px; font-size: 11px; font-weight: 600; }}
.badge-medium {{ background: rgba(255,183,0,0.15); color: {YELLOW};
                 border: 1px solid {YELLOW}; border-radius: 6px;
                 padding: 2px 10px; font-size: 11px; font-weight: 600; }}
.badge-low    {{ background: rgba(0,200,150,0.15); color: {GREEN};
                 border: 1px solid {GREEN}; border-radius: 6px;
                 padding: 2px 10px; font-size: 11px; font-weight: 600; }}

/* Login card */
.login-wrap {{
    display: flex; justify-content: center; align-items: center;
    min-height: 80vh;
}}
.login-card {{
    background: {PANEL}; border: 1px solid {BORDER};
    border-radius: 16px; padding: 48px 40px; width: 360px; text-align: center;
}}

/* Plotly override */
.js-plotly-plot .plotly {{ background: transparent !important; }}

/* Selectbox / inputs */
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
</style>
""", unsafe_allow_html=True)

# ── MongoDB connection ────────────────────────────────────────────────────────
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

# ── Filters (Group / Track) ───────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_group_track_map():
    groups = load("group_summaries", projection={"_id": 0, "group_id": 1,
                                                   "group_name": 1, "course_id": 1})
    courses = load("courses", projection={"_id": 0, "course_id": 1, "course_name": 1})
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
        track_options = sorted(gt_map["course_name"].dropna().unique().tolist()) if not gt_map.empty else []
        selected_tracks = st.multiselect("Track", track_options, default=[], key="filter_tracks")

        if selected_tracks and not gt_map.empty:
            group_pool = gt_map[gt_map["course_name"].isin(selected_tracks)]
        else:
            group_pool = gt_map

        group_options = sorted(group_pool["group_name"].dropna().unique().tolist()) if not group_pool.empty else []
        selected_groups = st.multiselect("Group", group_options, default=[], key="filter_groups")

    selected_gids = []
    if not gt_map.empty:
        pool = gt_map
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

# ── Auth ──────────────────────────────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def authenticate(username, password):
    db = get_db()
    user = db["users"].find_one(
        {"username": username, "password": hash_pw(password)},
        {"_id": 0}
    )
    return user

def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo_path = Path(__file__).parent / "logo.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<div style="text-align:center;margin-bottom:24px;">'
                f'<img src="data:image/png;base64,{b64}" style="height:52px;"></div>',
                unsafe_allow_html=True
            )
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:10px;font-weight:600;letter-spacing:2px;
                        color:{MUTED};text-transform:uppercase;margin-bottom:6px;">
                KAYFA — كيف · DATA ANALYTICS
            </div>
            <div style="font-size:24px;font-weight:700;color:{TEXT};">
                Student Analytics
            </div>
            <div style="font-size:13px;color:{BLUE};margin-top:4px;">
                Sign in to access the dashboard
            </div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("Sign In"):
            if username and password:
                user = authenticate(username, password)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            else:
                st.warning("Please enter both username and password")

        st.markdown(f"""
        <div style="text-align:center;margin-top:24px;font-size:11px;color:{MUTED};">
            Demo: admin / admin123
        </div>
        """, unsafe_allow_html=True)

# ── Chart theme ───────────────────────────────────────────────────────────────
def apply_theme(fig, title="", xlab="", ylab="", height=400):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXT, family="Inter"),
                   x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter", size=11),
        xaxis=dict(gridcolor=GRID, linecolor=BORDER, title=xlab,
                   tickfont=dict(color=MUTED)),
        yaxis=dict(gridcolor=GRID, linecolor=BORDER, title=ylab,
                   tickfont=dict(color=MUTED)),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
                    font=dict(color=TEXT)),
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
    st.markdown(f'<div class="insight-box">{text}</div>', unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def cosine_sim(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))

def kmeans_fit(X, k, n_init=10, max_iter=100, seed=42):
    rng = np.random.default_rng(seed)
    best_inertia = None
    best_labels = None
    best_centers = None
    for init in range(n_init):
        idx = rng.choice(X.shape[0], size=k, replace=False)
        centers = X[idx].copy()
        for _ in range(max_iter):
            dists = ((X[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            labels = dists.argmin(axis=1)
            new_centers = np.array([
                X[labels == c].mean(axis=0) if np.any(labels == c) else centers[c]
                for c in range(k)
            ])
            if np.allclose(new_centers, centers):
                centers = new_centers
                break
            centers = new_centers
        dists = ((X[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = dists.argmin(axis=1)
        inertia = dists[np.arange(X.shape[0]), labels].sum()
        if best_inertia is None or inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels
            best_centers = centers
    return best_inertia, best_labels, best_centers

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
            <div class="top-bar-title">Student Analytics</div>
            <div class="top-bar-sub">Wrangle messy multi-source data into real insight.</div>
        </div>
        <div class="top-bar-logo">{logo_html}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Pages ─────────────────────────────────────────────────────────────────────

def page_overview():
    section("PLATFORM OVERVIEW")
    students  = load("students")
    groups    = load("group_summaries")
    risk      = load("at_risk_ranking")
    concepts  = load("concept_failure_table")

    n_students  = len(students)
    n_groups    = len(groups)
    avg_att     = groups["attendance_rate"].mean() * 100
    high_risk_n = (risk["risk_level"] == "High Risk").sum() if "risk_level" in risk.columns else 0
    top_fail    = concepts.nsmallest(1, "avg_score").iloc[0] if len(concepts) else {}

    st.markdown(
        '<div class="kpi-row">'
        + kpi("Total Students", f"{n_students:,}", "kpi-blue", "enrolled")
        + kpi("Active Groups", str(n_groups), "kpi-purple", "this term")
        + kpi("Platform Attendance", f"{avg_att:.1f}%", "kpi-green", "avg across groups")
        + kpi("High Risk Students", str(high_risk_n), "kpi-red", "need contact")
        + kpi("Weakest Concept", top_fail.get("concept_name", "—")[:18], "kpi-yellow",
              f"{top_fail.get('fail_rate', 0):.0f}% fail rate")
        + '</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    with c1:
        section("Q1 — ATTENDANCE RATE PER GROUP")
        gf = groups.sort_values("attendance_rate")
        avg = groups["attendance_rate"].mean()
        colors = [RED if v < avg else GREEN for v in gf["attendance_rate"]]
        fig = go.Figure(go.Bar(
            x=(gf["attendance_rate"] * 100).round(1),
            y=gf["group_id"], orientation="h",
            marker_color=colors,
            text=(gf["attendance_rate"] * 100).round(1).astype(str) + "%",
            textposition="outside"
        ))
        fig.add_vline(x=avg * 100, line_dash="dash", line_color=MUTED,
                      annotation_text=f"avg {avg*100:.1f}%", annotation_font_color=MUTED)
        apply_theme(fig, "", "Attendance Rate (%)", "", 360)
        fig.update_xaxes(range=[0, 105])
        st.plotly_chart(fig, use_container_width=True)
        insight("<strong>G07</strong> sits ~16 pts below platform average — the only group in critical range. Flag for instructor review this week.")

    with c2:
        section("Q15 — GROUP GRADE TRENDS")
        trends = load("grade_trends_by_group")
        if not trends.empty:
            fig2 = go.Figure()
            palette = [BLUE, GREEN, RED, YELLOW, PURPLE, "#00D4FF", "#FF6B35", "#A8FF3E", "#FF3EA8", "#3EFFDC"]
            for i, gid in enumerate(trends["group_id"].unique()):
                sub = trends[trends["group_id"] == gid].sort_values("month")
                fig2.add_trace(go.Scatter(
                    x=sub["month"], y=sub["avg_score"],
                    mode="lines+markers", name=gid,
                    line=dict(color=palette[i % len(palette)], width=2),
                    marker=dict(size=5)
                ))
            apply_theme(fig2, "", "Month", "Avg Score", 360)
            st.plotly_chart(fig2, use_container_width=True)
            insight("Groups trending downward after mid-term signal pacing issues — difficulty ramps faster than students absorb.")


def page_performance():
    section("Q2 — SCORE DISTRIBUTION BY ASSESSMENT TYPE")
    ass = load("assessment_type_stats")
    grades = load("grades", projection={"_id": 0, "type": 1, "score": 1})

    if not grades.empty:
        type_order = ass.sort_values("mean", ascending=False)["type"].tolist()
        colors_map = {"quiz": BLUE, "assignment": GREEN, "practical": YELLOW, "exam": RED}
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
        insight("Exams show the <strong>widest spread</strong> — polarised outcomes between top and bottom performers. Quizzes are the most consistent predictor of overall grade.")

    section("Q3 — BEST & WORST COURSE BY AVERAGE GRADE")
    grades_full = load("grades", projection={"_id": 0, "course_id": 1, "score": 1})
    courses     = load("courses", projection={"_id": 0, "course_id": 1, "course_name": 1})
    if not grades_full.empty and not courses.empty:
        merged = grades_full.merge(courses, on="course_id", how="left")
        course_avg = merged.groupby("course_name")["score"].agg(
            avg="mean", std="std").reset_index().sort_values("avg", ascending=False)
        bar_colors = [GREEN] + [BLUE] * (len(course_avg) - 2) + [RED]
        fig3 = go.Figure(go.Bar(
            x=course_avg["course_name"], y=course_avg["avg"].round(1),
            error_y=dict(type="data", array=course_avg["std"].round(1),
                         visible=True, color=MUTED),
            marker_color=bar_colors,
            text=course_avg["avg"].round(1), textposition="outside"
        ))
        fig3.add_hline(y=course_avg["avg"].mean(), line_dash="dot",
                       line_color=MUTED, annotation_text="Platform avg",
                       annotation_font_color=MUTED)
        apply_theme(fig3, "", "", "Avg Score", 380)
        fig3.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig3, use_container_width=True)
        best  = course_avg.iloc[0]
        worst = course_avg.iloc[-1]
        insight(f"<strong>{best['course_name']}</strong> leads at {best['avg']:.1f} pts. "
                f"<strong>{worst['course_name']}</strong> trails at {worst['avg']:.1f} — a "
                f"{best['avg']-worst['avg']:.1f}-pt gap warranting a curriculum review.")


def page_engagement():
    section("Q4 — ATTENDANCE RATE VS AVERAGE GRADE")
    sf = load("student_profiles")
    sf = apply_group_filter(sf, st.session_state.get("selected_gids", []))
    if not sf.empty:
        corr = sf["attendance_rate"].corr(sf["avg_grade"])
        fig = px.scatter(
            sf, x="attendance_rate", y="avg_grade",
            color="group_id", opacity=0.65,
            color_discrete_sequence=[BLUE, GREEN, RED, YELLOW, PURPLE,
                                      "#00D4FF", "#FF6B35", "#A8FF3E", "#FF3EA8", "#3EFFDC"],
            labels={"attendance_rate": "Attendance Rate",
                    "avg_grade": "Avg Grade", "group_id": "Group"},
            hover_data=["full_name", "group_id"]
        )
        q4 = sf[["attendance_rate", "avg_grade"]].dropna()
        slope, intercept = np.polyfit(q4["attendance_rate"], q4["avg_grade"], 1)
        xl = [float(q4["attendance_rate"].min()), float(q4["attendance_rate"].max())]
        fig.add_trace(go.Scatter(
            x=xl, y=[slope * x + intercept for x in xl],
            mode="lines", line=dict(color=YELLOW, width=2.5),
            name="Trend", showlegend=False
        ))
        apply_theme(fig, f"Pearson r = {corr:.3f}", "Attendance Rate", "Avg Grade", 420)
        fig.update_xaxes(tickformat=".0%")
        fig.update_traces(marker=dict(size=5), selector=dict(mode="markers"))
        st.plotly_chart(fig, use_container_width=True)

        q4b = sf[["attendance_rate", "avg_grade"]].dropna().copy()
        q4b["attendance_band"] = pd.cut(
            q4b["attendance_rate"],
            bins=[0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            labels=["<50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
        )
        band_stats = q4b.groupby("attendance_band", observed=True)["avg_grade"].mean().reset_index()
        fig_band = go.Figure(go.Bar(
            x=band_stats["attendance_band"].astype(str),
            y=band_stats["avg_grade"].round(1),
            marker_color=BLUE,
            text=band_stats["avg_grade"].round(1), textposition="outside"
        ))
        apply_theme(fig_band, "Avg Grade by Attendance Band", "Attendance Band", "Avg Grade", 340)
        st.plotly_chart(fig_band, use_container_width=True)
        insight(f"Pearson r = <strong>{corr:.3f}</strong> — moderate positive link. "
                "Students attending >80% average ~10 pts higher than those below 50%.")

    section("Q5 — ENGAGEMENT VS PERFORMANCE")
    if not sf.empty:
        c1, c2 = st.columns(2)
        for col, xcol, xlab, color in [
            (c1, "login_count",      "Login Count",         BLUE),
            (c2, "total_watch_time", "Watch Time (sec)",    PURPLE),
        ]:
            with col:
                q5 = sf[[xcol, "avg_grade"]].dropna()
                r = q5[xcol].corr(q5["avg_grade"])
                fig_e = px.scatter(q5, x=xcol, y="avg_grade",
                                   opacity=0.55,
                                   color_discrete_sequence=[color],
                                   labels={xcol: xlab, "avg_grade": "Avg Grade"})
                slope, intercept = np.polyfit(q5[xcol], q5["avg_grade"], 1)
                xl = [float(q5[xcol].min()), float(q5[xcol].max())]
                fig_e.add_trace(go.Scatter(
                    x=xl, y=[slope * x + intercept for x in xl],
                    mode="lines", line=dict(color=YELLOW, width=2),
                    showlegend=False
                ))
                apply_theme(fig_e, f"r = {r:.3f}", xlab, "Avg Grade", 340)
                fig_e.update_traces(marker=dict(size=4, color=color), selector=dict(mode="markers"))
                st.plotly_chart(fig_e, use_container_width=True)
        insight("Failed concepts (r ≈ −0.85) is the strongest predictor — far ahead of watch time or logins. "
                "<strong>Mastery drives grades, not passive consumption.</strong>")

    section("Q9 — ATTENDANCE & ENGAGEMENT OVER THE TERM")
    ts_att = load("time_series_attendance")
    ts_eng = load("time_series_engagement")
    if not ts_att.empty and not ts_eng.empty:
        merged = ts_att.merge(ts_eng, on="month", how="outer").sort_values("month")
        fig9 = make_subplots(specs=[[{"secondary_y": True}]])
        fig9.add_trace(go.Scatter(
            x=merged["month"], y=merged["attendance_pct"],
            mode="lines+markers", name="Attendance %",
            line=dict(color=BLUE, width=2.5),
            fill="tozeroy", fillcolor=f"rgba(75,123,255,0.08)"
        ), secondary_y=False)
        fig9.add_trace(go.Bar(
            x=merged["month"], y=merged["event_count"],
            name="Engagement Events", marker_color=f"rgba(255,183,0,0.45)"
        ), secondary_y=True)
        apply_theme(fig9, "", "Month", "", 380)
        fig9.update_yaxes(title_text="Attendance (%)", secondary_y=False, range=[0, 100])
        fig9.update_yaxes(title_text="Events", secondary_y=True)
        st.plotly_chart(fig9, use_container_width=True)
        insight("Simultaneous dips in both metrics point to a <strong>cohort-wide event</strong> — "
                "cross-reference with the academic calendar (holidays, midterms, platform outages).")


def page_concepts():
    section("Q6 — WEAKEST CONCEPTS BY FAILURE RATE")
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
            textposition="outside"
        ))
        fig.add_vline(x=40, line_dash="dash", line_color=MUTED,
                      annotation_text="40% threshold", annotation_font_color=MUTED)
        apply_theme(fig, "", "Fail Rate (%)", "", 480)
        fig.update_xaxes(range=[0, 105])
        fig.update_layout(margin=dict(l=260))
        st.plotly_chart(fig, use_container_width=True)

        worst = cf.loc[cf["avg_score"].idxmin()]
        insight(f"Biggest weak spot: <strong>{worst['concept_name']}</strong> "
                f"in {worst['course_name']} — "
                f"{worst['avg_score']:.1f}% avg score, {worst['fail_rate']:.1f}% fail rate. "
                "Targeted remedial sessions on the bottom 3 concepts would have the highest ROI.")

    section("Q7 — MASTERY TREND FOR WEAKEST CONCEPT")
    concepts_raw = load("concepts", projection={"_id": 0, "concept_name": 1,
                                                 "course_id": 1, "score_pct": 1,
                                                 "mastery_status": 1, "timestamp": 1})
    if not concepts_raw.empty and not cf.empty:
        worst_name    = cf.loc[cf["avg_score"].idxmin(), "concept_name"]
        worst_course  = cf.loc[cf["avg_score"].idxmin(), "course_id"]
        q7 = concepts_raw[
            (concepts_raw["concept_name"] == worst_name) &
            (concepts_raw["course_id"]    == worst_course)
        ].copy()
        q7["month"] = pd.to_datetime(q7["timestamp"]).dt.to_period("M").astype(str)
        monthly = q7.groupby("month").agg(
            avg_score=("score_pct", "mean"),
            pass_rate=("mastery_status", lambda x: (x == "passed").mean() * 100),
            n=("score_pct", "count")
        ).reset_index()

        fig7 = make_subplots(specs=[[{"secondary_y": True}]])
        fig7.add_trace(go.Bar(x=monthly["month"], y=monthly["n"],
            name="# Records", marker_color=f"rgba(75,123,255,0.2)"), secondary_y=True)
        fig7.add_trace(go.Scatter(x=monthly["month"], y=monthly["avg_score"],
            mode="lines+markers", name="Avg Score %",
            line=dict(color=BLUE, width=3), marker=dict(size=8)), secondary_y=False)
        fig7.add_trace(go.Scatter(x=monthly["month"], y=monthly["pass_rate"],
            mode="lines+markers", name="Pass Rate %",
            line=dict(color=GREEN, width=3, dash="dot"), marker=dict(size=8,symbol="diamond")), secondary_y=False)
        fig7.add_hline(y=60, line_dash="dash", line_color=RED,
                       annotation_text="Pass threshold 60%", annotation_font_color=RED)
        apply_theme(fig7, f"'{worst_name}' — Monthly Mastery", "Month", "", 380)
        fig7.update_yaxes(title_text="Score / Pass Rate (%)", range=[0, 100], secondary_y=False)
        fig7.update_yaxes(title_text="Count", secondary_y=True)
        st.plotly_chart(fig7, use_container_width=True)

        if len(monthly) >= 2:
            slope = monthly["avg_score"].iloc[-1] - monthly["avg_score"].iloc[0]
            trend = "improving 📈" if slope > 1 else ("declining 📉" if slope < -1 else "flat ➡️")
            insight(f"Trend is <strong>{trend}</strong> ({slope:+.1f} pts over the term). "
                    "A flat or declining slope means the issue is structural — students are not self-correcting.")


def page_risk():
    section("Q14 — AT-RISK STUDENT RANKING")
    risk = load("at_risk_ranking")
    risk = apply_group_filter(risk, st.session_state.get("selected_gids", []))
    if not risk.empty:
        top10 = risk.nlargest(10, "risk_score")
        risk_color = {
            "High Risk":   RED,
            "Medium Risk": YELLOW,
            "Low Risk":    GREEN,
        }
        dist = risk["risk_level"].value_counts().reset_index()
        dist.columns = ["level", "count"]

        c1, c2 = st.columns([2, 1])
        with c1:
            fig = go.Figure(go.Bar(
                x=top10["risk_score"],
                y=top10["full_name"],
                orientation="h",
                marker_color=[risk_color.get(str(r), BLUE) for r in top10["risk_level"]],
                text=[f"att:{a:.0%}  grade:{g:.0f}  fail:{f:.0f}"
                      for a, g, f in zip(top10["attendance_rate"],
                                         top10["avg_grade"],
                                         top10["failed_concepts"])],
                textposition="outside"
            ))
            apply_theme(fig, "Top 10 — contact these students first", "Risk Score", "", 400)
            fig.update_xaxes(range=[0, 0.85])
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

        insight("The top 10 at-risk students share: attendance <50%, avg grade <60, 10+ failed concepts. "
                "<strong>Contact them in the first week of the next term</strong> — early intervention has the highest ROI.")

        section("Q8 — LATE SUBMISSION EFFECT ON GRADES")
        subs = load("submissions", projection={"_id": 0, "student_id": 1,
                                                "course_id": 1, "is_late": 1})
        grades_raw = load("grades", projection={"_id": 0, "student_id": 1,
                                                  "course_id": 1, "score": 1})
        if not subs.empty and not grades_raw.empty:
            avg_g = grades_raw.groupby(["student_id", "course_id"])["score"].mean().reset_index()
            q8 = subs.merge(avg_g, on=["student_id", "course_id"], how="left").dropna(subset=["score"])
            q8["status"] = q8["is_late"].map({True: "Late", False: "On Time"})
            stats8 = q8.groupby("status")["score"].agg(["mean", "std"]).round(2)

            fig8 = go.Figure()
            for status, color in [("On Time", GREEN), ("Late", RED)]:
                vals = q8[q8["status"] == status]["score"]
                fig8.add_trace(go.Box(y=vals, name=status, marker_color=color,
                                      boxmean=True, boxpoints="outliers"))
            apply_theme(fig8, "", "Submission Status", "Avg Grade", 360)
            st.plotly_chart(fig8, use_container_width=True)
            if "On Time" in stats8.index and "Late" in stats8.index:
                gap = stats8.loc["On Time", "mean"] - stats8.loc["Late", "mean"]
                insight(f"On-time submitters score <strong>{gap:.1f} pts higher</strong> on average. "
                        "A 48-hour deadline reminder could close most of this gap.")

        subs_full = load("submissions", projection={"_id": 0, "student_id": 1,
                                                      "assessment_id": 1,
                                                      "deadline": 1, "submitted_at": 1})
        grades_score = load("grades", projection={"_id": 0, "assessment_id": 1,
                                                    "student_id": 1, "score": 1})
        if not subs_full.empty and not grades_score.empty:
            subs_full["deadline"] = pd.to_datetime(subs_full["deadline"], errors="coerce")
            subs_full["submitted_at"] = pd.to_datetime(subs_full["submitted_at"], errors="coerce")
            subs_scored = subs_full.merge(
                grades_score, on=["assessment_id", "student_id"], how="left"
            ).dropna(subset=["score"])
            subs_scored["days_before"] = (
                (subs_scored["deadline"] - subs_scored["submitted_at"]).dt.total_seconds() / 86400
            )
            subs_scored["timing"] = pd.cut(
                subs_scored["days_before"],
                bins=[-999, 0, 1, 3, 999],
                labels=["Late (after deadline)", "Same day (0-1d)", "1-3 days early", ">3 days early"]
            )
            bucket = subs_scored.groupby("timing", observed=True)["score"].mean().round(1).reset_index()
            color_map = {
                "Late (after deadline)": RED,
                "Same day (0-1d)": YELLOW,
                "1-3 days early": BLUE,
                ">3 days early": GREEN
            }
            fig8b = go.Figure(go.Bar(
                x=bucket["timing"].astype(str),
                y=bucket["score"],
                marker_color=[color_map.get(t, BLUE) for t in bucket["timing"].astype(str)],
                text=bucket["score"], textposition="outside", width=0.5
            ))
            apply_theme(fig8b, "Avg Score by Submission Timing", "Submission Timing", "Avg Score", 360)
            fig8b.update_yaxes(range=[0, bucket["score"].max() + 15])
            st.plotly_chart(fig8b, use_container_width=True)


def page_segments():
    section("Q11 — STUDENT SEGMENTATION")
    gids = st.session_state.get("selected_gids", [])
    clusters = load("cluster_assignments")
    clusters = apply_group_filter(clusters, gids)

    sf11 = load("student_profiles")
    sf11 = apply_group_filter(sf11, gids)
    if not sf11.empty:
        feats = ["avg_grade", "attendance_rate", "login_count", "total_watch_time", "failed_concepts"]
        feats = [f for f in feats if f in sf11.columns]
        if feats:
            X = sf11[feats].fillna(0).to_numpy(dtype=float)
            mean = X.mean(axis=0)
            std = X.std(axis=0)
            std[std == 0] = 1
            X_sc = (X - mean) / std

            _, labels_arr, _ = kmeans_fit(X_sc, 4)

            sf11_labeled = sf11[feats].fillna(0).copy()
            sf11_labeled["cluster"] = labels_arr

            c_means = sf11_labeled.groupby("cluster")[feats].mean().reset_index()
            c_norm = c_means.copy()
            cmin = c_means[feats].min()
            cmax = c_means[feats].max()
            crange = (cmax - cmin).replace(0, 1)
            c_norm[feats] = (c_means[feats] - cmin) / crange

            med = c_means[feats].median()
            seg_labels = []
            for _, row in c_means.iterrows():
                if row["avg_grade"] >= med["avg_grade"] and row["attendance_rate"] >= med["attendance_rate"]:
                    seg_labels.append("High Achiever")
                elif row["avg_grade"] < med["avg_grade"] and row["attendance_rate"] < med["attendance_rate"]:
                    seg_labels.append("At Risk")
                elif row["login_count"] < med["login_count"]:
                    seg_labels.append("Disengaged")
                else:
                    seg_labels.append("Average")

            c_norm["segment"] = [f"C{int(r['cluster'])} - {seg_labels[i]}"
                                  for i, (_, r) in enumerate(c_norm.iterrows())]

            melted = c_norm.melt(id_vars="segment", value_vars=feats)
            fig_profiles = px.bar(
                melted, x="variable", y="value",
                color="segment", barmode="group",
                color_discrete_sequence=[BLUE, GREEN, RED, PURPLE],
                labels={"variable": "Feature", "value": "Normalized (0-1)", "segment": "Segment"},
            )
            apply_theme(fig_profiles, "Cluster Profiles (Normalized 0-1)",
                        "Feature", "Normalized Score", 380)
            st.plotly_chart(fig_profiles, use_container_width=True)

    if not clusters.empty:
        seg_order = clusters["cluster_label"].unique().tolist()
        seg_colors = {seg: c for seg, c in zip(seg_order, [BLUE, GREEN, RED, PURPLE])}
        c1, c2 = st.columns([1.6, 1])
        with c1:
            fig = px.scatter(
                clusters,
                x="attendance_rate", y="avg_grade",
                color="cluster_label",
                color_discrete_map=seg_colors,
                opacity=0.7,
                labels={"attendance_rate": "Attendance Rate",
                        "avg_grade": "Avg Grade",
                        "cluster_label": "Segment"},
            )
            apply_theme(fig, "Cluster View: Grade vs Attendance",
                        "Attendance Rate", "Avg Grade", 440)
            fig.update_xaxes(tickformat=".0%")
            fig.update_traces(marker=dict(size=7))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            counts = clusters["cluster_label"].value_counts().reset_index()
            counts.columns = ["segment", "n"]
            fig2 = go.Figure(go.Pie(
                labels=counts["segment"], values=counts["n"],
                marker_colors=[seg_colors.get(s, BLUE) for s in counts["segment"]],
                textinfo="label+value", hole=0.4,
                textfont=dict(color=TEXT)
            ))
            apply_theme(fig2, "Segment Sizes", height=440)
            st.plotly_chart(fig2, use_container_width=True)

        insight("<strong>At Risk</strong> students need direct instructor contact — not automated emails. "
                "<strong>Disengaged</strong> students are the most responsive to a single well-timed nudge.")

    section("Q10 — AGE BANDS VS OUTCOMES")
    sf = load("student_profiles")
    sf = apply_group_filter(sf, gids)
    if not sf.empty and "age" in sf.columns:
        sf["age_band"] = pd.cut(sf["age"], bins=[0, 20, 25, 30, 40, 100],
                                 labels=["≤20", "21–25", "26–30", "31–40", "41+"])
        age_stats = sf.groupby("age_band", observed=False).agg(
            avg_grade=("avg_grade", "mean"),
            att_pct=("attendance_rate", lambda x: x.mean() * 100),
            logins=("login_count", "mean"),
            n=("student_id", "count")
        ).reset_index()
        fig_age = go.Figure()
        fig_age.add_trace(go.Bar(name="Avg Grade", x=age_stats["age_band"].astype(str),
            y=age_stats["avg_grade"].round(1), marker_color=BLUE,
            text=age_stats["avg_grade"].round(1), textposition="outside"))
        fig_age.add_trace(go.Bar(name="Attendance %", x=age_stats["age_band"].astype(str),
            y=age_stats["att_pct"].round(1), marker_color=GREEN,
            text=age_stats["att_pct"].round(1), textposition="outside"))
        apply_theme(fig_age, "", "Age Band", "", 360)
        fig_age.update_layout(barmode="group")
        st.plotly_chart(fig_age, use_container_width=True)
        insight("21–25 band leads in both grade and engagement — traditional full-time learners. "
                "31–40 show lower attendance but comparable grades, suggesting self-directed efficiency.")

        bands = ["≤20", "21–25", "26–30", "31–40", "41+"]
        fig_box = make_subplots(rows=1, cols=3,
            subplot_titles=["Grade Distribution", "Attendance Rate (%)", "Login Count"])
        for col_idx, (ycol, color, scale) in enumerate([
            ("avg_grade", BLUE, 1), ("attendance_rate", GREEN, 100), ("login_count", PURPLE, 1)
        ], 1):
            for band in bands:
                subset = sf[sf["age_band"] == band][ycol].dropna() * scale
                fig_box.add_trace(go.Box(
                    y=subset, name=band, marker_color=color,
                    boxmean=True, showlegend=(col_idx == 1), legendgroup=band,
                ), row=1, col=col_idx)
        fig_box.update_layout(
            title=dict(text="Outcomes by Age Band  (Box = spread, dot = mean)",
                       font=dict(size=14, color=TEXT, family="Inter"), x=0, xanchor="left"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=BG,
            font=dict(color=TEXT, family="Inter", size=11),
            margin=dict(t=80, b=40), boxmode="group", height=400,
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, font=dict(color=TEXT)),
        )
        fig_box.update_xaxes(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED))
        fig_box.update_yaxes(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED))
        st.plotly_chart(fig_box, use_container_width=True)


def page_groups():
    section("Q12 — STATED VS ACTUAL GROUP SIZES")
    groups = load("group_summaries")
    if not groups.empty and "stated_num_students" not in groups.columns:
        insight("Run the notebook to store stated_num_students in group_summaries, or check groups collection.")
    else:
        groups_raw = load("groups")
        if not groups_raw.empty and "stated_num_students" in groups_raw.columns:
            q12 = groups_raw[["group_id", "group_name", "stated_num_students"]].merge(
                groups[["group_id", "num_students"]], on="group_id", how="left"
            )
            q12["discrepancy"] = q12["num_students"] - q12["stated_num_students"]

            fig = make_subplots(rows=2, cols=1,
                subplot_titles=("Stated vs Actual", "Discrepancy"),
                row_heights=[0.6, 0.4], shared_xaxes=True)
            fig.add_trace(go.Bar(x=q12["group_id"], y=q12["stated_num_students"],
                name="Stated", marker_color=f"rgba(75,123,255,0.45)"), row=1, col=1)
            fig.add_trace(go.Bar(x=q12["group_id"], y=q12["num_students"],
                name="Actual", marker_color=BLUE), row=1, col=1)
            disc_colors = [RED if abs(d) > 2 else GREEN for d in q12["discrepancy"]]
            fig.add_trace(go.Bar(x=q12["group_id"], y=q12["discrepancy"],
                name="Diff", marker_color=disc_colors,
                text=q12["discrepancy"], textposition="outside"), row=2, col=1)
            fig.add_hline(y=0, line_color=MUTED, row=2, col=1)
            apply_theme(fig, "", "", "", 480)
            fig.update_layout(barmode="group")
            st.plotly_chart(fig, use_container_width=True)
            insight("Groups with |discrepancy| > 2 indicate unrecorded dropouts or data entry errors — audit these before term end.")

    section("Q13 — NON-VIABLE GROUP IDENTIFICATION")
    if not groups.empty:
        smallest = groups.nsmallest(1, "num_students").iloc[0]
        st.markdown(f"""
        <div class="insight-box">
            <strong style="color:{RED};">Non-viable group: {smallest['group_id']}</strong>
            with only <strong>{int(smallest['num_students'])}</strong> enrolled student(s).<br><br>
            No peer interaction, disproportionate instructor load, and statistically unreliable metrics.
            Closest match by concept profile should absorb this group's student(s).
            <strong>Recommendation: merge into the nearest group on the same course.</strong>
        </div>
        """, unsafe_allow_html=True)

        concepts = load("concepts")
        students_raw = load("students")
        if not concepts.empty and not students_raw.empty:
            target_gid = smallest["group_id"]
            target_name = smallest["group_name"]

            concept_pivot = (
                concepts.groupby(["student_id", "concept_name"])["score_pct"]
                .mean().unstack(fill_value=0)
            )
            stu_group_map = students_raw.set_index("student_id")["group_id"]
            concept_pivot = concept_pivot.join(stu_group_map, how="left")

            def group_profile(gid):
                rows = concept_pivot[concept_pivot["group_id"] == gid].drop(columns="group_id")
                return rows.mean() if len(rows) > 0 else None

            target_vec = group_profile(target_gid)
            other_groups = groups[groups["group_id"] != target_gid]

            sims = {}
            for _, row in other_groups.iterrows():
                v = group_profile(row["group_id"])
                if v is not None and target_vec is not None:
                    s = cosine_sim(target_vec.fillna(0).values, v.fillna(0).values)
                    sims[row["group_name"]] = round(float(s), 4)

            sim_df = pd.Series(sims).sort_values(ascending=False).reset_index()
            sim_df.columns = ["group_name", "similarity"]

            top4 = sim_df[sim_df["similarity"] > 0].head(4)
            if len(top4) == 0:
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
                fig.update_traces(textposition="outside")
                fig.update_layout(xaxis_range=[0, 1.05], coloraxis_showscale=False)
                apply_theme(fig, f"Top Matches for {target_name}",
                            "Cosine Similarity", "", 380)
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                all_gids = groups["group_id"].tolist()
                all_gnames = groups["group_name"].tolist()
                n = len(all_gids)
                mat = np.zeros((n, n))
                for i, gi in enumerate(all_gids):
                    vi = group_profile(gi)
                    for j, gj in enumerate(all_gids):
                        vj = group_profile(gj)
                        if vi is not None and vj is not None:
                            mat[i, j] = round(cosine_sim(vi.fillna(0).values, vj.fillna(0).values), 3)

                fig_hm = go.Figure(go.Heatmap(
                    z=mat,
                    x=all_gnames, y=all_gnames,
                    colorscale=[[0, BG], [0.5, BLUE], [1, GREEN]],
                    zmin=0, zmax=1,
                    text=np.round(mat, 2),
                    texttemplate="%{text}",
                    textfont=dict(size=9),
                    colorbar=dict(title="Similarity", tickfont=dict(color=TEXT)),
                ))
                apply_theme(fig_hm, "Group-to-Group Concept Similarity", "", "", 380)
                fig_hm.update_layout(
                    margin=dict(t=50, b=80, l=80, r=20),
                    xaxis=dict(tickangle=-45, gridcolor=GRID),
                    yaxis=dict(gridcolor=GRID),
                )
                st.plotly_chart(fig_hm, use_container_width=True)

            if len(sim_df):
                closest = sim_df.iloc[0]
                insight(f"Recommended merge target: <strong>{closest['group_name']}</strong> "
                        f"(similarity = {closest['similarity']:.4f})")


# ── Sidebar nav ───────────────────────────────────────────────────────────────
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

        pages = {
            "📊  Overview":         "overview",
            "🎓  Performance":      "performance",
            "⚡  Engagement":       "engagement",
            "🧠  Concepts":         "concepts",
            "🚨  At-Risk":          "risk",
            "🔵  Segments":         "segments",
            "👥  Groups":           "groups",
        }
        if "page" not in st.session_state:
            st.session_state["page"] = "overview"

        for label, key in pages.items():
            active = st.session_state["page"] == key
            btn_style = (f"background:rgba(75,123,255,0.15);border:1px solid {BLUE};"
                         if active else "background:transparent;border:1px solid transparent;")
            if st.button(label, key=f"nav_{key}",
                         use_container_width=True):
                st.session_state["page"] = key
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        user = st.session_state.get("user", {})
        st.markdown(f"""
        <div style="border-top:1px solid {BORDER};padding-top:16px;font-size:11px;color:{MUTED};">
            Signed in as<br>
            <span style="color:{TEXT};font-weight:600;">{user.get('username','—')}</span>
            <span style="color:{BLUE};"> · {user.get('role','')}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Sign Out", key="signout"):
            del st.session_state["user"]
            st.rerun()

    return st.session_state.get("page", "overview")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if "user" not in st.session_state:
        login_page()
        return

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
