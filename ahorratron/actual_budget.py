"""
Integration module for Actual Budget system.
This is a mock implementation since the actual integration details are not specified.
"""
import uuid
from datetime import datetime
from typing import Dict, Any
import pandas as pd


class ActualBudgetError(Exception):
    """Custom exception for Actual Budget operations."""
    pass


class ActualBudgetIntegration:
    """Mock integration with Actual Budget system."""
    
    def __init__(self):
        # Mock storage for demonstration
        self.transactions = []
    
    def add_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """
        Add a transaction to the Actual Budget system.
        
        Args:
            transaction_data: Dictionary containing transaction data with keys:
                - date: Transaction date (YYYY-MM-DD format)
                - amount: Transaction amount (float)
                - description: Transaction description/merchant
                - notes: Additional notes/metadata
        
        Returns:
            str: Generated transaction ID
            
        Raises:
            ActualBudgetError: If the transaction cannot be added
        """
        try:
            # Validate required fields
            required_fields = ['date', 'amount', 'description']
            for field in required_fields:
                if field not in transaction_data:
                    raise ActualBudgetError(f"Missing required field: {field}")
            
            # Validate date format
            try:
                datetime.strptime(transaction_data['date'], '%Y-%m-%d')
            except ValueError:
                raise ActualBudgetError("Invalid date format. Expected YYYY-MM-DD")
            
            # Validate amount
            if not isinstance(transaction_data['amount'], (int, float)):
                raise ActualBudgetError("Amount must be a number")
            
            # Generate transaction ID
            transaction_id = str(uuid.uuid4())
            
            # Add timestamp and ID to transaction
            full_transaction = {
                'transaction_id': transaction_id,
                'created_at': datetime.now().isoformat(),
                **transaction_data
            }
            
            # Store transaction (in real implementation, this would save to Actual Budget)
            self.transactions.append(full_transaction)
            
            return transaction_id
            
        except Exception as e:
            if isinstance(e, ActualBudgetError):
                raise
            raise ActualBudgetError(f"Failed to add transaction: {str(e)}")
    
    def convert_apple_pay_to_actual_format(self, apple_pay_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Apple Pay transaction data to Actual Budget format.
        
        Args:
            apple_pay_data: Apple Pay transaction data
            
        Returns:
            Dictionary in Actual Budget format
        """
        # Build description from merchant and category
        description = apple_pay_data['merchant']
        if apple_pay_data.get('category'):
            description += f" ({apple_pay_data['category']})"
        
        # Build notes from metadata
        notes = description
        if apple_pay_data.get('metadata'):
            metadata_str = ", ".join([f"{k}: {v}" for k, v in apple_pay_data['metadata'].items()])
            notes += f" | {metadata_str}"
        
        return {
            'date': apple_pay_data['date'],
            'amount': apple_pay_data['amount'],
            'description': description,
            'notes': notes
        }


# Global instance for the API
actual_budget = ActualBudgetIntegration()