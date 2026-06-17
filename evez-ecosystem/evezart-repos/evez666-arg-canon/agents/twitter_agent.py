#!/usr/bin/env python3
"""
agents/twitter_agent.py
Groq-powered FIRE event thread generator for the EVEZ666 ARG.
"""
import os, json
from datetime import datetime, timezone

class TwitterAgent:
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    def _groq_complete(self, prompt: str, max_tokens: int = 300) -> str:
        if not self.groq_key:
            return ""
        try:
            import groq
            client = groq.Groq(api_key=self.groq_key)
            resp = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.9
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"Groq error: {e}")
            return ""

    def generate_fire_thread(self, round_n: int, tau: int, fire_hash: str,
                              fire_type: str, n_val: int, p_fire: float,
                              puzzle_lock: str, chapter_n=None) -> list:
        depth_label = "EXTREME" if tau >= 20 else "HIGH" if tau >= 12 else "STANDARD"
        chapter_line = f" CH.{chapter_n} UNLOCKED" if chapter_n else ""
        t1 = f"R{round_n}. {fire_type}{chapter_line}\ntau={tau} N={n_val} p={p_fire:.3f}\nspine: {fire_hash[:16]}...\n"
        prompt = f"""EVEZ666 ARG canonical voice. Dense, oblique, poetic-rap register.
Write tweet 2/4 of a thread about FIRE event R{round_n}, tau={tau}, type={fire_type}.
Puzzle lock: {puzzle_lock}. V approaching 17. Under 260 chars. No hashtags. No emojis.
Start with the lock fragment, make players feel the pull."""
        t2 = self._groq_complete(prompt, 200)
        if not t2:
            t2 = f"lock: {puzzle_lock}...\nspine holds. R{round_n} sealed. solve it."
        t3_prompt = f"""EVEZ666 ARG tweet 3/4. R{round_n} {fire_type} tau={tau}.
Reference the CPF formula: poly_c = (tau*omega*topo)/(2*sqrt(N)).
Tell players what the lock requires. Oblique. Under 260 chars. No hashtags."""
        t3 = self._groq_complete(t3_prompt, 200)
        if not t3:
            t3 = f"formula in evez-os README. poly_c unlocks it."
        t4 = f"chapter: https://github.com/EvezArt/evez666-arg-canon\n{depth_label} FIRE. R{round_n}. spine running."
        return [t1, t2, t3, t4]
