"""
Normalises bank / credit-card CSV exports into Transaction objects.
Includes validation, sanitization, and security checks.
"""

import csv
import io
import re
import logging
from datetime import date, datetime
from typing import Optional

from core.models import Transaction

logger = logging.getLogger(__name__)

# Configuration
MAX_CSV_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROWS = 10000
MAX_DESCRIPTION_LENGTH = 500

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
    """Parse date string in multiple formats."""
    raw = raw.strip()
    if not raw:
        raise ValueError("Date field is empty")
    
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    
    raise ValueError(f"Cannot parse date: {raw!r}")


def _parse_amount(raw: str) -> float:
    """Strip currency symbols, handle parentheses (UK negative format)."""
    raw = raw.strip()
    if not raw:
        raise ValueError("Amount field is empty")
    
    negative = raw.startswith("(") and raw.endswith(")")
    raw = re.sub(r"[£$€,\s()]", "", raw)
    raw = re.sub(r"^\+", "", raw)
    
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"Cannot parse amount: {raw!r}")
    
    return -abs(value) if negative else value


def _sanitize_description(desc: str, max_len: int = MAX_DESCRIPTION_LENGTH) -> str:
    """Sanitize description: trim, limit length, remove dangerous chars."""
    desc = desc.strip()
    
    # Limit length
    if len(desc) > max_len:
        logger.warning(f"Description truncated from {len(desc)} to {max_len} chars")
        desc = desc[:max_len]
    
    # Remove null bytes and control characters
    desc = "".join(ch for ch in desc if ch.isprintable() or ch.isspace())
    
    return desc


def _find_col(headers: list[str], aliases: set[str]) -> Optional[int]:
    """Find column index by alias."""
    for i, h in enumerate(headers):
        if h.lower().strip() in aliases:
            return i
    return None


def parse_csv(content: str) -> list[Transaction]:
    """
    Parse a CSV string and return a list of Transaction objects.
    
    Args:
        content: CSV string content
        
    Returns:
        List of validated Transaction objects
        
    Raises:
        ValueError: If CSV is invalid or exceeds size limits
    """
    # Validate size
    if len(content.encode('utf-8')) > MAX_CSV_SIZE_BYTES:
        raise ValueError(
            f"CSV file exceeds maximum size ({MAX_CSV_SIZE_BYTES / 1024 / 1024:.1f} MB)"
        )
    
    transactions: list[Transaction] = []
    reader = csv.reader(io.StringIO(content.strip()))
    headers = next(reader, None)
    
    if not headers:
        logger.warning("Empty CSV file provided")
        return []
    
    # Find required columns
    date_col = _find_col(headers, _DATE_ALIASES)
    desc_col = _find_col(headers, _DESC_ALIASES)
    amount_col = _find_col(headers, _AMOUNT_ALIASES)
    cat_col = _find_col(headers, _CAT_ALIASES)
    
    if date_col is None or desc_col is None or amount_col is None:
        raise ValueError(
            "CSV must have columns for date, description, and amount. "
            f"Found headers: {headers}"
        )
    
    logger.info(f"Parsing CSV with {len(headers)} columns")
    
    row_num = 0
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
        if not row or not any(row):
            continue
        
        # Check row limit
        if row_num > MAX_ROWS:
            logger.warning(f"CSV exceeds {MAX_ROWS} rows; stopping parse")
            break
        
        try:
            # Validate and parse each field
            parsed_date = _parse_date(row[date_col])
            parsed_desc = _sanitize_description(row[desc_col])
            parsed_amount = _parse_amount(row[amount_col])
            parsed_cat = (
                row[cat_col].strip() 
                if cat_col is not None and cat_col < len(row)
                else "Uncategorised"
            )
            
            # Create transaction
            txn = Transaction(
                date=parsed_date,
                description=parsed_desc,
                amount=parsed_amount,
                category=parsed_cat,
            )
            transactions.append(txn)
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Row {row_num}: Skipping due to parse error: {e}")
            continue
    
    logger.info(f"Successfully parsed {len(transactions)} transactions from {row_num} rows")
    return transactions


def parse_file(path: str) -> list[Transaction]:
    """
    Parse a CSV file and return a list of Transaction objects.
    
    Args:
        path: File path to CSV
        
    Returns:
        List of validated Transaction objects
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is invalid
    """
    logger.info(f"Reading CSV file: {path}")
    
    try:
        with open(path, encoding="utf-8") as f:
            return parse_csv(f.read())
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
    except UnicodeDecodeError as e:
        logger.error(f"File encoding error: {path}")
        raise ValueError(f"File must be UTF-8 encoded: {path}") from e
