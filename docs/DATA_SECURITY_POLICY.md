# Data Security & Privacy Policy

## Overview

This document outlines how **Intelligent Personal CFO** handles, processes, and protects your financial data.

## Key Principles

### 1. **Local Processing Only**
- ✅ All CSV data is processed **locally on your machine**
- ✅ Raw transaction details never leave your computer
- ✅ Only **anonymized, aggregated percentages** are sent to APIs

### 2. **No Personal Information Transit**

We **NEVER** send to external APIs:
- ❌ Transaction descriptions (e.g., "Sainsbury's", "Shell")
- ❌ Merchant names
- ❌ Customer names or account numbers
- ❌ Transaction dates or times
- ❌ Exact amounts
- ❌ Bank details

We **ONLY** send:
- ✅ Category percentages (e.g., "Housing: 32.5%")
- ✅ Transaction counts (e.g., "245 transactions analyzed")
- ✅ Generalized date ranges (e.g., "Q1 2024")
- ✅ Your financial goals (if provided)

### 3. **Data Anonymization**

#### Merchant Names
Merchant names are hashed using SHA-256:
```python
"Sainsbury's" → "a7f2c8e1" (hashed, not reversible)
```

#### Transaction Descriptions
Removed before any API transmission.

#### Dates
Generalized to month/quarter level:
```
Jan 15 → January 2024
Jan 15, Feb 3, Mar 20 → January - March 2024
```

### 4. **Encryption at Rest**

All stored financial data is encrypted using **Fernet (AES-128)**:

```bash
# Generate encryption key (do this once)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
ENCRYPTION_KEY=your-generated-key
```

## Data Lifecycle

### Upload Phase
1. User drops CSV file in `data/uploads/`
2. CSV is parsed locally (never uploaded anywhere)
3. Raw CSV remains **only** on local disk

### Processing Phase
1. Raw transactions are read into memory
2. Anonymization & sanitization applied in-memory
3. Anonymized summary created (percentages only)
4. Raw data discarded from memory

### API Phase
1. **Only** anonymized summary sent to Anthropic API
2. Claude processes percentages, not raw data
3. Response cached locally (encrypted)

### Storage Phase
1. Reports saved to `data/reports/` (encrypted)
2. Raw CSVs deleted after processing
3. Cached API responses stored encrypted

### Cleanup Phase

#### Raw Transaction Data
- **Retention**: 24 hours or `MAX_TRANSACTION_RETENTION_DAYS` config
- **Action**: Auto-deleted after expiration
- **Location**: `data/uploads/`

#### Processed Reports
- **Retention**: 90 days or `MAX_REPORT_RETENTION_DAYS` config
- **Action**: Auto-deleted after expiration
- **Location**: `data/reports/`

#### Encryption Keys
- **Stored in**: `.env` (never committed to git)
- **Backup**: Keep `.env` safe, regenerate if lost

## Configuration

Add to your `.env` file:

```bash
# API Configuration
ANTHROPIC_API_KEY=sk-...
ENCRYPTION_KEY=generated-key-here

# Data Retention (days)
MAX_TRANSACTION_RETENTION_DAYS=30
MAX_REPORT_RETENTION_DAYS=90

# Security Features (recommended: all true)
ANONYMIZE_MERCHANTS=true
CONVERT_TO_PERCENTAGES=true
HASH_TRANSACTION_DESCRIPTIONS=true
```

## File Structure

```
data/
├── uploads/              ← Drop CSV here (deleted after 24h)
│   └── .gitignore        ← Never commit CSV files
├── processed/            ← Anonymized data (encrypted)
│   └── .gitignore        ← Never commit processed data
└── reports/              ← Output reports (encrypted)
    └── .gitignore        ← Never commit report data
```

## What Gets Sent to Claude API

### ✅ YES - Safe to Send
```json
{
  "spending_distribution": {
    "Housing": 32.5,
    "Food": 18.2,
    "Transport": 15.0
  },
  "transaction_summary": "Analyzed 245 transactions",
  "date_range": "January - March 2024",
  "goal": "Save £5000 for emergency fund"
}
```

### ❌ NO - Never Send
```json
{
  "transactions": [
    {
      "date": "2024-01-15",
      "merchant": "Sainsbury's",
      "amount": 45.23,
      "description": "Weekly groceries"
    }
  ]
}
```

## Testing

### Mocked Tests (No Real Data)
```bash
pytest tests/  # Uses mock data, no API calls, safe
```

### Live API Tests (With Caution)
```bash
# Only with anonymized test data, never real transactions
TEST_LIVE_API=1 pytest tests/
```

## Security Checklist

- [ ] `.env` file created and in `.gitignore`
- [ ] `ENCRYPTION_KEY` generated and stored in `.env`
- [ ] `data/uploads/` in `.gitignore` (never commit CSVs)
- [ ] `data/processed/` in `.gitignore` (encrypted anyway)
- [ ] `data/reports/` in `.gitignore` (encrypted anyway)
- [ ] `.env.example` has placeholders, no real keys
- [ ] All transactions converted to percentages before API calls
- [ ] Merchant names hashed before processing
- [ ] Date ranges generalized (no exact dates in API)
- [ ] Regular cleanup of expired transaction data

## Troubleshooting

### "ENCRYPTION_KEY not set"
```bash
# Generate a key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env
echo "ENCRYPTION_KEY=your-key-here" >> .env
```

### Files Not Being Deleted
Check that cleanup tasks are running:
```bash
# Manually trigger cleanup
python -c "from core.cleanup import run_cleanup; run_cleanup()"
```

### Accidentally Committed Sensitive Files
```bash
# Remove from git history (one-time)
git filter-branch --tree-filter 'rm -f data/uploads/*.csv' HEAD

# Or use BFG tool for larger repos
```

## Contact

For security concerns, please file a private security advisory on GitHub.

---

**Last Updated**: 2024  
**Version**: 1.0
