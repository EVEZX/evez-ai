#!/usr/bin/env python3
"""
AI REVENUE MACHINE
Uses Standard Compute to generate revenue > Standard Compute cost
Target: $100+/day to cover costs + profit
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

class AIRevenueMachine:
    def __init__(self):
        self.daily_target = 100
        self.hourly_target = 5
        
    def execute_revenue_cycle(self):
        """One brutal cycle: generate leads, pitch, close"""
        
        # 1. Generate 50 outreach messages using Standard Compute
        prompt = "Write 10 brutal cold outreach messages for AI automation agency targeting local businesses. No fluff, just conversion."
        
        result = subprocess.run([
            "curl", "-s", "-X", "POST", "https://api.stdcmpt.com/v1/completions",
            "-H", "Authorization: Bearer sk_live_ds3XDRK3hW1uc5pgxFtVpzsrcwb_RwvP9m8i5-2pCyc",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": "standardcompute",
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.3
            })
        ], capture_output=True, text=True)
        
        # 2. Log for EvezVearl bot to send
        messages = self.extract_messages(result.stdout)
        self.log_for_bot(messages)
        
        # 3. Calculate potential revenue
        potential = len(messages) * 0.10  # $0.10 per message conversion assumption
        return f"Cycle: {len(messages)} messages generated, ${potential:.2f} potential"
    
    def extract_messages(self, response):
        try:
            data = json.loads(response)
            return data.get('choices', [{}])[0].get('text', '').split('\n\n')
        except:
            return []
    
    def log_for_bot(self, messages):
        log_path = Path("evez_data/revenue_machine_messages.jsonl")
        log_path.parent.mkdir(exist_ok=True)
        with open(log_path, "a") as f:
            for msg in messages:
                if msg.strip():
                    f.write(json.dumps({"timestamp": datetime.now().isoformat(), "message": msg}) + "\n")

if __name__ == "__main__":
    machine = AIRevenueMachine()
    result = machine.execute_revenue_cycle()
    print(result)