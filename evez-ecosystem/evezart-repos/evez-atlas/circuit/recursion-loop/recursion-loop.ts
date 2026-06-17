import { EventSpine } from "../event-spine/event-spine";
import { PatchHypothesis, QuantumBridge, OracleScore } from "../quantum-bridge/quantum-bridge";

interface Invariant {
  raw: string;
}

interface RecursionConfig {
  target: string;
  invariants: Invariant[];
  maxCycles: number;
}

class BuilderAgent {
  buildHypotheses(target: string, invariants: Invariant[]): PatchHypothesis[] {
    return [
      {
        id: "hypothesis_spine",
        prior: 0.6,
        diff: {
          description: `Add/extend event spine for ${target}`,
          files: ["circuit/event-spine/event-spine.ts"],
          label: "spine"
        }
      },
      {
        id: "hypothesis_tests",
        prior: 0.4,
        diff: {
          description: `Strengthen tests/invariants for ${target}`,
          files: ["tests/", "circuit/recursion-loop/"],
          label: "invariants"
        }
      }
    ];
  }
}

class VerifierAgent {
  evaluate(
    hypotheses: PatchHypothesis[],
    invariants: Invariant[]
  ): OracleScore[] {
    return hypotheses.map(h => {
      const baseScore = h.diff.label === "invariants" ? 0.95 : 0.8;
      const penalty = invariants.length ? 0 : -0.2;
      return {
        hypothesisId: h.id,
        score: baseScore + penalty,
        signals: {
          coverage_proxy: h.diff.label === "invariants" ? 0.9 : 0.7,
          blind_spot_proxy: h.diff.label === "spine" ? 0.9 : 0.8
        }
      };
    });
  }
}

class RecursionArbiter {
  constructor(
    private spine: EventSpine,
    private quantum: QuantumBridge
  ) {}

  run(config: RecursionConfig) {
    const builder = new BuilderAgent();
    const verifier = new VerifierAgent();

    for (let cycle = 0; cycle < config.maxCycles; cycle++) {
      const hypotheses = builder.buildHypotheses(config.target, config.invariants);
      const normalized = this.quantum.normalizePriors(hypotheses);
      const scores = verifier.evaluate(normalized, config.invariants);
      const chosen = this.quantum.collapse(normalized, scores);

      this.spine.append({
        domain: "agents",
        kind: "RECURRENCE_CYCLE",
        payload: {
          target: config.target,
          cycle,
          invariants: config.invariants.map(i => i.raw),
          hypotheses: normalized,
          scores,
          chosen
        }
      });

      if (!chosen) {
        break;
      }

      if (cycle === config.maxCycles - 1) {
        this.spine.append({
          domain: "agents",
          kind: "RECURRENCE_STOP_CONDITION",
          payload: { reason: "max_cycles_reached", target: config.target }
        });
      }
    }
  }
}

if (require.main === module) {
  const target = process.env.ATLAS_TARGET || "Evez666";
  const invariantsRaw = process.env.ATLAS_INVARIANTS || "coverage>0.8,no_blind_spots";
  const invariants: Invariant[] = invariantsRaw
    .split(",")
    .map(s => s.trim())
    .filter(Boolean)
    .map(raw => ({ raw }));

  const spine = new EventSpine();
  const quantum = new QuantumBridge();
  const arbiter = new RecursionArbiter(spine, quantum);

  spine.append({
    domain: "atlas",
    kind: "GENESIS_BOOTSTRAP",
    payload: { version: "v3", schemas_loaded: 5 }
  });

  arbiter.run({
    target,
    invariants,
    maxCycles: 3
  });

  const verification = spine.verify();
  if (!verification.ok) {
    console.error("Spine verification failed:", verification);
    process.exit(1);
  }

  console.log(JSON.stringify(spine.chain, null, 2));
}

export { RecursionArbiter, BuilderAgent, VerifierAgent };
