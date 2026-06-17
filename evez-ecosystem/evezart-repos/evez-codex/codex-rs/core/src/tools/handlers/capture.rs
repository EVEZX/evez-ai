use std::collections::BTreeMap;

use async_trait::async_trait;
use codex_protocol::models::FunctionCallOutputBody;
use codex_protocol::request_user_input::RequestUserInputArgs;
use codex_protocol::request_user_input::RequestUserInputQuestion;
use codex_protocol::request_user_input::RequestUserInputResponse;
use serde::Serialize;

use crate::codex::Session;
use crate::codex::TurnContext;
use crate::function_tool::FunctionCallError;
use crate::tools::context::ToolInvocation;
use crate::tools::context::ToolOutput;
use crate::tools::context::ToolPayload;
use crate::tools::handlers::request_user_input_unavailable_message;
use crate::tools::registry::ToolHandler;
use crate::tools::registry::ToolKind;

const MAX_PROMPT_ATTEMPTS: usize = 5;

pub struct CaptureHandler;

#[derive(Debug, Serialize)]
struct CaptureRecord {
    intent: IntentToken,
    event: EventDetails,
    hypotheses: Vec<Hypothesis>,
    tests: Vec<TestCase>,
    test_results: Vec<TestResult>,
    outcomes: Vec<Outcome>,
    patterns: Vec<Pattern>,
}

#[derive(Debug, Serialize)]
struct IntentToken {
    goal: String,
    constraints: String,
    success_signal: String,
    confidence: f64,
}

#[derive(Debug, Serialize)]
struct EventDetails {
    details: String,
}

#[derive(Debug, Serialize)]
struct Hypothesis {
    id: String,
    statement: String,
    probability: f64,
    falsifiers: Vec<String>,
    domain_signature: Vec<DomainSignatureWeight>,
    test_ids: Vec<String>,
    probability_updates: Vec<ProbabilityUpdate>,
}

#[derive(Debug, Serialize)]
struct DomainSignatureWeight {
    domain: String,
    weight: f64,
}

#[derive(Debug, Serialize)]
struct TestCase {
    id: String,
    description: String,
    procedure: String,
}

#[derive(Debug, Serialize)]
struct TestResult {
    test_id: String,
    result: String,
    notes: String,
    probability_updates: Vec<ProbabilityUpdate>,
}

#[derive(Debug, Serialize, Clone)]
struct ProbabilityUpdate {
    hypothesis_id: String,
    prior: f64,
    posterior: f64,
    evidence_test_id: String,
}

#[derive(Debug, Serialize)]
struct Outcome {
    summary: String,
    evidence_test_ids: Vec<String>,
}

#[derive(Debug, Serialize)]
struct Pattern {
    trigger: String,
    invariant: String,
    counterexample: String,
    best_response: String,
    domain_signature: Vec<DomainSignatureWeight>,
    evidence_test_ids: Vec<String>,
}

#[async_trait]
impl ToolHandler for CaptureHandler {
    fn kind(&self) -> ToolKind {
        ToolKind::Function
    }

    async fn handle(&self, invocation: ToolInvocation) -> Result<ToolOutput, FunctionCallError> {
        let ToolInvocation {
            session,
            turn,
            call_id,
            payload,
            ..
        } = invocation;

        let ToolPayload::Function { .. } = payload else {
            return Err(FunctionCallError::RespondToModel(
                "capture handler received unsupported payload".to_string(),
            ));
        };

        let mode = session.collaboration_mode().await.mode;
        if let Some(message) = request_user_input_unavailable_message(mode) {
            return Err(FunctionCallError::RespondToModel(message));
        }

        let intent = prompt_intent_token(session.as_ref(), turn.as_ref(), &call_id).await?;
        let event = prompt_event_details(session.as_ref(), turn.as_ref(), &call_id).await?;
        let mut hypotheses = prompt_hypotheses(session.as_ref(), turn.as_ref(), &call_id).await?;
        let tests = prompt_tests(session.as_ref(), turn.as_ref(), &call_id).await?;
        prompt_hypothesis_links(
            session.as_ref(),
            turn.as_ref(),
            &call_id,
            &tests,
            &mut hypotheses,
        )
        .await?;
        let test_results = prompt_test_results(
            session.as_ref(),
            turn.as_ref(),
            &call_id,
            &tests,
            &mut hypotheses,
        )
        .await?;
        let outcomes = prompt_outcomes(session.as_ref(), turn.as_ref(), &call_id, &tests).await?;
        let patterns = prompt_patterns(session.as_ref(), turn.as_ref(), &call_id, &tests).await?;

        let record = CaptureRecord {
            intent,
            event,
            hypotheses,
            tests,
            test_results,
            outcomes,
            patterns,
        };

        let content = serde_json::to_string_pretty(&record).map_err(|err| {
            FunctionCallError::Fatal(format!("failed to serialize capture payload: {err}"))
        })?;

        Ok(ToolOutput::Function {
            body: FunctionCallOutputBody::Text(content),
            success: Some(true),
        })
    }
}

pub(crate) fn capture_tool_description() -> String {
    "Capture intent, hypotheses, tests, outcomes, and patterns in a structured trace. Prompts the user for each step and returns a JSON record."
        .to_string()
}

async fn prompt_intent_token(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
) -> Result<IntentToken, FunctionCallError> {
    let mut attempts = 0;
    loop {
        attempts += 1;
        let answers = prompt_questions(
            session,
            turn,
            call_id,
            "Intent token",
            vec![
                ("goal", "What is the goal?"),
                ("constraints", "What constraints must be respected?"),
                ("success_signal", "What signals success?"),
                ("confidence", "What is your confidence (0-1 or 0-100%)?"),
            ],
        )
        .await?;

        let confidence = parse_probability(answers.get("confidence").map(String::as_str))?;
        if confidence.is_none() && attempts < MAX_PROMPT_ATTEMPTS {
            continue;
        }
        let confidence =
            confidence.ok_or_else(|| respond("confidence must be a number between 0 and 1"))?;

        return Ok(IntentToken {
            goal: require_field(&answers, "goal")?,
            constraints: require_field(&answers, "constraints")?,
            success_signal: require_field(&answers, "success_signal")?,
            confidence,
        });
    }
}

async fn prompt_event_details(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
) -> Result<EventDetails, FunctionCallError> {
    let answers = prompt_questions(
        session,
        turn,
        call_id,
        "Event details",
        vec![("details", "Describe the event details.")],
    )
    .await?;
    Ok(EventDetails {
        details: require_field(&answers, "details")?,
    })
}

async fn prompt_hypotheses(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
) -> Result<Vec<Hypothesis>, FunctionCallError> {
    let count = prompt_number_in_range(
        session,
        turn,
        call_id,
        "Hypotheses",
        "How many hypotheses? (3-7)",
        3,
        7,
    )
    .await?;

    let mut hypotheses = Vec::with_capacity(count);
    for index in 0..count {
        let id = format!("H{}", index + 1);
        let answers = prompt_questions(
            session,
            turn,
            call_id,
            "Hypothesis",
            vec![
                ("statement", "Hypothesis statement"),
                ("probability", "Prior probability (0-1 or 0-100%)"),
                (
                    "falsifiers",
                    "Falsifier(s) (comma/semicolon/newline separated)",
                ),
                (
                    "domain_signature",
                    "Domain-signature mixture vector (domain:weight, ...)",
                ),
            ],
        )
        .await?;

        let probability = parse_probability(answers.get("probability").map(String::as_str))?
            .ok_or_else(|| respond("probability must be a number between 0 and 1"))?;
        let falsifiers = split_list(require_field(&answers, "falsifiers")?.as_str())
            .into_iter()
            .collect();
        let domain_signature =
            parse_domain_signature(require_field(&answers, "domain_signature")?.as_str())?;

        hypotheses.push(Hypothesis {
            id,
            statement: require_field(&answers, "statement")?,
            probability,
            falsifiers,
            domain_signature,
            test_ids: Vec::new(),
            probability_updates: Vec::new(),
        });
    }
    Ok(hypotheses)
}

async fn prompt_tests(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
) -> Result<Vec<TestCase>, FunctionCallError> {
    let count = prompt_number_in_range(
        session,
        turn,
        call_id,
        "Tests",
        "How many tests? (1-10)",
        1,
        10,
    )
    .await?;

    let mut tests = Vec::with_capacity(count);
    for index in 0..count {
        let id = format!("T{}", index + 1);
        let answers = prompt_questions(
            session,
            turn,
            call_id,
            "Test",
            vec![
                ("description", "Test description"),
                ("procedure", "Test procedure / steps"),
            ],
        )
        .await?;

        tests.push(TestCase {
            id,
            description: require_field(&answers, "description")?,
            procedure: require_field(&answers, "procedure")?,
        });
    }

    Ok(tests)
}

async fn prompt_hypothesis_links(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    tests: &[TestCase],
    hypotheses: &mut [Hypothesis],
) -> Result<(), FunctionCallError> {
    let test_catalog = tests
        .iter()
        .map(|test| format!("{}: {}", test.id, test.description))
        .collect::<Vec<_>>()
        .join(" | ");

    for hypothesis in hypotheses {
        let question = format!(
            "Link tests for {} ({})? Available: {}",
            hypothesis.id, hypothesis.statement, test_catalog
        );
        let answers = prompt_questions(
            session,
            turn,
            call_id,
            "Hypothesis tests",
            vec![("tests", &question)],
        )
        .await?;
        let ids = split_list(require_field(&answers, "tests")?.as_str());
        let validated = validate_test_ids(&ids, tests)?;
        hypothesis.test_ids = validated;
    }
    Ok(())
}

async fn prompt_test_results(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    tests: &[TestCase],
    hypotheses: &mut [Hypothesis],
) -> Result<Vec<TestResult>, FunctionCallError> {
    let count = prompt_number_in_range(
        session,
        turn,
        call_id,
        "Test results",
        "How many test results are you recording? (1-10)",
        1,
        10,
    )
    .await?;

    let test_catalog = tests
        .iter()
        .map(|test| format!("{}: {}", test.id, test.description))
        .collect::<Vec<_>>()
        .join(" | ");

    let hypothesis_catalog = hypotheses
        .iter()
        .map(|hypothesis| format!("{}: {}", hypothesis.id, hypothesis.statement))
        .collect::<Vec<_>>()
        .join(" | ");

    let mut results = Vec::with_capacity(count);
    for _ in 0..count {
        let answers = prompt_questions(
            session,
            turn,
            call_id,
            "Test result",
            vec![
                ("test_id", &format!("Test id (choose one): {test_catalog}")),
                ("result", "Result (pass/fail/inconclusive)"),
                ("notes", "Notes / observations"),
                (
                    "updates",
                    &format!(
                        "Update hypothesis probabilities as H1=0.7,H2=0.2 (available: {hypothesis_catalog})"
                    ),
                ),
            ],
        )
        .await?;

        let test_id = require_field(&answers, "test_id")?;
        let test_id = validate_test_id(test_id.as_str(), tests)?;
        let updates = parse_probability_updates(
            require_field(&answers, "updates")?.as_str(),
            &test_id,
            hypotheses,
        )?;
        results.push(TestResult {
            test_id,
            result: require_field(&answers, "result")?,
            notes: require_field(&answers, "notes")?,
            probability_updates: updates,
        });
    }
    Ok(results)
}

async fn prompt_outcomes(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    tests: &[TestCase],
) -> Result<Vec<Outcome>, FunctionCallError> {
    let count = prompt_number_in_range(
        session,
        turn,
        call_id,
        "Outcomes",
        "How many outcomes are you recording? (1-5)",
        1,
        5,
    )
    .await?;
    let test_catalog = tests
        .iter()
        .map(|test| format!("{}: {}", test.id, test.description))
        .collect::<Vec<_>>()
        .join(" | ");

    let mut outcomes = Vec::with_capacity(count);
    for _ in 0..count {
        let answers = prompt_questions(
            session,
            turn,
            call_id,
            "Outcome",
            vec![
                ("summary", "Outcome summary"),
                (
                    "evidence",
                    &format!("Evidence test ids (available: {test_catalog})"),
                ),
            ],
        )
        .await?;

        let evidence_ids = validate_test_ids(
            &split_list(require_field(&answers, "evidence")?.as_str()),
            tests,
        )?;
        outcomes.push(Outcome {
            summary: require_field(&answers, "summary")?,
            evidence_test_ids: evidence_ids,
        });
    }
    Ok(outcomes)
}

async fn prompt_patterns(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    tests: &[TestCase],
) -> Result<Vec<Pattern>, FunctionCallError> {
    let count = prompt_number_in_range(
        session,
        turn,
        call_id,
        "Patterns",
        "How many patterns are you recording? (1-5)",
        1,
        5,
    )
    .await?;
    let test_catalog = tests
        .iter()
        .map(|test| format!("{}: {}", test.id, test.description))
        .collect::<Vec<_>>()
        .join(" | ");
    let mut patterns = Vec::with_capacity(count);
    for _ in 0..count {
        let answers = prompt_questions(
            session,
            turn,
            call_id,
            "Pattern",
            vec![
                ("trigger", "Trigger"),
                ("invariant", "Invariant"),
                ("counterexample", "Counterexample"),
                ("best_response", "Best response"),
                (
                    "domain_signature",
                    "Domain-signature mixture vector (domain:weight, ...)",
                ),
                (
                    "evidence",
                    &format!("Evidence test ids (available: {test_catalog})"),
                ),
            ],
        )
        .await?;

        let domain_signature =
            parse_domain_signature(require_field(&answers, "domain_signature")?.as_str())?;
        let evidence_ids = validate_test_ids(
            &split_list(require_field(&answers, "evidence")?.as_str()),
            tests,
        )?;
        patterns.push(Pattern {
            trigger: require_field(&answers, "trigger")?,
            invariant: require_field(&answers, "invariant")?,
            counterexample: require_field(&answers, "counterexample")?,
            best_response: require_field(&answers, "best_response")?,
            domain_signature,
            evidence_test_ids: evidence_ids,
        });
    }
    Ok(patterns)
}

async fn prompt_questions(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    header: &str,
    questions: Vec<(&str, &str)>,
) -> Result<BTreeMap<String, String>, FunctionCallError> {
    let mut attempts = 0;
    loop {
        attempts += 1;
        let args = RequestUserInputArgs {
            questions: questions
                .iter()
                .map(|(id, question)| RequestUserInputQuestion {
                    id: (*id).to_string(),
                    header: header.to_string(),
                    question: (*question).to_string(),
                    is_other: false,
                    is_secret: false,
                    options: None,
                })
                .collect(),
        };
        let response =
            request_user_input(session, turn, &format!("capture-{call_id}-{header}"), args).await?;
        let mut answers = BTreeMap::new();
        for (id, _) in questions.iter() {
            if let Some(value) = extract_answer(&response, id) {
                if !value.is_empty() {
                    answers.insert((*id).to_string(), value);
                }
            }
        }
        if answers.len() == questions.len() || attempts >= MAX_PROMPT_ATTEMPTS {
            return Ok(answers);
        }
    }
}

async fn request_user_input(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    args: RequestUserInputArgs,
) -> Result<RequestUserInputResponse, FunctionCallError> {
    session
        .request_user_input(turn, call_id.to_string(), args)
        .await
        .ok_or_else(|| {
            FunctionCallError::RespondToModel(
                "capture was cancelled before receiving a response".to_string(),
            )
        })
}

fn extract_answer(response: &RequestUserInputResponse, id: &str) -> Option<String> {
    response.answers.get(id).and_then(|answer| {
        answer
            .answers
            .iter()
            .find_map(|entry| entry.strip_prefix("user_note: "))
            .or_else(|| {
                answer
                    .answers
                    .iter()
                    .find(|entry| !entry.trim().is_empty())
                    .map(String::as_str)
            })
            .map(|entry| entry.trim().to_string())
    })
}

fn require_field(
    answers: &BTreeMap<String, String>,
    key: &str,
) -> Result<String, FunctionCallError> {
    answers
        .get(key)
        .cloned()
        .filter(|value| !value.trim().is_empty())
        .ok_or_else(|| respond(format!("{key} is required")))
}

fn parse_probability(value: Option<&str>) -> Result<Option<f64>, FunctionCallError> {
    let Some(value) = value else {
        return Ok(None);
    };
    let trimmed = value.trim().trim_end_matches('%');
    let mut parsed = trimmed
        .parse::<f64>()
        .map_err(|err| respond(format!("failed to parse probability '{value}': {err}")))?;
    if parsed > 1.0 && parsed <= 100.0 {
        parsed /= 100.0;
    }
    if !(0.0..=1.0).contains(&parsed) {
        return Err(respond(format!(
            "probability must be between 0 and 1, got {parsed}"
        )));
    }
    Ok(Some(parsed))
}

async fn prompt_number_in_range(
    session: &Session,
    turn: &TurnContext,
    call_id: &str,
    header: &str,
    question: &str,
    min: usize,
    max: usize,
) -> Result<usize, FunctionCallError> {
    let mut attempts = 0;
    loop {
        attempts += 1;
        let answers =
            prompt_questions(session, turn, call_id, header, vec![("count", question)]).await?;
        let Some(count_text) = answers.get("count") else {
            if attempts >= MAX_PROMPT_ATTEMPTS {
                return Err(respond(format!("count must be between {min} and {max}")));
            }
            continue;
        };
        let count = count_text
            .trim()
            .parse::<usize>()
            .map_err(|err| respond(format!("failed to parse count '{count_text}': {err}")))?;
        if (min..=max).contains(&count) {
            return Ok(count);
        }
        if attempts >= MAX_PROMPT_ATTEMPTS {
            return Err(respond(format!("count must be between {min} and {max}")));
        }
    }
}

fn split_list(text: &str) -> Vec<String> {
    text.split(|ch| ch == ',' || ch == ';' || ch == '\n')
        .map(str::trim)
        .filter(|entry| !entry.is_empty())
        .map(str::to_string)
        .collect()
}

fn parse_domain_signature(text: &str) -> Result<Vec<DomainSignatureWeight>, FunctionCallError> {
    let mut entries = Vec::new();
    for pair in split_list(text) {
        let (domain, weight) = pair.split_once(':').ok_or_else(|| {
            respond(format!(
                "domain-signature entry must be domain:weight, got '{pair}'"
            ))
        })?;
        let weight = weight
            .trim()
            .parse::<f64>()
            .map_err(|err| respond(format!("invalid weight '{weight}': {err}")))?;
        entries.push(DomainSignatureWeight {
            domain: domain.trim().to_string(),
            weight,
        });
    }
    if entries.is_empty() {
        return Err(respond(
            "domain-signature vector cannot be empty".to_string(),
        ));
    }
    Ok(entries)
}

fn validate_test_id(test_id: &str, tests: &[TestCase]) -> Result<String, FunctionCallError> {
    let test_id = test_id.trim();
    if tests.iter().any(|test| test.id == test_id) {
        return Ok(test_id.to_string());
    }
    Err(respond(format!("unknown test id '{test_id}'")))
}

fn validate_test_ids(ids: &[String], tests: &[TestCase]) -> Result<Vec<String>, FunctionCallError> {
    let mut validated = Vec::new();
    for id in ids {
        validated.push(validate_test_id(id, tests)?);
    }
    if validated.is_empty() {
        return Err(respond("at least one test id is required".to_string()));
    }
    Ok(validated)
}

fn parse_probability_updates(
    text: &str,
    test_id: &str,
    hypotheses: &mut [Hypothesis],
) -> Result<Vec<ProbabilityUpdate>, FunctionCallError> {
    let mut updates = Vec::new();
    for entry in split_list(text) {
        let (hypothesis_id, value) = entry.split_once('=').ok_or_else(|| {
            respond(format!(
                "updates must be in hypothesis=probability format, got '{entry}'"
            ))
        })?;
        let hypothesis_id = hypothesis_id.trim();
        let posterior = parse_probability(Some(value.trim()))?
            .ok_or_else(|| respond("posterior probability is required".to_string()))?;
        let hypothesis = hypotheses
            .iter_mut()
            .find(|hypothesis| hypothesis.id == hypothesis_id)
            .ok_or_else(|| respond(format!("unknown hypothesis id '{hypothesis_id}'")))?;
        let update = ProbabilityUpdate {
            hypothesis_id: hypothesis_id.to_string(),
            prior: hypothesis.probability,
            posterior,
            evidence_test_id: test_id.to_string(),
        };
        hypothesis.probability = posterior;
        hypothesis.probability_updates.push(update.clone());
        updates.push(update);
    }
    if updates.is_empty() {
        return Err(respond(
            "at least one probability update is required".to_string(),
        ));
    }
    Ok(updates)
}

fn respond(message: impl Into<String>) -> FunctionCallError {
    FunctionCallError::RespondToModel(message.into())
}
