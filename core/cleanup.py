"""Data retention and cleanup utilities.

Automatically manages:
- Expiring old transaction files
- Deleting processed data after retention period
- Removing decrypted temporary files
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List


class DataCleanup:
    """Manages data retention and cleanup."""

    def __init__(
        self,
        transaction_retention_days: int = 30,
        report_retention_days: int = 90
    ):
        """Initialize cleanup manager.
        
        Args:
            transaction_retention_days: Days to keep raw transaction files
            report_retention_days: Days to keep generated reports
        """
        self.transaction_retention = timedelta(days=transaction_retention_days)
        self.report_retention = timedelta(days=report_retention_days)

    def cleanup_old_uploads(self, uploads_dir: str = 'data/uploads') -> List[str]:
        """Delete old transaction CSV files beyond retention period.
        
        Args:
            uploads_dir: Directory containing uploaded CSV files
            
        Returns:
            List of deleted file paths
        """
        deleted_files = []
        
        if not os.path.exists(uploads_dir):
            return deleted_files

        now = datetime.now()
        cutoff_time = now - self.transaction_retention

        for file_path in Path(uploads_dir).glob('*.csv'):
            # Get file modification time
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if mod_time < cutoff_time:
                try:
                    os.remove(file_path)
                    deleted_files.append(str(file_path))
                    print(f"Deleted old transaction file: {file_path}")
                except OSError as e:
                    print(f"Failed to delete {file_path}: {e}")

        return deleted_files

    def cleanup_old_reports(self, reports_dir: str = 'data/reports') -> List[str]:
        """Delete old report files beyond retention period.
        
        Args:
            reports_dir: Directory containing generated reports
            
        Returns:
            List of deleted file paths
        """
        deleted_files = []
        
        if not os.path.exists(reports_dir):
            return deleted_files

        now = datetime.now()
        cutoff_time = now - self.report_retention

        for file_path in Path(reports_dir).glob('*'):
            if file_path.is_file():
                # Get file modification time
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if mod_time < cutoff_time:
                    try:
                        os.remove(file_path)
                        deleted_files.append(str(file_path))
                        print(f"Deleted old report file: {file_path}")
                    except OSError as e:
                        print(f"Failed to delete {file_path}: {e}")

        return deleted_files

    def cleanup_temp_files(self, temp_dir: str = '/tmp') -> List[str]:
        """Delete temporary decrypted files.
        
        Args:
            temp_dir: Temporary directory to clean
            
        Returns:
            List of deleted file paths
        """
        deleted_files = []
        
        if not os.path.exists(temp_dir):
            return deleted_files

        # Only delete files we created (with specific prefix)
        for file_path in Path(temp_dir).glob('cfo_temp_*'):
            if file_path.is_file():
                try:
                    os.remove(file_path)
                    deleted_files.append(str(file_path))
                except OSError:
                    pass

        return deleted_files

    def run_full_cleanup(
        self,
        uploads_dir: str = 'data/uploads',
        reports_dir: str = 'data/reports'
    ) -> dict:
        """Run all cleanup tasks.
        
        Args:
            uploads_dir: Directory containing uploaded files
            reports_dir: Directory containing reports
            
        Returns:
            Dict with counts of deleted files per category
        """
        return {
            'deleted_uploads': len(self.cleanup_old_uploads(uploads_dir)),
            'deleted_reports': len(self.cleanup_old_reports(reports_dir)),
            'deleted_temp_files': len(self.cleanup_temp_files())
        }


def run_cleanup(
    transaction_days: int = None,
    report_days: int = None
) -> dict:
    """Convenience function to run cleanup.
    
    Args:
        transaction_days: Override retention days for transactions
        report_days: Override retention days for reports
        
    Returns:
        Summary of deleted files
    """
    import os
    
    # Read from environment if not provided
    if transaction_days is None:
        transaction_days = int(
            os.environ.get('MAX_TRANSACTION_RETENTION_DAYS', 30)
        )
    if report_days is None:
        report_days = int(
            os.environ.get('MAX_REPORT_RETENTION_DAYS', 90)
        )
    
    cleanup = DataCleanup(
        transaction_retention_days=transaction_days,
        report_retention_days=report_days
    )
    
    return cleanup.run_full_cleanup()
