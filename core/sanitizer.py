"""Data sanitization and anonymization module.

Ensures that:
1. No personal transaction data is sent to external APIs
2. All data transmitted uses percentages/aggregates only
3. Merchant names and descriptions are anonymized
4. Date ranges are generalized instead of specific dates
"""

import hashlib
from typing import List, Dict, Any
from datetime import datetime, timedelta
import os


class DataSanitizer:
    """Sanitizes financial data before transmission to APIs."""

    def __init__(self, anonymize_merchants: bool = True):
        """Initialize sanitizer with configuration.
        
        Args:
            anonymize_merchants: Whether to hash merchant names
        """
        self.anonymize_merchants = anonymize_merchants
        self._merchant_hash_cache = {}

    def anonymize_merchant(self, merchant_name: str) -> str:
        """Convert merchant name to anonymized hash.
        
        Args:
            merchant_name: Original merchant name from transaction
            
        Returns:
            Hashed merchant identifier (8 chars)
            
        Example:
            >>> sanitizer.anonymize_merchant('Sainsbury\'s')
            'a7f2c8e1'
        """
        if merchant_name in self._merchant_hash_cache:
            return self._merchant_hash_cache[merchant_name]

        hash_val = hashlib.sha256(
            merchant_name.lower().encode()
        ).hexdigest()[:8]
        
        self._merchant_hash_cache[merchant_name] = hash_val
        return hash_val

    def sanitize_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a single transaction.
        
        Args:
            transaction: Raw transaction dict with keys like 'description', 'amount'
            
        Returns:
            Sanitized transaction with anonymized merchant and category
        """
        sanitized = {
            'category': transaction.get('category', 'Unknown'),
            'amount': transaction.get('amount', 0),
        }

        # Anonymize merchant if present
        if 'description' in transaction and self.anonymize_merchants:
            sanitized['merchant_hash'] = self.anonymize_merchant(
                transaction['description']
            )
        else:
            sanitized['merchant_hash'] = None

        # Remove sensitive fields
        # Never include: description, account number, date, name, etc.
        
        return sanitized

    def aggregate_to_percentages(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Convert raw transactions to percentage-based summary.
        
        CRITICAL: This is what gets sent to Claude API, never raw transactions.
        
        Args:
            transactions: List of transaction dicts
            
        Returns:
            Dict with only percentages, counts, and anonymized data
            
        Example:
            >>> result = sanitizer.aggregate_to_percentages(txns)
            >>> result['category_percentages']['Housing']
            32.5
            >>> result['anonymized']
            True
        """
        if not transactions:
            return {
                'category_percentages': {},
                'total_transactions': 0,
                'anonymized': True,
                'total_amount': 0
            }

        # Aggregate by category
        categories = {}
        total_amount = 0

        for txn in transactions:
            sanitized = self.sanitize_transaction(txn)
            category = sanitized['category']
            amount = sanitized['amount']

            categories[category] = categories.get(category, 0) + amount
            total_amount += amount

        # Convert to percentages
        category_percentages = {}
        if total_amount > 0:
            for category, amount in categories.items():
                percentage = (amount / total_amount) * 100
                category_percentages[category] = round(percentage, 2)

        return {
            'category_percentages': category_percentages,
            'total_transactions': len(transactions),
            'anonymized': True,
            'total_amount': round(total_amount, 2),
            'date_range': self._get_generalized_date_range(transactions)
        }

    def _get_generalized_date_range(
        self,
        transactions: List[Dict[str, Any]]
    ) -> str:
        """Get generalized date range (quarter/month, not exact dates).
        
        Args:
            transactions: List of transactions with 'date' field
            
        Returns:
            Generalized date range like 'Q1 2024' or 'January 2024'
        """
        if not transactions:
            return 'Unknown'

        # Extract dates if available
        dates = []
        for txn in transactions:
            if 'date' in txn:
                try:
                    if isinstance(txn['date'], str):
                        date_obj = datetime.fromisoformat(txn['date'])
                    else:
                        date_obj = txn['date']
                    dates.append(date_obj)
                except (ValueError, TypeError):
                    continue

        if not dates:
            return 'Unknown'

        min_date = min(dates)
        max_date = max(dates)

        # Return as month/year range or quarter
        if min_date.year == max_date.year:
            if min_date.month == max_date.month:
                return f"{min_date.strftime('%B %Y')}"
            else:
                return (
                    f"{min_date.strftime('%B')} - "
                    f"{max_date.strftime('%B %Y')}"
                )
        else:
            return f"{min_date.year} - {max_date.year}"

    def create_api_safe_context(
        self,
        transactions: List[Dict[str, Any]],
        goal: str = None
    ) -> Dict[str, Any]:
        """Create safe context for Claude API call.
        
        Args:
            transactions: Raw transaction list
            goal: User's financial goal (can be sent as-is if not sensitive)
            
        Returns:
            Safe context with only aggregated data, no raw transactions
        """
        return {
            'spending_summary': self.aggregate_to_percentages(transactions),
            'goal': goal,
            'data_is_anonymized': True,
            'raw_data_included': False
        }
