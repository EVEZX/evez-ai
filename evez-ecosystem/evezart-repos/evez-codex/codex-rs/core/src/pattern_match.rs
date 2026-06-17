use serde::Deserialize;
use serde::Serialize;
use std::cmp::Ordering;
use std::collections::HashMap;
use std::collections::HashSet;

const TEXT_WEIGHT: f64 = 0.4;
const DOMAIN_WEIGHT: f64 = 0.5;
const OUTCOME_WEIGHT: f64 = 0.1;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PatternDefinition {
    pub id: String,
    pub trigger: String,
    pub invariant: String,
    #[serde(default)]
    pub domain_signature: Vec<f64>,
    #[serde(default)]
    pub evidence_refs: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PatternMatchEvent {
    pub trigger: String,
    pub invariant: String,
    #[serde(default)]
    pub domain_signature: Vec<f64>,
    #[serde(default)]
    pub tests: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PatternMatchResult {
    pub pattern_id: String,
    pub text_score: f64,
    pub domain_score: f64,
    pub outcome_affinity: f64,
    pub total: f64,
    pub rationale: String,
}

pub fn rank_patterns(
    event: &PatternMatchEvent,
    patterns: &[PatternDefinition],
    limit: usize,
) -> Vec<PatternMatchResult> {
    let event_text = format!(
        "{trigger} {invariant}",
        trigger = event.trigger,
        invariant = event.invariant
    );
    let event_tf = term_frequencies(&tokenize(&event_text));

    let mut results: Vec<PatternMatchResult> = patterns
        .iter()
        .map(|pattern| {
            let pattern_text =
                format!("{trigger} {invariant}", trigger = pattern.trigger, invariant = pattern.invariant);
            let text_score = cosine_similarity_tf(&event_tf, &term_frequencies(&tokenize(&pattern_text)));
            let domain_score = cosine_similarity_vec(&event.domain_signature, &pattern.domain_signature);
            let outcome_affinity = outcome_affinity(&event.tests, &pattern.evidence_refs);
            let total = (text_score * TEXT_WEIGHT
                + domain_score * DOMAIN_WEIGHT
                + outcome_affinity * OUTCOME_WEIGHT)
                .clamp(0.0, 1.0);
            let rationale = format!(
                "text={text_score:.2} domain={domain_score:.2} outcome_affinity={outcome_affinity:.2} total={total:.2}",
                text_score = text_score,
                domain_score = domain_score,
                outcome_affinity = outcome_affinity,
                total = total
            );
            PatternMatchResult {
                pattern_id: pattern.id.clone(),
                text_score,
                domain_score,
                outcome_affinity,
                total,
                rationale,
            }
        })
        .collect();

    results.sort_by(|left, right| {
        right
            .total
            .partial_cmp(&left.total)
            .unwrap_or(Ordering::Equal)
            .then_with(|| left.pattern_id.cmp(&right.pattern_id))
    });

    if results.len() > limit {
        results.truncate(limit);
    }

    results
}

fn tokenize(text: &str) -> Vec<String> {
    text.split(|ch: char| !ch.is_alphanumeric())
        .filter(|token| !token.is_empty())
        .map(|token| token.to_ascii_lowercase())
        .collect()
}

fn term_frequencies(tokens: &[String]) -> HashMap<String, f64> {
    let mut counts = HashMap::new();
    for token in tokens {
        let entry = counts.entry(token.clone()).or_insert(0.0);
        *entry += 1.0;
    }
    counts
}

fn cosine_similarity_tf(left: &HashMap<String, f64>, right: &HashMap<String, f64>) -> f64 {
    if left.is_empty() || right.is_empty() {
        return 0.0;
    }

    let mut dot = 0.0;
    for (token, value) in left {
        if let Some(other) = right.get(token) {
            dot += value * other;
        }
    }

    let left_norm = left.values().map(|value| value * value).sum::<f64>().sqrt();
    let right_norm = right
        .values()
        .map(|value| value * value)
        .sum::<f64>()
        .sqrt();
    if left_norm == 0.0 || right_norm == 0.0 {
        0.0
    } else {
        dot / (left_norm * right_norm)
    }
}

fn cosine_similarity_vec(left: &[f64], right: &[f64]) -> f64 {
    let len = left.len().min(right.len());
    if len == 0 {
        return 0.0;
    }

    let mut dot = 0.0;
    let mut left_norm = 0.0;
    let mut right_norm = 0.0;

    for idx in 0..len {
        let left_value = left[idx];
        let right_value = right[idx];
        dot += left_value * right_value;
        left_norm += left_value * left_value;
        right_norm += right_value * right_value;
    }

    if left_norm == 0.0 || right_norm == 0.0 {
        0.0
    } else {
        dot / (left_norm.sqrt() * right_norm.sqrt())
    }
}

fn outcome_affinity(tests: &[String], evidence_refs: &[String]) -> f64 {
    if tests.is_empty() || evidence_refs.is_empty() {
        return 0.0;
    }

    let mut best = 0.0;
    for test in tests {
        let test_tokens = token_set(test);
        for evidence in evidence_refs {
            let score = jaccard_similarity(&test_tokens, &token_set(evidence));
            if score > best {
                best = score;
            }
        }
    }
    best
}

fn token_set(text: &str) -> HashSet<String> {
    tokenize(text).into_iter().collect()
}

fn jaccard_similarity(left: &HashSet<String>, right: &HashSet<String>) -> f64 {
    if left.is_empty() || right.is_empty() {
        return 0.0;
    }

    let intersection = left.intersection(right).count() as f64;
    let union = (left.len() + right.len()) as f64 - intersection;
    if union == 0.0 {
        0.0
    } else {
        intersection / union
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;

    #[test]
    fn ranks_patterns_by_scores() {
        let event = PatternMatchEvent {
            trigger: "compile error".to_string(),
            invariant: "missing import".to_string(),
            domain_signature: vec![1.0, 0.0, 0.0],
            tests: vec!["test_parser failed".to_string()],
        };

        let patterns = vec![
            PatternDefinition {
                id: "pattern-a".to_string(),
                trigger: "compile error".to_string(),
                invariant: "missing import".to_string(),
                domain_signature: vec![0.9, 0.1, 0.0],
                evidence_refs: vec!["test_parser failed".to_string()],
            },
            PatternDefinition {
                id: "pattern-b".to_string(),
                trigger: "runtime error".to_string(),
                invariant: "panic".to_string(),
                domain_signature: vec![0.0, 1.0, 0.0],
                evidence_refs: vec!["test_runtime failed".to_string()],
            },
        ];

        let results = rank_patterns(&event, &patterns, 2);
        let ids: Vec<&str> = results
            .iter()
            .map(|result| result.pattern_id.as_str())
            .collect();
        assert_eq!(ids, vec!["pattern-a", "pattern-b"]);
    }

    #[test]
    fn ranking_returns_rationale_and_descending_totals() {
        let event = PatternMatchEvent {
            trigger: "auth timeout".to_string(),
            invariant: "session token expired".to_string(),
            domain_signature: vec![0.8, 0.2],
            tests: vec!["auth timeout integration test".to_string()],
        };

        let patterns = vec![
            PatternDefinition {
                id: "strong-match".to_string(),
                trigger: "auth timeout".to_string(),
                invariant: "session token expired".to_string(),
                domain_signature: vec![0.9, 0.1],
                evidence_refs: vec!["auth timeout integration test".to_string()],
            },
            PatternDefinition {
                id: "weak-match".to_string(),
                trigger: "render glitch".to_string(),
                invariant: "css mismatch".to_string(),
                domain_signature: vec![0.0, 1.0],
                evidence_refs: vec!["ui snapshot".to_string()],
            },
        ];

        let results = rank_patterns(&event, &patterns, 2);
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].pattern_id, "strong-match".to_string());
        assert_eq!(results[1].pattern_id, "weak-match".to_string());
        assert!(results[0].total >= results[1].total);
        assert_eq!(
            results[0].rationale.contains("text="),
            true,
            "rationale includes text score"
        );
        assert_eq!(
            results[0].rationale.contains("domain="),
            true,
            "rationale includes domain score"
        );
        assert_eq!(
            results[0].rationale.contains("outcome_affinity="),
            true,
            "rationale includes outcome affinity"
        );
        assert_eq!(
            results[0].rationale.contains("total="),
            true,
            "rationale includes total"
        );
    }

    #[test]
    fn empty_domain_signature_scores_zero() {
        let score = cosine_similarity_vec(&[], &[1.0, 0.5]);
        assert_eq!(score, 0.0);
    }
}
