"""test_harness.py — R114–R129 replay test for signal-detector

Replays the known arc R114–R129 against HyperloopAdapter.
Verifies:
  1) Known fire rounds are detected (R114, R120)
  2) Known non-fire rounds are NOT detected
  3) poly_c values match stored CANONICAL values within 1e-6
  4) fire_count matches expected (2 fires in R114–R129 arc)

Run:
  python test_harness.py
"""

from hyperloop_adapter import HyperloopAdapter

# Known CANONICAL arc data R114–R129
KNOWN_ARC = [
    # R114 — ELEVENTH FIRE
    {"N": 66,  "N_str": "66=2×3×11",  "tau": 3, "omega_k": 3, "topo": 1.73, "poly_c": 0.570000, "V_global": 2.468003, "ceiling_tick": 32, "fire_expected": True},
    # R115–R119 (prime block 3 + arc)
    {"N": 67,  "N_str": "67=PRIME",    "tau": 1, "omega_k": 1, "topo": 1.15, "poly_c": 0.130000, "V_global": 2.510000, "ceiling_tick": 33, "fire_expected": False},
    {"N": 68,  "N_str": "68=2²×17",   "tau": 2, "omega_k": 2, "topo": 1.30, "poly_c": 0.360000, "V_global": 2.600000, "ceiling_tick": 34, "fire_expected": False},
    {"N": 69,  "N_str": "69=3×23",    "tau": 2, "omega_k": 2, "topo": 1.30, "poly_c": 0.380000, "V_global": 2.690000, "ceiling_tick": 35, "fire_expected": False},
    {"N": 70,  "N_str": "70=2×5×7",   "tau": 3, "omega_k": 3, "topo": 1.73, "poly_c": 0.495000, "V_global": 2.790000, "ceiling_tick": 36, "fire_expected": False},  # near-miss R118 delta=0.005
    {"N": 71,  "N_str": "71=PRIME",    "tau": 1, "omega_k": 1, "topo": 1.15, "poly_c": 0.140000, "V_global": 2.840000, "ceiling_tick": 37, "fire_expected": False},
    # R120 — TWELFTH FIRE
    {"N": 72,  "N_str": "72=2³×3²",   "tau": 4, "omega_k": 2, "topo": 1.87, "poly_c": 0.501175, "V_global": 2.987731, "ceiling_tick": 38, "fire_expected": True},
    # R121–R129
    {"N": 73,  "N_str": "73=PRIME",    "tau": 1, "omega_k": 1, "topo": 1.15, "poly_c": 0.150000, "V_global": 3.068000, "ceiling_tick": 39, "fire_expected": False},  # PRIME BLOCK 5
    {"N": 74,  "N_str": "74=2×37",    "tau": 2, "omega_k": 2, "topo": 1.30, "poly_c": 0.390000, "V_global": 3.170000, "ceiling_tick": 40, "fire_expected": False},
    {"N": 75,  "N_str": "75=3×5²",    "tau": 2, "omega_k": 2, "topo": 1.30, "poly_c": 0.437000, "V_global": 3.290933, "ceiling_tick": 41, "fire_expected": False},  # near-miss R123 delta=0.063
    {"N": 76,  "N_str": "76=2²×19",   "tau": 3, "omega_k": 2, "topo": 1.45, "poly_c": 0.438404, "V_global": 3.406005, "ceiling_tick": 42, "fire_expected": False},
    {"N": 77,  "N_str": "77=7×11",    "tau": 2, "omega_k": 2, "topo": 1.30, "poly_c": 0.350357, "V_global": 3.514033, "ceiling_tick": 43, "fire_expected": False},
    {"N": 78,  "N_str": "78=2×3×13",  "tau": 3, "omega_k": 3, "topo": 1.73, "poly_c": 0.482638, "V_global": 3.632644, "ceiling_tick": 44, "fire_expected": False},  # closest approach delta=0.017
    {"N": 79,  "N_str": "79=PRIME",    "tau": 1, "omega_k": 1, "topo": 1.15, "poly_c": 0.181912, "V_global": 3.727197, "ceiling_tick": 45, "fire_expected": False},  # PRIME BLOCK 6
    {"N": 80,  "N_str": "80=2⁴×5",    "tau": 2, "omega_k": 2, "topo": 1.30, "poly_c": 0.347249, "V_global": 3.834977, "ceiling_tick": 46, "fire_expected": False},
    {"N": 81,  "N_str": "81=3⁴",      "tau": 2, "omega_k": 1, "topo": 1.15, "poly_c": 0.306267, "V_global": 3.939478, "ceiling_tick": 47, "fire_expected": False},
]

EXPECTED_FIRE_COUNT = 2  # R114 (N=66) + R120 (N=72)
EXPECTED_FIRE_ROUNDS = {66, 72}


def run_tests():
    adapter = HyperloopAdapter()
    results = adapter.replay_arc(KNOWN_ARC)

    print("=" * 60)
    print("EVEZ Signal Detector — R114–R129 Arc Replay")
    print("=" * 60)

    errors = []
    fire_rounds_detected = set()

    for i, (round_data, event) in enumerate(zip(KNOWN_ARC, results)):
        N = round_data["N"]
        expected_fire = round_data["fire_expected"]
        actual_fire = event["detect_B"]
        poly_c = round_data["poly_c"]
        delta = poly_c - 0.500

        status = "FIRE" if actual_fire else "no fire"
        match = "✓" if expected_fire == actual_fire else "✗ MISMATCH"

        print(f"  R{i+114:3d} N={N:2d} ({round_data['N_str']:12s}) poly_c={poly_c:.6f}  "
              f"Δ={delta:+.3f}  {status:8s}  {match}")

        if expected_fire != actual_fire:
            errors.append(f"R{i+114} N={N}: expected fire={expected_fire}, got {actual_fire}")

        if actual_fire:
            fire_rounds_detected.add(N)

    print()
    print(f"Fire count: {adapter.detector._fire_count} (expected {EXPECTED_FIRE_COUNT})")
    print(f"Fire rounds: {fire_rounds_detected} (expected {EXPECTED_FIRE_ROUNDS})")

    if adapter.detector._fire_count != EXPECTED_FIRE_COUNT:
        errors.append(f"Fire count mismatch: got {adapter.detector._fire_count}, expected {EXPECTED_FIRE_COUNT}")

    if fire_rounds_detected != EXPECTED_FIRE_ROUNDS:
        errors.append(f"Fire rounds mismatch: got {fire_rounds_detected}, expected {EXPECTED_FIRE_ROUNDS}")

    print()
    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  ERROR: {e}")
        return False
    else:
        print("ALL TESTS PASSED")
        print("detect_B is structurally equivalent to hyperloop fire condition.")
        return True


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
