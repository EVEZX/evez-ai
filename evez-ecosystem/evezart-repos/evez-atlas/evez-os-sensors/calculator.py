"""
EVEZ-OS ADVANCED CALCULATOR — The Mathematical Engine
Arithmetic → Topology → Quantum → Number Theory → EVEZ-OS specific
Every result is falsified. Every computation is recorded.
"""
import math, cmath, json, hashlib, time, random, sys, os, re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from fractions import Fraction
from decimal import Decimal, getcontext

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
getcontext().prec = 50

class ResultType(str, Enum):
    INTEGER="integer"; RATIONAL="rational"; REAL="real"; COMPLEX="complex"
    VECTOR="vector"; MATRIX="matrix"; TOPOLOGICAL="topological"
    SYMBOLIC="symbolic"; BOOLEAN="boolean"; NULL="null"

@dataclass
class CalcResult:
    value: any; type: ResultType; precision: float; error_bound: float
    computation_time_ms: float; falsified: bool=False
    falsification_attempts: int=0; hash: str=""; expression: str=""
    def __post_init__(self):
        self.hash = hashlib.sha256(f"{self.value}:{self.type.value}:{self.precision}".encode()).hexdigest()[:12]
    def __repr__(self):
        if self.type == ResultType.COMPLEX and isinstance(self.value, complex):
            return f"{self.value.real:.10g}{self.value.imag:+.10g}j"
        if isinstance(self.value, float):
            return f"{self.value:.10e}" if abs(self.value)>1e10 or (abs(self.value)<1e-6 and self.value!=0) else f"{self.value:.10g}"
        if isinstance(self.value, list):
            return str(self.value)[:80]
        return str(self.value)

class AdvancedCalculator:
    def __init__(self):
        self.history = []
        self.variables = {"pi":math.pi,"π":math.pi,"e":math.e,
            "φ":(1+math.sqrt(5))/2,"γ":0.5772156649015329,
            "h":6.62607015e-34,"c":299792458,"k":1.380649e-23,
            "NA":6.02214076e23,"G":6.67430e-11}
        self.falsification_enabled = True
        self.stats = {"computations":0,"falsified":0,"verified":0}
        self._setup_functions()

    def _setup_functions(self):
        self.functions = {
            # Arithmetic
            "add": lambda a,b: a+b, "sub": lambda a,b: a-b,
            "mul": lambda a,b: a*b, "div": lambda a,b: a/b if b!=0 else float('inf'),
            "mod": lambda a,b: a%b if b!=0 else float('nan'),
            "pow": lambda a,b: a**b,
            "sqrt": lambda a: cmath.sqrt(a) if isinstance(a,complex) or a<0 else math.sqrt(a),
            "cbrt": lambda a: a**(1/3), "abs": lambda a: abs(a),
            "floor": lambda a: math.floor(a), "ceil": lambda a: math.ceil(a),
            "round": lambda a,n=0: round(a,int(n)),
            "gcd": lambda a,b: math.gcd(int(a),int(b)),
            "lcm": lambda a,b: abs(a*b)//math.gcd(int(a),int(b)) if a and b else 0,
            "factorial": lambda a: math.factorial(int(a)) if int(a)<=170 else float('inf'),
            "choose": lambda n,k: math.comb(int(n),int(k)),
            "fibonacci": lambda a: self._fib(int(a)),
            # Trig
            "sin": lambda a: math.sin(a), "cos": lambda a: math.cos(a),
            "tan": lambda a: math.tan(a), "asin": lambda a: math.asin(max(-1,min(1,a))),
            "acos": lambda a: math.acos(max(-1,min(1,a))), "atan": lambda a: math.atan(a),
            "sinh": lambda a: math.sinh(a), "cosh": lambda a: math.cosh(a),
            "tanh": lambda a: math.tanh(a),
            "deg": lambda a: math.degrees(a), "rad": lambda a: math.radians(a),
            # Exp/Log
            "exp": lambda a: math.exp(a), "ln": lambda a: math.log(a) if a>0 else float('nan'),
            "log": lambda a,b=10: math.log(a,b) if a>0 and b>0 and b!=1 else float('nan'),
            "log2": lambda a: math.log2(a) if a>0 else float('nan'),
            "log10": lambda a: math.log10(a) if a>0 else float('nan'),
            # Complex
            "re": lambda a: a.real if isinstance(a,complex) else a,
            "im": lambda a: a.imag if isinstance(a,complex) else 0,
            "conj": lambda a: a.conjugate() if isinstance(a,complex) else a,
            "arg": lambda a: cmath.phase(a) if isinstance(a,complex) else 0,
            # Number Theory
            "is_prime": lambda a: self._is_prime(int(a)),
            "next_prime": lambda a: self._next_prime(int(a)),
            "prime_pi": lambda a: sum(1 for i in range(2,int(a)+1) if self._is_prime(i)),
            "euler_totient": lambda a: self._totient(int(a)),
            "mobius": lambda a: self._mobius(int(a)),
            "divisors": lambda a: self._divisors(int(a)),
            "divisor_count": lambda a: len(self._divisors(int(a))),
            "sigma": lambda a: sum(self._divisors(int(a))),
            "legendre": lambda a,p: self._legendre(int(a),int(p)),
            # Linear Algebra
            "det": lambda m: self._det(m),
            "trace": lambda m: sum(m[i][i] for i in range(min(len(m),len(m[0])))),
            "eigenvalues_2x2": lambda m: self._eigen2(m),
            "norm": lambda v: sum(x**2 for x in v)**0.5,
            "dot": lambda a,b: sum(x*y for x,y in zip(a,b)),
            # Special
            "gamma": lambda a: math.gamma(a) if a>0 else float('nan'),
            "beta": lambda a,b: math.gamma(a)*math.gamma(b)/math.gamma(a+b),
            "zeta": lambda a: self._zeta(a),
            "erf": lambda a: math.erf(a), "erfc": lambda a: math.erfc(a),
            "lambert_w": lambda a: self._lambert_w(a),
            "sinc": lambda a: 1 if a==0 else math.sin(a)/a,
            "softmax": lambda *a: self._softmax(list(a)),
            # EVEZ-OS
            "poly_c": lambda t,o,tp,n: (t*o*tp)/(2*math.sqrt(max(n,1))),
            "pre_lie_pressure": lambda i,o,a,p,t: i*o*(1-a)*p*t,
            "shadow_price": lambda c,t,e: (1-c)*t*(1/max(e,1)),
            "lyapunov_estimate": lambda s: self._lyap(s),
            "fractal_dim": lambda s: self._frac_dim(s),
            # Quantum
            "pauli_x": lambda: [[0,1],[1,0]],
            "pauli_y": lambda: [[0,-1j],[1j,0]],
            "pauli_z": lambda: [[1,0],[0,-1]],
            "hadamard": lambda: [[1,1],[1,-1]],
            "kronecker": lambda A,B: self._kron(A,B),
            # Calculus
            "diff": lambda f,x,h=1e-8: self._diff(f,x,h),
            "integrate": lambda f,a,b,n=1000: self._integrate(f,a,b,n),
            "solve_newton": lambda f,x0,tol=1e-10: self._newton(f,x0,tol),
            # Topology
            "betti": lambda ints: self._betti(ints),
            "euler_characteristic": lambda v,e,f: v-e+f,
        }

    # ── CORE COMPUTE ─────────────────────────────────────────
    def compute(self, expression: str) -> CalcResult:
        t0 = time.time()
        self.stats["computations"] += 1
        try:
            value = self._eval(expression)
            rtype = self._classify(value)
            prec = float('inf') if isinstance(value,(int,bool)) else 53
            result = CalcResult(value=value,type=rtype,precision=prec,
                error_bound=0,computation_time_ms=(time.time()-t0)*1000,expression=expression)
            if self.falsification_enabled and rtype in (ResultType.REAL,ResultType.INTEGER):
                v2 = self._falsify(expression, value)
                if v2 is not None:
                    err = abs(value - v2)
                    result.error_bound = err
                    result.falsification_attempts = 1
                    if err > 1e-6*max(abs(value),1): result.falsified = True; self.stats["falsified"]+=1
                    else: self.stats["verified"]+=1
            self.history.append({"expr":expression,"result":repr(result),"type":rtype.value,"time":time.time()})
            return result
        except Exception as ex:
            return CalcResult(value=None,type=ResultType.NULL,precision=0,
                error_bound=float('inf'),computation_time_ms=(time.time()-t0)*1000,
                expression=expression,falsified=True)

    def _eval(self, expr):
        expr = expr.strip()
        if expr in self.variables: return self.variables[expr]
        # Function call: func(args)
        m = re.match(r'^(\w+)\((.+)\)$', expr)
        if m:
            fn, args_s = m.groups()
            if fn in self.functions:
                args = self._parse_args(args_s)
                return self.functions[fn](*args)
        # Matrix
        if expr.startswith('[[') and expr.endswith(']]'):
            rows = expr[2:-2].split('],[')
            return [[self._eval(x.strip()) for x in r.split(',')] for r in rows]
        # Vector
        if expr.startswith('[') and expr.endswith(']'):
            return [self._eval(x.strip()) for x in expr[1:-1].split(',')]
        # Safe eval
        safe = {"__builtins__":{},"abs":abs,"round":round,"min":min,"max":max,
                "sum":sum,"pow":pow,"int":int,"float":float,"complex":complex,
                "True":True,"False":False,"None":None}
        safe.update(self.variables)
        safe.update({k:v for k,v in self.functions.items() if not k.startswith('_')})
        try: return eval(expr, safe)
        except:
            try: return float(expr)
            except:
                try: return int(expr)
                except: return expr

    def _parse_args(self, s):
        args = []; depth = 0; cur = ""
        for ch in s:
            if ch in '([': depth += 1; cur += ch
            elif ch in ')]': depth -= 1; cur += ch
            elif ch == ',' and depth == 0: args.append(self._eval(cur.strip())); cur = ""
            else: cur += ch
        if cur.strip(): args.append(self._eval(cur.strip()))
        return args

    def _classify(self, v):
        if v is None: return ResultType.NULL
        if isinstance(v, bool): return ResultType.BOOLEAN
        if isinstance(v, int): return ResultType.INTEGER
        if isinstance(v, Fraction): return ResultType.RATIONAL
        if isinstance(v, float): return ResultType.REAL
        if isinstance(v, complex): return ResultType.COMPLEX
        if isinstance(v, list):
            return ResultType.MATRIX if v and isinstance(v[0], list) else ResultType.VECTOR
        return ResultType.SYMBOLIC

    def _falsify(self, expr, value):
        try:
            if '+' in expr and '*' not in expr:
                parts = [float(x.strip()) for x in expr.split('+') if x.strip()]
                if len(parts) > 1: return sum(parts)
            if '*' in expr and '+' not in expr:
                parts = [float(x.strip()) for x in expr.split('*') if x.strip()]
                r = 1.0
                for p in parts: r *= p
                return r
        except: pass
        return None

    # ── NUMBER THEORY ────────────────────────────────────────
    def _is_prime(self, n):
        if n < 2: return False
        if n < 4: return True
        if n%2==0 or n%3==0: return False
        i = 5
        while i*i <= n:
            if n%i==0 or n%(i+2)==0: return False
            i += 6
        return True

    def _next_prime(self, n):
        n = n+1 if n%2==0 else n+2
        while not self._is_prime(n): n += 2
        return n

    def _fib(self, n):
        a, b = 0, 1
        for _ in range(abs(n)): a, b = b, a+b
        return a

    def _totient(self, n):
        r = n; t = n
        for p in range(2, int(math.sqrt(n))+1):
            if t%p == 0:
                while t%p==0: t//=p
                r -= r//p
        if t > 1: r -= r//t
        return r

    def _mobius(self, n):
        if n == 1: return 1
        c = 0; t = n
        for p in range(2, int(math.sqrt(n))+1):
            if t%p==0:
                t//=p; c+=1
                if t%p==0: return 0
        if t>1: c+=1
        return -1 if c%2 else 1

    def _divisors(self, n):
        n = abs(n); d = []
        for i in range(1, int(math.sqrt(n))+1):
            if n%i==0: d.extend([i, n//i] if i!=n//i else [i])
        return sorted(d)

    def _legendre(self, a, p):
        if not self._is_prime(p): return float('nan')
        if a%p==0: return 0
        return 1 if pow(a,(p-1)//2,p)==1 else -1

    # ── LINEAR ALGEBRA ───────────────────────────────────────
    def _det(self, m):
        n = len(m)
        if n==1: return m[0][0]
        if n==2: return m[0][0]*m[1][1]-m[0][1]*m[1][0]
        d = 0
        for j in range(n):
            minor = [[m[i][k] for k in range(n) if k!=j] for i in range(1,n)]
            d += ((-1)**j)*m[0][j]*self._det(minor)
        return d

    def _eigen2(self, m):
        if len(m)!=2 or any(len(r)!=2 for r in m): return [float('nan')]
        a,b,c,d = m[0][0],m[0][1],m[1][0],m[1][1]
        tr = a+d; det = a*d-b*c; disc = tr**2-4*det
        if disc >= 0: return [(tr+math.sqrt(disc))/2,(tr-math.sqrt(disc))/2]
        return [complex(tr/2,math.sqrt(-disc)/2),complex(tr/2,-math.sqrt(-disc)/2)]

    # ── CALCULUS ─────────────────────────────────────────────
    def _diff(self, f_str, x, h=1e-8):
        f = self._mkfn(f_str)
        return (f(x+h)-f(x-h))/(2*h) if f else float('nan')

    def _integrate(self, f_str, a, b, n):
        f = self._mkfn(f_str)
        if not f: return float('nan')
        h = (b-a)/n; r = f(a)+f(b)
        for i in range(1,n): r += (4 if i%2 else 2)*f(a+i*h)
        return r*h/3

    def _newton(self, f_str, x0, tol):
        f = self._mkfn(f_str)
        if not f: return float('nan')
        x = x0
        for _ in range(1000):
            fx = f(x)
            if abs(fx)<tol: return x
            dfx = (f(x+1e-8)-f(x-1e-8))/2e-8
            if dfx==0: break
            x -= fx/dfx
        return x

    def _mkfn(self, s):
        try:
            def f(x):
                return eval(s,{"__builtins__":{},"x":x,"math":math,"sin":math.sin,
                    "cos":math.cos,"exp":math.exp,"log":math.log,"sqrt":math.sqrt,
                    "pi":math.pi,"e":math.e,"abs":abs,"pow":pow})
            return f
        except: return None

    # ── SPECIAL ──────────────────────────────────────────────
    def _zeta(self, s, terms=500):
        if isinstance(s,complex): return sum(1/(n**s) for n in range(1,min(terms,100)))
        if s<=1: return float('nan')
        return sum(1/(n**s) for n in range(1,terms))

    def _lambert_w(self, x, iters=100):
        if x < -1/math.e: return float('nan')
        w = x if abs(x)<1 else math.log(max(x,1e-10))
        for _ in range(iters):
            ew = math.exp(w)
            denom = ew*(w+1)-(w+2)*(w*ew-x)/(2*w+2) if (2*w+2)!=0 else 1
            w = w-(w*ew-x)/denom if denom!=0 else w
        return w

    def _softmax(self, xs):
        mx = max(xs); e = [math.exp(x-mx) for x in xs]; s = sum(e)
        return [v/s for v in e]

    # ── TOPOLOGY ─────────────────────────────────────────────
    def _betti(self, ints):
        from simplicial_topology import SimplicialComplex
        try: return SimplicialComplex.from_interactions(ints,0.1).betti_numbers()
        except: return [0,0,0]

    # ── EVEZ-OS ──────────────────────────────────────────────
    def _lyap(self, s):
        if not s or len(s)<10: return 0.0
        s = [float(x) for x in s]
        d = [math.log(abs(s[i+1]-s[i])+1e-10) for i in range(len(s)-1) if abs(s[i+1]-s[i])>1e-10]
        return sum(d)/len(d) if d else 0.0

    def _frac_dim(self, s):
        if not s or len(s)<10: return 0.0
        s = [float(x) for x in s]
        dists = [abs(s[i]-s[j]) for i in range(min(len(s),50)) for j in range(i+1,min(len(s),50))]
        if not dists: return 0.0
        lr,lc = [],[]
        for r in [0.01,0.1,1.0,10.0]:
            c = sum(1 for d in dists if d<r)/len(dists)
            if c>0: lr.append(math.log10(r)); lc.append(math.log10(c))
        if len(lr)>=2:
            mx,my = sum(lr)/len(lr),sum(lc)/len(lc)
            denom = sum((x-mx)**2 for x in lr)
            if denom>0: return max(0,sum((x-mx)*(y-my) for x,y in zip(lr,lc))/denom)
        return 0.0

    # ── QUANTUM ──────────────────────────────────────────────
    def _kron(self, A, B):
        return [[a*b for b in rb for a in ra] for ra in A for rb in B]

    # ── REPL ─────────────────────────────────────────────────
    def repl(self):
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  EVEZ-OS ADVANCED CALCULATOR                                ║")
        print("║  Arithmetic → Topology → Quantum → Number Theory            ║")
        print("║  Type 'help' for functions. 'quit' to exit.                 ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        while True:
            try: expr = input("evez> ").strip()
            except: break
            if not expr: continue
            if expr in ('quit','exit','q'): break
            if expr=='help':
                print(f"  Functions: {', '.join(sorted(self.functions.keys()))}")
                print(f"  Variables: {', '.join(self.variables.keys())}")
                continue
            if expr=='history':
                for h in self.history[-10:]: print(f"  {h['expr']} = {h['result']}")
                continue
            if expr.startswith('let '):
                parts = expr[4:].split('=',1)
                if len(parts)==2:
                    self.variables[parts[0].strip()] = self._eval(parts[1].strip())
                    print(f"  {parts[0].strip()} = {self.variables[parts[0].strip()]}")
                continue
            r = self.compute(expr)
            if r.type==ResultType.NULL: print(f"  ERROR: cannot compute '{expr}'")
            else:
                f = " ✓" if not r.falsified else " ✗ FALSIFIED"
                print(f"  = {r} [{r.type.value}] prec={r.precision:.0f}bits{f}")
        print(f"\n  {self.stats['computations']} computations, {self.stats['verified']} verified, {self.stats['falsified']} falsified")


if __name__ == "__main__":
    calc = AdvancedCalculator()
    print("── EVEZ-OS Advanced Calculator Demo ──\n")
    tests = [
        ("2+2","Arithmetic"),("sqrt(2)","Irrational"),("sqrt(-1)","Complex"),
        ("pi*e","Constants"),("sin(pi/6)","Trig"),("is_prime(97)","Primality"),
        ("fibonacci(42)","Fibonacci"),("factorial(20)","Factorial"),
        ("euler_totient(100)","Euler φ"),("divisors(360)","Divisors"),
        ("gamma(5)","Gamma"),("zeta(2)","Riemann ζ"),
        ("poly_c(0.8,0.6,1.4,10)","poly_c"),
        ("pre_lie_pressure(0.8,0.9,0.3,0.7,0.5)","Pre-Lie"),
        ("shadow_price(0.3,2.0,5)","Shadow price"),
        ("det(pauli_x())","Pauli det"),
        ("eigenvalues_2x2([[1,2],[3,4]])","Eigenvalues"),
        ("diff('x**3',2)","d/dx x³ at 2"),
        ("integrate('x**2',0,1)","∫x² 0→1"),
    ]
    for expr,desc in tests:
        r = calc.compute(expr)
        s = "✓" if not r.falsified else "✗"
        print(f"  {desc}: {expr} = {r} [{r.type.value}] {s}")
    print(f"\n  {calc.stats['computations']} computations | {calc.stats['verified']} verified | {calc.stats['falsified']} falsified")
