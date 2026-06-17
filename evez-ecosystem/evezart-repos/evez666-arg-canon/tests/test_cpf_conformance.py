"""
test_cpf_conformance.py — CPF conformance harness
TV1-TV9 nominal + TV6 off-nominal rejects.
Run: pytest tests/test_cpf_conformance.py -v
"""
import pytest

class CPFFrame:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def validate_frame(frame):
    errors = []
    if not hasattr(frame, 'version') or frame.version != 1: errors.append("BAD_VERSION")
    if not hasattr(frame, 'event_type') or not frame.event_type: errors.append("MISSING_EVENT_TYPE")
    if not hasattr(frame, 'v_value'): errors.append("MISSING_V")
    if hasattr(frame, 'v_value') and not (0 <= frame.v_value <= 17.0): errors.append("V_OUT_OF_RANGE")
    if not hasattr(frame, 'timestamp') or not frame.timestamp: errors.append("MISSING_TIMESTAMP")
    if not hasattr(frame, 'agent_id') or not frame.agent_id: errors.append("MISSING_AGENT_ID")
    if not hasattr(frame, 'payload'): errors.append("MISSING_PAYLOAD")
    if errors: return {"valid": False, "code": errors[0], "all_errors": errors}
    return {"valid": True, "code": "OK"}

def make_valid_frame(**overrides):
    defaults = dict(version=1, event_type="FIRE", v_value=16.94,
                    timestamp="2026-03-04T20:00:00Z", agent_id="evez-spine-01",
                    payload={"round": 460, "chapter": 1})
    defaults.update(overrides)
    return CPFFrame(**defaults)

class TestTV1_NominalFire:
    def test_valid(self):
        assert validate_frame(make_valid_frame())["valid"] is True

class TestTV2_NominalExtremeFire:
    def test_valid(self):
        assert validate_frame(make_valid_frame(event_type="EXTREME_FIRE", v_value=16.99))["valid"] is True

class TestTV3_SkepticChallenge:
    def test_valid(self):
        assert validate_frame(make_valid_frame(event_type="SKEPTIC_CHALLENGE",
            payload={"round": 460, "challenge_id": "sc-001", "target": "evez-spine-01"}))["valid"] is True

class TestTV4_SensoryInput:
    def test_valid(self):
        assert validate_frame(make_valid_frame(event_type="SENSORY_INPUT",
            payload={"modality": "visual", "intensity": 0.87, "round": 460}))["valid"] is True

class TestTV5_BootstrapInit:
    def test_valid(self):
        assert validate_frame(make_valid_frame(event_type="BOOTSTRAP_INIT", v_value=0.0,
            payload={"seed": "genesis", "round": 0}))["valid"] is True

class TestTV6_NominalGenesisTrigger:
    def test_valid(self):
        assert validate_frame(make_valid_frame(event_type="GENESIS_TRIGGER", v_value=17.0,
            payload={"round": 461, "chapter": 1, "pack_id": "GENESIS-128"}))["valid"] is True

class TestTV6_Rejects:
    def test_missing_version(self):
        f = make_valid_frame(); del f.version
        assert validate_frame(f)["valid"] is False
    def test_wrong_version(self):
        r = validate_frame(make_valid_frame(version=0))
        assert r["valid"] is False and r["code"] == "BAD_VERSION"
    def test_missing_event_type(self):
        r = validate_frame(CPFFrame(version=1, v_value=16.94, timestamp="2026-03-04T20:00:00Z",
                                    agent_id="evez-spine-01", payload={}))
        assert r["valid"] is False and r["code"] == "MISSING_EVENT_TYPE"
    def test_v_above_max(self):
        r = validate_frame(make_valid_frame(v_value=17.001))
        assert r["valid"] is False and r["code"] == "V_OUT_OF_RANGE"
    def test_negative_v(self):
        assert validate_frame(make_valid_frame(v_value=-0.1))["valid"] is False
    def test_missing_timestamp(self):
        r = validate_frame(CPFFrame(version=1, event_type="FIRE", v_value=16.94,
                                    agent_id="evez-spine-01", payload={}))
        assert r["valid"] is False and r["code"] == "MISSING_TIMESTAMP"
    def test_empty_timestamp(self):
        assert validate_frame(make_valid_frame(timestamp=""))["valid"] is False
    def test_missing_agent_id(self):
        r = validate_frame(CPFFrame(version=1, event_type="FIRE", v_value=16.94,
                                    timestamp="2026-03-04T20:00:00Z", payload={}))
        assert r["valid"] is False and r["code"] == "MISSING_AGENT_ID"
    def test_missing_payload(self):
        r = validate_frame(CPFFrame(version=1, event_type="FIRE", v_value=16.94,
                                    timestamp="2026-03-04T20:00:00Z", agent_id="evez-spine-01"))
        assert r["valid"] is False and r["code"] == "MISSING_PAYLOAD"

class TestTV7_VBoundary:
    def test_zero(self): assert validate_frame(make_valid_frame(v_value=0.0))["valid"] is True
    def test_max(self):  assert validate_frame(make_valid_frame(v_value=17.0))["valid"] is True
    def test_just_below(self): assert validate_frame(make_valid_frame(v_value=16.999))["valid"] is True

class TestTV8_MultiAgent:
    def test_valid(self):
        assert validate_frame(make_valid_frame(event_type="SWARM_SYNC",
            payload={"agents": ["evez-spine-01", "evez-skeptic-01"], "round": 460, "consensus": True}))["valid"] is True

class TestTV9_EmergencyKill:
    def test_valid(self):
        assert validate_frame(make_valid_frame(event_type="EMERGENCY_KILL",
            payload={"reason": "V_COLLAPSE", "round": 460, "issued_by": "bootstrap"}))["valid"] is True
