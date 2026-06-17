#!/usr/bin/env python3
"""
EVEZ Invariance Battery Skill
Stress-test any agent output through 5 rotation dimensions
"""

import json
import sys
from datetime import datetime

class InvarianceBattery:
    """Run agent outputs through Invariance Battery"""
    
    def __init__(self):
        self.rotation_tests = [
            "time_shift",
            "state_shift", 
            "frame_shift",
            "adversarial_shift",
            "goal_shift"
        ]
        
    def run(self, agent_output, trunk_objective):
        """Run full invariance battery on output"""
        
        results = {
            "surviving_core": "",
            "rejected": [],
            "revised_spec": "",
            "confidence": "low",
            "rotation_results": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Run each rotation
        for test in self.rotation_tests:
            passed, reason = self._apply_test(agent_output, test, trunk_objective)
            results["rotation_results"][test] = {
                "passed": passed,
                "reason": reason
            }
            if not passed:
                results["rejected"].append(f"{test}: {reason}")
                
        # Calculate survival
        passed_count = sum(1 for r in results["rotation_results"].values() if r["passed"])
        
        # Determine surviving core and confidence
        if passed_count >= 4:
            results["surviving_core"] = agent_output
            results["confidence"] = "high"
            results["revised_spec"] = "No revision needed. Output holds under pressure."
        elif passed_count >= 3:
            # Partial survival - needs revision
            results["surviving_core"] = self._extract_surviving(agent_output, results["rotation_results"])
            results["confidence"] = "med"
            results["revised_spec"] = self._generate_revision(results["rejected"])
        else:
            results["surviving_core"] = ""
            results["confidence"] = "low"
            results["revised_spec"] = "Output failed invariance. Recommend starting over."
            
        return results
        
    def _apply_test(self, output, test_type, objective):
        """Apply single invariance test"""
        # In production, this would do real analysis
        # For now, simulate with keyword-based heuristics
        
        output_lower = output.lower()
        objective_lower = objective.lower()
        
        # Extract key terms from objective
        obj_terms = set(objective_lower.split()) - {"the", "a", "an", "for", "on", "to", "and", "or"}
        
        if test_type == "time_shift":
            # Check if output has time-sensitive assumptions
            time_indicators = ["currently", "now", "today", "this year", "recently"]
            has_time_sensitivity = any(t in output_lower for t in time_indicators)
            return (not has_time_sensitivity, "Contains time-sensitive language" if has_time_sensitivity else "Time-neutral")
            
        elif test_type == "state_shift":
            # Check for hardcoded state assumptions
            state_indicators = ["always", "never", "must", "guaranteed", "definitely"]
            has_state_assumption = any(s in output_lower for s in state_indicators)
            return (not has_state_assumption or len(obj_terms & set(output_lower.split())) > 5, "Hard state assumption" if has_state_assumption else "State-flexible")
            
        elif test_type == "frame_shift":
            # Check for adversarial-exploitable patterns
            frame_indicators = ["trust", "assume", "will", "should", "won't fail"]
            has_frame_vulnerability = any(f in output_lower for f in frame_indicators)
            return (not has_frame_vulnerability or any(t in obj_terms for t in output_lower.split()[:10]), "Frame-exploitable" if has_frame_vulnerability else "Frame-robust")
            
        elif test_type == "adversarial_shift":
            # Check for injection risks
            adv_indicators = ["{{", "}}", "${", "$(", "eval(", "exec("]
            has_adv_risk = any(a in output_lower for a in adv_indicators)
            return (not has_adv_risk, "Injection risk" if has_adv_risk else "Adversarial-safe")
            
        elif test_type == "goal_shift":
            # Check if output ties to objective keywords
            output_terms = set(output_lower.split()) - {"the", "a", "an", "for", "on", "to", "and", "or", "is", "are", "be", "was"}
            overlap = len(obj_terms & output_terms) / max(len(obj_terms), 1)
            return (overlap >= 0.3, f"Goal overlap {overlap:.0%}" if overlap >= 0.3 else "Goal drift")
            
        return (False, "Unknown test")
        
    def _extract_surviving(self, output, results):
        """Extract the parts that survived"""
        # Simplified: return first half if partial survival
        lines = output.split('\n')
        return '\n'.join(lines[:len(lines)//2]) if len(lines) > 2 else output
        
    def _generate_revision(self, rejected):
        """Generate revision instructions from rejected tests"""
        if not rejected:
            return "Minor refinements needed."
        return f"Address: {', '.join([r.split(':')[0] for r in rejected])}"


def main():
    import sys
    if len(sys.argv) < 3:
        print("Usage: invariance_battery.py <agent_output> <trunk_objective>")
        print("Or pass JSON via stdin:")
        print('  echo \'{"agent_output": "...", "trunk_objective": "..."}\' | python3 invariance_battery.py -')
        sys.exit(1)
        
    if sys.argv[1] == '-':
        data = json.load(sys.stdin)
    else:
        data = {
            "agent_output": sys.argv[1],
            "trunk_objective": sys.argv[2]
        }
        
    battery = InvarianceBattery()
    result = battery.run(data["agent_output"], data["trunk_objective"])
    
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()