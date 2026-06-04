import streamlit as st
import pandas as pd
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
    .stApp, .main, .block-container {
        background-color: #060d1f !important;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #070e20 0%, #0a1628 100%) !important;
        border-right: 1px solid #1a2f55;
    }
    section[data-testid="stSidebar"] * { color: #c8d6f0 !important; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0d1e3d 0%, #112244 100%);
        border: 1px solid #1e3a6e;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 20px rgba(0,80,200,0.15);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #ffffff !important;
        font-weight: 700;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        color: #7aabdd !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    h1, h2, h3, h4 { color: #e8f0ff !important; }
    .stTabs [data-baseweb="tab"] {
        background: #0d1e3d;
        color: #7aabdd;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: #1a3a70 !important;
        color: #ffffff !important;
    }
    .stDataFrame { border: 1px solid #1e3a6e; border-radius: 8px; }
    hr { border-color: #1a2f55; }
    .block-container { padding-top: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

CARD   = "#0d1e3d"
BLUE   = "#3a8fd1"
RED    = "#e74c3c"
GREEN  = "#2ecc71"
ORANGE = "#f39c12"
WHITE  = "#e8f0ff"

LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor=CARD,
    plot_bgcolor=CARD,
    font=dict(color=WHITE, family="Arial"),
    margin=dict(t=50, b=40, l=40, r=20),
    title_font=dict(size=14, color=WHITE)
)

@st.cache_data
def load_data():
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    return pd.read_csv(os.path.join(BASE_DIR, "data", "predictions.csv"))

df = load_data()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logo_path = Path(os.path.join(BASE_DIR, "assets", "logo.png"))
if logo_path.exists():
    st.sidebar.image(str(logo_path), use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

job_roles    = ["All"] + sorted(df["job_role"].dropna().unique().tolist())
genders      = ["All"] + sorted(df["gender"].dropna().unique().tolist())
job_levels   = ["All"] + sorted(df["job_level"].dropna().unique().tolist())
risk_options = ["All", "High Risk", "Medium Risk", "Low Risk"]

selected_role   = st.sidebar.selectbox("Job Role",   job_roles)
selected_gender = st.sidebar.selectbox("Gender",     genders)
selected_level  = st.sidebar.selectbox("Job Level",  job_levels)
selected_risk   = st.sidebar.selectbox("Risk Label", risk_options)

pages = ["📊 KPI Overview", "👥 Employee Segments"]
page  = st.sidebar.radio("Navigate", pages)
st.sidebar.markdown("---")
st.sidebar.caption(f"Total records: {len(df):,}")

filtered = df.copy()
if selected_role   != "All": filtered = filtered[filtered["job_role"]   == selected_role]
if selected_gender != "All": filtered = filtered[filtered["gender"]     == selected_gender]
if selected_level  != "All": filtered = filtered[filtered["job_level"]  == selected_level]
if selected_risk   != "All": filtered = filtered[filtered["risk_label"] == selected_risk]


if page == "📊 KPI Overview":
    st.markdown("## 📊 HR Attrition — KPI Overview")
    st.markdown("---")

    total         = len(filtered)
    actual_left   = int((filtered["attrition"] == 1).sum())
    pred_high     = int((filtered["risk_label"] == "High Risk").sum())
    avg_income    = filtered["monthly_income"].mean()
    avg_tenure    = filtered["years_at_company"].mean()
    attrition_pct = actual_left / total * 100 if total > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Employees",    f"{total:,}")
    c2.metric("Actual Attrition",   f"{actual_left:,}", delta=f"{attrition_pct:.1f}%")
    c3.metric("High Risk (Model)",  f"{pred_high:,}")
    c4.metric("Avg Monthly Income", f"${avg_income:,.0f}")
    c5.metric("Avg Tenure",         f"{avg_tenure:.1f} yrs")

    st.markdown("---")
    stayed_count = int((filtered["attrition"] == 0).sum())
    left_count   = int((filtered["attrition"] == 1).sum())

    fig0 = go.Figure(go.Pie(
        labels=["Stayed", "Left"],
        values=[stayed_count, left_count],
        hole=0.5,
        marker_colors=[BLUE, RED],
        textinfo="percent+label",
        textfont_size=14
    ))
    fig0.update_layout(
        title=f"Overall Attrition — {left_count / (stayed_count + left_count):.1%} of employees left",
        **LAYOUT
    )
    st.plotly_chart(fig0, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        role_d = (
            filtered.groupby("job_role")["attrition"]
            .mean().reset_index()
            .rename(columns={"attrition": "Attrition Rate", "job_role": "Job Role"})
            .sort_values("Attrition Rate", ascending=False)
        )
        role_d["label"] = role_d["Attrition Rate"].map(lambda x: f"{x:.1%}")
        fig1 = px.bar(
            role_d, x="Job Role", y="Attrition Rate",
            title="Attrition Rate by Job Role",
            color="Attrition Rate", color_continuous_scale="Reds", text="label"
        )
        fig1.update_traces(textposition="outside")
        fig1.update_yaxes(tickformat=".0%")
        fig1.update_layout(**LAYOUT)
        fig1.update_coloraxes(showscale=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        risk_d = (
            filtered["risk_label"]
            .value_counts()
            .reindex(["High Risk", "Medium Risk", "Low Risk"])
            .reset_index()
        )
        risk_d.columns = ["Risk Level", "Count"]
        fig2 = px.pie(
            risk_d, names="Risk Level", values="Count",
            title="Employee Risk Distribution",
            color="Risk Level",
            color_discrete_map={"High Risk": RED, "Medium Risk": ORANGE, "Low Risk": GREEN},
            hole=0.45
        )
        fig2.update_traces(textinfo="percent+label", textfont_size=13)
        fig2.update_layout(**LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        age_bins   = list(range(18, 62, 4))
        age_labels = [f"{a}-{a+3}" for a in age_bins[:-1]]
        f_age = filtered.copy()
        f_age["age_group"] = pd.cut(f_age["age"], bins=age_bins, labels=age_labels, right=False)
        age_attr = (
            f_age.groupby("age_group", observed=True)["attrition"]
            .agg(["mean", "count"]).reset_index()
            .rename(columns={"mean": "Attrition Rate", "count": "Employees", "age_group": "Age Group"})
        )
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(go.Bar(
            x=age_attr["Age Group"], y=age_attr["Employees"],
            name="Employees", marker_color="#1e3a6e", opacity=0.85
        ), secondary_y=False)
        fig3.add_trace(go.Scatter(
            x=age_attr["Age Group"], y=age_attr["Attrition Rate"],
            name="Attrition Rate", mode="lines+markers",
            line=dict(color=RED, width=3), marker=dict(size=8, color=RED)
        ), secondary_y=True)
        fig3.update_layout(title="Attrition Rate by Age Group", **LAYOUT)
        fig3.update_yaxes(title_text="Employees",      secondary_y=False, color=BLUE)
        fig3.update_yaxes(title_text="Attrition Rate", secondary_y=True,  tickformat=".0%", color=RED)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        bins_inc   = [0, 3000, 6000, 9000, 12000, 17000]
        labels_inc = ["<3K", "3K-6K", "6K-9K", "9K-12K", ">12K"]
        f_inc = filtered.copy()
        f_inc["income_band"] = pd.cut(f_inc["monthly_income"], bins=bins_inc, labels=labels_inc)
        band = (
            f_inc.groupby(["income_band", "attrition"], observed=True)
            .size().reset_index(name="Count")
        )
        band["Status"] = band["attrition"].map({0: "Stayed", 1: "Left"})
        fig4 = px.bar(
            band, x="income_band", y="Count", color="Status",
            barmode="group",
            title="Income Band vs Attrition",
            color_discrete_map={"Stayed": BLUE, "Left": RED},
            labels={"income_band": "Monthly Income Band", "Count": "Employees"}
        )
        fig4.update_layout(**LAYOUT)
        st.plotly_chart(fig4, use_container_width=True)

    tenure_attr = (
        filtered.groupby("years_at_company")["attrition"]
        .mean()
        .reset_index()
        .rename(columns={"years_at_company": "Years at Company", "attrition": "Attrition Rate"})
    )
    fig_tenure = px.line(
        tenure_attr,
        x="Years at Company",
        y="Attrition Rate",
        markers=True,
        title="Seniority Trap: When do employees decide to leave?",
    )
    fig_tenure.update_traces(
        line_color="#66FCF1",
        line_width=3,
        marker=dict(size=8, color="#66FCF1", line=dict(width=2, color=WHITE))
    )
    fig_tenure.update_yaxes(tickformat=".0%")
    fig_tenure.update_layout(**LAYOUT)
    st.plotly_chart(fig_tenure, use_container_width=True)

    col5, col6 = st.columns(2)

    with col5:
        promo = (
            filtered.groupby("number_of_promotions")["attrition"]
            .agg(["mean", "count"]).reset_index()
            .rename(columns={
                "number_of_promotions": "Promotions",
                "mean": "Attrition Rate", "count": "Employees"
            })
        )
        fig5 = make_subplots(specs=[[{"secondary_y": True}]])
        fig5.add_trace(go.Bar(
            x=promo["Promotions"], y=promo["Employees"],
            name="Employees", marker_color="#1e3a6e", opacity=0.85
        ), secondary_y=False)
        fig5.add_trace(go.Scatter(
            x=promo["Promotions"], y=promo["Attrition Rate"],
            name="Attrition Rate", mode="lines+markers",
            line=dict(color=RED, width=3), marker=dict(size=8, color=RED)
        ), secondary_y=True)
        fig5.update_layout(title="Promotions vs Attrition Rate", **LAYOUT)
        fig5.update_yaxes(title_text="Employees",      secondary_y=False, color=BLUE)
        fig5.update_yaxes(title_text="Attrition Rate", secondary_y=True,  tickformat=".0%", color=RED)
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        remote = (
            filtered.groupby("remote_work")["attrition"]
            .mean().reset_index()
            .rename(columns={"remote_work": "Remote", "attrition": "Attrition Rate"})
        )
        remote["label"] = remote["Attrition Rate"].map(lambda x: f"{x:.1%}")
        wlb = (
            filtered.groupby("work-life_balance")["attrition"]
            .mean().reset_index()
            .rename(columns={"work-life_balance": "WLB Score", "attrition": "Attrition Rate"})
        )
        fig6 = make_subplots(rows=1, cols=2,
            subplot_titles=["Remote Work", "Work-Life Balance"])
        fig6.add_trace(go.Bar(
            x=remote["Remote"], y=remote["Attrition Rate"],
            text=remote["label"], textposition="outside",
            marker_color=[RED, GREEN], showlegend=False
        ), row=1, col=1)
        fig6.add_trace(go.Scatter(
            x=wlb["WLB Score"], y=wlb["Attrition Rate"],
            mode="lines+markers",
            line=dict(color=BLUE, width=3),
            marker=dict(size=10, color=RED),
            showlegend=False
        ), row=1, col=2)
        fig6.update_layout(title="Remote Work & WLB Impact", **LAYOUT)
        fig6.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig6, use_container_width=True)


elif page == "👥 Employee Segments":
    st.markdown("## 👥 Employee Segments by Model Classification")
    st.markdown("---")

    display_cols = [
        "employee_id", "age", "gender", "job_role", "job_level",
        "monthly_income", "years_at_company", "performance_rating",
        "number_of_promotions", "attrition_probability", "risk_label"
    ]
    available_cols = [c for c in display_cols if c in filtered.columns]

    def render_segment(tab_obj, risk, accent):
        with tab_obj:
            seg = (
                filtered[filtered["risk_label"] == risk][available_cols]
                .sort_values("attrition_probability", ascending=(risk == "Low Risk"))
                .reset_index(drop=True)
            )

            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            col_kpi1.metric("Total in Segment", f"{len(seg):,}")
            col_kpi2.metric("Avg Risk Probability",
                            f"{seg['attrition_probability'].mean():.1%}" if len(seg) > 0 else "N/A")
            col_kpi3.metric("Avg Monthly Income",
                            f"${seg['monthly_income'].mean():,.0f}" if len(seg) > 0 else "N/A")

            st.markdown("---")

            seg_show = seg.copy()
            seg_show["attrition_probability"] = seg_show["attrition_probability"].map(
                lambda x: f"{x:.1%}"
            )
            st.dataframe(seg_show, use_container_width=True, height=300)

            if len(seg) == 0:
                st.info("No employees match current filters.")
                return

            st.markdown("---")

            role_counts = (
                seg.groupby("job_role")
                .agg(
                    Count=("employee_id", "count"),
                    Avg_Prob=("attrition_probability", "mean"),
                    Avg_Income=("monthly_income", "mean")
                )
                .reset_index()
                .rename(columns={"job_role": "Job Role"})
                .sort_values("Count", ascending=False)
            )
            role_counts["Avg_Prob"]   = role_counts["Avg_Prob"].round(3)
            role_counts["Avg_Income"] = role_counts["Avg_Income"].round(0).astype(int)
            role_counts["label"]      = role_counts["Count"].astype(str)

            fig_roles = px.bar(
                role_counts,
                x="Job Role", y="Count",
                color="Avg_Prob",
                color_continuous_scale="Reds" if risk == "High Risk"
                    else "Oranges" if risk == "Medium Risk" else "Greens",
                text="label",
                title=f"{risk} — Employee Count per Role (color = avg risk probability)",
                hover_data={"Avg_Prob": ":.1%", "Avg_Income": ":,"}
            )
            fig_roles.update_traces(textposition="outside")
            fig_roles.update_coloraxes(
                colorbar=dict(title="Avg Risk", tickformat=".0%", tickfont=dict(color=WHITE))
            )
            fig_roles.update_layout(**LAYOUT)
            st.plotly_chart(fig_roles, use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["🔴 High Risk", "🟡 Medium Risk", "🟢 Low Risk"])
    render_segment(tab1, "High Risk",   RED)
    render_segment(tab2, "Medium Risk", ORANGE)
    render_segment(tab3, "Low Risk",    GREEN)
