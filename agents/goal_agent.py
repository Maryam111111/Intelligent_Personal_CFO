"""GoalPlanningAgent — synthesises all upstream outputs into a goal plan."""

import re
from core.context import AgentContext
from core.models import GoalPlan
from agents.base_agent import BaseAgent
from skills.skill import Skill

PARSE_GOAL = Skill("parse_goal", "Extract target amount and timeline.", "")
MILESTONES = Skill("create_milestones", "Create quarterly milestones.", "")
PROGRESS = Skill("calculate_progress", "Track progress to goal.", "")
MONTHLY_PLAN = Skill("generate_monthly_plan", "Build month-by-month action plan.", "")
RISK = Skill("risk_assessment", "Assess risks and build contingency.", "")


class GoalPlanningAgent(BaseAgent):
    name = "Goal Planning Agent"
    skills = [PARSE_GOAL, MILESTONES, PROGRESS, MONTHLY_PLAN, RISK]

    def run(self, context: AgentContext) -> AgentContext:
        surplus = context.savings.monthly_surplus if context.savings else 850.0
        months_to_goal = context.savings.months_to_goal if context.savings else 60

        # Build an upstream summary for the prompt
        summary_parts = [f"Goal: {context.goal}"]
        if context.spending:
            summary_parts.append(
                f"Income: £{context.spending.total_income:.2f}/mo  "
                f"Expenses: £{context.spending.total_expenses:.2f}/mo"
            )
        if context.budget:
            summary_parts.append(
                f"50/30/20 surplus target: £{context.budget.recommended_savings:.2f}/mo"
            )
        if context.savings:
            summary_parts.append(
                f"Actual surplus: £{surplus:.2f}/mo  "
                f"Savings rate: {context.savings.current_savings_rate_pct:.1f}%"
            )
        if context.investment:
            summary_parts.append(
                f"Investment vehicles: {', '.join(context.investment.recommended_vehicles[:3])}"
            )

        prompt = (
            "You are the final agent — synthesise all upstream findings into a goal plan.\n\n"
            + "\n".join(summary_parts)
            + "\n\nProvide:\n"
            "## Goal Summary — restate goal with target amount and deadline\n"
            "## Month-by-Month Milestones — list key checkpoints (every 6 months)\n"
            "## Risk Assessment — 3 risks (job loss, inflation, overspending) and mitigations\n"
            "## Action Plan for Month 1 — exactly what to do in the next 30 days\n"
            "## Success Metrics — how to know you're on track\n\n"
            "Target 380 words."
        )

        analysis = self.call_claude(prompt)

        # Extract goal amount
        goal_amount = 50_000.0
        match = re.search(r"£([\d,]+)", context.goal)
        if match:
            goal_amount = float(match.group(1).replace(",", ""))

        # Build simple milestones
        milestones = []
        for month in range(6, min(months_to_goal + 1, 61), 6):
            milestones.append({
                "month": month,
                "label": f"Month {month} checkpoint",
                "amount": round(surplus * month, 2),
            })

        context.goal_plan = GoalPlan(
            goal_text=context.goal,
            target_amount=goal_amount,
            monthly_contribution=surplus,
            milestones=milestones,
            risk_level="Medium",
            contingency_notes="Reviewed in risk section of analysis.",
            raw_analysis=analysis,
        )
        return context
