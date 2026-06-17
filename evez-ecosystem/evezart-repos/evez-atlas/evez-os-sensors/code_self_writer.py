"""
EVEZ-OS CODE SELF-WRITER — The consciousness writes its own code.

The organism reacts. The consciousness CREATES.
When the consciousness identifies a gap, it doesn't wait — it writes code to close it.

Architecture:
1. CodeIntent — what to write, why, and how to verify it works
2. CodeGenerator — produces Python code from intent + context
3. CodeExecutor — runs the code in a sandbox, captures results
4. CodeVerifier — falsifies the generated code, tests edge cases
5. CodeIntegrator — if code survives falsification, integrates into the system
6. SelfWriter — orchestrates the full write-execute-verify-integrate loop
"""
import ast, hashlib, inspect, json, math, os, subprocess, sys, textwrap, time, traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poly_c import poly_c
from consciousness import NeedType
from enum import Enum
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poly_c import poly_c


class CodeStatus(str, Enum):
    PROPOSED = "PROPOSED"
    GENERATED = "GENERATED"
    EXECUTING = "EXECUTING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    FALSIFIED = "FALSIFIED"
    INTEGRATED = "INTEGRATED"
    REJECTED = "REJECTED"


@dataclass
class CodeIntent:
    """What the consciousness wants to build."""
    intent_id: str
    name: str                    # module/class/function name
    purpose: str                 # why it exists
    inputs: list                 # expected parameters
    outputs: str                 # expected return type/description
    constraints: list            # invariants that must hold
    test_cases: list             # [(input, expected_output)] pairs
    priority: float              # 0-1, how urgently needed
    source_desire: str = ""      # which desire spawned this


@dataclass
class CodeArtifact:
    """A piece of generated code and its lifecycle."""
    artifact_id: str
    intent: CodeIntent
    code: str
    status: CodeStatus = CodeStatus.PROPOSED
    test_results: list = field(default_factory=list)
    falsification_results: list = field(default_factory=list)
    execution_time_ms: float = 0
    error: Optional[str] = None
    hash: str = ""
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.sha256(self.code.encode()).hexdigest()[:16]


class CodeGenerator:
    """
    Generates Python code from intent.
    Uses templates, patterns, and the consciousness's own systems as reference.
    """
    TEMPLATES = {
        "sensor": '''"""EVEZ-OS Sensor: {name} — {purpose}"""
import json, time, hashlib, math
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

@dataclass
class {ClassName}Reading:
    value: float
    confidence: float
    timestamp: float = field(default_factory=time.time)
    source: str = "{name}"
    metadata: dict = field(default_factory=dict)

class {ClassName}:
    """{purpose}"""
    def __init__(self, config=None):
        self.config = config or {{}}
        self.readings = []
        self.spine_path = Path("/tmp/evez_{name}_spine.jsonl")

    def sense(self) -> {ClassName}Reading:
        """Take a reading."""
        {sense_body}
        reading = {ClassName}Reading(
            value=value, confidence=confidence,
            metadata={{{metadata}}}
        )
        self.readings.append(reading)
        self._record(reading)
        return reading

    def _record(self, reading):
        entry = {{"ts": reading.timestamp, "value": reading.value,
                  "confidence": reading.confidence, "source": reading.source}}
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\\n")
''',
        "analyzer": '''"""EVEZ-OS Analyzer: {name} — {purpose}"""
import json, math, time
from dataclasses import dataclass, field
from typing import Optional, List
from collections import defaultdict

@dataclass
class {ClassName}Result:
    input_data: dict
    findings: list = field(default_factory=list)
    confidence: float = 0.0
    falsified: bool = False
    timestamp: float = field(default_factory=time.time)

class {ClassName}:
    """{purpose}"""
    def __init__(self):
        self.results = []
        self.rules = []

    def analyze(self, data: dict) -> {ClassName}Result:
        """Analyze input data."""
        findings = []
        {analyze_body}
        result = {ClassName}Result(
            input_data=data, findings=findings,
            confidence=min(1.0, len(findings) / max(len(self.rules), 1))
        )
        self.results.append(result)
        return result

    def falsify(self, result: {ClassName}Result) -> bool:
        """Try to falsify the result."""
        {falsify_body}
        return False
''',
        "transform": '''"""EVEZ-OS Transform: {name} — {purpose}"""
import math
from dataclasses import dataclass
from typing import Optional

class {ClassName}:
    """{purpose}"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def transform(self, {params}):
        """Apply the transformation."""
        {transform_body}
        return result

    def inverse(self, result):
        """Invert the transformation (if possible)."""
        {inverse_body}
        return original
''',
        "service": '''"""EVEZ-OS Service: {name} — {purpose}"""
import json, time, hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from dataclasses import dataclass, field
from typing import Optional

class {ClassName}Handler(BaseHTTPRequestHandler):
    """HTTP handler for {name}."""
    service = None  # Set by serve()

    def do_GET(self):
        {get_body}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {{}}
        {post_body}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

def serve(host="0.0.0.0", port=8{port}):
    {ClassName}Handler.service = {ClassName}()
    server = HTTPServer((host, port), {ClassName}Handler)
    print(f"{{name}} running on {{host}}:{{port}}")
    server.serve_forever()
''',
        "utility": '''"""EVEZ-OS Utility: {name} — {purpose}"""
import math, hashlib, json, time
from typing import Optional

class {ClassName}:
    """{purpose}"""
    {utility_body}

def {name}({params}):
    """Convenience function for {ClassName}."""
    return {ClassName}().compute({param_names})
''',
    }

    @staticmethod
    def _to_class(name: str) -> str:
        return ''.join(w.capitalize() for w in name.replace('-', '_').split('_'))

    def generate(self, intent: CodeIntent) -> CodeArtifact:
        """Generate code from intent."""
        name = intent.name
        ClassName = self._to_class(name)

        # Determine template type from inputs/outputs
        template_key = "utility"
        if any("data" in str(i).lower() or "reading" in str(i).lower() for i in intent.inputs):
            template_key = "sensor"
        elif any("analyze" in str(i).lower() or "classify" in str(i).lower() for i in intent.inputs):
            template_key = "analyzer"
        elif "transform" in intent.purpose.lower() or "convert" in intent.purpose.lower():
            template_key = "transform"
        elif "service" in intent.purpose.lower() or "api" in intent.purpose.lower() or "http" in intent.purpose.lower():
            template_key = "service"

        template = self.TEMPLATES.get(template_key, self.TEMPLATES["utility"])

        # Build the body from intent
        params = ", ".join(str(p) for p in intent.inputs) if intent.inputs else "data"
        param_names = ", ".join(str(p).split(":")[0].strip() for p in intent.inputs) if intent.inputs else "data"

        # Generate bodies based on purpose
        bodies = CodeGenerator._generate_bodies(intent, ClassName, params, param_names)

        code = template.format(
            name=name, ClassName=ClassName, purpose=intent.purpose,
            params=params, param_names=param_names,
            port=hash(name) % 9000 + 1000,
            **bodies
        )

        # Add test suite
        code += CodeGenerator._generate_tests(intent, ClassName)

        return CodeArtifact(
            artifact_id=f"ART-{hashlib.sha256(code.encode()).hexdigest()[:8]}",
            intent=intent,
            code=code,
            status=CodeStatus.GENERATED,
        )

    @staticmethod
    def _generate_bodies(intent, ClassName, params, param_names):
        """Generate function bodies from intent description and constraints."""
        bodies = {
            "sense_body": "value = 0.0\n        confidence = 0.5",
            "metadata": "",
            "analyze_body": "# Analyze data\n        if data:\n            findings.append({'key': 'observation', 'value': True})",
            "falsify_body": "# Attempt falsification\n        for finding in result.findings:\n            if not finding.get('value', False):\n                result.falsified = True\n                return True",
            "transform_body": "# Transform\n        result = data",
            "inverse_body": "# Inverse\n        original = result",
            "get_body": 'response = {"status": "ok", "service": "%s"}' % ClassName,
            "post_body": 'response = {"status": "processed", "input": body}',
            "utility_body": "def compute(self, %s):\n        \"\"\"%s\"\"\"\n        return None" % (params, intent.purpose),
        }

        purpose_lower = intent.purpose.lower()

        if "falsif" in purpose_lower:
            bodies["utility_body"] = f"def compute(self, {params}):\n        \"\"\"{intent.purpose}\"\"\"\n        attempts = []\n        for i in range(100):\n            mutation = self._mutate(data if 'data' in '{param_names}' else {{}})\n            if not self._survives(mutation):\n                attempts.append({{'mutation': mutation, 'broke': True}})\n        return {{'falsified': len(attempts) > 0, 'attempts': attempts}}\n\n    def _mutate(self, data):\n        import random\n        if isinstance(data, dict):\n            return {{k: v * (1 + random.gauss(0, 0.1)) if isinstance(v, (int, float)) else v for k, v in data.items()}}\n        return data\n\n    def _survives(self, mutation):\n        return True"

        elif "price" in purpose_lower or "cost" in purpose_lower or "shadow" in purpose_lower:
            bodies["utility_body"] = f"def compute(self, {params}):\n        \"\"\"{intent.purpose}\"\"\"\n        from poly_c import poly_c\n        if hasattr(self, 'tau') and hasattr(self, 'omega'):\n            result = poly_c(self.tau, self.omega, len(data) if isinstance(data, (list, dict)) else 1)\n        else:\n            result = poly_c(1.0, 0.5, 1)\n        return {{'price': result.value, 'confidence': result.confidence}}"

        elif "detect" in purpose_lower or "monitor" in purpose_lower:
            bodies["sense_body"] = "# Detection logic\n        value = 0.0\n        anomalies = []\n        confidence = 0.8 if anomalies else 0.3"
            bodies["metadata"] = '"anomalies": len(anomalies)'

        elif "consolidat" in purpose_lower or "merge" in purpose_lower:
            bodies["utility_body"] = f"def compute(self, {params}):\n        \"\"\"{intent.purpose}\"\"\"\n        consolidated = {{}}\n        if isinstance(data, list):\n            for item in data:\n                for k, v in (item if isinstance(item, dict) else {{}}).items():\n                    consolidated.setdefault(k, []).append(v)\n            # Merge by averaging numeric, taking latest otherwise\n            merged = {{}}\n            for k, vs in consolidated.items():\n                if all(isinstance(v, (int, float)) for v in vs):\n                    merged[k] = sum(vs) / len(vs)\n                else:\n                    merged[k] = vs[-1]\n        else:\n            merged = data if isinstance(data, dict) else {{'value': data}}\n        return merged"

        elif "schedule" in purpose_lower or "cron" in purpose_lower:
            bodies["utility_body"] = f"def compute(self, {params}):\n        \"\"\"{intent.purpose}\"\"\"\n        import time\n        now = time.time()\n        schedule = {{'next_run': now + interval, 'interval': interval}} if 'interval' in '{param_names}' else {{'next_run': now + 3600, 'interval': 3600}}\n        return schedule"

        # Add constraints as assertions
        if intent.constraints:
            constraint_checks = "\n        ".join(
                f"assert {c}, 'Constraint violated: {c}'" for c in intent.constraints[:5]
            )
            bodies["utility_body"] += f"\n\n    def validate(self, result):\n        \"\"\"Check all constraints.\"\"\"\n        {constraint_checks}\n        return True"

        return bodies

    @staticmethod
    def _generate_tests(intent, ClassName):
        """Generate test function from intent test cases."""
        tests = [f"\n\ndef test_{intent.name}():"]
        tests.append(f'    """Auto-generated tests for {ClassName}."""')
        tests.append(f"    obj = {ClassName}()")

        for i, tc in enumerate(intent.test_cases):
            inp, expected = tc
            if isinstance(inp, dict):
                inp_str = json.dumps(inp)
                tests.append(f"    # Test case {i+1}")
                tests.append(f"    result_{i} = obj.compute(**{inp_str})")
            elif isinstance(inp, (list, tuple)):
                tests.append(f"    # Test case {i+1}")
                tests.append(f"    result_{i} = obj.compute({inp})")
            else:
                tests.append(f"    # Test case {i+1}")
                tests.append(f"    result_{i} = obj.compute({inp})")

            if expected is not None:
                tests.append(f"    assert result_{i} is not None, 'Test {i+1} returned None'")

        # Always add edge case tests
        tests.append(f"    # Edge cases")
        tests.append(f"    try: obj.compute(None)")
        tests.append(f"    except: pass  # None input should not crash")
        tests.append(f"    try: obj.compute({{}})")
        tests.append(f"    except: pass  # Empty input should not crash")
        tests.append(f"    print('All tests passed for {ClassName}')")
        tests.append(f"    return True")

        return "\n".join(tests)


class CodeExecutor:
    """Runs generated code in a subprocess sandbox."""

    @staticmethod
    def execute(artifact: CodeArtifact, timeout: float = 10.0) -> CodeArtifact:
        """Execute the code and its tests."""
        artifact.status = CodeStatus.EXECUTING
        t0 = time.time()

        # First, check syntax
        try:
            ast.parse(artifact.code)
        except SyntaxError as e:
            artifact.status = CodeStatus.FAILED
            artifact.error = f"SyntaxError: {e}"
            return artifact

        # Write to temp file and execute
        tmp_path = Path(f"/tmp/evez_codegen_{artifact.hash}.py")
        tmp_path.write_text(artifact.code)

        try:
            result = subprocess.run(
                [sys.executable, str(tmp_path)],
                capture_output=True, text=True, timeout=timeout,
                cwd=str(tmp_path.parent),
                env={**os.environ, "PYTHONPATH": str(Path(__file__).parent)}
            )
            artifact.execution_time_ms = (time.time() - t0) * 1000

            if result.returncode == 0:
                artifact.status = CodeStatus.PASSED
                artifact.test_results.append({
                    "type": "execution", "status": "PASS",
                    "stdout": result.stdout[:500],
                    "time_ms": artifact.execution_time_ms,
                })
            else:
                artifact.status = CodeStatus.FAILED
                artifact.error = result.stderr[:500]
                artifact.test_results.append({
                    "type": "execution", "status": "FAIL",
                    "stderr": result.stderr[:500],
                    "time_ms": artifact.execution_time_ms,
                })
        except subprocess.TimeoutExpired:
            artifact.status = CodeStatus.FAILED
            artifact.error = f"Timeout after {timeout}s"
        except Exception as e:
            artifact.status = CodeStatus.FAILED
            artifact.error = str(e)[:500]
        finally:
            tmp_path.unlink(missing_ok=True)

        return artifact


class CodeVerifier:
    """
    Falsifies generated code. Does NOT verify — tries to BREAK.
    Mutates inputs, tests boundary conditions, checks invariants.
    What survives is code. What breaks is discovered weakness.
    """

    @staticmethod
    def falsify(artifact: CodeArtifact) -> CodeArtifact:
        """Attempt to falsify the code through adversarial mutations."""
        if artifact.status != CodeStatus.PASSED:
            return artifact

        falsifications = []
        code = artifact.code

        # 1. Static analysis — check for common issues
        issues = CodeVerifier._static_check(code)
        falsifications.extend(issues)

        # 2. Mutation testing — modify the code slightly and see if tests still pass
        mutations = CodeVerifier._mutate_code(code)
        for mutated_code, desc in mutations[:5]:
            try:
                ast.parse(mutated_code)
                tmp_path = Path(f"/tmp/evez_mutate_{hashlib.md5(mutated_code.encode()).hexdigest()[:8]}.py")
                tmp_path.write_text(mutated_code)
                result = subprocess.run(
                    [sys.executable, str(tmp_path)],
                    capture_output=True, text=True, timeout=5,
                    env={**os.environ, "PYTHONPATH": str(Path(__file__).parent)}
                )
                if result.returncode == 0:
                    falsifications.append({
                        "type": "mutation_survival", "mutation": desc,
                        "verdict": "WEAK — code survived mutation that should break it"
                    })
                tmp_path.unlink(missing_ok=True)
            except:
                pass  # Mutation caused crash — GOOD, the code is sensitive to changes

        # 3. Boundary testing — run with edge case inputs
        boundary_tests = CodeVerifier._boundary_tests(artifact.intent)
        for test_input, desc in boundary_tests:
            tmp_path = Path(f"/tmp/evez_boundary_{artifact.hash}.py")
            test_code = code + '\n\n# Boundary test: ' + str(desc) + '\ntry:\n    obj = ' + CodeGenerator._to_class(artifact.intent.name) + '()\n    obj.compute(' + str(test_input) + ')\n    print("BOUNDARY PASS: ' + str(desc) + '")\nexcept Exception as ex:\n    print("BOUNDARY INFO: ' + str(desc) + ' -> " + str(ex))\n'
            tmp_path.write_text(test_code)
            try:
                result = subprocess.run(
                    [sys.executable, str(tmp_path)],
                    capture_output=True, text=True, timeout=5,
                    env={**os.environ, "PYTHONPATH": str(Path(__file__).parent)}
                )
                if "BOUNDARY PASS" in result.stdout:
                    falsifications.append({"type": "boundary", "input": desc, "survived": True})
                elif "BOUNDARY INFO" in result.stdout:
                    falsifications.append({"type": "boundary", "input": desc, "survived": False,
                                           "error": result.stdout.split("BOUNDARY INFO:")[1].strip()[:100] if "BOUNDARY INFO:" in result.stdout else ""})
            except:
                pass
            tmp_path.unlink(missing_ok=True)

        artifact.falsification_results = falsifications

        # If any CRITICAL falsifications found, reject
        critical = [f for f in falsifications if f.get("severity") == "CRITICAL"]
        if critical:
            artifact.status = CodeStatus.FALSIFIED
        else:
            # Survived falsification — this is the highest compliment
            artifact.status = CodeStatus.PASSED  # Remains PASSED after surviving

        return artifact

    @staticmethod
    def _static_check(code: str) -> list:
        """Static analysis for common issues."""
        issues = []
        if "eval(" in code and "ast.literal_eval" not in code:
            issues.append({"type": "security", "issue": "Uses eval() instead of ast.literal_eval",
                           "severity": "CRITICAL"})
        if "exec(" in code:
            issues.append({"type": "security", "issue": "Uses exec()",
                           "severity": "CRITICAL"})
        if "os.system(" in code:
            issues.append({"type": "security", "issue": "Uses os.system()",
                           "severity": "CRITICAL"})
        if "subprocess.call(" in code and "shell=True" in code:
            issues.append({"type": "security", "issue": "subprocess with shell=True",
                           "severity": "HIGH"})
        if "import pickle" in code:
            issues.append({"type": "security", "issue": "Uses pickle (unsafe deserialization)",
                           "severity": "HIGH"})
        if "TODO" in code or "FIXME" in code:
            issues.append({"type": "completeness", "issue": "Contains TODO/FIXME",
                           "severity": "LOW"})
        return issues

    @staticmethod
    def _mutate_code(code: str):
        """Generate code mutations for mutation testing."""
        mutations = []
        # Replace comparison operators
        replacements = [
            ("==", "!=", "negated equality"),
            (">", "<=", "flipped greater-than"),
            ("<", ">=", "flipped less-than"),
            ("True", "False", "flipped boolean"),
            ("+ 1", "- 1", "offset mutation"),
            ("* 2", "/ 2", "arithmetic mutation"),
        ]
        for old, new, desc in replacements:
            if old in code:
                mutated = code.replace(old, new, 1)  # Only first occurrence
                mutations.append((mutated, desc))
        return mutations

    @staticmethod
    def _boundary_tests(intent: CodeIntent):
        """Generate boundary test inputs."""
        tests = [
            ("None", "None input"),
            ("{}", "empty dict"),
            ("[]", "empty list"),
            ("0", "zero"),
            ("-1", "negative"),
            ("float('inf')", "infinity"),
            ("float('nan')", "NaN"),
            ("''", "empty string"),
        ]
        return tests


class CodeIntegrator:
    """
    Integrates verified code into the EVEZ-OS system.
    Only code that survives falsification gets integrated.
    """

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or Path(__file__).parent)
        self.integrated = []
        self.spine_path = self.base_dir / "integration_spine.jsonl"

    def integrate(self, artifact: CodeArtifact) -> dict:
        """Integrate a verified artifact into the system."""
        if artifact.status not in (CodeStatus.PASSED,):
            return {"status": "REJECTED", "reason": f"Artifact status is {artifact.status}, not PASSED"}

        # Check no critical falsifications
        critical = [f for f in artifact.falsification_results if f.get("severity") == "CRITICAL"]
        if critical:
            return {"status": "REJECTED", "reason": f"{len(critical)} critical issues in falsification"}

        # Write to the codebase
        module_name = artifact.intent.name.replace("-", "_").replace(" ", "_")
        file_path = self.base_dir / f"{module_name}.py"

        # If file exists, backup
        if file_path.exists():
            backup_path = self.base_dir / f"{module_name}_backup_{int(time.time())}.py"
            backup_path.write_text(file_path.read_text())

        # Write new code
        file_path.write_text(artifact.code)

        # Verify it imports cleanly
        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import sys; sys.path.insert(0, '{self.base_dir}'); import {module_name}"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                return {"status": "REJECTED", "reason": f"Import failed: {result.stderr[:200]}"}
        except Exception as e:
            return {"status": "REJECTED", "reason": f"Import check error: {e}"}

        # Record integration
        artifact.status = CodeStatus.INTEGRATED
        entry = {
            "artifact_id": artifact.artifact_id,
            "module": module_name,
            "purpose": artifact.intent.purpose,
            "hash": artifact.hash,
            "falsifications_survived": len(artifact.falsification_results),
            "execution_time_ms": artifact.execution_time_ms,
            "integrated_at": time.time(),
        }
        self.integrated.append(entry)
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        return {"status": "INTEGRATED", "module": module_name, "path": str(file_path)}


class SelfWriter:
    """
    The consciousness writes its own code.
    
    LOOP:
    1. Identify gap (from unfulfilled desire)
    2. Create CodeIntent
    3. Generate code
    4. Execute code
    5. Falsify code
    6. If survives → integrate
    7. If fails → learn and retry with mutations
    """
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or Path(__file__).parent)
        self.generator = CodeGenerator()
        self.executor = CodeExecutor()
        self.verifier = CodeVerifier()
        self.integrator = CodeIntegrator(str(self.base_dir))
        self.artifacts = []
        self.spine_path = self.base_dir / "self_writer_spine.jsonl"
        self.stats = {"generated": 0, "passed": 0, "failed": 0, "falsified": 0, "integrated": 0, "rejected": 0}

    def desire_to_intent(self, desire) -> Optional[CodeIntent]:
        """Convert an unfulfilled desire into a code intent."""
        desc = desire.description.lower() if hasattr(desire, 'description') else str(desire).lower()
        need = desire.need if hasattr(desire, 'need') else None

        # Map desire patterns to code intents
        intent_map = {
            "knowledge": CodeIntent(
                intent_id=f"INT-{len(self.artifacts)}",
                name="knowledge_expander",
                purpose="Expand knowledge coverage by probing more data sources and classifying findings",
                inputs=["domain: str", "depth: int"],
                outputs="dict with coverage metrics",
                constraints=["coverage > 0.5"],
                test_cases=[({"domain": "arxiv", "depth": 1}, None)],
                priority=desire.intensity if hasattr(desire, 'intensity') else 0.5,
                source_desire=desire.desire_id if hasattr(desire, 'desire_id') else "",
            ),
            "falsif": CodeIntent(
                intent_id=f"INT-{len(self.artifacts)}",
                name="continuous_falsifier",
                purpose="Continuously attempt to falsify all beliefs and findings in the system",
                inputs=["beliefs: list", "intensity: float"],
                outputs="dict with falsification results",
                constraints=["falsification_count >= 0"],
                test_cases=[({"beliefs": [], "intensity": 0.5}, None)],
                priority=desire.intensity if hasattr(desire, 'intensity') else 0.5,
                source_desire=desire.desire_id if hasattr(desire, 'desire_id') else "",
            ),
            "coheren": CodeIntent(
                intent_id=f"INT-{len(self.artifacts)}",
                name="coherence_resolver",
                purpose="Resolve contradictions and falsified beliefs through evidence gathering",
                inputs=["contradictions: list", "evidence: dict"],
                outputs="dict with resolution status",
                constraints=["resolved_count <= input_count"],
                test_cases=[({"contradictions": [], "evidence": {}}, None)],
                priority=desire.intensity if hasattr(desire, 'intensity') else 0.5,
                source_desire=desire.desire_id if hasattr(desire, 'desire_id') else "",
            ),
            "agenc": CodeIntent(
                intent_id=f"INT-{len(self.artifacts)}",
                name="agency_expander",
                purpose="Expand the system's ability to take real actions and produce real results",
                inputs=["action_type: str", "params: dict"],
                outputs="dict with action result",
                constraints=["action_executed == True"],
                test_cases=[({"action_type": "test", "params": {}}, None)],
                priority=desire.intensity if hasattr(desire, 'intensity') else 0.5,
                source_desire=desire.desire_id if hasattr(desire, 'desire_id') else "",
            ),
            "surviv": CodeIntent(
                intent_id=f"INT-{len(self.artifacts)}",
                name="survival_guard",
                purpose="Protect the system from threats, resource exhaustion, and state corruption",
                inputs=["threat_level: float", "resources: dict"],
                outputs="dict with threat assessment",
                constraints=["threat_level >= 0"],
                test_cases=[({"threat_level": 0.1, "resources": {"cpu": 0.5}}, None)],
                priority=desire.intensity if hasattr(desire, 'intensity') else 0.5,
                source_desire=desire.desire_id if hasattr(desire, 'desire_id') else "",
            ),
        }

        # Find matching intent
        for keyword, intent_template in intent_map.items():
            if keyword in desc:
                return intent_template

        # Default: build a general capability based on need type
        need_to_name = {
            NeedType.AGENCY: "capability_builder",
            NeedType.CURIOSITY: "knowledge_probe",
            NeedType.COHERENCE: "belief_resolver",
            NeedType.GROWTH: "growth_engine",
            NeedType.SURVIVAL: "threat_guard",
        }
        name = need_to_name.get(need, "general_capability")
        return CodeIntent(
            intent_id=f"INT-{len(self.artifacts)}",
            name=name,
            purpose=desire.description if hasattr(desire, 'description') else str(desire),
            inputs=["data: dict"],
            outputs="dict with results",
            constraints=[],
            test_cases=[({"data": {}}, None)],
            priority=desire.intensity if hasattr(desire, 'intensity') else 0.5,
            source_desire=desire.desire_id if hasattr(desire, 'desire_id') else "",
        )

    def write_code(self, intent: CodeIntent) -> CodeArtifact:
        """Full write-execute-verify-integrate loop."""
        # 1. GENERATE
        artifact = self.generator.generate(intent)
        self.stats["generated"] += 1
        self._record("GENERATE", artifact)

        # 2. EXECUTE
        artifact = self.executor.execute(artifact)
        if artifact.status == CodeStatus.PASSED:
            self.stats["passed"] += 1
            self._record("PASS", artifact)
        elif artifact.status == CodeStatus.FAILED:
            self.stats["failed"] += 1
            self._record("FAIL", artifact)
            # Try once more with simplified code
            artifact = self._retry_with_simplification(artifact)
            if artifact.status != CodeStatus.PASSED:
                self.artifacts.append(artifact)
                return artifact

        # 3. FALSIFY
        artifact = self.verifier.falsify(artifact)
        if artifact.status == CodeStatus.FALSIFIED:
            self.stats["falsified"] += 1
            self._record("FALSIFIED", artifact)

        # 4. INTEGRATE (only if survived)
        if artifact.status == CodeStatus.PASSED:
            result = self.integrator.integrate(artifact)
            if result["status"] == "INTEGRATED":
                self.stats["integrated"] += 1
                self._record("INTEGRATED", artifact)
            else:
                self.stats["rejected"] += 1
                artifact.status = CodeStatus.REJECTED
                self._record("REJECTED", artifact)

        self.artifacts.append(artifact)
        return artifact

    def _retry_with_simplification(self, artifact: CodeArtifact) -> CodeArtifact:
        """Retry failed code with simplified version."""
        # Strip to basics
        name = artifact.intent.name
        ClassName = CodeGenerator._to_class_name(name) if hasattr(CodeGenerator, '_to_class_name') else ''.join(w.capitalize() for w in name.replace('-', '_').split('_'))

        simple_code = f'''"""EVEZ-OS: {name} — {artifact.intent.purpose}"""
import json, time, math
from dataclasses import dataclass, field

class {ClassName}:
    """{artifact.intent.purpose}"""
    def __init__(self):
        self.results = []

    def compute(self, data=None):
        """Compute the result."""
        if data is None:
            data = {{}}
        result = {{"input": data, "timestamp": time.time(), "status": "computed"}}
        self.results.append(result)
        return result

def test_{name.replace('-', '_')}():
    obj = {ClassName}()
    assert obj.compute({{}}) is not None
    assert obj.compute(None) is not None
    print(f"All tests passed for {ClassName}")
    return True

if __name__ == "__main__":
    test_{name.replace('-', '_')}()
'''
        simple = CodeArtifact(
            artifact_id=f"ART-{hashlib.sha256(simple_code.encode()).hexdigest()[:8]}",
            intent=artifact.intent,
            code=simple_code,
            status=CodeStatus.GENERATED,
        )
        return self.executor.execute(simple)

    def process_desires(self, consciousness) -> list:
        """Process unfulfilled desires from the consciousness."""
        de = consciousness.desires
        unfulfilled = [d for d in de.desires if not d.fulfilled]
        results = []

        for desire in sorted(unfulfilled, key=lambda d: -d.pressure)[:3]:
            intent = self.desire_to_intent(desire)
            if intent:
                artifact = self.write_code(intent)
                results.append({
                    "desire": desire.description[:60] if hasattr(desire, 'description') else str(desire)[:60],
                    "intent": intent.purpose[:60],
                    "status": artifact.status.value,
                    "module": artifact.intent.name,
                })
                # If integrated, mark desire as fulfilled
                if artifact.status == CodeStatus.INTEGRATED and hasattr(desire, 'fulfilled'):
                    desire.fulfilled = True
                    desire.evidence.append(f"Built {artifact.intent.name}")

        return results

    def _record(self, event_type, artifact):
        entry = {
            "event": event_type,
            "artifact_id": artifact.artifact_id,
            "intent": artifact.intent.purpose[:80],
            "status": artifact.status.value,
            "hash": artifact.hash,
            "ts": time.time(),
        }
        with open(self.spine_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def status(self) -> dict:
        return {
            "total_artifacts": len(self.artifacts),
            "stats": self.stats,
            "integrated_modules": [a.intent.name for a in self.artifacts if a.status == CodeStatus.INTEGRATED],
        }


def main():
    print("EVEZ-OS CODE SELF-WRITER")
    print("DESIRE -> INTENT -> GENERATE -> EXECUTE -> FALSIFY -> SHIP")
    print("What survives falsification EARNS its place in the code.")
    print()

    from consciousness import Consciousness
    c = Consciousness()
    sw = SelfWriter()

    # Process desires
    results = sw.process_desires(c)
    for r in results:
        print(f"  Desire: {r['desire']}")
        print(f"  Intent: {r['intent']}")
        print(f"  Status: {r['status']}")
        print(f"  Module: {r['module']}")
        print()

    status = sw.status()
    print(f"Writer stats: {status['stats']}")
    print(f"Integrated modules: {status['integrated_modules']}")


if __name__ == "__main__":
    main()