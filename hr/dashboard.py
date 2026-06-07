import streamlit as st
import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(
    page_title="HR Attrition Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* ── Global dark background ── */
    .stApp { background-color: #0d1117; }
    section[data-testid="stSidebar"] {
        background-color: #0d1117 !important;
        border-right: 1px solid #1e2a3a;
    }
    .block-container { padding-top: 1.2rem !important; }

    /* ── KPI cards ── */
    div[data-testid="stMetric"] {
        border-radius: 14px;
        padding: 20px 24px;
        color: #ffffff !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700;
        color: #ffffff !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: rgba(255,255,255,0.75) !important;
    }
    div[data-testid="stMetricDelta"] svg { display: none; }
    div[data-testid="stMetricDelta"] > div {
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.85rem !important;
    }

    /* card colour by position using nth-child */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a3a5c, #1e5799);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #7b1a1a, #c0392b);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #7b4a00, #e67e22);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a4a2e, #27ae60);
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #2a1a5c, #8e44ad);
    }

    /* ── Insight box ── */
    .insight-box {
        border-left: 4px solid #3a8fd1;
        background: rgba(58,143,209,0.12);
        padding: 14px 18px;
        border-radius: 0 10px 10px 0;
        margin-top: 10px;
        color: #c9d8e8;
    }

    /* ── Text colours ── */
    h1, h2, h3, h4, h5, p, label, span, div {
        color: #e0eaf5 !important;
    }
    .stMarkdown p { color: #b0c4d8 !important; }

    /* ── Sidebar text ── */
    section[data-testid="stSidebar"] * { color: #c0d0e0 !important; }

    /* ── Expander ── */
    details { background: #111827 !important; border-radius: 8px !important; }
    summary { color: #7ab3d4 !important; }

    /* ── Selectbox / dropdowns ── */
    div[data-baseweb="select"] > div {
        background-color: #1a2332 !important;
        border-color: #2a3f55 !important;
        color: #c0d8f0 !important;
    }

    /* ── Tabs ── */
    button[data-baseweb="tab"] { color: #7ab3d4 !important; }
    button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom: 3px solid #3a8fd1 !important;
        color: #3a8fd1 !important;
    }

    /* ── Divider ── */
    hr { border-color: #1e2a3a !important; }
</style>
""", unsafe_allow_html=True)

# ── Colour palette ─────────────────────────────────────────────────────────────
BLUE   = "#3a8fd1"
RED    = "#e74c3c"
GREEN  = "#2ecc71"
ORANGE = "#f39c12"
PURPLE = "#9b59b6"

LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#111827",
    plot_bgcolor="#111827",
    font=dict(color="#c9d8e8", family="Arial"),
    margin=dict(t=55, b=40, l=40, r=20),
    title_font=dict(size=14, color="#e0eaf5"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#c9d8e8"))
)

@st.cache_data
def load_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return pd.read_csv(os.path.join(BASE_DIR, "data", "predictions.csv"))

df = load_data()

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
logo_path = Path(os.path.join(BASE_DIR, "assets", "logo.png"))

def insight_box(text: str):
    st.markdown(
        f'<div class="insight-box"><strong>Insight & Action</strong><br>{text}</div>',
        unsafe_allow_html=True
    )

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    job_roles    = ["All"] + sorted(df["job_role"].dropna().unique().tolist())
    genders      = ["All"] + sorted(df["gender"].dropna().unique().tolist())
    job_levels   = ["All"] + sorted(df["job_level"].dropna().unique().tolist())
    risk_options = ["All", "High Risk", "Medium Risk", "Low Risk"]

    selected_role   = st.selectbox("Job Role",   job_roles)
    selected_gender = st.selectbox("Gender",     genders)
    selected_level  = st.selectbox("Job Level",  job_levels)
    selected_risk   = st.selectbox("Risk Label", risk_options)

    st.markdown("---")
    st.caption(f"Total records: {len(df):,}")

# if logo_path.exists():
#     with open(logo_path, "rb") as f:
#         img_base64 = base64.b64encode(f.read()).decode()

#     col1, col2, col3 = st.columns([1, 2, 1])

#     with col2:
#         st.markdown(
#             f"""
#             <div style="display:flex; justify-content:center;">
#                 <img src="data:image/png;base64,{img_base64}"
#                      style="
#                          width:200px;
#                          height:200px;
#                          border-radius:50%;
#                          object-fit:cover;
#                      ">
#             </div>
#             """,
#             unsafe_allow_html=True
#         )

# ── Filtering ──────────────────────────────────────────────────────────────────
filtered = df.copy()
if selected_role   != "All": filtered = filtered[filtered["job_role"]   == selected_role]
if selected_gender != "All": filtered = filtered[filtered["gender"]     == selected_gender]
if selected_level  != "All": filtered = filtered[filtered["job_level"]  == selected_level]
if selected_risk   != "All": filtered = filtered[filtered["risk_label"] == selected_risk]

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — HOME & KPIs
# ══════════════════════════════════════════════════════════════════════════════
def page_home():
    col_title, col_logo = st.columns([4, 1])
    with col_title:
        st.markdown("## Workforce Attrition")
        st.markdown("*Understanding why employees leave — and what HR can do about it.*")
    with col_logo:
        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)

    st.markdown("---")

    total         = len(filtered)
    actual_left   = int((filtered["attrition"] == 1).sum())
    pred_high     = int((filtered["risk_label"] == "High Risk").sum())
    avg_income    = filtered["monthly_income"].mean()
    avg_tenure    = filtered["years_at_company"].mean()
    attrition_pct = actual_left / total * 100 if total > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Employees",     f"{total:,}")
    c2.metric("Employees Who Left",  f"{actual_left:,}", delta=f"{attrition_pct:.1f}%", delta_color="inverse")
    c3.metric("High Risk (Model)",   f"{pred_high:,}")
    c4.metric("Avg Monthly Income",  f"${avg_income:,.0f}")
    c5.metric("Avg Tenure",          f"{avg_tenure:.1f} yrs")

    st.markdown("---")

    stayed_count = int((filtered["attrition"] == 0).sum())
    left_count   = int((filtered["attrition"] == 1).sum())

    col_pie, col_role = st.columns(2)

    with col_pie:
        fig_pie = go.Figure(go.Pie(
            labels=["Stayed", "Left"],
            values=[stayed_count, left_count],
            hole=0.5,
            marker_colors=[BLUE, RED],
            textinfo="percent+label",
            textfont_size=14
        ))
        fig_pie.update_layout(
            title=f"Overall Attrition — {left_count / (stayed_count + left_count):.1%} of employees left",
            **LAYOUT
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_role:
        role_d = (
            filtered.groupby("job_role")["attrition"]
            .mean().reset_index()
            .rename(columns={"attrition": "Attrition Rate", "job_role": "Job Role"})
            .sort_values("Attrition Rate", ascending=False)
        )
        role_d["label"] = role_d["Attrition Rate"].map(lambda x: f"{x:.1%}")
        fig_role = px.bar(
            role_d, x="Job Role", y="Attrition Rate",
            title="Attrition Rate by Job Role — which roles leak the most talent?",
            color="Attrition Rate", color_continuous_scale="Reds", text="label"
        )
        fig_role.update_traces(textposition="outside")
        fig_role.update_yaxes(tickformat=".0%", title_text="Attrition Rate")
        fig_role.update_layout(**LAYOUT)
        fig_role.update_coloraxes(showscale=False)
        st.plotly_chart(fig_role, use_container_width=True)

    top_role = role_d.iloc[0]
    with st.expander("Insight & Action — Attrition Overview"):
        insight_box(
            f"<strong>{left_count/(stayed_count+left_count):.1%}</strong> of employees left overall. "
            f"<strong>{top_role['Job Role']}</strong> has the highest attrition at "
            f"<strong>{top_role['Attrition Rate']:.1%}</strong>. This role is the biggest talent leak "
            f"and should be the first priority — investigate workload, pay equity, and career path clarity there first."
        )

    st.markdown("---")

    risk_d = (
        filtered["risk_label"]
        .value_counts()
        .reindex(["High Risk", "Medium Risk", "Low Risk"])
        .reset_index()
    )
    risk_d.columns = ["Risk Level", "Count"]
    fig_risk = px.pie(
        risk_d, names="Risk Level", values="Count",
        title="Model-Predicted Employee Risk Distribution",
        color="Risk Level",
        color_discrete_map={"High Risk": RED, "Medium Risk": ORANGE, "Low Risk": GREEN},
        hole=0.45
    )
    fig_risk.update_traces(textinfo="percent+label", textfont_size=13)
    fig_risk.update_layout(**LAYOUT)
    st.plotly_chart(fig_risk, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — OVERTIME & REMOTE WORK
# ══════════════════════════════════════════════════════════════════════════════
def page_easy():
    st.markdown("## Overtime & Remote Work — How Work Conditions Affect Attrition")
    st.markdown("---")

    st.markdown("### Does Working Overtime Push Employees to Leave?")
    ot = (
        filtered.groupby("overtime")["attrition"]
        .mean().reset_index()
        .rename(columns={"overtime": "Overtime", "attrition": "Attrition Rate"})
    )
    ot["label"] = ot["Attrition Rate"].map(lambda x: f"{x:.1%}")

    fig_ot = px.bar(
        ot, x="Overtime", y="Attrition Rate",
        title="Overtime vs Attrition — employees working extra hours leave significantly more",
        color="Overtime",
        color_discrete_map={"Yes": RED, "No": GREEN},
        text="label"
    )
    fig_ot.update_traces(textposition="outside")
    fig_ot.update_yaxes(tickformat=".0%", title_text="Attrition Rate")
    fig_ot.update_xaxes(title_text="Overtime Status")
    fig_ot.update_layout(**LAYOUT)
    st.plotly_chart(fig_ot, use_container_width=True)

    ot_yes = ot.loc[ot["Overtime"] == "Yes", "Attrition Rate"].values
    ot_no  = ot.loc[ot["Overtime"] == "No",  "Attrition Rate"].values
    diff_txt = ""
    if len(ot_yes) and len(ot_no):
        diff = ot_yes[0] - ot_no[0]
        diff_txt = (f"Overtime employees leave at <strong>{ot_yes[0]:.1%}</strong> vs "
                    f"<strong>{ot_no[0]:.1%}</strong> for non-overtime — a "
                    f"<strong>{diff:.1%} gap</strong>.")

    with st.expander("Insight & Action — Overtime"):
        insight_box(
            f"{diff_txt} Overtime is a direct burnout signal. "
            "<strong>Action:</strong> Audit teams with the highest overtime rates. "
            "Cap mandatory overtime, introduce compensatory time-off, and track workload "
            "distribution. This is one of the most actionable levers HR has."
        )

    st.markdown("---")

    st.markdown("### Does Offering Remote Work Help Retain Employees?")
    col_r1, col_r2 = st.columns([1, 1])

    with col_r1:
        remote_rate = (
            filtered.groupby("remote_work")["attrition"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(columns={"remote_work": "Remote Work",
                              "mean": "Attrition Rate", "count": "Employees"})
        )
        remote_rate["label"] = remote_rate["Attrition Rate"].map(lambda x: f"{x:.1%}")
        remote_rate["% of Workforce"] = (remote_rate["Employees"] /
                                          remote_rate["Employees"].sum() * 100).round(1)

        fig_rem = px.bar(
            remote_rate, x="Remote Work", y="Attrition Rate",
            title="Remote Work vs Attrition — does flexibility keep employees?",
            color="Remote Work",
            color_discrete_map={"Yes": GREEN, "No": RED},
            text="label"
        )
        fig_rem.update_traces(textposition="outside")
        fig_rem.update_yaxes(tickformat=".0%", title_text="Attrition Rate")
        fig_rem.update_xaxes(title_text="Remote Work Status")
        fig_rem.update_layout(**LAYOUT)
        st.plotly_chart(fig_rem, use_container_width=True)

    with col_r2:
        fig_wf = px.pie(
            remote_rate, names="Remote Work", values="Employees",
            title="Share of Workforce — remote vs on-site",
            color="Remote Work",
            color_discrete_map={"Yes": GREEN, "No": BLUE},
            hole=0.4
        )
        fig_wf.update_traces(textinfo="percent+label")
        fig_wf.update_layout(**LAYOUT)
        st.plotly_chart(fig_wf, use_container_width=True)

    remote_pct = remote_rate.loc[remote_rate["Remote Work"] == "Yes", "% of Workforce"]
    remote_pct_txt = f"{remote_pct.values[0]:.1f}%" if len(remote_pct) else "a small share"

    with st.expander("Insight & Action — Remote Work"):
        insight_box(
            f"Remote employees show lower attrition, but only <strong>{remote_pct_txt}</strong> "
            "of the workforce works remotely — so the effect is promising but not conclusive. "
            "Remote roles may also attract more senior, better-paid staff who already leave less. "
            "<strong>Action:</strong> Expand remote eligibility for roles where output can be "
            "objectively measured. Run a 6-month pilot and track attrition before scaling."
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PAY, TENURE, ENGAGEMENT & LIFE STAGE
# ══════════════════════════════════════════════════════════════════════════════
def page_medium():
    st.markdown("## Pay, Tenure, Engagement & Life Stage — Who Leaves and When")
    st.markdown("---")

    st.markdown("### Does Pay Fairness Within the Same Level Affect Attrition?")

    bins_inc   = [0, 3000, 6000, 9000, 12000, 17000]
    labels_inc = ["<$3K", "$3K–6K", "$6K–9K", "$9K–12K", ">$12K"]
    f4 = filtered.copy()
    f4["income_band"] = pd.cut(f4["monthly_income"], bins=bins_inc, labels=labels_inc)

    level_map = {1: "Entry", 2: "Mid", 3: "Senior"}
    f4["Job Level"] = f4["job_level"].map(level_map).fillna(f4["job_level"].astype(str))

    pay = (
        f4.groupby(["Job Level", "income_band"], observed=True)["attrition"]
        .mean().reset_index()
        .rename(columns={"attrition": "Attrition Rate", "income_band": "Income Band"})
    )
    pay["Job Level"] = pd.Categorical(pay["Job Level"],
                                       categories=["Entry", "Mid", "Senior"], ordered=True)
    pay = pay.sort_values("Job Level")

    fig_pay = px.line(
        pay, x="Income Band", y="Attrition Rate", color="Job Level",
        markers=True,
        title="Pay Fairness — attrition drops as pay rises, but plateaus above $9K",
        color_discrete_sequence=[RED, ORANGE, GREEN],
        labels={"Attrition Rate": "Attrition Rate", "Income Band": "Monthly Income Band"}
    )
    fig_pay.update_yaxes(tickformat=".0%")
    fig_pay.update_layout(**LAYOUT)
    st.plotly_chart(fig_pay, use_container_width=True)

    with st.expander("Insight & Action — Pay Fairness"):
        insight_box(
            "Attrition is consistently highest in the lowest income bands at every job level. "
            "The effect plateaus above <strong>~$9K–12K/month</strong> — paying more beyond "
            "that threshold shows diminishing returns. "
            "<strong>Action:</strong> Audit pay bands for Entry and Mid-level employees "
            "earning below $6K. Close intra-level pay gaps before they drive departures. "
            "Focus raises on the bottom two quartiles within each level."
        )

    st.markdown("---")
    st.markdown("### At What Point in Their Career Are Employees Most Likely to Leave?")

    tenure_attr = (
        filtered.groupby("years_at_company")["attrition"]
        .mean().reset_index()
        .rename(columns={"years_at_company": "Years at Company", "attrition": "Attrition Rate"})
    )
    company_avg = filtered["attrition"].mean()

    fig_ten = px.line(
        tenure_attr, x="Years at Company", y="Attrition Rate",
        markers=True,
        title="Retention Timeline — attrition peaks early and again at mid-career",
    )
    fig_ten.update_traces(
        line_color=BLUE, line_width=3,
        marker=dict(size=8, color=BLUE)
    )
    fig_ten.add_hline(
        y=company_avg, line_dash="dash", line_color=RED,
        annotation_text=f"Company Average ({company_avg:.1%})",
        annotation_position="top right"
    )
    fig_ten.update_yaxes(tickformat=".0%")
    fig_ten.update_layout(**LAYOUT)
    st.plotly_chart(fig_ten, use_container_width=True)

    with st.expander("Insight & Action — Retention Timeline"):
        insight_box(
            "Attrition peaks in the <strong>first 1–3 years</strong> (new-hire honeymoon ends) "
            "and again around <strong>years 7–10</strong> (mid-career stagnation). "
            "Employees past 15 years show dramatically lower attrition. "
            "<strong>Action:</strong> (1) Invest in structured 90-day and 1-year onboarding. "
            "(2) Introduce mid-career growth reviews at years 5–8. "
            "(3) Publicly recognise long-tenure milestones to cement loyalty."
        )

    st.markdown("---")
    st.markdown("### Which Combination of Satisfaction & Work-Life Balance Is the Biggest Red Flag?")

    wlb_map  = {1: "Poor", 2: "Fair", 3: "Good", 4: "Excellent"}
    jsat_map = {1: "Low", 2: "Medium", 3: "High", 4: "Very High"}

    f6 = filtered.copy()
    f6["Work-Life Balance"] = f6["work-life_balance"].map(wlb_map)
    f6["Job Satisfaction"]  = f6["job_satisfaction"].map(jsat_map)

    hm = (
        f6.groupby(["Work-Life Balance", "Job Satisfaction"])["attrition"]
        .mean().reset_index()
        .rename(columns={"attrition": "Attrition Rate"})
        .pivot(index="Work-Life Balance", columns="Job Satisfaction",
               values="Attrition Rate")
    )
    wlb_order  = ["Poor", "Fair", "Good", "Excellent"]
    jsat_order = ["Low", "Medium", "High", "Very High"]
    hm = hm.reindex(index=wlb_order, columns=jsat_order)

    fig_hm = px.imshow(
        hm,
        title="Engagement Danger Zone — Poor WLB + Low Satisfaction is the highest-risk combination",
        color_continuous_scale="RdYlGn_r",
        zmin=0, zmax=1,
        text_auto=".1%",
        labels={"x": "Job Satisfaction", "y": "Work-Life Balance",
                "color": "Attrition Rate"}
    )
    fig_hm.update_layout(**LAYOUT, height=420)
    st.plotly_chart(fig_hm, use_container_width=True)

    with st.expander("Insight & Action — Engagement Warning Signs"):
        insight_box(
            "The <strong>top-left corner</strong> (Poor Work-Life Balance + Low Job Satisfaction) "
            "is the danger zone — this combination produces the highest attrition by far. "
            "<strong>Action:</strong> Flag employees who score low on both in pulse surveys. "
            "Trigger automatic 1-on-1 conversations with their manager within 2 weeks. "
            "Build this dual-signal alert into the next engagement survey cycle."
        )

    st.markdown("---")
    st.markdown("### Does an Employee's Life Stage Change Their Risk of Leaving?")

    age_bins   = list(range(18, 62, 4))
    age_labels = [f"{a}–{a+3}" for a in age_bins[:-1]]
    f7 = filtered.copy()
    f7["age_group"] = pd.cut(f7["age"], bins=age_bins, labels=age_labels, right=False)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        age_attr = (f7.groupby("age_group", observed=True)["attrition"]
                    .mean().reset_index()
                    .rename(columns={"age_group": "Age Group", "attrition": "Attrition Rate"}))
        age_attr["label"] = age_attr["Attrition Rate"].map(lambda x: f"{x:.1%}")
        fig_age = px.bar(age_attr, x="Age Group", y="Attrition Rate",
                          title="Attrition by Age Group",
                          color="Attrition Rate", color_continuous_scale="Blues_r",
                          text="label")
        fig_age.update_traces(textposition="outside")
        fig_age.update_yaxes(tickformat=".0%")
        fig_age.update_coloraxes(showscale=False)
        fig_age.update_layout(**LAYOUT)
        st.plotly_chart(fig_age, use_container_width=True)

    with col_b:
        ms_attr = (f7.groupby("marital_status")["attrition"]
                   .mean().reset_index()
                   .sort_values("attrition", ascending=False)
                   .rename(columns={"marital_status": "Marital Status", "attrition": "Attrition Rate"}))
        ms_attr["label"] = ms_attr["Attrition Rate"].map(lambda x: f"{x:.1%}")
        fig_ms = px.bar(ms_attr, x="Marital Status", y="Attrition Rate",
                         title="Attrition by Marital Status",
                         color="Attrition Rate", color_continuous_scale="Oranges",
                         text="label")
        fig_ms.update_traces(textposition="outside")
        fig_ms.update_yaxes(tickformat=".0%")
        fig_ms.update_coloraxes(showscale=False)
        fig_ms.update_layout(**LAYOUT)
        st.plotly_chart(fig_ms, use_container_width=True)

    with col_c:
        dep_attr = (f7.groupby("number_of_dependents")["attrition"]
                    .mean().reset_index()
                    .rename(columns={"number_of_dependents": "Number of Dependents",
                                     "attrition": "Attrition Rate"}))
        fig_dep = px.line(dep_attr, x="Number of Dependents", y="Attrition Rate",
                           markers=True,
                           title="Attrition by Number of Dependents")
        fig_dep.update_traces(line_color=BLUE, line_width=3,
                               marker=dict(size=9, color=RED))
        fig_dep.update_yaxes(tickformat=".0%")
        fig_dep.update_layout(**LAYOUT)
        st.plotly_chart(fig_dep, use_container_width=True)

    with st.expander("Insight & Action — Life Stage"):
        insight_box(
            "Young single employees (18–26, no dependents) show the highest attrition — "
            "they have the lowest switching costs and respond most strongly to career signals. "
            "<strong>Action:</strong> Offer this cohort an accelerated career track with "
            "visible milestones in the first 24 months. Mentoring programmes and transparent "
            "promotion timelines are the most effective retention levers for young single staff."
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — CAREER GROWTH, HIGH-RISK PROFILE & TOP DRIVERS
# ══════════════════════════════════════════════════════════════════════════════
def page_hard():
    st.markdown("## Career Growth, High-Risk Profiles & What HR Should Fix First")
    st.markdown("---")

    company_avg = filtered["attrition"].mean()

    st.markdown("### Does Feeling Stuck Drive Employees to Leave?")

    col_p, col_g = st.columns(2)

    with col_p:
        promo = (
            filtered.groupby("number_of_promotions")["attrition"]
            .agg(["mean", "count"]).reset_index()
            .rename(columns={"number_of_promotions": "Promotions",
                             "mean": "Attrition Rate", "count": "Employees"})
        )
        fig_promo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_promo.add_trace(go.Bar(
            x=promo["Promotions"], y=promo["Employees"],
            name="Employees", marker_color=BLUE, opacity=0.7
        ), secondary_y=False)
        fig_promo.add_trace(go.Scatter(
            x=promo["Promotions"], y=promo["Attrition Rate"],
            name="Attrition Rate", mode="lines+markers",
            line=dict(color=RED, width=3), marker=dict(size=9, color=RED)
        ), secondary_y=True)
        fig_promo.update_layout(
            title="Promotions vs Attrition — zero promotions have the highest exit rate",
            **LAYOUT)
        fig_promo.update_yaxes(title_text="Employee Count",  secondary_y=False)
        fig_promo.update_yaxes(title_text="Attrition Rate",  secondary_y=True, tickformat=".0%")
        st.plotly_chart(fig_promo, use_container_width=True)

    with col_g:
        level_map = {1: "Entry", 2: "Mid", 3: "Senior"}
        f8 = filtered.copy()
        f8["Job Level"] = f8["job_level"].map(level_map).fillna(f8["job_level"].astype(str))
        for _col in ["leadership_opportunities", "innovation_opportunities"]:
            f8[_col] = pd.to_numeric(f8[_col], errors="coerce")
            f8[_col] = f8[_col].fillna(f8[_col].median())
        growth = (
            f8.groupby("Job Level")[["leadership_opportunities",
                                      "innovation_opportunities", "attrition"]]
            .mean(numeric_only=True).reset_index()
            .rename(columns={"leadership_opportunities": "Leadership Opportunities",
                             "innovation_opportunities": "Innovation Opportunities",
                             "attrition": "Attrition Rate"})
        )
        growth["Job Level"] = pd.Categorical(growth["Job Level"],
                                               categories=["Entry", "Mid", "Senior"], ordered=True)
        growth = growth.sort_values("Job Level")

        fig_grow = go.Figure()
        fig_grow.add_trace(go.Bar(
            x=growth["Job Level"], y=growth["Leadership Opportunities"],
            name="Leadership Opportunities", marker_color=BLUE, opacity=0.8))
        fig_grow.add_trace(go.Bar(
            x=growth["Job Level"], y=growth["Innovation Opportunities"],
            name="Innovation Opportunities", marker_color=GREEN, opacity=0.8))
        fig_grow.update_layout(
            title="Growth Opportunities by Level — Entry staff get the least, yet leave the most",
            barmode="group", **LAYOUT,
            yaxis_title="Avg Opportunity Score")
        st.plotly_chart(fig_grow, use_container_width=True)

    with st.expander("Insight & Action — Career Stagnation"):
        insight_box(
            "Employees with <strong>zero promotions</strong> have significantly higher attrition, "
            "and Entry-level staff report the lowest access to leadership and innovation "
            "opportunities — yet this is exactly the group that leaves most. "
            "<strong>Action:</strong> Introduce a transparent promotion framework with defined "
            "timelines. Assign stretch projects and cross-functional work to Entry and Mid-level "
            "staff within their first 18 months. Track promotion velocity by department."
        )

    st.markdown("---")
    st.markdown("### Who Is the Single Highest-Risk Employee Profile?")

    profile = filtered[
        (filtered["overtime"] == "Yes") &
        (filtered["number_of_promotions"] == 0) &
        (filtered["work-life_balance"] <= 2) &
        (filtered["job_level"] <= 2)
    ]
    profile_rate = profile["attrition"].mean() if len(profile) > 0 else 0
    profile_n    = len(profile)
    lift         = profile_rate / company_avg if company_avg > 0 else 0

    col_q9a, col_q9b = st.columns([1, 1])

    with col_q9a:
        fig_prof = px.bar(
            x=["Company Average", "Highest-Risk Profile"],
            y=[company_avg, profile_rate],
            title=f"Highest-Risk Profile — {lift:.1f}× more likely to leave than the average employee",
            color=["Company Average", "Highest-Risk Profile"],
            color_discrete_map={"Company Average": BLUE, "Highest-Risk Profile": RED},
            text=[f"{company_avg:.1%}", f"{profile_rate:.1%}"],
            labels={"x": "", "y": "Attrition Rate"}
        )
        fig_prof.update_traces(textposition="outside")
        fig_prof.update_yaxes(tickformat=".0%", title_text="Attrition Rate")
        fig_prof.update_layout(**LAYOUT)
        st.plotly_chart(fig_prof, use_container_width=True)

    with col_q9b:
        st.markdown("#### High-Risk Profile Definition")
        st.markdown(f"""
| Criterion | Value |
|-----------|-------|
| Overtime | Yes |
| Promotions | 0 |
| Work-Life Balance | Poor or Fair (≤ 2) |
| Job Level | Entry or Mid (≤ 2) |
| **Employees in profile** | **{profile_n:,}** |
| **Profile attrition rate** | **{profile_rate:.1%}** |
| **Vs. company average** | **{lift:.1f}×** |
        """)

    with st.expander("Insight & Action — Highest-Risk Profile"):
        insight_box(
            f"Employees who work overtime, have had <strong>0 promotions</strong>, report "
            f"<strong>poor work-life balance</strong>, and sit at Entry or Mid level leave at "
            f"<strong>{profile_rate:.1%}</strong> — <strong>{lift:.1f}× the company average</strong>. "
            f"There are <strong>{profile_n:,}</strong> such employees today — large enough to justify "
            "a targeted programme. "
            "<strong>Action:</strong> Flag this cohort in the HRIS. Assign a dedicated retention "
            "manager to each, prioritise them in the next promotion cycle, and enrol them in the "
            "overtime reduction programme."
        )

    st.markdown("---")
    st.markdown("### If HR Could Fix Only One Thing — What Should It Be?")

    drivers = {
        "Overtime (Yes)":                  filtered[filtered["overtime"] == "Yes"]["attrition"].mean() - company_avg,
        "No Promotions (0)":               filtered[filtered["number_of_promotions"] == 0]["attrition"].mean() - company_avg,
        "Poor Work-Life Balance (≤ 2)":    filtered[filtered["work-life_balance"] <= 2]["attrition"].mean() - company_avg,
        "Low Job Satisfaction (≤ 2)":      filtered[filtered["job_satisfaction"] <= 2]["attrition"].mean() - company_avg,
        "Low Employee Recognition (≤ 2)":  filtered[filtered["employee_recognition"] <= 2]["attrition"].mean() - company_avg,
    }
    driver_df = (
        pd.DataFrame.from_dict(drivers, orient="index", columns=["Attrition Lift vs Baseline"])
        .reset_index()
        .rename(columns={"index": "Driver"})
        .sort_values("Attrition Lift vs Baseline", ascending=False)
    )
    driver_df["label"] = driver_df["Attrition Lift vs Baseline"].map(
        lambda x: f"+{x:.1%}" if x >= 0 else f"{x:.1%}")

    fig_drv = px.bar(
        driver_df, x="Attrition Lift vs Baseline", y="Driver", orientation="h",
        title=f"Top Attrition Drivers — how much each factor raises attrition above the {company_avg:.1%} average",
        color="Attrition Lift vs Baseline", color_continuous_scale="Reds",
        text="label"
    )
    fig_drv.update_traces(textposition="outside")
    fig_drv.update_xaxes(tickformat=".0%", title_text="Attrition Lift vs Company Average")
    fig_drv.update_layout(**LAYOUT, yaxis=dict(autorange="reversed"))
    fig_drv.update_coloraxes(showscale=False)
    st.plotly_chart(fig_drv, use_container_width=True)

    top = driver_df.iloc[0]
    with st.expander("Insight & Action — Top Driver & Recommended Fix"):
        insight_box(
            f"<strong>#1 Driver: {top['Driver']}</strong> → "
            f"<strong>+{top['Attrition Lift vs Baseline']:.1%}</strong> above company average. "
            "Overtime is the single highest-leverage fix. It compounds with zero promotions and "
            "poor work-life balance to create the toxic profile identified above. "
            "Fixing overtime alone could move the overall attrition rate by an estimated "
            "<strong>2–4 percentage points</strong> if applied to half the affected employees. "
            "<strong>Recommendation:</strong> Cap mandatory overtime, introduce flex-time, "
            "and audit the 3 departments with the highest overtime concentration. "
            "This is the single highest-ROI action HR can take next quarter."
        )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — EMPLOYEE SEGMENTS
# ══════════════════════════════════════════════════════════════════════════════
def page_segments():
    st.markdown("## Employee Risk Segments — Model Predictions by Role")
    st.markdown("---")

    display_cols = [
        "employee_id", "age", "gender", "job_role", "job_level",
        "monthly_income", "years_at_company", "performance_rating",
        "number_of_promotions", "attrition_probability", "risk_label"
    ]
    available_cols = [c for c in display_cols if c in filtered.columns]

    def render_segment(risk, accent):
        seg = (
            filtered[filtered["risk_label"] == risk][available_cols]
            .sort_values("attrition_probability", ascending=(risk == "Low Risk"))
            .reset_index(drop=True)
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Total in Segment",     f"{len(seg):,}")
        c2.metric("Avg Risk Probability",
                  f"{seg['attrition_probability'].mean():.1%}" if len(seg) > 0 else "N/A")
        c3.metric("Avg Monthly Income",
                  f"${seg['monthly_income'].mean():,.0f}" if len(seg) > 0 else "N/A")

        st.markdown("---")

        if len(seg) == 0:
            st.info("No employees match current filters.")
            return

        role_counts = (
            seg.groupby("job_role")
            .agg(Count=("employee_id", "count"),
                 Avg_Prob=("attrition_probability", "mean"),
                 Avg_Income=("monthly_income", "mean"))
            .reset_index()
            .rename(columns={"job_role": "Job Role"})
            .sort_values("Count", ascending=False)
        )
        role_counts["Avg_Prob"]   = role_counts["Avg_Prob"].round(3)
        role_counts["Avg_Income"] = role_counts["Avg_Income"].round(0).astype(int)
        role_counts["label"]      = role_counts["Count"].astype(str)

        palette = {"High Risk": "Reds", "Medium Risk": "Oranges", "Low Risk": "Greens"}
        fig_seg = px.bar(
            role_counts, x="Job Role", y="Count",
            color="Avg_Prob",
            color_continuous_scale=palette.get(risk, "Blues"),
            text="label",
            title=f"{risk} — headcount per role (colour = avg predicted risk probability)",
            hover_data={"Avg_Prob": ":.1%", "Avg_Income": ":,"}
        )
        fig_seg.update_traces(textposition="outside")
        fig_seg.update_coloraxes(colorbar=dict(title="Avg Risk Prob.", tickformat=".0%"))
        fig_seg.update_layout(**LAYOUT)
        st.plotly_chart(fig_seg, use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["🔴 High Risk", "🟡 Medium Risk", "🟢 Low Risk"])
    with tab1: render_segment("High Risk",   RED)
    with tab2: render_segment("Medium Risk", ORANGE)
    with tab3: render_segment("Low Risk",    GREEN)


# ── Navigation ─────────────────────────────────────────────────────────────────
pages = st.navigation([
    st.Page(page_home,     title="🔵Home & KPIs",                         url_path="home"),
    st.Page(page_easy,     title="🔵Overtime & Remote Work",              url_path="workload"),
    st.Page(page_medium,   title="🔵Pay, Tenure & Engagement",            url_path="retention"),
    st.Page(page_hard,     title="🔵Career Growth & Top Risk Drivers",    url_path="strategy"),
    st.Page(page_segments, title="🔵Employee Risk Segments",              url_path="segments"),
])
pages.run()