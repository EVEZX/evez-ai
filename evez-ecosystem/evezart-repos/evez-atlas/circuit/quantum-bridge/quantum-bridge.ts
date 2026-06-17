export interface PatchDiff {
  description: string;
  files: string[];
  label?: string;
}

export interface PatchHypothesis {
  id: string;
  prior: number;
  diff: PatchDiff;
}

export interface OracleScore {
  hypothesisId: string;
  score: number;
  signals: Record<string, number>;
}

export class QuantumBridge {
  normalizePriors(hypotheses: PatchHypothesis[]): PatchHypothesis[] {
    const sum = hypotheses.reduce((acc, h) => acc + h.prior, 0) || 1;
    return hypotheses.map(h => ({ ...h, prior: h.prior / sum }));
  }

  collapse(
    hypotheses: PatchHypothesis[],
    scores: OracleScore[]
  ): PatchHypothesis | null {
    if (!hypotheses.length || !scores.length) return null;

    const scoreMap = new Map<string, OracleScore>();
    scores.forEach(s => scoreMap.set(s.hypothesisId, s));

    let best: PatchHypothesis | null = null;
    let bestScore = -Infinity;

    for (const h of hypotheses) {
      const oracle = scoreMap.get(h.id);
      if (!oracle) continue;
      const effectiveScore = h.prior * oracle.score;
      if (effectiveScore > bestScore) {
        bestScore = effectiveScore;
        best = h;
      }
    }

    return best;
  }
}
