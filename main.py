"""
main.py — Personal Finance AI CFO
──────────────────────────────────
Usage:
    python main.py

  Reads CSV files from data/uploads/, runs all 5 agents in sequence,
  and writes a report to data/reports/.

  Set ANTHROPIC_API_KEY in .env before running.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()

from core.csv_parser import parse_file
from core.context import AgentContext
from core.models import CFOReport
from core.report_generator import write_report
from agents import (
    SpendingAgent, BudgetAgent, SavingsAgent,
    InvestmentAgent, GoalPlanningAgent,
)

console = Console()

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")
DEFAULT_GOAL = "I want £50,000 for a house deposit in 5 years"


def find_csvs() -> tuple[list, list]:
    """Return (bank_files, credit_files) from data/uploads/."""
    bank, credit = [], []
    for fname in os.listdir(UPLOADS_DIR):
        if not fname.endswith(".csv"):
            continue
        lower = fname.lower()
        if "credit" in lower or "card" in lower:
            credit.append(os.path.join(UPLOADS_DIR, fname))
        else:
            bank.append(os.path.join(UPLOADS_DIR, fname))
    return bank, credit


def main():
    console.print(Panel.fit(
        "[bold white]Personal Finance AI CFO[/bold white]\n"
        "[dim]5-agent analysis pipeline[/dim]",
        border_style="bright_black",
    ))

    # ── Load data ────────────────────────────────────────────────
    bank_files, credit_files = find_csvs()
    if not bank_files and not credit_files:
        console.print(
            "[yellow]No CSV files found in data/uploads/.[/yellow]\n"
            "Add your bank_transactions.csv and/or credit_card.csv there, then re-run."
        )
        sys.exit(0)

    bank_txns, credit_txns = [], []
    for f in bank_files:
        console.print(f"  Loading bank file: [cyan]{os.path.basename(f)}[/cyan]")
        bank_txns.extend(parse_file(f))
    for f in credit_files:
        console.print(f"  Loading credit file: [cyan]{os.path.basename(f)}[/cyan]")
        credit_txns.extend(parse_file(f))

    console.print(
        f"\n  [green]✓[/green] {len(bank_txns)} bank transactions, "
        f"{len(credit_txns)} credit card transactions loaded.\n"
    )

    # ── Goal ────────────────────────────────────────────────────
    goal = os.getenv("FINANCIAL_GOAL", DEFAULT_GOAL)
    console.print(f"  [bold]Goal:[/bold] [italic]{goal}[/italic]\n")

    context = AgentContext(
        goal=goal,
        bank_transactions=bank_txns,
        credit_transactions=credit_txns,
    )

    # ── Run agents ───────────────────────────────────────────────
    pipeline = [
        SpendingAgent(),
        BudgetAgent(),
        SavingsAgent(),
        InvestmentAgent(),
        GoalPlanningAgent(),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for agent in pipeline:
            task = progress.add_task(f"[cyan]{agent.name}[/cyan] running...", total=None)
            context = agent.run(context)
            progress.update(task, description=f"[green]✓[/green] {agent.name} complete")
            progress.stop_task(task)

    # ── Build report ─────────────────────────────────────────────
    report = CFOReport(
        goal=goal,
        spending=context.spending,
        budget=context.budget,
        savings=context.savings,
        investment=context.investment,
        goal_plan=context.goal_plan,
        generated_at=datetime.now().isoformat(timespec="seconds"),
    )

    md_path, json_path = write_report(report)
    console.print(f"\n  [bold green]Report saved:[/bold green]")
    console.print(f"    Markdown → [cyan]{md_path}[/cyan]")
    console.print(f"    JSON     → [cyan]{json_path}[/cyan]")
    console.print("\n  Run [bold]streamlit run app.py[/bold] to view the dashboard.\n")


if __name__ == "__main__":
    main()
