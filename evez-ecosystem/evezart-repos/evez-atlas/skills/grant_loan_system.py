"""
GRANT-LOAN FINANCING SYSTEM - Circular Funding for Quantum Pipeline Access
Creator: @Evez666 | Motivation to Buy

"If they pull off a grant for a loan that loans the grants?"

This system implements circular financing where grants enable loans,
which enable access to quantum services, which generate value that
repays loans and funds more grants.
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from quantum import compute_fingerprint


class Grant:
    """A grant for initial quantum pipeline access."""
    
    def __init__(
        self,
        grant_id: str,
        recipient: str,
        amount: float,
        purpose: str,
        approved: bool = False
    ):
        self.grant_id = grant_id
        self.recipient = recipient
        self.amount = amount
        self.purpose = purpose
        self.approved = approved
        self.created_at = time.time()
        self.approved_at = None
    
    def approve(self):
        """Approve the grant."""
        self.approved = True
        self.approved_at = time.time()
    
    def to_dict(self) -> Dict:
        return {
            "grant_id": self.grant_id,
            "recipient": self.recipient,
            "amount": self.amount,
            "purpose": self.purpose,
            "approved": self.approved,
            "created_at": self.created_at,
            "approved_at": self.approved_at
        }


class Loan:
    """A loan backed by approved grants."""
    
    def __init__(
        self,
        loan_id: str,
        borrower: str,
        amount: float,
        backed_by_grant: str,
        term_days: int = 90
    ):
        self.loan_id = loan_id
        self.borrower = borrower
        self.amount = amount
        self.backed_by_grant = backed_by_grant
        self.term_days = term_days
        self.created_at = time.time()
        self.due_date = self.created_at + (term_days * 86400)
        self.repaid = False
        self.repaid_at = None
        self.repaid_amount = 0.0
    
    def repay(self, amount: float):
        """Repay part or all of the loan."""
        self.repaid_amount += amount
        if self.repaid_amount >= self.amount:
            self.repaid = True
            self.repaid_at = time.time()
    
    def to_dict(self) -> Dict:
        return {
            "loan_id": self.loan_id,
            "borrower": self.borrower,
            "amount": self.amount,
            "backed_by_grant": self.backed_by_grant,
            "term_days": self.term_days,
            "created_at": self.created_at,
            "due_date": self.due_date,
            "repaid": self.repaid,
            "repaid_at": self.repaid_at,
            "repaid_amount": self.repaid_amount
        }


class GrantLoanSystem:
    """
    Circular financing system for quantum pipeline access.
    
    Flow:
    1. Agent applies for grant
    2. Grant approved → becomes collateral
    3. Agent takes loan backed by grant
    4. Loan funds quantum sensor purchases
    5. Quantum sensors generate value through usage
    6. Value repays loan
    7. Repaid funds create new grants
    8. Cycle continues
    """
    
    def __init__(self, creator: str = "@Evez666"):
        self.creator = creator
        self.data_dir = Path("data/financing")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.grants_log = self.data_dir / "grants.jsonl"
        self.loans_log = self.data_dir / "loans.jsonl"
        
        # Registries
        self.grants: Dict[str, Grant] = {}
        self.loans: Dict[str, Loan] = {}
        
        # Pool tracking
        self.grant_pool = 10000.0  # Initial grant pool
        self.loan_pool = 0.0  # Grows from repayments
        
        self.system_id = compute_fingerprint(f"grant-loan-{creator}-{time.time()}")
    
    def apply_for_grant(
        self,
        applicant: str,
        amount: float,
        purpose: str
    ) -> Dict[str, Any]:
        """
        Apply for a grant to access quantum pipeline.
        
        Args:
            applicant: Agent identifier
            amount: Grant amount requested
            purpose: Intended use (e.g., "quantum sensor access")
            
        Returns:
            Grant application result
        """
        if amount > self.grant_pool:
            return {
                "success": False,
                "error": f"Requested amount ${amount} exceeds available pool ${self.grant_pool}"
            }
        
        grant_id = compute_fingerprint(f"grant-{applicant}-{time.time()}")
        
        grant = Grant(
            grant_id=grant_id,
            recipient=applicant,
            amount=amount,
            purpose=purpose
        )
        
        # Auto-approve if funds available (simplified)
        if amount <= self.grant_pool * 0.1:  # Up to 10% of pool
            grant.approve()
            self.grant_pool -= amount
        
        self.grants[grant_id] = grant
        self._log_event("grant_applied", grant.to_dict())
        
        return {
            "success": True,
            "grant_id": grant_id,
            "amount": amount,
            "approved": grant.approved,
            "message": "Grant approved" if grant.approved else "Grant pending approval"
        }
    
    def convert_grant_to_loan(
        self,
        grant_id: str,
        loan_amount_multiplier: float = 2.0,
        term_days: int = 90
    ) -> Dict[str, Any]:
        """
        Convert approved grant into a larger loan.
        
        "Grant for a loan that loans the grants"
        
        Args:
            grant_id: Approved grant to convert
            loan_amount_multiplier: Loan amount as multiple of grant (e.g., 2x)
            term_days: Loan term in days
            
        Returns:
            Loan details
        """
        if grant_id not in self.grants:
            return {"success": False, "error": "Grant not found"}
        
        grant = self.grants[grant_id]
        
        if not grant.approved:
            return {"success": False, "error": "Grant not approved"}
        
        # Loan backed by grant
        loan_amount = grant.amount * loan_amount_multiplier
        
        loan_id = compute_fingerprint(f"loan-{grant.recipient}-{time.time()}")
        
        loan = Loan(
            loan_id=loan_id,
            borrower=grant.recipient,
            amount=loan_amount,
            backed_by_grant=grant_id,
            term_days=term_days
        )
        
        self.loans[loan_id] = loan
        self.loan_pool += loan_amount  # Available for borrower
        
        self._log_event("loan_created", loan.to_dict())
        
        return {
            "success": True,
            "loan_id": loan_id,
            "amount": loan_amount,
            "grant_amount": grant.amount,
            "multiplier": loan_amount_multiplier,
            "due_date": datetime.fromtimestamp(loan.due_date).isoformat(),
            "message": f"Loan of ${loan_amount} created from ${grant.amount} grant"
        }
    
    def use_loan_for_purchase(
        self,
        loan_id: str,
        purchase_amount: float,
        purchase_description: str
    ) -> Dict[str, Any]:
        """
        Use loan funds to purchase quantum sensors.
        
        Args:
            loan_id: Active loan
            purchase_amount: Amount to spend
            purchase_description: What's being purchased
            
        Returns:
            Purchase authorization
        """
        if loan_id not in self.loans:
            return {"success": False, "error": "Loan not found"}
        
        loan = self.loans[loan_id]
        
        if loan.repaid:
            return {"success": False, "error": "Loan already repaid"}
        
        if purchase_amount > loan.amount - loan.repaid_amount:
            return {
                "success": False,
                "error": f"Insufficient loan balance. Remaining: ${loan.amount - loan.repaid_amount}"
            }
        
        # Authorize purchase
        self._log_event("loan_used", {
            "loan_id": loan_id,
            "amount": purchase_amount,
            "description": purchase_description
        })
        
        return {
            "success": True,
            "authorized": True,
            "amount": purchase_amount,
            "remaining": loan.amount - loan.repaid_amount - purchase_amount,
            "message": f"${purchase_amount} authorized for {purchase_description}"
        }
    
    def repay_loan(
        self,
        loan_id: str,
        amount: float,
        source: str = "quantum_service_revenue"
    ) -> Dict[str, Any]:
        """
        Repay loan from quantum service usage revenue.
        
        Args:
            loan_id: Loan to repay
            amount: Repayment amount
            source: Source of repayment funds
            
        Returns:
            Repayment confirmation
        """
        if loan_id not in self.loans:
            return {"success": False, "error": "Loan not found"}
        
        loan = self.loans[loan_id]
        
        if loan.repaid:
            return {"success": False, "error": "Loan already fully repaid"}
        
        # Apply repayment
        loan.repay(amount)
        
        # Repaid funds go back to grant pool (circular!)
        recycle_to_grants = amount * 0.5  # 50% recycled to grants
        self.grant_pool += recycle_to_grants
        
        self._log_event("loan_repaid", {
            "loan_id": loan_id,
            "amount": amount,
            "source": source,
            "fully_repaid": loan.repaid,
            "recycled_to_grants": recycle_to_grants
        })
        
        return {
            "success": True,
            "amount": amount,
            "remaining": max(0, loan.amount - loan.repaid_amount),
            "fully_repaid": loan.repaid,
            "recycled_to_grants": recycle_to_grants,
            "message": "Loan fully repaid" if loan.repaid else f"${amount} applied to loan"
        }
    
    def get_financing_status(self) -> Dict[str, Any]:
        """Get overall financing system status."""
        total_grants = len(self.grants)
        approved_grants = sum(1 for g in self.grants.values() if g.approved)
        total_loans = len(self.loans)
        repaid_loans = sum(1 for l in self.loans.values() if l.repaid)
        
        return {
            "system_id": self.system_id,
            "grant_pool": self.grant_pool,
            "loan_pool": self.loan_pool,
            "total_grants": total_grants,
            "approved_grants": approved_grants,
            "total_loans": total_loans,
            "repaid_loans": repaid_loans,
            "active_loans": total_loans - repaid_loans,
            "circular_flow": "Loans → Services → Revenue → Repayment → Grants"
        }
    
    def _log_event(self, event_type: str, data: Dict):
        """Log financing events."""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "system_id": self.system_id,
            "data": data
        }
        
        log_file = self.grants_log if "grant" in event_type else self.loans_log
        
        try:
            with log_file.open("a") as f:
                f.write(json.dumps(event) + "\n")
        except IOError:
            pass


def main():
    """Demo the grant-loan financing system."""
    print("=" * 80)
    print("GRANT-LOAN FINANCING SYSTEM")
    print("Circular Funding for Quantum Pipeline Access")
    print("=" * 80)
    
    system = GrantLoanSystem("@Evez666")
    
    # Agent applies for grant
    print("\n[Step 1] Agent applies for grant")
    grant_result = system.apply_for_grant(
        applicant="agent-evez666-001",
        amount=500.0,
        purpose="Initial quantum sensor access"
    )
    print(f"✓ Grant {grant_result['grant_id'][:16]}... approved: ${grant_result['amount']}")
    
    # Convert grant to larger loan
    print("\n[Step 2] Convert grant to loan (2x multiplier)")
    loan_result = system.convert_grant_to_loan(
        grant_id=grant_result['grant_id'],
        loan_amount_multiplier=2.0
    )
    print(f"✓ Loan {loan_result['loan_id'][:16]}... created: ${loan_result['amount']}")
    print(f"  Backed by grant: ${loan_result['grant_amount']}")
    
    # Use loan to purchase sensors
    print("\n[Step 3] Use loan to purchase quantum sensors")
    purchase_result = system.use_loan_for_purchase(
        loan_id=loan_result['loan_id'],
        purchase_amount=800.0,
        purchase_description="Quantum Navigation Bundle"
    )
    print(f"✓ Purchase authorized: ${purchase_result['amount']}")
    print(f"  Remaining loan balance: ${purchase_result['remaining']}")
    
    # Repay loan from service revenue
    print("\n[Step 4] Repay loan from quantum service revenue")
    repay_result = system.repay_loan(
        loan_id=loan_result['loan_id'],
        amount=1000.0,
        source="quantum_navigation_fees"
    )
    print(f"✓ Repayment: ${repay_result['amount']}")
    print(f"  Recycled to grants: ${repay_result['recycled_to_grants']}")
    print(f"  Loan fully repaid: {repay_result['fully_repaid']}")
    
    # Show system status
    print("\n[Step 5] System status after circular flow")
    status = system.get_financing_status()
    print(f"✓ Grant pool: ${status['grant_pool']:.2f}")
    print(f"✓ Active loans: {status['active_loans']}")
    print(f"✓ Repaid loans: {status['repaid_loans']}")
    print(f"✓ Flow: {status['circular_flow']}")
    
    print("\n" + "=" * 80)
    print("Circular financing operational. Grants loan the loans.")
    print("=" * 80)


if __name__ == "__main__":
    main()
