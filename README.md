# Personal Finance AI CFO

A **multi-agent AI system** that acts as your personal Chief Financial Officer. Five specialist agents collaborate in sequence to analyse your transactions, build a budget, plan savings, recommend investments, and track progress toward your financial goals.

## Architecture

```
                    ┌──────────────────────────────────────────┐
                    │            AgentContext                    │
                    │  (passed downstream through all agents)   │
                    └──────────────────────────────────────────┘
                                       │
             ┌──────────┬──────────────┼──────────────┬──────────┐
             ▼          ▼              ▼               ▼          ▼
        Spending    Budget          Savings       Investment    Goal
         Agent      Agent           Agent          Agent      Planning
           │          │               │               │         Agent
           ▼          ▼               ▼               ▼          ▼
      SpendingReport BudgetPlan SavingsEstimate InvestmentStrategy GoalPlan
                                                              │
                                                              ▼
                                                         CFOReport
                                                      (MD + JSON output)
```

Each agent:
1. Reads from `AgentContext` (including all upstream outputs)
2. Builds a structured prompt using its **skills**
3. Calls Claude via `core/claude_client.py`
4. Populates a typed dataclass back into the context

## Skills per Agent

| Agent | Skills |
|---|---|
| SpendingAgent | `categorise_transactions`, `detect_anomalies`, `rank_categories`, `flag_recurring` |
| BudgetAgent | `build_50_30_20`, `compare_actual_vs_target`, `identify_overruns`, `suggest_cuts` |
| SavingsAgent | `estimate_monthly_surplus`, `emergency_fund_plan`, `savings_rate_benchmark`, `timeline_to_goal` |
| InvestmentAgent | `recommend_vehicles`, `allocate_portfolio`, `project_returns`, `tax_wrapper_advice` |
| GoalPlanningAgent | `parse_goal`, `create_milestones`, `calculate_progress`, `generate_monthly_plan`, `risk_assessment` |

## Quick Start

```bash
git clone https://github.com/yourname/finance-ai-cfo
cd finance-ai-cfo
pip install -r requirements.txt
cp .env.example .env
# Edit .env → add your ANTHROPIC_API_KEY
```

**CLI pipeline:**
```bash
# Drop CSV files in data/uploads/
python main.py
# Report saved to data/reports/
```

**Streamlit dashboard:**
```bash
streamlit run app.py
```

**Tests:**
```bash
pytest tests/                        # mocked (no API key needed)
TEST_LIVE_API=1 pytest tests/        # live API
```

## Project Structure

```
finance-ai-cfo/
├── main.py                # CLI entry point
├── app.py                 # Streamlit dashboard
├── requirements.txt
├── .env.example
├── agents/
│   ├── base_agent.py      # Abstract BaseAgent
│   ├── spending_agent.py
│   ├── budget_agent.py
│   ├── savings_agent.py
│   ├── investment_agent.py
│   └── goal_agent.py
├── skills/
│   ├── skill.py           # Skill dataclass
│   ├── spending_skills.py
│   └── ...
├── core/
│   ├── claude_client.py   # Anthropic SDK wrapper
│   ├── models.py          # Pydantic dataclasses
│   ├── csv_parser.py      # Bank CSV normaliser
│   ├── context.py         # AgentContext
│   └── report_generator.py
├── data/
│   ├── uploads/           # Drop CSV files here
│   └── reports/           # Output reports
└── tests/
    ├── test_spending_agent.py
    └── test_pipeline.py
```

## CSV Format

Any bank export with these columns (names are normalised):

```csv
Date,Description,Amount,Category
2024-01-14,Salary,+3800.00,Income
2024-01-15,Rent,-1200.00,Housing
```

Supported date formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `DD Mon YYYY`.
Supported banks: Barclays, HSBC, Monzo, Starling, Lloyds (column names auto-detected).

## Notes

- All data is processed locally — only the CSV text and goal are sent to the Anthropic API.
- Financial outputs are AI-generated and for informational purposes only; consult a qualified adviser for regulated financial advice.
