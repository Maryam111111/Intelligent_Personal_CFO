"""BudgetAgent — builds 50/30/20 budget and flags overruns."""

from core.context import AgentContext
from core.models import BudgetPlan
from agents.base_agent import BaseAgent
from skills.skill import Skill

BUILD_50_30_20 = Skill("build_50_30_20", "Construct a 50/30/20 budget.", "{income} {expenses}")
COMPARE = Skill("compare_actual_vs_target", "Compare actual spend to target.", "{breakdown}")
IDENTIFY_OVERRUNS = Skill("identify_overruns", "Find over-budget categories.", "{breakdown}")
SUGGEST_CUTS = Skill("suggest_cuts", "Recommend specific spending cuts.", "{breakdown}")


class BudgetAgent(BaseAgent):
    name = "Budget Agent"
    skills = [BUILD_50_30_20, COMPARE, IDENTIFY_OVERRUNS, SUGGEST_CUTS]

    def run(self, context: AgentContext) -> AgentContext:
        income = context.monthly_income
        expenses = context.spending.total_expenses if context.spending else context.monthly_expenses
        cat_summary = (
            "\n".join(
                f"  {c}: £{a:.2f}"
                for c, a in sorted(
                    context.spending.category_breakdown.items(),
                    key=lambda x: -x[1],
                )
            )
            if context.spending
            else "No category data."
        )

        prompt = (
            f"Build a monthly budget for a user with goal: '{context.goal}'\n\n"
            f"Monthly income: £{income:.2f}\n"
            f"Actual total expenses: £{expenses:.2f}\n\n"
            f"CATEGORY BREAKDOWN:\n{cat_summary}\n\n"
            "Provide:\n"
            "## Recommended 50/30/20 Budget — needs/wants/savings with £ targets\n"
            "## Actual vs Target — compare each category\n"
            "## Overruns — which categories exceed their allocation and by how much\n"
            "## Suggested Cuts — 4 specific, actionable reductions with £ impact\n\n"
            "Target 350 words."
        )

        analysis = self.call_claude(prompt)
        n, w, s = income * 0.5, income * 0.3, income * 0.2

        context.budget = BudgetPlan(
            recommended_needs=n,
            recommended_wants=w,
            recommended_savings=s,
            actual_needs=expenses * 0.6,
            actual_wants=expenses * 0.4,
            overruns=[],
            suggested_cuts=[],
            raw_analysis=analysis,
        )
        return context
