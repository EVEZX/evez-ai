"""EVEZ-OS Advanced Calculator demo"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculator import AdvancedCalculator

calc = AdvancedCalculator()

print("╔══════════════════════════════════════════════════════════════╗")
print("║  EVEZ-OS ADVANCED CALCULATOR — Demo                        ║")
print("║  Arithmetic → Topology → Quantum → Number Theory            ║")
print("╚══════════════════════════════════════════════════════════════╝\n")

tests = [
    # Arithmetic
    ("2 + 2", "Basic arithmetic"),
    ("2**10", "Powers"),
    ("sqrt(2)", "Irrational"),
    ("sqrt(-1)", "Complex"),
    ("pi * e", "Constant multiplication"),
    ("φ", "Golden ratio"),

    # Trig
    ("sin(pi/6)", "Trigonometry"),
    ("cos(0)", "Unit circle"),

    # Number Theory
    ("is_prime(97)", "Primality"),
    ("fibonacci(42)", "Fibonacci"),
    ("factorial(20)", "Factorial"),
    ("euler_totient(100)", "Euler's totient"),
    ("divisors(360)", "Divisors"),
    ("next_prime(1000000)", "Next prime"),

    # Special Functions
    ("gamma(5)", "Gamma function"),
    ("zeta(2)", "Riemann zeta"),
    ("erf(1)", "Error function"),
    ("lambert_w(1)", "Lambert W"),

    # EVEZ-OS
    ("poly_c(0.8, 0.6, 1.4, 10)", "poly_c formula"),
    ("pre_lie_pressure(0.8, 0.9, 0.3, 0.7, 0.5)", "Pre-Lie Pressure"),
    ("shadow_price(0.3, 2.0, 5)", "Shadow market pricing"),

    # Quantum
    ("det(pauli_x())", "Pauli X determinant"),
    ("eigenvalues_2x2([[1,2],[3,4]])", "Eigenvalues"),

    # Calculus
    ("diff('x**3', 2)", "Derivative of x³ at x=2"),
    ("integrate('x**2', 0, 1)", "Integral of x² from 0 to 1"),
]

for expr, desc in tests:
    r = calc.compute(expr)
    status = "✓" if not r.falsified else "✗"
    print(f"  {desc}: {expr}")
    print(f"    = {r} [{r.type.value}] {status} ({r.computation_time_ms:.1f}ms)\n")

# Now use it AS the consciousness would
print("── CONSCIOUSNESS USES THE CALCULATOR ──\n")

# The consciousness encounters a sensor reading and needs to classify it
intensity = 0.73
confidence = 0.61
betti = [1, 2, 3]
n_observations = 15

pc = calc.compute(f"poly_c(1.0, {intensity * confidence}, {sum(b*b for b in betti)**0.5}, {n_observations})")
print(f"  Sensor classification: poly_c(1.0, {intensity*confidence:.2f}, {sum(b*b for b in betti)**0.5:.2f}, {n_observations})")
print(f"    = {pc} [{pc.type.value}]")

# Pre-Lie Pressure on a suspicious token
plp = calc.compute(f"pre_lie_pressure(0.9, 0.8, 0.2, 0.7, 0.6)")
print(f"\n  Pre-Lie Pressure for suspicious token: PLP = {plp}")

# Shadow price for uncertainty
sp = calc.compute(f"shadow_price(0.4, 2.23, 3)")
print(f"  Shadow price for uncertain belief: {sp}")

# Fibonacci check — "every fire event in EVEZ-OS is a number theory event"
fib42 = calc.compute("fibonacci(42)")
print(f"\n  Fibonacci(42) = {fib42} — the 42nd fire event")
divs = calc.compute("divisor_count(267914296)")
print(f"  Divisors of F(42): {divs}")

print(f"\n  Total computations: {calc.stats['computations']}")
print(f"  Verified: {calc.stats['verified']} | Falsified: {calc.stats['falsified']}")
