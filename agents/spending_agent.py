"""SpendingAgent — categorises transactions and detects anomalies."""

from core.context import AgentContext
from core.models import SpendingReport
from agents.base_agent import BaseAgent
from skills.spending_skills import CATEGORISE, DETECT_ANOMALIES, RANK_CATEGORIES, FLAG_RECURRING


class SpendingAgent(BaseAgent):
    name = "Spending Agent"
    skills = [CATEGORISE, DETECT_ANOMALIES, RANK_CATEGORIES, FLAG_RECURRING]

    def run(self, context: AgentContext) -> AgentContext:
        txn_csv = context.transactions_as_csv()
        income = context.monthly_income
        expenses = context.monthly_expenses

        # Build category totals from raw data
        category_totals: dict[str, float] = {}
        for t in context.all_transactions:
            if t.amount < 0:
                category_totals[t.category] = (
                    category_totals.get(t.category, 0) + abs(t.amount)
                )

        cat_summary = "\n".join(
            f"  {cat}: £{amt:.2f}" for cat, amt in sorted(
                category_totals.items(), key=lambda x: -x[1]
            )
        )

        prompt = (
            f"Analyse these transactions for a user with goal: '{context.goal}'\n\n"
            f"TRANSACTIONS (CSV):\n{txn_csv}\n\n"
            f"CATEGORY TOTALS:\n{cat_summary}\n\n"
            "Provide:\n"
            "## Spending Overview — total income, total expenses, net\n"
            "## Top Categories — rank top 5, comment on proportionality\n"
            "## Anomalies — flag unusual transactions\n"
            "## Recurring Costs — list subscriptions with monthly total\n"
            "## Quick Wins — 3 specific cuts to make this month\n\n"
            "Be specific with £ amounts. Target 350 words."
        )

        analysis = self.call_claude(prompt)

        top_cats = sorted(category_totals, key=lambda k: -category_totals[k])[:3]

        context.spending = SpendingReport(
            total_income=income,
            total_expenses=expenses,
            category_breakdown=category_totals,
            anomalies=[],        # populated from analysis narrative
            recurring=[],        # populated from analysis narrative
            top_3_categories=top_cats,
            raw_analysis=analysis,
        )
        return context
