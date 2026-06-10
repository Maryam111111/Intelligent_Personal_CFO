# Personal Finance AI CFO

A **multi-agent AI system** that acts as your personal Chief Financial Officer. Five specialist agents collaborate in sequence to analyse your transactions, build a budget, plan savings, recommend investments, and chart a path to your financial goals.

## Table of Contents
- [Architecture](#architecture)
- [Skills per Agent](#skills-per-agent)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [CSV Format](#csv-format)
- [Security](#security)
- [FAQ](#faq)

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

### Prerequisites
- Python 3.9+
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Installation

```bash
git clone https://github.com/Maryam111111/Intelligent_Personal_CFO
cd Intelligent_Personal_CFO
pip install -r requirements.txt
cp .env.example .env
# Edit .env → add your ANTHROPIC_API_KEY
```

### Usage

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
Intelligent_Personal_CFO/
├── main.py                # CLI entry point
├── app.py                 # Streamlit dashboard
├── requirements.txt
├── .env.example
├── .gitignore            # ← Don't commit .env!
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

**Supported date formats:** `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, `DD Mon YYYY`

**Supported banks:** Barclays, HSBC, Monzo, Starling, Lloyds (column names auto-detected)

---

## Security

### 🔐 Data Privacy & Protection

#### 1. **Local Processing**
- **All transaction data is processed locally** — only the CSV text and your goal are sent to the Anthropic API
- No data is stored on external servers beyond Anthropic's processing
- Reports are saved to your local `data/reports/` directory

#### 2. **Environment Variables**
- **Never commit your API key** — it's ignored via `.gitignore`
- Use `.env` for local secrets (not committed to version control)
- Example `.env`:
  ```
  ANTHROPIC_API_KEY=sk-ant-...
  ENCRYPTION_KEY=your-32-char-key
  MAX_TRANSACTION_RETENTION_DAYS=30
  ```

#### 3. **API Key Best Practices**
- Rotate your API key regularly via [Anthropic console](https://console.anthropic.com/)
- Use a **project-specific key** (don't share personal keys)
- If compromised, revoke immediately and regenerate
- Never paste your key in logs, error messages, or bug reports
- API keys are **masked in logs** (only first 8 characters visible)

#### 4. **CSV File Handling**
- **Validate all uploads:**
  - Maximum file size: 10 MB
  - Only accept `.csv` format
  - Maximum 10,000 rows per file
  - Sanitize descriptions (remove null bytes, limit length to 500 chars)
- **Temporary files are cleaned up** after processing

#### 5. **Report Output**
- **Reports contain sensitive data** — store in a secure location
- Files are saved to `data/reports/` (not web-accessible)
- Consider encrypting files at rest if stored long-term
- Implement `MAX_REPORT_RETENTION_DAYS` to auto-clean old reports

#### 6. **Streamlit Dashboard Security**
- **No authentication built in** — deploy behind auth (e.g., Basic Auth, OAuth)
- **File size limits enforced** (10 MB max uploads)
- **Security notices displayed** to users about data privacy
- If running on shared server:
  - Restrict network access (firewall rules)
  - Use HTTPS with valid certificates
  - Add session timeout & user verification
- **Never share session links publicly** — they expose your financial data

#### 7. **Input Validation & Sanitization**
- **CSV parsing validates:**
  - Date formats (multiple UK formats supported)
  - Amount fields (numeric only, currency symbols stripped)
  - Description length (max 500 chars)
  - Row counts (max 10,000 rows)
  - Null bytes and control characters removed
- **Goal field** is user-provided — validated in Streamlit (max 500 chars)

#### 8. **Error Handling**
- **Clear error messages** without exposing system details
- **Logging enabled** for audit trails (sensitive data masked)
- **Graceful degradation** if API calls fail
- Rate limit retries with exponential backoff

#### 9. **Compliance & Regulations**
- This tool is **for personal use only** — not regulated financial advice
- Consult a qualified financial adviser before making investment decisions
- If handling others' data (e.g., family members):
  - Ensure explicit consent
  - Comply with local data protection laws (GDPR, CCPA, etc.)
  - Implement access controls

#### 10. **Dependency Security**
- Keep dependencies up-to-date:
  ```bash
  pip install --upgrade -r requirements.txt
  pip-audit  # Check for known vulnerabilities
  ```
- Review `requirements.txt` regularly for unmaintained packages

### 📋 Configuration Security

Ensure `.gitignore` exists and contains:
```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Secrets
secrets.json
*.key
*.pem

# Reports & uploads (optional)
data/uploads/*
data/reports/*

# Python
__pycache__/
*.pyc
*.egg-info/

# IDE
.vscode/
.idea/
```

### 🚨 Security Checklist

Before deploying:
- [ ] `.env` is in `.gitignore` (not committed)
- [ ] API key is rotated and unique to this project
- [ ] `.env.example` has no real secrets
- [ ] Report directory is not web-accessible
- [ ] Streamlit dashboard is behind authentication (if shared)
- [ ] Logs don't contain API keys or financial data
- [ ] Dependencies are up-to-date (`pip-audit`)
- [ ] CSV uploads have size limits enforced (10 MB)
- [ ] Old reports are cleaned up (`MAX_REPORT_RETENTION_DAYS`)

---

## FAQ

### Q: Is my data safe?
**A:** Yes — transactions only leave your computer to Anthropic's API. No third-party storage. Treat reports like you would a private spreadsheet.

### Q: Can I use this for others' finances?
**A:** Only with explicit consent and compliance with local data protection laws. The tool is designed for personal use.

### Q: What if I leak my API key?
**A:** Revoke it immediately in the [Anthropic console](https://console.anthropic.com/) and regenerate. Leaked keys can incur unexpected charges.

### Q: How do I delete old reports?
**A:** Set `MAX_REPORT_RETENTION_DAYS=30` in `.env` to auto-clean. Or manually delete from `data/reports/`.

### Q: Can I run this on a shared server?
**A:** Yes, but add authentication (Streamlit's built-in community cloud auth, or deploy behind Nginx with Basic Auth).

### Q: What financial advice does this give?
**A:** AI-generated recommendations for informational purposes only. Not regulated financial advice. Consult a qualified adviser before making major decisions.

---

## Notes

- **All data is processed locally** — only the CSV text and goal are sent to the Anthropic API.
- **Financial outputs are AI-generated** and for informational purposes only; consult a qualified adviser for regulated financial advice.
- **Disclaimer:** This tool is not a substitute for professional financial, tax, or investment advice.
