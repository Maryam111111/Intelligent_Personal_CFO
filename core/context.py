"""AgentContext — carries data downstream through the agent pipeline."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from core.models import (
    Transaction, SpendingReport, BudgetPlan,
    SavingsEstimate, InvestmentStrategy, GoalPlan,
)


@dataclass
class AgentContext:
    """Passed from agent to agent, accumulating outputs."""
    goal: str
    bank_transactions: list[Transaction] = field(default_factory=list)
    credit_transactions: list[Transaction] = field(default_factory=list)

    # Filled progressively as agents run
    spending: Optional[SpendingReport] = None
    budget: Optional[BudgetPlan] = None
    savings: Optional[SavingsEstimate] = None
    investment: Optional[InvestmentStrategy] = None
    goal_plan: Optional[GoalPlan] = None

    @property
    def all_transactions(self) -> list[Transaction]:
        return self.bank_transactions + self.credit_transactions

    @property
    def monthly_income(self) -> float:
        return sum(t.amount for t in self.all_transactions if t.amount > 0)

    @property
    def monthly_expenses(self) -> float:
        return abs(sum(t.amount for t in self.all_transactions if t.amount < 0))

    def transactions_as_csv(self) -> str:
        lines = ["Date,Description,Amount,Category"]
        for t in sorted(self.all_transactions, key=lambda x: x.date):
            lines.append(
                f"{t.date},{t.description},{t.amount:.2f},{t.category}"
            )
        return "\n".join(lines)
