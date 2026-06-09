"""Normalises bank / credit-card CSV exports into Transaction objects."""

import csv
import io
import re
from datetime import date, datetime
from typing import Optional

from core.models import Transaction

# Common date formats found in UK bank exports
_DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y",
    "%d %b %Y", "%d %B %Y", "%m/%d/%Y",
]

# Normalised column-name aliases
_DATE_ALIASES = {"date", "transaction date", "trans date", "posted date"}
_DESC_ALIASES = {"description", "details", "narrative", "merchant", "payee"}
_AMOUNT_ALIASES = {"amount", "value", "debit/credit", "transaction amount"}
_CAT_ALIASES = {"category", "type", "transaction type"}


def _parse_date(raw: str) -> date:
    raw = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Cannot parse date: {raw!r}")


def _parse_amount(raw: str) -> float:
    """Strip currency symbols, handle parentheses (UK negative format)."""
    raw = raw.strip()
    negative = raw.startswith("(") and raw.endswith(")")
    raw = re.sub(r"[£$€,\s()]", "", raw)
    raw = re.sub(r"^\+", "", raw)
    value = float(raw)
    return -abs(value) if negative else value


def _find_col(headers: list[str], aliases: set[str]) -> Optional[int]:
    for i, h in enumerate(headers):
        if h.lower().strip() in aliases:
            return i
    return None


def parse_csv(content: str) -> list[Transaction]:
    """Parse a CSV string and return a list of Transaction objects."""
    transactions: list[Transaction] = []
    reader = csv.reader(io.StringIO(content.strip()))
    headers = next(reader, None)
    if not headers:
        return []

    date_col = _find_col(headers, _DATE_ALIASES)
    desc_col = _find_col(headers, _DESC_ALIASES)
    amount_col = _find_col(headers, _AMOUNT_ALIASES)
    cat_col = _find_col(headers, _CAT_ALIASES)

    if date_col is None or desc_col is None or amount_col is None:
        raise ValueError(
            "CSV must have columns for date, description, and amount. "
            f"Found headers: {headers}"
        )

    for row in reader:
        if not row or not any(row):
            continue
        try:
            txn = Transaction(
                date=_parse_date(row[date_col]),
                description=row[desc_col].strip(),
                amount=_parse_amount(row[amount_col]),
                category=row[cat_col].strip() if cat_col is not None else "Uncategorised",
            )
            transactions.append(txn)
        except (ValueError, IndexError) as e:
            print(f"  [warn] Skipping row {row}: {e}")

    return transactions


def parse_file(path: str) -> list[Transaction]:
    with open(path, encoding="utf-8") as f:
        return parse_csv(f.read())
