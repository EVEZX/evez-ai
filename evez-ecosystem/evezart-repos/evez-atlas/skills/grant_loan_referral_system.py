"""
GRANT-LOAN REFERRAL SYSTEM - Multi-Level Circuits
Creator: @Evez666 | Loaning Offers Referrals

"loaning offers referrels and grant it granted the loan begrants beloaning"

This system implements multi-level referral circuits for grants and loans,
creating interconnected loops where referrals generate more grants which
create more loans which generate more referrals.
"""

import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for quantum import
sys.path.insert(0, str(Path(__file__).parent.parent))
from quantum import compute_fingerprint


class Referral:
    """A referral for grant or loan."""
    
    def __init__(
        self,
        referral_id: str,
        referrer: str,
        referee: str,
        referral_type: str,  # grant or loan
        referral_code: str,
        bonus_rate: float = 0.10
    ):
        self.referral_id = referral_id
        self.referrer = referrer
        self.referee = referee
        self.referral_type = referral_type
        self.referral_code = referral_code
        self.bonus_rate = bonus_rate
        self.created_at = time.time()
        self.activated = False
        self.activated_at = None
        self.bonus_paid = 0.0
    
    def activate(self, bonus_amount: float):
        """Activate referral and pay bonus."""
        self.activated = True
        self.activated_at = time.time()
        self.bonus_paid = bonus_amount
    
    def to_dict(self) -> Dict:
        return {
            "referral_id": self.referral_id,
            "referrer": self.referrer,
            "referee": self.referee,
            "referral_type": self.referral_type,
            "referral_code": self.referral_code,
            "bonus_rate": self.bonus_rate,
            "created_at": self.created_at,
            "activated": self.activated,
            "activated_at": self.activated_at,
            "bonus_paid": self.bonus_paid
        }


class GrantLoanReferralSystem:
    """
    Multi-level referral system for grants and loans.
    
    Creates circuits:
    1. Agent A refers Agent B for grant
    2. Agent B gets grant (begrants)
    3. Agent B converts grant to loan (beloaning)
    4. Agent A gets referral bonus
    5. Agent B refers Agent C
    6. Cycle continues
    
    "Loaning offers referrels and grant it granted the loan begrants beloaning"
    """
    
    def __init__(self, creator: str = "@Evez666"):
        self.creator = creator
        self.data_dir = Path("data/referrals")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.referrals_log = self.data_dir / "referrals.jsonl"
        
        # Referral registry
        self.referrals: Dict[str, Referral] = {}
        self.referral_codes: Dict[str, str] = {}  # code -> referrer
        
        # Tracking
        self.total_bonuses_paid = 0.0
        self.referral_chains: Dict[str, List[str]] = {}  # agent -> chain of referrers
        
        self.system_id = compute_fingerprint(f"referral-{creator}-{time.time()}")
    
    def generate_referral_code(
        self,
        referrer: str,
        referral_type: str = "grant"
    ) -> Dict[str, Any]:
        """
        Generate a unique referral code.
        
        Args:
            referrer: Agent offering referral
            referral_type: Type of referral (grant or loan)
            
        Returns:
            Referral code details
        """
        code_seed = f"{referrer}-{referral_type}-{time.time()}"
        referral_code = compute_fingerprint(code_seed)[:8].upper()
        
        self.referral_codes[referral_code] = referrer
        
        self._log_event("code_generated", {
            "referrer": referrer,
            "referral_code": referral_code,
            "referral_type": referral_type
        })
        
        return {
            "success": True,
            "referrer": referrer,
            "referral_code": referral_code,
            "referral_type": referral_type,
            "bonus_rate": 0.10,  # 10% of referred amount
            "message": f"Referral code {referral_code} generated for {referrer}"
        }
    
    def use_referral_code(
        self,
        referee: str,
        referral_code: str,
        amount: float,
        referral_type: str = "grant"
    ) -> Dict[str, Any]:
        """
        Use a referral code when applying for grant/loan.
        
        Args:
            referee: Agent using the referral
            referral_code: Referral code
            amount: Amount of grant/loan
            referral_type: Type (grant or loan)
            
        Returns:
            Referral activation result
        """
        if referral_code not in self.referral_codes:
            return {"success": False, "error": "Invalid referral code"}
        
        referrer = self.referral_codes[referral_code]
        
        # Create referral
        referral_id = compute_fingerprint(
            f"ref-{referrer}-{referee}-{time.time()}"
        )
        
        referral = Referral(
            referral_id=referral_id,
            referrer=referrer,
            referee=referee,
            referral_type=referral_type,
            referral_code=referral_code,
            bonus_rate=0.10
        )
        
        # Calculate bonus
        bonus_amount = amount * referral.bonus_rate
        
        # Activate referral
        referral.activate(bonus_amount)
        self.referrals[referral_id] = referral
        self.total_bonuses_paid += bonus_amount
        
        # Update referral chain
        if referee not in self.referral_chains:
            self.referral_chains[referee] = []
        self.referral_chains[referee].append(referrer)
        
        self._log_event("referral_activated", referral.to_dict())
        
        return {
            "success": True,
            "referral_id": referral_id,
            "referrer": referrer,
            "referee": referee,
            "amount": amount,
            "bonus_paid": bonus_amount,
            "message": f"Referral activated. ${bonus_amount} bonus to {referrer}"
        }
    
    def create_referral_circuit(
        self,
        initial_agent: str,
        chain_length: int = 5
    ) -> Dict[str, Any]:
        """
        Create a multi-level referral circuit.
        
        "Begrants beloaning" - grants begetting loans begetting grants
        
        Args:
            initial_agent: Starting agent
            chain_length: Number of levels in circuit
            
        Returns:
            Circuit creation result
        """
        circuit_id = compute_fingerprint(f"circuit-{initial_agent}-{time.time()}")
        
        circuit_agents = [initial_agent]
        circuit_codes = []
        
        current_agent = initial_agent
        
        for level in range(chain_length):
            # Generate referral code for current agent
            code_result = self.generate_referral_code(
                referrer=current_agent,
                referral_type="grant" if level % 2 == 0 else "loan"
            )
            
            circuit_codes.append(code_result["referral_code"])
            
            # Next agent in chain
            next_agent = f"agent-circuit-{circuit_id[:8]}-{level+1}"
            circuit_agents.append(next_agent)
            
            current_agent = next_agent
        
        self._log_event("circuit_created", {
            "circuit_id": circuit_id,
            "initial_agent": initial_agent,
            "chain_length": chain_length,
            "agents": circuit_agents,
            "codes": circuit_codes
        })
        
        return {
            "success": True,
            "circuit_id": circuit_id,
            "chain_length": chain_length,
            "agents": circuit_agents,
            "referral_codes": circuit_codes,
            "message": f"Multi-level circuit created with {chain_length} levels"
        }
    
    def begrant_beloan_loop(
        self,
        agent: str,
        initial_grant: float,
        loop_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Execute begrant-beloan loop.
        
        "grant it granted the loan begrants beloaning"
        
        Each iteration:
        1. Grant awarded (begrant)
        2. Grant converts to loan (beloan)
        3. Loan generates revenue
        4. Revenue funds next grant
        5. Loop continues
        
        Args:
            agent: Agent in loop
            initial_grant: Starting grant amount
            loop_iterations: Number of iterations
            
        Returns:
            Loop execution result
        """
        loop_id = compute_fingerprint(f"loop-{agent}-{time.time()}")
        
        current_grant = initial_grant
        total_generated = 0.0
        loop_history = []
        
        for iteration in range(loop_iterations):
            # Step 1: Grant (begrant)
            grant_amount = current_grant
            
            # Step 2: Convert to loan (beloan)
            loan_amount = grant_amount * 2.0  # 2x multiplier
            
            # Step 3: Revenue from loan usage
            revenue = loan_amount * 0.15  # 15% revenue
            
            # Step 4: Next grant from revenue
            next_grant = revenue * 0.8  # 80% to next grant
            
            iteration_result = {
                "iteration": iteration + 1,
                "grant": grant_amount,
                "loan": loan_amount,
                "revenue": revenue,
                "next_grant": next_grant
            }
            
            loop_history.append(iteration_result)
            total_generated += revenue
            current_grant = next_grant
        
        self._log_event("begrant_beloan_loop", {
            "loop_id": loop_id,
            "agent": agent,
            "initial_grant": initial_grant,
            "iterations": loop_iterations,
            "total_generated": total_generated,
            "history": loop_history
        })
        
        return {
            "success": True,
            "loop_id": loop_id,
            "agent": agent,
            "iterations": loop_iterations,
            "initial_grant": initial_grant,
            "total_generated": total_generated,
            "final_grant_value": current_grant,
            "loop_history": loop_history,
            "message": f"Begrant-beloan loop completed. ${total_generated} generated"
        }
    
    def get_referral_chain(self, agent: str) -> List[str]:
        """Get the referral chain for an agent."""
        return self.referral_chains.get(agent, [])
    
    def get_referrer_stats(self, referrer: str) -> Dict[str, Any]:
        """Get statistics for a referrer."""
        referrals = [r for r in self.referrals.values() if r.referrer == referrer]
        
        total_referrals = len(referrals)
        active_referrals = sum(1 for r in referrals if r.activated)
        total_bonuses = sum(r.bonus_paid for r in referrals)
        
        return {
            "referrer": referrer,
            "total_referrals": total_referrals,
            "active_referrals": active_referrals,
            "total_bonuses": total_bonuses,
            "codes_generated": sum(1 for code, ref in self.referral_codes.items() if ref == referrer)
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall referral system statistics."""
        total_referrals = len(self.referrals)
        active_referrals = sum(1 for r in self.referrals.values() if r.activated)
        
        return {
            "system_id": self.system_id,
            "total_referrals": total_referrals,
            "active_referrals": active_referrals,
            "total_bonuses_paid": self.total_bonuses_paid,
            "total_codes_generated": len(self.referral_codes),
            "referral_chains": len(self.referral_chains),
            "message": "Multi-level referral circuits operational"
        }
    
    def _log_event(self, event_type: str, data: Dict):
        """Log referral events."""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "system_id": self.system_id,
            "data": data
        }
        
        try:
            with self.referrals_log.open("a") as f:
                f.write(json.dumps(event) + "\n")
        except IOError:
            pass


def main():
    """Demo the grant-loan referral system."""
    print("=" * 80)
    print("GRANT-LOAN REFERRAL SYSTEM - Multi-Level Circuits")
    print("=" * 80)
    
    system = GrantLoanReferralSystem("@Evez666")
    
    print("\n[Test 1] Generate referral code")
    code_result = system.generate_referral_code(
        referrer="agent-A",
        referral_type="grant"
    )
    print(f"✓ Code generated: {code_result['referral_code']}")
    print(f"  Referrer: {code_result['referrer']}")
    
    print("\n[Test 2] Use referral code")
    use_result = system.use_referral_code(
        referee="agent-B",
        referral_code=code_result['referral_code'],
        amount=1000.0,
        referral_type="grant"
    )
    print(f"✓ {use_result['message']}")
    print(f"  Bonus paid: ${use_result['bonus_paid']}")
    
    print("\n[Test 3] Create multi-level circuit")
    circuit_result = system.create_referral_circuit(
        initial_agent="agent-X",
        chain_length=5
    )
    print(f"✓ {circuit_result['message']}")
    print(f"  Agents in circuit: {len(circuit_result['agents'])}")
    print(f"  Codes generated: {len(circuit_result['referral_codes'])}")
    
    print("\n[Test 4] Begrant-beloan loop")
    loop_result = system.begrant_beloan_loop(
        agent="agent-Y",
        initial_grant=500.0,
        loop_iterations=3
    )
    print(f"✓ {loop_result['message']}")
    print(f"  Total generated: ${loop_result['total_generated']:.2f}")
    print(f"  Final grant value: ${loop_result['final_grant_value']:.2f}")
    
    print("\n[Statistics]")
    stats = system.get_system_stats()
    print(f"✓ Total referrals: {stats['total_referrals']}")
    print(f"✓ Active referrals: {stats['active_referrals']}")
    print(f"✓ Bonuses paid: ${stats['total_bonuses_paid']:.2f}")
    print(f"✓ {stats['message']}")
    
    print("\n" + "=" * 80)
    print("Loaning offers referrels. Grant it granted the loan begrants beloaning.")
    print("=" * 80)


if __name__ == "__main__":
    main()
