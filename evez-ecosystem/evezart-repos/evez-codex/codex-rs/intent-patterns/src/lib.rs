use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;

pub type RecordId = u64;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub struct IntentToken {
    pub text: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub struct Hypothesis {
    pub summary: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub struct CaptureTest {
    pub description: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub struct Outcome {
    pub summary: String,
    pub success: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub struct CompiledPattern {
    pub intent: String,
    pub outcome: String,
    pub tokens: Vec<String>,
}

impl CompiledPattern {
    pub fn compile(intent: &IntentToken, outcome: &Outcome) -> Self {
        let tokens = tokenize(&intent.text);
        Self {
            intent: intent.text.clone(),
            outcome: outcome.summary.clone(),
            tokens,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub enum RecordKind {
    IntentToken,
    Hypothesis,
    Test,
    Outcome,
    CompiledPattern,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "type", content = "data")]
pub enum CapturePayload {
    IntentToken(IntentToken),
    Hypothesis(Hypothesis),
    Test(CaptureTest),
    Outcome(Outcome),
    CompiledPattern(CompiledPattern),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub struct CaptureRecord {
    pub id: RecordId,
    pub kind: RecordKind,
    pub links: Vec<RecordId>,
    pub payload: CapturePayload,
}

#[derive(Debug, Clone)]
pub struct CaptureFlow {
    records: Vec<CaptureRecord>,
    next_id: RecordId,
    intent_id: RecordId,
}

impl CaptureFlow {
    pub fn new(intent_token: IntentToken) -> Self {
        let mut flow = Self {
            records: Vec::new(),
            next_id: 1,
            intent_id: 0,
        };
        let intent_id = flow.push_record(RecordKind::IntentToken, Vec::new(), CapturePayload::IntentToken(intent_token));
        flow.intent_id = intent_id;
        flow
    }

    pub fn add_hypothesis(&mut self, hypothesis: Hypothesis) -> RecordId {
        self.push_record(
            RecordKind::Hypothesis,
            vec![self.intent_id],
            CapturePayload::Hypothesis(hypothesis),
        )
    }

    pub fn add_test(&mut self, hypothesis_id: RecordId, test: CaptureTest) -> RecordId {
        self.push_record(
            RecordKind::Test,
            vec![hypothesis_id],
            CapturePayload::Test(test),
        )
    }

    pub fn add_outcome(&mut self, test_id: RecordId, outcome: Outcome) -> RecordId {
        self.push_record(
            RecordKind::Outcome,
            vec![test_id],
            CapturePayload::Outcome(outcome),
        )
    }

    pub fn add_compiled_pattern(&mut self, outcome_id: RecordId, pattern: CompiledPattern) -> RecordId {
        self.push_record(
            RecordKind::CompiledPattern,
            vec![outcome_id],
            CapturePayload::CompiledPattern(pattern),
        )
    }

    pub fn records(&self) -> &[CaptureRecord] {
        &self.records
    }

    fn push_record(&mut self, kind: RecordKind, links: Vec<RecordId>, payload: CapturePayload) -> RecordId {
        let id = self.next_id;
        self.next_id += 1;
        self.records.push(CaptureRecord {
            id,
            kind,
            links,
            payload,
        });
        id
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PatternMatch {
    pub pattern: CompiledPattern,
    pub score: usize,
    pub rationale: String,
}

#[derive(Debug, Default)]
pub struct PatternMatcher;

impl PatternMatcher {
    pub fn rank(&self, query: &str, patterns: &[CompiledPattern]) -> Vec<PatternMatch> {
        let query_tokens = tokenize(query);
        let query_set: HashSet<&str> = query_tokens.iter().map(String::as_str).collect();
        let mut matches: Vec<PatternMatch> = patterns
            .iter()
            .cloned()
            .map(|pattern| {
                let (score, rationale) = score_pattern(&query_set, &pattern);
                PatternMatch {
                    pattern,
                    score,
                    rationale,
                }
            })
            .collect();

        matches.sort_by(|left, right| right.score.cmp(&left.score));
        matches
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Covenant {
    allowed_actions: HashSet<String>,
}

impl Covenant {
    pub fn new<I>(allowed_actions: I) -> Self
    where
        I: IntoIterator<Item = String>,
    {
        let allowed_actions = allowed_actions.into_iter().collect();
        Self { allowed_actions }
    }

    pub fn enforce(&self, action: &str) -> Result<(), CovenantError> {
        if self.allowed_actions.contains(action) {
            Ok(())
        } else {
            Err(CovenantError {
                action: action.to_string(),
            })
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CovenantError {
    pub action: String,
}

pub fn capture_schema() -> serde_json::Value {
    let schema = schemars::schema_for!(CaptureRecord);
    serde_json::to_value(schema).expect("schema should serialize")
}

fn tokenize(text: &str) -> Vec<String> {
    let mut cleaned = String::with_capacity(text.len());
    for ch in text.chars() {
        if ch.is_alphanumeric() {
            cleaned.push(ch.to_ascii_lowercase());
        } else {
            cleaned.push(' ');
        }
    }
    cleaned
        .split_whitespace()
        .map(str::to_string)
        .collect()
}

fn score_pattern(query_set: &HashSet<&str>, pattern: &CompiledPattern) -> (usize, String) {
    let matched: Vec<&str> = pattern
        .tokens
        .iter()
        .map(String::as_str)
        .filter(|token| query_set.contains(*token))
        .collect();
    let score = matched.len();
    let rationale = if matched.is_empty() {
        "no shared intent tokens".to_string()
    } else {
        format!("matched tokens: {}", matched.join(", "))
    };
    (score, rationale)
}

#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;

    #[test]
    fn schema_creation_includes_core_fields() {
        let schema = capture_schema();
        let properties = schema
            .get("properties")
            .and_then(serde_json::Value::as_object)
            .expect("schema should include properties");
        assert_eq!(properties.contains_key("id"), true);
        assert_eq!(properties.contains_key("kind"), true);
    }

    #[test]
    fn capture_flow_links_records() {
        let intent = IntentToken {
            text: "pressed play".to_string(),
        };
        let mut flow = CaptureFlow::new(intent);
        let hypothesis_id = flow.add_hypothesis(Hypothesis {
            summary: "bluetooth output not selected".to_string(),
        });
        let test_id = flow.add_test(
            hypothesis_id,
            CaptureTest {
                description: "switch output to headset".to_string(),
            },
        );
        let outcome_id = flow.add_outcome(
            test_id,
            Outcome {
                summary: "audio routed to bluetooth".to_string(),
                success: true,
            },
        );
        let pattern_id = flow.add_compiled_pattern(
            outcome_id,
            CompiledPattern {
                intent: "pressed play".to_string(),
                outcome: "audio routed to bluetooth".to_string(),
                tokens: vec!["pressed".to_string(), "play".to_string()],
            },
        );

        let records = flow.records();
        let hypothesis = records
            .iter()
            .find(|record| record.id == hypothesis_id)
            .expect("hypothesis record");
        let test = records
            .iter()
            .find(|record| record.id == test_id)
            .expect("test record");
        let outcome = records
            .iter()
            .find(|record| record.id == outcome_id)
            .expect("outcome record");
        let pattern = records
            .iter()
            .find(|record| record.id == pattern_id)
            .expect("pattern record");

        assert_eq!(hypothesis.links.len(), 1);
        assert_eq!(test.links, vec![hypothesis_id]);
        assert_eq!(outcome.links, vec![test_id]);
        assert_eq!(pattern.links, vec![outcome_id]);
    }

    #[test]
    fn pattern_match_ranks_with_rationale() {
        let matcher = PatternMatcher::default();
        let patterns = vec![
            CompiledPattern {
                intent: "pressed play".to_string(),
                outcome: "audio routed to bluetooth".to_string(),
                tokens: vec!["pressed".to_string(), "play".to_string()],
            },
            CompiledPattern {
                intent: "paused playback".to_string(),
                outcome: "audio muted".to_string(),
                tokens: vec!["paused".to_string(), "playback".to_string()],
            },
        ];

        let results = matcher.rank("hit play on bluetooth", &patterns);
        assert_eq!(results.len(), 2);
        assert_eq!(results[0].pattern.intent, "pressed play");
        assert_eq!(results[0].score, 1);
        assert_eq!(results[0].rationale.contains("matched tokens"), true);
    }

    #[test]
    fn covenant_refuses_out_of_scope_actions() {
        let covenant = Covenant::new(["route_audio".to_string()]);
        let err = covenant
            .enforce("delete_files")
            .expect_err("should refuse out-of-scope action");
        assert_eq!(err.action, "delete_files");
    }
}
