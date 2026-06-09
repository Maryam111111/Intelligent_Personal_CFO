"""
app.py — Streamlit dashboard for Personal Finance AI CFO
─────────────────────────────────────────────────────────
Run:  streamlit run app.py
"""

import io
import os
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core.csv_parser import parse_csv
from core.context import AgentContext
from core.models import CFOReport
from core.report_generator import write_report
from agents import (
    SpendingAgent, BudgetAgent, SavingsAgent,
    InvestmentAgent, GoalPlanningAgent,
)

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="Personal Finance AI CFO",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .agent-card {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 8px;
  }
  .skill-tag {
    display: inline-block; background: #f0fdf4; color: #166534;
    font-size: 11px; padding: 2px 8px; border-radius: 4px;
    margin: 2px; font-family: monospace;
  }
  .status-dot-green { color: #16a34a; font-size: 10px; }
</style>
""", unsafe_allow_html=True)

AGENTS_META = [
    {"id": "spending",    "name": "Spending Agent",       "icon": "💳", "color": "#e85d4a"},
    {"id": "budget",      "name": "Budget Agent",         "icon": "📊", "color": "#2563eb"},
    {"id": "savings",     "name": "Savings Agent",        "icon": "🏦", "color": "#059669"},
    {"id": "investment",  "name": "Investment Agent",     "icon": "📈", "color": "#7c3aed"},
    {"id": "goal",        "name": "Goal Planning Agent",  "icon": "🎯", "color": "#d97706"},
]

SAMPLE_BANK = """Date,Description,Amount,Category
2024-01-02,Tesco Superstore,-142.50,Groceries
2024-01-03,Netflix,-17.99,Entertainment
2024-01-05,Shell Petrol,-68.20,Transport
2024-01-07,Nando's Restaurant,-34.50,Dining Out
2024-01-10,Gym Membership,-45.00,Health
2024-01-14,Salary,+3800.00,Income
2024-01-15,Rent,-1200.00,Housing
2024-01-16,BT Broadband,-42.00,Utilities
2024-01-18,Costa Coffee,-12.40,Dining Out
2024-01-21,Sainsbury's,-95.30,Groceries
2024-01-25,Electric Bill,-78.00,Utilities
2024-01-28,John Lewis,-156.00,Shopping"""

SAMPLE_CREDIT = """Date,Description,Amount,Category
2024-01-08,ASOS Online,-234.00,Shopping
2024-01-13,Odeon Cinema,-28.50,Entertainment
2024-01-22,Booking.com,-320.00,Travel
2024-01-26,Apple Store,-149.00,Electronics"""


def run_pipeline(context: AgentContext, placeholders: list) -> AgentContext:
    pipeline = [
        SpendingAgent(), BudgetAgent(), SavingsAgent(),
        InvestmentAgent(), GoalPlanningAgent(),
    ]
    for i, agent in enumerate(pipeline):
        placeholders[i].markdown(f"⏳ **{agent.name}** — processing…")
        context = agent.run(context)
        placeholders[i].markdown(f"✅ **{agent.name}** — complete")
    return context


# ── Session state ──────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = "upload"
if "outputs" not in st.session_state:
    st.session_state.outputs = {}
if "report" not in st.session_state:
    st.session_state.report = None

# ── Upload / configure step ────────────────────────────────────
if st.session_state.step == "upload":
    st.markdown("# 💼 Personal Finance AI CFO")
    st.markdown("A **5-agent AI system** that analyses your finances and charts a path to your goal.")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏦 Bank Transactions")
        if st.button("Load sample bank data", key="sample_bank"):
            st.session_state.bank_text = SAMPLE_BANK
        bank_text = st.text_area(
            "Paste CSV", value=st.session_state.get("bank_text", ""),
            height=180, key="bank_input", placeholder="Date,Description,Amount,Category\n..."
        )
        uploaded_bank = st.file_uploader("Or upload a CSV", type=["csv"], key="bank_upload")
        if uploaded_bank:
            bank_text = uploaded_bank.read().decode("utf-8")

    with col2:
        st.subheader("💳 Credit Card Statements")
        if st.button("Load sample credit data", key="sample_credit"):
            st.session_state.credit_text = SAMPLE_CREDIT
        credit_text = st.text_area(
            "Paste CSV", value=st.session_state.get("credit_text", ""),
            height=180, key="credit_input", placeholder="Date,Description,Amount,Category\n..."
        )
        uploaded_credit = st.file_uploader("Or upload a CSV", type=["csv"], key="credit_upload")
        if uploaded_credit:
            credit_text = uploaded_credit.read().decode("utf-8")

    st.divider()
    goal = st.text_input(
        "🎯 Your financial goal",
        value="I want £50,000 for a house deposit in 5 years",
        help="Be specific — include amount and timeline.",
    )

    if st.button("🚀 Run 5-Agent Analysis", type="primary", use_container_width=True):
        if not bank_text.strip() and not credit_text.strip():
            st.error("Please add at least one CSV (or load sample data).")
        else:
            st.session_state.step = "analyzing"
            st.session_state.goal = goal
            st.session_state.bank_csv = bank_text
            st.session_state.credit_csv = credit_text
            st.rerun()

# ── Analysis step ──────────────────────────────────────────────
elif st.session_state.step == "analyzing":
    st.markdown("# ⚙️ Agents processing your data…")
    progress_bar = st.progress(0)
    placeholders = [st.empty() for _ in AGENTS_META]

    bank_txns = parse_csv(st.session_state.bank_csv) if st.session_state.bank_csv.strip() else []
    credit_txns = parse_csv(st.session_state.credit_csv) if st.session_state.credit_csv.strip() else []

    context = AgentContext(
        goal=st.session_state.goal,
        bank_transactions=bank_txns,
        credit_transactions=credit_txns,
    )

    pipeline = [
        SpendingAgent(), BudgetAgent(), SavingsAgent(),
        InvestmentAgent(), GoalPlanningAgent(),
    ]
    outputs = {}
    for i, agent in enumerate(pipeline):
        placeholders[i].markdown(f"⏳ **{agent.name}** — processing…")
        context = agent.run(context)
        placeholders[i].markdown(f"✅ **{agent.name}** — complete")
        # Store raw analysis
        attr = ["spending", "budget", "savings", "investment", "goal_plan"][i]
        obj = getattr(context, attr)
        outputs[AGENTS_META[i]["id"]] = obj.raw_analysis if obj else ""
        progress_bar.progress((i + 1) / len(pipeline))

    report = CFOReport(
        goal=st.session_state.goal,
        spending=context.spending,
        budget=context.budget,
        savings=context.savings,
        investment=context.investment,
        goal_plan=context.goal_plan,
        generated_at=datetime.now().isoformat(timespec="seconds"),
    )

    st.session_state.outputs = outputs
    st.session_state.report = report
    st.session_state.step = "results"
    time.sleep(0.5)
    st.rerun()

# ── Results step ───────────────────────────────────────────────
elif st.session_state.step == "results":
    report: CFOReport = st.session_state.report
    outputs: dict = st.session_state.outputs

    st.markdown("# 💼 CFO Report")
    st.caption(f"Analysis complete · {report.generated_at}")

    st.info(f"🎯 **Goal:** {report.goal}")

    # Quick stats
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monthly Income", f"£{report.spending.total_income:,.0f}")
    c2.metric("Monthly Expenses", f"£{report.spending.total_expenses:,.0f}")
    c3.metric("Monthly Surplus", f"£{report.savings.monthly_surplus:,.0f}")
    c4.metric("Savings Rate", f"{report.savings.current_savings_rate_pct:.1f}%")

    st.divider()

    # Tab per agent
    tabs = st.tabs([f"{m['icon']} {m['name']}" for m in AGENTS_META])
    for tab, meta in zip(tabs, AGENTS_META):
        with tab:
            st.markdown(outputs.get(meta["id"], "_No output yet._"))

    st.divider()
    col_a, col_b = st.columns(2)
    if col_a.button("⬇️ Download Markdown Report"):
        md_path, _ = write_report(report)
        with open(md_path) as f:
            col_a.download_button("Save .md", f.read(), file_name="cfo_report.md")
    if col_b.button("🔄 New Analysis"):
        for k in ["step", "outputs", "report", "bank_text", "credit_text"]:
            st.session_state.pop(k, None)
        st.rerun()
