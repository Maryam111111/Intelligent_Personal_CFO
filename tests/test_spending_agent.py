"""Unit tests for SpendingAgent — mocks the Claude API."""

from unittest.mock import patch
from datetime import date

import pytest

from core.models import Transaction
from core.context import AgentContext
from agents.spending_agent import SpendingAgent


MOCK_TRANSACTIONS = [
    Transaction(date(2024, 1, 14), "Salary", 3800.0, "Income"),
    Transaction(date(2024, 1, 15), "Rent", -1200.0, "Housing"),
    Transaction(date(2024, 1, 2), "Tesco", -142.5, "Groceries"),
    Transaction(date(2024, 1, 3), "Netflix", -17.99, "Entertainment"),
    Transaction(date(2024, 1, 10), "Gym", -45.0, "Health"),
]

MOCK_ANALYSIS = "## Spending Overview\nIncome: £3,800. Expenses: £1,405.49"


@patch("agents.base_agent.call_claude", return_value=MOCK_ANALYSIS)
def test_spending_agent_populates_context(mock_claude):
    context = AgentContext(
        goal="Save £50,000 in 5 years",
        bank_transactions=MOCK_TRANSACTIONS,
    )
    agent = SpendingAgent()
    result = agent.run(context)

    assert result.spending is not None
    assert result.spending.total_income == pytest.approx(3800.0)
    assert result.spending.total_expenses > 0
    assert "Housing" in result.spending.category_breakdown
    assert result.spending.raw_analysis == MOCK_ANALYSIS


@patch("agents.base_agent.call_claude", return_value=MOCK_ANALYSIS)
def test_spending_agent_top_3_categories(mock_claude):
    context = AgentContext(
        goal="Test goal",
        bank_transactions=MOCK_TRANSACTIONS,
    )
    result = SpendingAgent().run(context)
    assert len(result.spending.top_3_categories) <= 3
    # Housing should be the largest expense
    assert result.spending.top_3_categories[0] == "Housing"


@patch("agents.base_agent.call_claude", return_value=MOCK_ANALYSIS)
def test_spending_agent_skill_names(mock_claude):
    agent = SpendingAgent()
    skills = agent.skill_names()
    assert "categorise_transactions" in skills
    assert "detect_anomalies" in skills
    assert "flag_recurring" in skills
