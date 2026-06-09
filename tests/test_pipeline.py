"""
Integration test — runs the full pipeline with mocked Claude calls.
For a live API test, set TEST_LIVE_API=1 in your environment.
"""

import os
from unittest.mock import patch
from datetime import date

import pytest

from core.models import Transaction
from core.context import AgentContext
from agents import (
    SpendingAgent, BudgetAgent, SavingsAgent,
    InvestmentAgent, GoalPlanningAgent,
)

MOCK_RESPONSE = (
    "## Analysis\n"
    "- Income: £3,800\n"
    "- Expenses: £2,400\n"
    "- Surplus: £1,400\n"
)

TRANSACTIONS = [
    Transaction(date(2024, 1, 14), "Salary", 3800.0, "Income"),
    Transaction(date(2024, 1, 15), "Rent", -1200.0, "Housing"),
    Transaction(date(2024, 1, 2), "Tesco", -142.5, "Groceries"),
    Transaction(date(2024, 1, 5), "Shell", -68.2, "Transport"),
    Transaction(date(2024, 1, 8), "ASOS", -234.0, "Shopping"),
]


@pytest.mark.skipif(
    os.getenv("TEST_LIVE_API") != "1",
    reason="Live API test — set TEST_LIVE_API=1 to run",
)
def test_full_pipeline_live():
    """End-to-end test using the real Anthropic API."""
    context = AgentContext(
        goal="Save £50,000 for a house deposit in 5 years",
        bank_transactions=TRANSACTIONS,
    )
    for AgentClass in [SpendingAgent, BudgetAgent, SavingsAgent, InvestmentAgent, GoalPlanningAgent]:
        context = AgentClass().run(context)

    assert context.spending is not None
    assert context.budget is not None
    assert context.savings is not None
    assert context.investment is not None
    assert context.goal_plan is not None


@patch("agents.base_agent.call_claude", return_value=MOCK_RESPONSE)
def test_full_pipeline_mocked(mock_claude):
    """Full pipeline with mocked Claude — validates data flow between agents."""
    context = AgentContext(
        goal="Save £50,000 for a house deposit in 5 years",
        bank_transactions=TRANSACTIONS,
    )
    for AgentClass in [SpendingAgent, BudgetAgent, SavingsAgent, InvestmentAgent, GoalPlanningAgent]:
        context = AgentClass().run(context)

    # Each agent must populate its output
    assert context.spending is not None
    assert context.budget is not None
    assert context.savings is not None
    assert context.investment is not None
    assert context.goal_plan is not None

    # Data flows: savings reads from spending
    assert context.savings.monthly_surplus >= 0

    # Goal plan reads from savings
    assert context.goal_plan.monthly_contribution == context.savings.monthly_surplus

    # All raw analyses populated
    for attr in ["spending", "budget", "savings", "investment", "goal_plan"]:
        obj = getattr(context, attr)
        assert obj.raw_analysis.strip(), f"{attr}.raw_analysis is empty"
