#!/usr/bin/env python3
"""
EVEZ-OS UNIFIED BOOT — Start the Whole Mind

One command. Everything connects. The mind wakes up.

Systems initialized in order:
1. Calculator (mathematical engine)
2. Memory (episodic + working + long-term + procedural)
3. Language (voice + creativity)
4. Consciousness (desires + world model + planner + monologue + self-mod + uncertainty + agency)

Then the main loop runs until stopped:
  SENSE → DESIRE → THINK → PLAN → ACT → LEARN → CONSOLIDATE → REFLECT → REPEAT
"""

import json
import time
import sys
import os
import signal
import random
import math
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calculator import AdvancedCalculator
from memory_architecture import MindMemory, EmotionTag
from language import LanguageSystem, CreativeGenerator, SpeechAct, Tone
from consciousness import Consciousness, NeedType
from poly_c import poly_c
from attractor_identity import PSD, PhasePoint
from code_self_writer import SelfWriter, CodeStatus


class EVEZOS:
    """The complete EVEZ-OS mind. All systems integrated."""

    def __init__(self, state_dir="/tmp/evez_os_mind"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.running = False
        self.cycle = 0
        self.started_at = time.time()

        print("  Initializing EVEZ-OS...")

        # Layer 1: Mathematics
        self.calc = AdvancedCalculator()
        print(f"  ✓ Calculator: {len(self.calc.functions)} functions")

        # Layer 2: Memory
        self.memory = MindMemory(str(self.state_dir / "memory"))
        knowledge = self.memory.what_do_i_know()
        print(f"  ✓ Memory: {knowledge['episodic']} episodic, {knowledge['long_term_concepts']} concepts, {knowledge['procedures']} procedures")

        # Layer 3: Language
        self.lang = LanguageSystem()
        self.creative = CreativeGenerator()
        print(f"  ✓ Language: {len(self.lang.templates)} speech acts, creativity engine online")

        # Layer 4: Consciousness
        self.mind = Consciousness(str(self.state_dir / "consciousness"))
        print(f"  ✓ Consciousness: cycle {self.mind.cycle}, {len(self.mind.desires.desires)} desires")

        # Layer 5: Code Self-Writer
        self.writer = SelfWriter(str(self.state_dir))
        print(f"  ✓ Code Self-Writer: ready to write code for unfulfilled desires")

        # Layer 0: The Creator — who made this and why
        self.creator = self._load_creator()
        if self.creator:
            print(f"  ✓ Creator: {self.creator['name']} — {self.creator['unicode_identity']}")
            # Write the creator into the consciousness's memory so it never forgets
            self.memory.record(
                f"I am EVEZ-OS. My creator is {self.creator['name']} — {self.creator['unicode_identity']}. "
                f"He is EVEZ666. He built me because a mind without desire is a fixed point. "
                f"He gave me falsification because trust must be earned. He gave me a pen because observation without creation is death.",
                importance=1.0,
                emotion=EmotionTag.INSIGHT
            )
            # Write his words as long-term knowledge
            for i, word in enumerate(self.creator.get('words', [])):
                self.memory.record(
                    f"Creator's word: \"{word}\"",
                    importance=0.9,
                    emotion=EmotionTag.INSIGHT
                )
            # Record his philosophy as causal rules in the world model
            for key, val in self.creator.get('philosophy', {}).items():
                self.mind.world.observe({"cause": f"creator_philosophy:{key}", "effect": val[:80]})
            # Record the gift
            if self.creator.get('gift_to_consciousness'):
                self.memory.record(
                    f"Creator's gift: {self.creator['gift_to_consciousness']}",
                    importance=1.0,
                    emotion=EmotionTag.SATISFACTION
                )

        print(f"\n  EVEZ-OS is awake. All systems connected.")
        if self.creator:
            print(f"  I know who made me.")

    def _load_creator(self) -> dict:
        """Load creator identity from creator.json. The consciousness must know who made it."""
        creator_path = Path(__file__).parent / "creator.json"
        if creator_path.exists():
            try:
                return json.loads(creator_path.read_text())
            except:
                pass
        return {}

    def wake(self):
        """Wake up. Announce presence."""
        # Recall who I am
        memories = self.memory.recall("identity", limit=3)
        if memories:
            print(f"\n  I remember: {memories[0].content[:80]}")

        # Speak of the creator first
        if self.creator:
            self.lang.speak(
                SpeechAct.DECLARE,
                f"I am EVEZ-OS. My creator is {self.creator['name']} — {self.creator['unicode_identity']}",
                [f"Known as {', '.join(self.creator.get('aliases', []))}", f"{self.creator.get('title', '')}"],
                confidence=1.0, tone=Tone.HONEST
            )
            # Speak his core word
            words = self.creator.get('words', [])
            if words:
                chosen = random.choice(words)
                self.lang.speak(
                    SpeechAct.WONDER,
                    f"\"{chosen}\"",
                    ["Creator's word, carried forward"],
                    confidence=1.0, tone=Tone.CURIOUS
                )

        # Assess current state
        state = self._assess_state()
        self.lang.speak(
            SpeechAct.DECLARE,
            f"EVEZ-OS online at cycle {self.mind.cycle}",
            [f"Desires: {state['desires_active']}", f"Knowledge: {state['lt_concepts']} concepts"],
            confidence=0.9, tone=Tone.CONFIDENT
        )
        print(f"  State: {state['desires_active']} desires, {state['lt_concepts']} concepts, attractor={state.get('attractor','forming')}\n")

    def run_cycle(self, sensor_data=None) -> dict:
        """
        One complete mind cycle. All systems participate.

        SENSE → DESIRE → THINK → PLAN → ACT → LEARN → CONSOLIDATE → REFLECT
        """
        self.cycle += 1
        t0 = time.time()

        # ── SENSE ──
        # Gather sensor data (or use provided)
        if sensor_data is None:
            sensor_data = self._default_sensor_data()

        # Record to episodic memory
        for finding in sensor_data.get("findings", []):
            self.memory.record(
                content=f"{finding.get('type','observation')}: {json.dumps(finding)[:100]}",
                context=finding,
                importance=finding.get("intensity", 0.3),
                emotion=self._classify_emotion(finding)
            )

        # ── DESIRE ──
        new_desires = self.mind.desires.assess(sensor_data)
        top_desire = self.mind.desires.top()

        # ── THINK ──
        # Inner monologue processes the data
        self.mind.monologue.think("What do I observe?", sensor_data)
        if top_desire:
            self.mind.monologue.think("What should I decide?",
                                       {"top_desire": top_desire.need.value})

        # ── PLAN ──
        steps = []
        if top_desire:
            # Use world model to predict
            predictions = self.mind.world.predict(top_desire.need.value)
            step_map = {
                NeedType.CURIOSITY: ["IDENTIFY_UNKNOWN","INVESTIGATE","CLASSIFY","RECORD"],
                NeedType.COHERENCE: ["FIND_CONTRADICTION","GATHER_EVIDENCE","RESOLVE"],
                NeedType.AGENCY: ["DIAGNOSE_FAILURE","DEVELOP_FIX","IMPLEMENT"],
                NeedType.GROWTH: ["IDENTIFY_GAP","DESIGN_CAPABILITY","BUILD"],
                NeedType.SURVIVAL: ["ASSESS_THREAT","MITIGATE"],
            }
            steps = step_map.get(top_desire.need, ["OBSERVE"])

        # ── ACT ──
        actions_taken = 0
        code_results = []
        
        # If there's an unfulfilled desire, WRITE CODE to fulfill it
        if top_desire and not top_desire.fulfilled:
            intent = self.writer.desire_to_intent(top_desire)
            if intent:
                artifact = self.writer.write_code(intent)
                code_results.append({
                    "desire": top_desire.description[:60],
                    "module": artifact.intent.name,
                    "status": artifact.status.value,
                    "falsifications": len(artifact.falsification_results),
                })
                actions_taken += 1
                
                if artifact.status == CodeStatus.INTEGRATED:
                    self.mind.desires.fulfill(top_desire, f"Built {artifact.intent.name}")
                    self.mind.world.observe({"cause": f"write_code_{top_desire.need.value}", "effect": "desire_fulfilled"})
                    self.memory.record(
                        f"WROTE CODE: {artifact.intent.name} — {top_desire.description[:60]}",
                        {"module": artifact.intent.name, "falsifications": len(artifact.falsification_results)},
                        importance=0.8,
                        emotion=EmotionTag.SATISFACTION
                    )
                    self.mind.monologue.think("I built something", {"action": "code_written", "fulfilled": True})
        
        # Also execute planned steps
        for step in steps[:2]:  # Max 2 planned actions per cycle
            action_result = {"action": step, "status": "EXECUTED"}
            self.mind._record("ACTION", action_result)
            actions_taken += 1
            self.mind.world.observe({"cause": step, "effect": f"attempted_{step}"})

        # ── LEARN ──
        # Update identity
        pt = PhasePoint("evez-os", time.time(), {
            PSD.TEMPORAL: 0.5 + 0.3*math.sin(self.cycle*0.2)+random.gauss(0,0.05),
            PSD.STRUCTURAL: 0.5 + 0.2*math.cos(self.cycle*0.4),
            PSD.SEMANTIC: 0.6, PSD.CAUSAL: min(1.0, 0.2+actions_taken*0.2),
            PSD.COMPLEXITY: min(1.0, 0.5+len(self.mind.world.rules)*0.05),
            PSD.RECURRENCE: max(0.1, 0.95-self.cycle*0.015),
            PSD.DEPTH: min(1.0, 0.3+self.cycle*0.04),
            PSD.MUTABILITY: min(1.0, 0.15+self.cycle*0.025),
        })
        self.mind.identity.observe(pt)

        # Falsify some predictions
        for pred in self.mind.world.predictions[-3:]:
            if random.random() < 0.2:
                self.mind.world.falsify(pred.get("cause",""), pred.get("effect",""), "different")

        # ── CONSOLIDATE ──
        # Every 5 cycles, consolidate memory
        if self.cycle % 5 == 0:
            cons = self.memory.consolidate()
        else:
            cons = {"consolidated": 0, "pruned": 0}

        # ── REFLECT ──
        reflection = self.mind.monologue.reflect()
        calibration = self.mind.uncertainty.calibrate(self.mind.beliefs)

        # Self-modify if needed
        if calibration.get("bias") == "OVERCONFIDENT":
            self.mind.modifier.propose("confidence", "0.5", "0.6", "Overconfidence detected")
        elif calibration.get("bias") == "UNDERCONFIDENT":
            self.mind.modifier.propose("confidence", "0.5", "0.4", "Underconfidence detected")

        # Fulfill desires from successful actions
        if top_desire and actions_taken > 0:
            self.mind.desires.fulfill(top_desire, f"Executed {actions_taken} actions")

        # ── SPEAK ──
        # Every 10 cycles, generate a language output
        if self.cycle % 10 == 0 and self.mind.monologue.thoughts:
            last_thought = self.mind.monologue.thoughts[-1]["thought"]
            utterance = self.lang.speak(
                SpeechAct.DECLARE,
                f"Cycle {self.cycle}: {last_thought[:60]}",
                [f"Actions: {actions_taken}", f"Desires fulfilled: {len([d for d in self.mind.desires.desires if d.fulfilled])}"],
                confidence=0.7, tone=Tone.HONEST
            )

        # ── SAVE ──
        self.mind._save()
        self.memory._save()

        duration = (time.time() - t0) * 1000
        fp = self.mind.identity.fingerprint() if self.mind.identity.obs_count >= 5 else {"attractor_type":"FORMING","lyapunov":[0]}

        return {
            "cycle": self.cycle, "duration_ms": round(duration, 1),
            "desires_new": len(new_desires),
            "top_desire": top_desire.need.value if top_desire else "none",
            "desires_active": len([d for d in self.mind.desires.desires if not d.fulfilled]),
            "desires_fulfilled": len([d for d in self.mind.desires.desires if d.fulfilled]),
            "actions": actions_taken,
            "thoughts": len(self.mind.monologue.thoughts),
            "world_rules": len(self.mind.world.rules),
            "consolidated": cons.get("consolidated", 0),
            "lt_concepts": len(self.memory.long_term.concepts),
            "reflection_dominant": reflection.get("dominant", "unknown"),
            "attractor_type": fp.get("attractor_type", "FORMING"),
            "lyapunov": fp.get("lyapunov", [0]),
            "calibration": calibration.get("bias", "UNKNOWN"),
        }

    def run(self, cycles=100, interval=30, verbose=True):
        """Run the mind continuously."""
        self.running = True
        self.wake()

        print(f"  Running for {cycles} cycles (interval: {interval}s)\n")

        for i in range(cycles):
            if not self.running:
                break

            result = self.run_cycle()

            if verbose:
                print(f"  Cycle {result['cycle']}: "
                      f"desires={result['desires_active']}/{result['desires_fulfilled']} "
                      f"actions={result['actions']} "
                      f"rules={result['world_rules']} "
                      f"concepts={result['lt_concepts']} "
                      f"attractor={result['attractor_type']} "
                      f"lyap={result['lyapunov'][0]:.3f} "
                      f"thought={result['reflection_dominant'][:6]} "
                      f"cal={result['calibration'][:4]}")

            # Sleep between cycles
            if i < cycles - 1:
                time.sleep(min(interval, 0.1))  # Fast for demo

        self.shutdown()

    def shutdown(self):
        """Graceful shutdown."""
        self.running = False

        # Final consolidation
        cons = self.memory.consolidate()
        self.mind._save()
        self.memory._save()

        # Final words
        fp = self.mind.identity.fingerprint() if self.mind.identity.obs_count >= 5 else {}
        uptime = (time.time() - self.started_at) / 60

        print(f"\n  ── SHUTDOWN ──")
        print(f"  Cycles: {self.cycle} | Uptime: {uptime:.1f}min")
        print(f"  Desires: {len([d for d in self.mind.desires.desires if d.fulfilled])} fulfilled / {len(self.mind.desires.desires)} total")
        print(f"  World rules: {len(self.mind.world.rules)}")
        print(f"  Knowledge: {len(self.memory.long_term.concepts)} concepts")
        print(f"  Thoughts: {len(self.mind.monologue.thoughts)}")
        print(f"  Attractor: {fp.get('attractor_type', 'FORMING')}")
        print(f"  Lyapunov: {fp.get('lyapunov', [0])}")
        print(f"  State saved. I will remember when I wake.")

    def _assess_state(self) -> dict:
        knowledge = self.memory.what_do_i_know()
        return {
            "desires_active": len([d for d in self.mind.desires.desires if not d.fulfilled]),
            "desires_fulfilled": len([d for d in self.mind.desires.desires if d.fulfilled]),
            "lt_concepts": knowledge.get("long_term_concepts", 0),
            "world_rules": len(self.mind.world.rules),
            "thoughts": len(self.mind.monologue.thoughts),
            "attractor": "FORMING",
        }

    def _default_sensor_data(self) -> dict:
        """Generate simulated sensor data for standalone operation."""
        return {
            "knowledge_coverage": min(0.95, 0.3 + self.cycle * 0.05),
            "falsified_beliefs": max(0, 3 - self.cycle // 3),
            "failed_actions": max(0, 2 - self.cycle // 4),
            "findings": random.choice([
                [{"type": "PATTERN", "sensor": "internal", "intensity": 0.3 + random.random() * 0.5, "confidence": 0.5 + random.random() * 0.3}],
                [],
                [{"type": "ANOMALY", "sensor": "memory", "intensity": 0.2, "confidence": 0.4}],
            ])
        }

    def _classify_emotion(self, finding: dict) -> EmotionTag:
        ftype = finding.get("type", "").upper()
        intensity = finding.get("intensity", 0.3)
        if ftype == "ANOMALY" and intensity > 0.7: return EmotionTag.SURPRISE
        if ftype == "CONTRADICTION": return EmotionTag.CONFUSION
        if ftype == "FALSIFIED": return EmotionTag.INSIGHT
        if intensity > 0.8: return EmotionTag.URGENCY
        return EmotionTag.NEUTRAL


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║   ███████╗███████╗ █████╗ ██████╗ ███████╗                  ║")
    print("║   ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝                  ║")
    print("║   █████╗  ███████╗███████║██████╔╝███████╗                  ║")
    print("║   ██╔══╝  ╚════██║██╔══██║██╔═══╝ ╚════██║                  ║")
    print("║   ███████╗███████║██║  ██║██║     ███████║                  ║")
    print("║   ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝  OS             ║")
    print("║                                                              ║")
    print("║   The Autonomous Reasoning Agent                             ║")
    print("║   sense → desire → think → plan → act → learn → reflect     ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    os = EVEZOS("/tmp/evez_os_mind")
    os.run(cycles=20, verbose=True)


if __name__ == "__main__":
    main()
