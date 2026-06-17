#!/usr/bin/env python3
import hashlib, json

class PuzzleEngine:
    @staticmethod
    def generate(fire_hash: str, tau: int, round_n: int, difficulty_tier: str) -> dict:
        N = round_n + 80
        lock_hex = hashlib.sha256(f"{fire_hash}:{round_n}:EVEZ_PUZZLE".encode()).hexdigest()
        hints = {
            "STANDARD": ["τ is the number of divisors", "N = round + 80", "formula in evez-os README"],
            "SIGNIFICANT": ["τ is explicit divisor enumeration", "ω = distinct prime factors only", "poly_c = (τ×ω×topo)/(2×√N)"],
            "EXTREME": ["formula is in the spine", "V is aggregate voltage", "topo: {1:1.15, 2:1.30, 3:1.45}"]
        }
        return {
            "round": round_n, "tau": tau, "difficulty_tier": difficulty_tier,
            "lock_hex": lock_hex, "lock_preview": lock_hex[:32] + "...",
            "hints": hints.get(difficulty_tier, hints["STANDARD"]),
            "reward_gumroad_slug": {"STANDARD": "standard_lore_pack", "SIGNIFICANT": "significant_lore_pack", "EXTREME": "extreme_lore_pack_chapter_unlock"}.get(difficulty_tier, "standard_lore_pack"),
            "solution_format": f"SHA256('{tau}:{{N}}:{{omega}}:{fire_hash[:8]}')",
            "verification_endpoint": f"https://evez666-arg.vercel.app/api/verify/{lock_hex[:16]}"
        }
    @staticmethod
    def verify(lock_hex: str, submitted: str, fire_hash: str, tau: int, round_n: int) -> bool:
        N = round_n + 80
        for omega in range(1, 6):
            if hashlib.sha256(f"{tau}:{N}:{omega}:{fire_hash[:8]}".encode()).hexdigest() == submitted:
                return True
        return False
