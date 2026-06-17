use anyhow::Context;
use clap::Parser;
use codex_core::pattern_match::PatternDefinition;
use codex_core::pattern_match::PatternMatchEvent;
use codex_core::pattern_match::rank_patterns;
use std::fs;
use std::path::Path;
use std::path::PathBuf;

#[derive(Debug, Parser)]
pub struct PatternsMatchCommand {
    /// JSON file containing an array of stored patterns.
    #[arg(long, value_name = "FILE")]
    pub patterns: PathBuf,

    /// JSON file describing the event to match.
    #[arg(long, value_name = "FILE")]
    pub event: PathBuf,

    /// Maximum number of matches to print.
    #[arg(long, default_value_t = 5)]
    pub limit: usize,
}

pub fn run_patterns_match(cmd: PatternsMatchCommand) -> anyhow::Result<()> {
    let patterns: Vec<PatternDefinition> = read_json(&cmd.patterns)?;
    let event: PatternMatchEvent = read_json(&cmd.event)?;

    let results = rank_patterns(&event, &patterns, cmd.limit);
    for result in results {
        println!("{} {}", result.pattern_id, result.rationale);
    }

    Ok(())
}

fn read_json<T>(path: &Path) -> anyhow::Result<T>
where
    T: serde::de::DeserializeOwned,
{
    let contents = fs::read_to_string(path)
        .with_context(|| format!("failed to read {path}", path = path.display()))?;
    serde_json::from_str(&contents)
        .with_context(|| format!("failed to parse JSON from {path}", path = path.display()))
}
