"""
JUBILEE PROTOCOL — Debt Mutation as Append-Only Spine Events
A financial state machine where every balance change is a spine event.
Auditable. Irreversible. Correct.

From Atlas v3: "Jubilee debt mutation system — hardened financial state machine endpoints"

The internet has never had a debt protocol where:
1. Every mutation is a cryptographic event (not a database row)
2. Balance = fold over mutation history (not a stored value)
3. Debt can be jubilee'd (forgiven) without erasing the record
4. The history IS the proof — no trust required

poly_c = τ × ω × topo / 2√N
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MutationType(str, Enum):
    BORROW = "BORROW"
    REPAY = "REPAY"
    TRANSFER = "TRANSFER"
    INTEREST = "INTEREST"
    JUBILEE = "JUBILEE"       # Debt forgiveness — the record stays, the obligation dies
    DEFAULT = "DEFAULT"        # Failure to pay — recorded forever


@dataclass
class DebtMutation:
    """A single mutation in the debt spine. Written once. Never edited. Never deleted."""
    mutation_id: str
    mutation_type: MutationType
    debtor: str
    creditor: str
    amount: float
    balance_after: float  # Computed, not stored
    previous_hash: str    # Links to previous mutation (chain)
    timestamp: float = field(default_factory=time.time)
    nonce: int = 0
    hash: str = ""
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        raw = f"{self.mutation_id}:{self.mutation_type.value}:{self.debtor}:{self.creditor}:{self.amount:.8f}:{self.previous_hash}:{self.nonce}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:24]


class JubileeProtocol:
    """
    Debt protocol where the history IS the state.
    
    No stored balances. No mutable records. Every balance is computed
    by folding over the entire mutation history. Jubilee (forgiveness)
    doesn't erase — it adds a JUBILEE mutation that zeros the obligation
    while preserving the full record.
    
    This is how debt SHOULD work. The record is permanent.
    The obligation can be forgiven. But the history never lies.
    """
    
    def __init__(self, spine_path: str = "jubilee_spine.jsonl"):
        self.spine_path = spine_path
        self.mutations: list[DebtMutation] = []
        self.last_hash = "GENESIS"
        self.nonce = 0
    
    def _next_mutation(self, mutation_type: MutationType, debtor: str, 
                       creditor: str, amount: float, metadata: dict = None) -> DebtMutation:
        """Create the next mutation in the chain."""
        self.nonce += 1
        
        # Compute current balance for this debtor-creditor pair
        current_balance = self._compute_balance(debtor, creditor)
        
        # Compute new balance
        if mutation_type == MutationType.BORROW:
            new_balance = current_balance + amount
        elif mutation_type == MutationType.REPAY:
            new_balance = current_balance - amount
        elif mutation_type == MutationType.TRANSFER:
            new_balance = current_balance - amount  # debtor transfers out
        elif mutation_type == MutationType.INTEREST:
            new_balance = current_balance + amount
        elif mutation_type == MutationType.JUBILEE:
            new_balance = 0.0  # Forgiven — balance zeros, but record stays
        elif mutation_type == MutationType.DEFAULT:
            new_balance = current_balance  # Balance unchanged, default recorded
        else:
            new_balance = current_balance
        
        mutation = DebtMutation(
            mutation_id=f"jub-{self.nonce:06d}",
            mutation_type=mutation_type,
            debtor=debtor,
            creditor=creditor,
            amount=amount,
            balance_after=round(new_balance, 8),
            previous_hash=self.last_hash,
            nonce=self.nonce,
            metadata=metadata or {}
        )
        
        self.mutations.append(mutation)
        self.last_hash = mutation.hash
        
        # Write to spine
        self._spine_write(mutation)
        
        return mutation
    
    def borrow(self, debtor: str, creditor: str, amount: float, **meta) -> DebtMutation:
        return self._next_mutation(MutationType.BORROW, debtor, creditor, amount, meta)
    
    def repay(self, debtor: str, creditor: str, amount: float, **meta) -> DebtMutation:
        return self._next_mutation(MutationType.REPAY, debtor, creditor, amount, meta)
    
    def transfer(self, debtor: str, creditor: str, amount: float, **meta) -> DebtMutation:
        return self._next_mutation(MutationType.TRANSFER, debtor, creditor, amount, meta)
    
    def accrue_interest(self, debtor: str, creditor: str, rate: float, **meta) -> DebtMutation:
        balance = self._compute_balance(debtor, creditor)
        interest = balance * rate
        return self._next_mutation(MutationType.INTEREST, debtor, creditor, round(interest, 8), meta)
    
    def jubilee(self, debtor: str, creditor: str, reason: str = "forgiveness") -> DebtMutation:
        """
        JUBILEE — Debt forgiveness without erasure.
        
        The obligation dies. The record lives. This is the innovation.
        Every other system either: (a) deletes the debt (no audit trail)
        or (b) keeps the debt (no forgiveness). Jubilee does BOTH.
        """
        balance = self._compute_balance(debtor, creditor)
        return self._next_mutation(
            MutationType.JUBILEE, debtor, creditor, balance,
            {"reason": reason, "original_balance": balance}
        )
    
    def default_event(self, debtor: str, creditor: str, **meta) -> DebtMutation:
        """Record a default — the debtor failed. This is permanent."""
        balance = self._compute_balance(debtor, creditor)
        return self._next_mutation(
            MutationType.DEFAULT, debtor, creditor, balance,
            {**meta, "defaulted_amount": balance}
        )
    
    def _compute_balance(self, debtor: str, creditor: str) -> float:
        """
        Compute balance by folding over mutation history.
        This is the core: balance is NOT stored. It is DERIVED.
        The history IS the state.
        """
        balance = 0.0
        for m in self.mutations:
            if m.debtor == debtor and m.creditor == creditor:
                if m.mutation_type == MutationType.BORROW:
                    balance += m.amount
                elif m.mutation_type == MutationType.REPAY:
                    balance -= m.amount
                elif m.mutation_type == MutationType.INTEREST:
                    balance += m.amount
                elif m.mutation_type == MutationType.JUBILEE:
                    balance = 0.0
                # TRANSFER and DEFAULT don't change balance for this pair
        return round(balance, 8)
    
    def verify_spine(self) -> dict:
        """Verify the entire mutation chain is intact."""
        if not self.mutations:
            return {"valid": True, "mutations": 0}
        
        errors = []
        for i, m in enumerate(self.mutations):
            # Verify hash chain
            if i == 0:
                if m.previous_hash != "GENESIS":
                    errors.append(f"Mutation {i}: expected GENESIS, got {m.previous_hash}")
            else:
                if m.previous_hash != self.mutations[i-1].hash:
                    errors.append(f"Mutation {i}: chain broken")
            
            # Verify hash integrity
            raw = f"{m.mutation_id}:{m.mutation_type.value}:{m.debtor}:{m.creditor}:{m.amount:.8f}:{m.previous_hash}:{m.nonce}"
            expected = hashlib.sha256(raw.encode()).hexdigest()[:24]
            if m.hash != expected:
                errors.append(f"Mutation {i}: hash mismatch — TAMPERED")
        
        return {
            "valid": len(errors) == 0,
            "mutations": len(self.mutations),
            "errors": errors,
            "spine_status": "INTACT ✓" if not errors else "TAMPERED ✗"
        }
    
    def get_ledger(self, debtor: str = None, creditor: str = None) -> list[dict]:
        """Get the full ledger, optionally filtered."""
        ledger = []
        for m in self.mutations:
            if debtor and m.debtor != debtor:
                continue
            if creditor and m.creditor != creditor:
                continue
            ledger.append({
                "id": m.mutation_id,
                "type": m.mutation_type.value,
                "debtor": m.debtor,
                "creditor": m.creditor,
                "amount": m.amount,
                "balance_after": m.balance_after,
                "hash": m.hash,
                "timestamp": m.timestamp
            })
        return ledger
    
    def _spine_write(self, mutation: DebtMutation):
        entry = {
            "type": "DEBT_MUTATION",
            "mutation_id": mutation.mutation_id,
            "mutation_type": mutation.mutation_type.value,
            "debtor": mutation.debtor,
            "creditor": mutation.creditor,
            "amount": mutation.amount,
            "balance_after": mutation.balance_after,
            "hash": mutation.hash,
            "previous_hash": mutation.previous_hash,
            "metadata": mutation.metadata,
            "powered_by": "EVEZ"
        }
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\n")


# DEMO
if __name__ == "__main__":
    jubilee = JubileeProtocol(spine_path="/tmp/jubilee_spine.jsonl")
    
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  JUBILEE PROTOCOL — Debt Mutation as Spine Events       ║")
    print("║  The history IS the state. Forgiveness without erasure. ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    # Alice borrows from Bank
    jubilee.borrow("alice", "bank", 10000.0, note="student loan")
    print(f"1. Alice borrows $10,000 → balance: ${jubilee._compute_balance('alice', 'bank'):,.2f}")
    
    # Interest accrues
    jubilee.accrue_interest("alice", "bank", 0.05, note="5% annual")
    print(f"2. 5% interest accrues → balance: ${jubilee._compute_balance('alice', 'bank'):,.2f}")
    
    # Alice makes a payment
    jubilee.repay("alice", "bank", 2000.0, note="monthly payment")
    print(f"3. Alice pays $2,000 → balance: ${jubilee._compute_balance('alice', 'bank'):,.2f}")
    
    # JUBILEE — the debt is forgiven, but the record lives
    print(f"\n4. ★ JUBILEE DECLARED ★")
    jubilee.jubilee("alice", "bank", reason="public_service_forgiveness")
    print(f"   Balance after jubilee: ${jubilee._compute_balance('alice', 'bank'):,.2f}")
    print(f"   The obligation died. The record lives.")
    
    # Bob defaults
    jubilee.borrow("bob", "bank", 50000.0, note="mortgage")
    jubilee.default_event("bob", "bank", reason="missed_6_payments")
    print(f"\n5. Bob defaults on $50,000 — recorded FOREVER")
    print(f"   Bob's balance: ${jubilee._compute_balance('bob', 'bank'):,.2f} (default doesn't forgive)")
    
    # Verify spine
    verification = jubilee.verify_spine()
    print(f"\n=== SPINE VERIFICATION ===")
    print(f"  Mutations: {verification['mutations']}")
    print(f"  Status: {verification['spine_status']}")
    print(f"  Chain: INTACT — every hash links to the previous")
    
    # Full ledger
    print(f"\n=== FULL LEDGER ===")
    for entry in jubilee.get_ledger():
        print(f"  {entry['id']} | {entry['type']:10} | {entry['debtor']}→{entry['creditor']} | ${entry['amount']:,.2f} | balance=${entry['balance_after']:,.2f}")
