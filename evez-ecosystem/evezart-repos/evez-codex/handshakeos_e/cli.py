import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


def _prompt_text(label: str, allow_empty: bool = False) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value or allow_empty:
            return value
        print("Please provide a value.")


def _prompt_choice(label: str, options: Iterable[str]) -> str:
    options_list = list(options)
    options_str = "/".join(options_list)
    while True:
        value = input(f"{label} ({options_str}): ").strip().lower()
        if value in options_list:
            return value
        print(f"Please choose one of: {options_str}.")


def _prompt_float(label: str, min_value: float = 0.0, max_value: float = 1.0) -> float:
    while True:
        raw = input(f"{label} ({min_value}-{max_value}): ").strip()
        try:
            value = float(raw)
        except ValueError:
            print("Please enter a number.")
            continue
        if min_value <= value <= max_value:
            return value
        print(f"Value must be between {min_value} and {max_value}.")


def _prompt_int(label: str, min_value: int, max_value: int) -> int:
    while True:
        raw = input(f"{label} ({min_value}-{max_value}): ").strip()
        try:
            value = int(raw)
        except ValueError:
            print("Please enter an integer.")
            continue
        if min_value <= value <= max_value:
            return value
        print(f"Value must be between {min_value} and {max_value}.")


def _parse_mixture_vector(raw: str) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError("Mixture vector must be JSON (list of objects).")
    if not isinstance(data, list):
        raise ValueError("Mixture vector must be a JSON list.")
    cleaned: list[dict[str, Any]] = []
    for entry in data:
        if not isinstance(entry, dict):
            raise ValueError("Each mixture entry must be an object.")
        domain = entry.get("domain")
        weight = entry.get("weight")
        if not isinstance(domain, str) or not domain:
            raise ValueError("Each mixture entry needs a non-empty 'domain' string.")
        if not isinstance(weight, (int, float)):
            raise ValueError("Each mixture entry needs a numeric 'weight'.")
        cleaned.append({"domain": domain, "weight": float(weight)})
    return cleaned


def _prompt_mixture_vector(label: str) -> list[dict[str, Any]]:
    while True:
        raw = input(
            f"{label} (JSON list of {{domain, weight}}, empty for []): "
        ).strip()
        try:
            return _parse_mixture_vector(raw)
        except ValueError as exc:
            print(str(exc))


def _parse_evidence_refs(raw: str) -> list[str]:
    if not raw:
        return []
    if raw.lstrip().startswith("["):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Evidence refs must be JSON list or comma-separated.") from exc
        if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
            raise ValueError("Evidence refs JSON must be a list of strings.")
        return [item.strip() for item in data if item.strip()]
    return [item.strip() for item in raw.split(",") if item.strip()]


def _prompt_evidence_refs(label: str) -> list[str]:
    while True:
        raw = input(f"{label} (comma-separated or JSON list): ").strip()
        try:
            return _parse_evidence_refs(raw)
        except ValueError as exc:
            print(str(exc))


@dataclass(frozen=True)
class HypothesisInput:
    model_type: str
    probability: float
    falsifiers: str
    domain_signature: list[dict[str, Any]]


@dataclass(frozen=True)
class TestInput:
    hypothesis_id: int
    description: str
    result: str
    evidence: str


@dataclass(frozen=True)
class OutcomeInput:
    hypothesis_id: int
    summary: str
    evidence_refs: list[str]


@dataclass(frozen=True)
class PatternSeedInput:
    outcome_id: int
    trigger: str
    invariant: str
    counterexample: str
    best_response: str
    domain_signature: list[dict[str, Any]]
    evidence_refs: list[str]


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal TEXT NOT NULL,
            constraints TEXT NOT NULL,
            success_signal TEXT NOT NULL,
            confidence REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intent_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            domain_signature TEXT NOT NULL,
            FOREIGN KEY (intent_id) REFERENCES intents(id)
        );
        CREATE TABLE IF NOT EXISTS hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observation_id INTEGER NOT NULL,
            model_type TEXT NOT NULL,
            probability REAL NOT NULL,
            falsifiers TEXT NOT NULL,
            domain_signature TEXT NOT NULL,
            FOREIGN KEY (observation_id) REFERENCES observations(id)
        );
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hypothesis_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            result TEXT NOT NULL,
            evidence TEXT NOT NULL,
            FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
        );
        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observation_id INTEGER NOT NULL,
            hypothesis_id INTEGER NOT NULL,
            summary TEXT NOT NULL,
            evidence_refs TEXT NOT NULL,
            FOREIGN KEY (observation_id) REFERENCES observations(id),
            FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
        );
        CREATE TABLE IF NOT EXISTS pattern_seeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            outcome_id INTEGER NOT NULL,
            trigger TEXT NOT NULL,
            invariant TEXT NOT NULL,
            counterexample TEXT NOT NULL,
            best_response TEXT NOT NULL,
            domain_signature TEXT NOT NULL,
            evidence_refs TEXT NOT NULL,
            FOREIGN KEY (outcome_id) REFERENCES outcomes(id)
        );
        """
    )


def capture(db_path: str = "handshakeos_e.sqlite") -> dict[str, Any]:
    """Capture an intent, observation, hypotheses, tests, outcome, and pattern seed."""
    db_file = Path(db_path)
    conn = sqlite3.connect(db_file)
    try:
        _ensure_schema(conn)

        goal = _prompt_text("Intent goal")
        constraints = _prompt_text("Intent constraints")
        success_signal = _prompt_text("Intent success signal")
        confidence = _prompt_float("Intent confidence")

        cursor = conn.execute(
            "INSERT INTO intents (goal, constraints, success_signal, confidence) VALUES (?, ?, ?, ?)",
            (goal, constraints, success_signal, confidence),
        )
        intent_id = cursor.lastrowid

        observation_desc = _prompt_text("Observation description")
        observation_domain_signature = _prompt_mixture_vector(
            "Observation domain signature mixture"
        )
        cursor = conn.execute(
            "INSERT INTO observations (intent_id, description, domain_signature) VALUES (?, ?, ?)",
            (
                intent_id,
                observation_desc,
                json.dumps(observation_domain_signature),
            ),
        )
        observation_id = cursor.lastrowid

        hypothesis_count = _prompt_int("Number of hypotheses", 3, 7)
        hypotheses: list[HypothesisInput] = []
        for index in range(1, hypothesis_count + 1):
            model_type = _prompt_choice(
                f"Hypothesis {index} model type",
                ["me", "we", "they", "system"],
            )
            probability = _prompt_float(f"Hypothesis {index} probability")
            falsifiers = _prompt_text(f"Hypothesis {index} falsifiers")
            domain_signature = _prompt_mixture_vector(
                f"Hypothesis {index} domain signature mixture"
            )
            hypotheses.append(
                HypothesisInput(
                    model_type=model_type,
                    probability=probability,
                    falsifiers=falsifiers,
                    domain_signature=domain_signature,
                )
            )

        hypothesis_ids: list[int] = []
        for hypothesis in hypotheses:
            cursor = conn.execute(
                """
                INSERT INTO hypotheses (observation_id, model_type, probability, falsifiers, domain_signature)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    observation_id,
                    hypothesis.model_type,
                    hypothesis.probability,
                    hypothesis.falsifiers,
                    json.dumps(hypothesis.domain_signature),
                ),
            )
            hypothesis_ids.append(cursor.lastrowid)

        print("Captured hypotheses:")
        for idx, hypothesis_id in enumerate(hypothesis_ids, start=1):
            print(f"  {idx}. hypothesis_id={hypothesis_id}")

        test_hypothesis_index = _prompt_int(
            "Choose hypothesis to test (index)", 1, len(hypothesis_ids)
        )
        test_description = _prompt_text("Test description")
        test_result = _prompt_text("Test result")
        test_evidence = _prompt_text("Test evidence")
        test_input = TestInput(
            hypothesis_id=hypothesis_ids[test_hypothesis_index - 1],
            description=test_description,
            result=test_result,
            evidence=test_evidence,
        )
        cursor = conn.execute(
            "INSERT INTO tests (hypothesis_id, description, result, evidence) VALUES (?, ?, ?, ?)",
            (
                test_input.hypothesis_id,
                test_input.description,
                test_input.result,
                test_input.evidence,
            ),
        )
        test_id = cursor.lastrowid

        print(
            "Provide outcome evidence refs. Include the test reference "
            f"(e.g., test:{test_id})."
        )
        outcome_summary = _prompt_text("Outcome summary")
        outcome_refs = _prompt_evidence_refs("Outcome evidence refs")
        test_ref = f"test:{test_id}"
        if test_ref not in outcome_refs:
            outcome_refs.append(test_ref)
        outcome_input = OutcomeInput(
            hypothesis_id=test_input.hypothesis_id,
            summary=outcome_summary,
            evidence_refs=outcome_refs,
        )
        cursor = conn.execute(
            """
            INSERT INTO outcomes (observation_id, hypothesis_id, summary, evidence_refs)
            VALUES (?, ?, ?, ?)
            """,
            (
                observation_id,
                outcome_input.hypothesis_id,
                outcome_input.summary,
                json.dumps(outcome_input.evidence_refs),
            ),
        )
        outcome_id = cursor.lastrowid

        print("Capture pattern seed.")
        trigger = _prompt_text("Pattern trigger")
        invariant = _prompt_text("Pattern invariant")
        counterexample = _prompt_text("Pattern counterexample")
        best_response = _prompt_text("Pattern best response")
        pattern_domain_signature = _prompt_mixture_vector(
            "Pattern domain signature mixture"
        )
        pattern_evidence_refs = _prompt_evidence_refs("Pattern evidence refs")
        pattern_input = PatternSeedInput(
            outcome_id=outcome_id,
            trigger=trigger,
            invariant=invariant,
            counterexample=counterexample,
            best_response=best_response,
            domain_signature=pattern_domain_signature,
            evidence_refs=pattern_evidence_refs,
        )
        conn.execute(
            """
            INSERT INTO pattern_seeds (
                outcome_id,
                trigger,
                invariant,
                counterexample,
                best_response,
                domain_signature,
                evidence_refs
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                pattern_input.outcome_id,
                pattern_input.trigger,
                pattern_input.invariant,
                pattern_input.counterexample,
                pattern_input.best_response,
                json.dumps(pattern_input.domain_signature),
                json.dumps(pattern_input.evidence_refs),
            ),
        )

        conn.commit()
        return {
            "intent_id": intent_id,
            "observation_id": observation_id,
            "hypothesis_ids": hypothesis_ids,
            "test_id": test_id,
            "outcome_id": outcome_id,
        }
    finally:
        conn.close()


def main() -> int:
    capture()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
