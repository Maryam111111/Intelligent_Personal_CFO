"""InvestmentAgent — recommends vehicles, allocation, and projected returns."""

from core.context import AgentContext
from core.models import InvestmentStrategy
from agents.base_agent import BaseAgent
from skills.skill import Skill

RECOMMEND = Skill("recommend_vehicles", "Recommend investment vehicles.", "")
ALLOCATE = Skill("allocate_portfolio", "Suggest portfolio allocation.", "")
PROJECT = Skill("project_returns", "Project portfolio value over time.", "")
TAX = Skill("tax_wrapper_advice", "Advise on ISA / SIPP wrappers.", "")


class InvestmentAgent(BaseAgent):
    name = "Investment Agent"
    skills = [RECOMMEND, ALLOCATE, PROJECT, TAX]

    def run(self, context: AgentContext) -> AgentContext:
        surplus = context.savings.monthly_surplus if context.savings else 850.0
        income = context.monthly_income

        prompt = (
            f"Create an investment strategy for a user with goal: '{context.goal}'\n\n"
            f"Monthly income: £{income:.2f}\n"
            f"Monthly investable amount: £{surplus:.2f}\n\n"
            "Assume UK-based investor. Provide:\n"
            "## Recommended Vehicles — Stocks & Shares ISA, index funds, bonds, etc. "
            "with rationale for each\n"
            "## Portfolio Allocation — % split across asset classes\n"
            "## Projected Returns — 5-year and 10-year projection at conservative 6% p.a.\n"
            "## Tax-Efficient Wrappers — ISA allowance, SIPP, and how to prioritise\n"
            "## Risk Profile — match allocation to user goal timeline\n\n"
            "Target 350 words."
        )

        analysis = self.call_claude(prompt)

        allocation = {
            "Global index funds": 60,
            "Bonds / gilts": 20,
            "Cash / LISA": 10,
            "Emerging markets": 10,
        }
        projected = surplus * 12 * 5 * 1.06 ** 5  # simplified

        context.investment = InvestmentStrategy(
            monthly_investable=surplus,
            recommended_vehicles=list(allocation.keys()),
            allocation=allocation,
            projected_value_5yr=projected,
            tax_wrappers=["Stocks & Shares ISA", "LISA"],
            raw_analysis=analysis,
        )
        return context
