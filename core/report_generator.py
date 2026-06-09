"""Writes the final CFO report to data/reports/ as Markdown and JSON."""

import json
import os
from datetime import datetime
from dataclasses import asdict

from core.models import CFOReport

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reports")


def _safe_asdict(obj) -> dict:
    """Convert dataclass to dict, handling nested dataclasses."""
    try:
        return asdict(obj)
    except TypeError:
        return {"raw": str(obj)}


def write_report(report: CFOReport) -> tuple[str, str]:
    """
    Write report to disk. Returns (markdown_path, json_path).
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # ── Markdown ──────────────────────────────────────────────
    md_lines = [
        f"# Personal Finance CFO Report",
        f"**Generated:** {report.generated_at}",
        f"**Goal:** {report.goal}",
        "",
        "---",
        "",
        "## 1. Spending Analysis",
        f"- Monthly income: £{report.spending.total_income:,.2f}",
        f"- Monthly expenses: £{report.spending.total_expenses:,.2f}",
        "",
        "**Category breakdown:**",
    ]
    for cat, amt in sorted(
        report.spending.category_breakdown.items(), key=lambda x: -x[1]
    ):
        md_lines.append(f"- {cat}: £{amt:,.2f}")

    if report.spending.anomalies:
        md_lines += ["", "**Anomalies:**"]
        for a in report.spending.anomalies:
            md_lines.append(f"- {a}")

    md_lines += [
        "",
        report.spending.raw_analysis,
        "",
        "---",
        "",
        "## 2. Budget Plan",
        f"- Recommended needs (50%): £{report.budget.recommended_needs:,.2f}",
        f"- Recommended wants (30%): £{report.budget.recommended_wants:,.2f}",
        f"- Recommended savings (20%): £{report.budget.recommended_savings:,.2f}",
        "",
        report.budget.raw_analysis,
        "",
        "---",
        "",
        "## 3. Savings Estimate",
        f"- Monthly surplus: £{report.savings.monthly_surplus:,.2f}",
        f"- Emergency fund target: £{report.savings.emergency_fund_target:,.2f}",
        f"- Current savings rate: {report.savings.current_savings_rate_pct:.1f}%",
        f"- Months to goal: {report.savings.months_to_goal}",
        "",
        report.savings.raw_analysis,
        "",
        "---",
        "",
        "## 4. Investment Strategy",
        f"- Monthly investable: £{report.investment.monthly_investable:,.2f}",
        f"- Projected 5-yr value: £{report.investment.projected_value_5yr:,.2f}",
        "",
        "**Allocation:**",
    ]
    for vehicle, pct in report.investment.allocation.items():
        md_lines.append(f"- {vehicle}: {pct:.0f}%")

    md_lines += [
        "",
        report.investment.raw_analysis,
        "",
        "---",
        "",
        "## 5. Goal Plan",
        f"- Risk level: {report.goal_plan.risk_level}",
        f"- Monthly contribution: £{report.goal_plan.monthly_contribution:,.2f}",
        "",
        "**Milestones:**",
    ]
    for m in report.goal_plan.milestones:
        md_lines.append(
            f"- Month {m.get('month', '?')}: {m.get('label', '')} "
            f"(£{float(m.get('amount', 0)):,.0f})"
        )

    md_lines += ["", report.goal_plan.raw_analysis]

    md_path = os.path.join(REPORTS_DIR, f"cfo_report_{stamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # ── JSON ──────────────────────────────────────────────────
    json_path = os.path.join(REPORTS_DIR, f"cfo_report_{stamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(_safe_asdict(report), f, indent=2, default=str)

    return md_path, json_path
