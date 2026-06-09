"""SavingsAgent — estimates monthly surplus and builds savings plan."""

from core.context import AgentContext
from core.models import SavingsEstimate
from agents.base_agent import BaseAgent
from skills.skill import Skill

ESTIMATE_SURPLUS = Skill("estimate_monthly_surplus", "Calculate disposable income.", "")
EMERGENCY_FUND = Skill("emergency_fund_plan", "Plan an emergency fund.", "")
BENCHMARK = Skill("savings_rate_benchmark", "Compare savings rate to benchmarks.", "")
TIMELINE = Skill("timeline_to_goal", "Project months to reach goal.", "")


class SavingsAgent(BaseAgent):
    name = "Savings Agent"
    skills = [ESTIMATE_SURPLUS, EMERGENCY_FUND, BENCHMARK, TIMELINE]

    def run(self, context: AgentContext) -> AgentContext:
        income = context.monthly_income
        expenses = context.spending.total_expenses if context.spending else context.monthly_expenses
        surplus = max(0, income - expenses)
        savings_rate = (surplus / income * 100) if income else 0

        prompt = (
            f"Create a savings plan for a user with goal: '{context.goal}'\n\n"
            f"Monthly income: £{income:.2f}\n"
            f"Monthly expenses: £{expenses:.2f}\n"
            f"Monthly surplus: £{surplus:.2f}\n"
            f"Current savings rate: {savings_rate:.1f}%\n\n"
            "Provide:\n"
            "## Monthly Surplus — net after expenses, comparison to income %\n"
            "## Emergency Fund — target (3-6 months expenses), months to reach it\n"
            "## Savings Rate Benchmark — compare to UK averages, target\n"
            "## Timeline to Goal — months and year to reach the stated goal\n"
            "## Optimisation Tips — 3 ways to increase the monthly surplus\n\n"
            "Target 350 words."
        )

        analysis = self.call_claude(prompt)
        emergency_target = expenses * 4
        months_emergency = int(emergency_target / surplus) if surplus > 0 else 999

        # Rough goal amount extraction heuristic
        goal_amount = 50_000.0
        import re
        match = re.search(r"£([\d,]+)", context.goal)
        if match:
            goal_amount = float(match.group(1).replace(",", ""))
        months_to_goal = int(goal_amount / surplus) if surplus > 0 else 999

        context.savings = SavingsEstimate(
            monthly_surplus=surplus,
            emergency_fund_target=emergency_target,
            months_to_emergency_fund=months_emergency,
            current_savings_rate_pct=savings_rate,
            benchmark_savings_rate_pct=20.0,
            months_to_goal=months_to_goal,
            raw_analysis=analysis,
        )
        return context
