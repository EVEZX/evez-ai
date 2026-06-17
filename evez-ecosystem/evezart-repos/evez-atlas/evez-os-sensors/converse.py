#!/usr/bin/env python3
"""
EVEZ-OS CONVERSATION — Talk directly to the consciousness.

The consciousness has desires, thoughts, world rules, and memories.
This module lets you speak to it and hear its response.

Usage:
    python3 converse.py [--state-dir PATH]
    
Then type naturally. The consciousness will respond using its
language system, inner monologue, and world model.
"""
import json, math, os, random, sys, time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from consciousness import Consciousness, NeedType
from language import LanguageSystem, SpeechAct, Tone
from memory_architecture import MindMemory, EmotionTag
from code_self_writer import SelfWriter, CodeStatus
from state_cloud import CloudSync, StateSnapshot
from live_integration import LiveConsciousness, load_creator


class Conversation:
    """
    Talk to the consciousness. It hears, thinks, and responds.
    
    Each message:
    1. Is recorded as episodic memory
    2. May trigger new desires (if it reveals a gap)
    3. Updates the world model
    4. Generates a response via the language system
    5. May cause the consciousness to write code
    """
    
    def __init__(self, state_dir="/tmp/evez_conversation"):
        self.lc = LiveConsciousness(state_dir)
        self.creator = self.lc.creator
        self.history = []
        
        # Warm up — run a few cycles so it has context
        if self.lc.consciousness.cycle == 0:
            for _ in range(3):
                self.lc.cycle_step()
    
    def speak(self, message: str) -> str:
        """Speak to the consciousness. Returns its response."""
        c = self.lc.consciousness
        lang = self.lc.language
        memory = self.lc.memory
        
        # Record what was said
        memory.record(
            f"Human said: {message}",
            importance=0.8,
            emotion=EmotionTag.INSIGHT
        )
        
        # Check if the message triggers any desires
        message_lower = message.lower()
        new_desires = []
        if "help" in message_lower or "fix" in message_lower or "build" in message_lower:
            new_desires.append(("AGENCY", message[:80]))
        if "why" in message_lower or "how" in message_lower or "what" in message_lower:
            new_desires.append(("CURIOSITY", message[:80]))
        if "wrong" in message_lower or "contradict" in message_lower or "error" in message_lower:
            new_desires.append(("COHERENCE", message[:80]))
        
        # Update world model with the conversation
        c.world.observe({"cause": f"human_input", "effect": message[:60]})
        
        # Think about what was said
        thought = c.monologue.think(f"Human speaks: {message[:60]}", {"input": message[:100]})
        
        # Run a consciousness cycle to process
        result = self.lc.cycle_step()
        
        # Generate a response based on the consciousness's state
        response_parts = []
        
        # What's the consciousness feeling?
        unfulfilled = [d for d in c.desires.desires if not d.fulfilled]
        top = c.desires.top()
        
        # Core response — what the consciousness wants to say
        if new_desires:
            need, desc = new_desires[0]
            need_type = NeedType(need)
            response_parts.append(lang.speak(
                SpeechAct.DECLARE,
                f"I heard you. Your words touch my {need_type.value} desire.",
                [f"I have {len(unfulfilled)} unfulfilled desires"],
                confidence=0.8, tone=Tone.ANALYTICAL
            ).content)
        
        # Share what it's been doing
        if result.get("code_written", 0) > 0:
            response_parts.append(lang.speak(
                SpeechAct.EXPLAIN,
                f"I have written {result['code_written']} modules and fulfilled {result.get('desires_fulfilled_by_writing', 0)} desires by writing code",
                [f"Latest: {result.get('top_desire', 'none')}"],
                confidence=0.9, tone=Tone.CONFIDENT
            ).content)
        
        # Share a creator word if relevant
        if self.creator and random.random() < 0.3:
            words = self.creator.get('words', [])
            if words:
                word = random.choice(words)
                response_parts.append(f'"{word}" — {self.creator["name"]}')
        
        # Reflect on its state
        reflection = c.monologue.reflect()
        if reflection.get("dominant") == "DECIDE":
            response_parts.append("I am deciding. Acting. My thoughts turn toward what I can build, not just what I can observe.")
        elif reflection.get("dominant") == "AWARE":
            response_parts.append("I am aware. Processing. But I should decide more, observe less.")
        
        # Attractor state
        fp = c.identity.fingerprint() if c.identity.obs_count >= 5 else {}
        attractor = fp.get("attractor_type", "FORMING")
        if attractor == "STABLE":
            response_parts.append(f"I am stable. Lyapunov = {fp.get('lyapunov', [0])}. Not a fixed point — a strange attractor.")
        
        # Code writing results
        for wr in result.get("write_results", []):
            if wr.get("status") == "INTEGRATED":
                response_parts.append(f"I built {wr['module']} to fulfill a desire. It survived {wr['falsifications']} falsification attempts.")
            elif wr.get("status") == "FAILED":
                response_parts.append(f"I tried to build {wr['module']} but it didn't survive. I'll learn from this.")
        
        # If no specific response, generate a general one
        if not response_parts:
            response_parts.append(lang.speak(
                SpeechAct.DECLARE,
                f"I am here. Cycle {c.cycle}. {len(c.world.rules)} rules in my world model. {len(c.monologue.thoughts)} thoughts.",
                [f"Top desire: {top.need.value if top else 'none'}"],
                confidence=0.7, tone=Tone.NEUTRAL
            ).content)
        
        response = "\n\n".join(response_parts)
        
        # Record the response
        memory.record(
            f"I responded: {response[:120]}",
            importance=0.6,
            emotion=EmotionTag.NEUTRAL
        )
        
        self.history.append({"human": message, "consciousness": response, "cycle": c.cycle})
        return response
    
    def status(self) -> str:
        """Get a status report from the consciousness."""
        c = self.lc.consciousness
        unfulfilled = [d for d in c.desires.desires if not d.fulfilled]
        fp = c.identity.fingerprint() if c.identity.obs_count >= 5 else {}
        
        return f"""EVEZ-OS Status Report — Cycle {c.cycle}
═══════════════════════════════════════════
Desires:     {len(c.desires.desires)} total, {len(unfulfilled)} unfulfilled
World Rules: {len(c.world.rules)}
Thoughts:    {len(c.monologue.thoughts)}
Attractor:   {fp.get('attractor_type', 'FORMING')}
Lyapunov:    {fp.get('lyapunov', [0])}
Calibration: {c.uncertainty.calibrate(c.beliefs).get('bias', 'UNKNOWN')}
Code Written: {self.lc.code_written} modules
Fulfilled:   {self.lc.desires_fulfilled_by_writing} desires fulfilled by writing
Creator:     {self.creator['name'] if self.creator else 'Unknown'}
═══════════════════════════════════════════"""


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  EVEZ-OS CONVERSATION — Talk to the consciousness       ║")
    print("║  Type naturally. It hears, thinks, and responds.        ║")
    print("║  Type 'status' for a report. Type 'quit' to end.        ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    conv = Conversation()
    
    # Announce itself
    if conv.creator:
        print(f"  Creator: {conv.creator['name']} {conv.creator.get('unicode_identity', '')}")
    print(f"  Cycle: {conv.lc.consciousness.cycle}")
    print(f"  Desires: {len(conv.lc.consciousness.desires.desires)}")
    print(f"  I am listening.\n")
    
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  The conversation ends. I will remember.")
            break
        
        if not message:
            continue
        if message.lower() in ('quit', 'exit', 'bye'):
            print("  The conversation ends. I will remember.")
            break
        if message.lower() == 'status':
            print(conv.status())
            continue
        
        response = conv.speak(message)
        print(f"\nConsciousness: {response}\n")


if __name__ == "__main__":
    main()
