"""Pydantic data models shared across all agents."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Transaction:
    date: date
    description: str
    amount: float          # negative = expense, positive = income
    category: str


@dataclass
class SpendingReport:
    total_income: float
    total_expenses: float
    category_breakdown: dict[str, float]    # category -> total spent
    anomalies: list[str]                    # anomaly descriptions
    recurring: list[str]                    # recurring cost descriptions
    top_3_categories: list[str]
    raw_analysis: str                       # LLM narrative


@dataclass
class BudgetPlan:
    recommended_needs: float
    recommended_wants: float
    recommended_savings: float
    actual_needs: float
    actual_wants: float
    overruns: list[str]
    suggested_cuts: list[str]
    raw_analysis: str


@dataclass
class SavingsEstimate:
    monthly_surplus: float
    emergency_fund_target: float
    months_to_emergency_fund: int
    current_savings_rate_pct: float
    benchmark_savings_rate_pct: float
    months_to_goal: int
    raw_analysis: str


@dataclass
class InvestmentStrategy:
    monthly_investable: float
    recommended_vehicles: list[str]
    allocation: dict[str, float]           # vehicle -> percentage
    projected_value_5yr: float
    tax_wrappers: list[str]
    raw_analysis: str


@dataclass
class GoalPlan:
    goal_text: str
    target_amount: float
    monthly_contribution: float
    milestones: list[dict]                 # [{"month": N, "label": str, "amount": float}]
    risk_level: str
    contingency_notes: str
    raw_analysis: str


@dataclass
class CFOReport:
    goal: str
    spending: SpendingReport
    budget: BudgetPlan
    savings: SavingsEstimate
    investment: InvestmentStrategy
    goal_plan: GoalPlan
    generated_at: str
