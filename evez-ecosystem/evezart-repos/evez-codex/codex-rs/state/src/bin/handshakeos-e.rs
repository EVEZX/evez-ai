use std::path::Path;
use std::path::PathBuf;

use anyhow::Context;
use chrono::Utc;
use clap::Args;
use clap::Parser;
use clap::Subcommand;
use dirs::home_dir;
use serde::Deserialize;
use serde_json::json;
use sqlx::Row;
use sqlx::SqlitePool;
use sqlx::sqlite::SqliteConnectOptions;
use sqlx::sqlite::SqliteJournalMode;
use sqlx::sqlite::SqlitePoolOptions;
use sqlx::sqlite::SqliteSynchronous;
use uuid::Uuid;

#[derive(Debug, Parser)]
#[command(name = "handshakeos-e")]
#[command(about = "Record and manage HandshakeOS event knowledge")]
struct Cli {
    /// Covenant scope used to authorize command execution.
    #[arg(long, default_value = "default")]
    scope: String,

    /// Actor identity written to the audit trail.
    #[arg(long, default_value = "cli")]
    actor: String,

    /// Path to the SQLite database. Defaults to $CODEX_HOME/state.sqlite.
    #[arg(long)]
    db: Option<PathBuf>,

    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Initialize covenant and domain tables.
    Init(InitArgs),
    /// Insert an event and optional intent.
    Log(LogArgs),
    /// Attach hypotheses to an existing event.
    Predict(PredictArgs),
    /// Attach test results to an existing hypothesis.
    Test(TestArgs),
    /// Resolve an event using evidence references.
    Resolve(ResolveArgs),
    /// Create or update a reusable pattern definition.
    #[command(name = "patterns-add")]
    PatternsAdd(PatternsAddArgs),
}

#[derive(Debug, Args)]
struct InitArgs {
    /// Covenant version to seed if missing.
    #[arg(long, default_value = "1")]
    covenant_version: String,
}

#[derive(Debug, Args)]
struct LogArgs {
    #[arg(long)]
    event_id: Option<String>,
    #[arg(long)]
    description: String,
    #[arg(long)]
    domain_signature: String,
    #[arg(long)]
    intent_goal: Option<String>,
    #[arg(long)]
    intent_constraints: Option<String>,
    #[arg(long)]
    intent_success_signal: Option<String>,
    #[arg(long)]
    intent_confidence: Option<f64>,
}

#[derive(Debug, Args)]
struct PredictArgs {
    #[arg(long)]
    event_id: String,
    #[arg(long)]
    model_type: String,
    #[arg(long)]
    probability: f64,
    #[arg(long, value_delimiter = ',')]
    falsifiers: Vec<String>,
    #[arg(long)]
    domain_signature: Option<String>,
}

#[derive(Debug, Args)]
struct TestArgs {
    #[arg(long)]
    event_id: String,
    #[arg(long)]
    hypothesis_id: String,
    #[arg(long)]
    description: String,
    #[arg(long)]
    result: String,
    #[arg(long)]
    evidence_ref: String,
}

#[derive(Debug, Args)]
struct ResolveArgs {
    #[arg(long)]
    event_id: String,
    #[arg(long)]
    summary: String,
    #[arg(long, value_delimiter = ',')]
    evidence_refs: Vec<String>,
}

#[derive(Debug, Args)]
struct PatternsAddArgs {
    #[arg(long)]
    pattern_id: Option<String>,
    #[arg(long)]
    trigger: String,
    #[arg(long)]
    invariant: String,
    #[arg(long)]
    counterexample: String,
    #[arg(long)]
    best_response: String,
    #[arg(long)]
    domain_signature: String,
    #[arg(long, value_delimiter = ',')]
    evidence_refs: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct Covenant {
    version: String,
    scopes: Vec<CovenantScope>,
}

#[derive(Debug, Deserialize)]
struct CovenantScope {
    name: String,
    capabilities: Vec<String>,
}

impl Covenant {
    fn allows(&self, scope: &str, capability: &str) -> bool {
        self.scopes.iter().any(|entry| {
            entry.name == scope
                && entry
                    .capabilities
                    .iter()
                    .any(|capability_entry| capability_entry == capability)
        })
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    let db_path = cli.db.clone().unwrap_or_else(default_state_db_path);
    let pool = open_sqlite_pool(db_path.as_path()).await?;
    ensure_schema(&pool).await?;

    let covenant = load_covenant(std::env::current_dir()?.as_path()).await?;
    let (capability, event_ref) = match &cli.command {
        Command::Init(_) => ("system.init", None),
        Command::Log(_) => ("event.log", None),
        Command::Predict(args) => ("event.predict", Some(args.event_id.as_str())),
        Command::Test(args) => ("event.test", Some(args.event_id.as_str())),
        Command::Resolve(args) => ("event.resolve", Some(args.event_id.as_str())),
        Command::PatternsAdd(_) => ("patterns.add", None),
    };

    let allowed = covenant.allows(cli.scope.as_str(), capability);
    let action_type = if allowed {
        capability.to_string()
    } else {
        format!("{capability}:denied")
    };
    let covenant_version = covenant.version.clone();
    insert_audit_action(
        &pool,
        cli.actor.as_str(),
        action_type.as_str(),
        cli.scope.as_str(),
        covenant_version.as_str(),
        event_ref,
        None,
    )
    .await?;

    anyhow::ensure!(
        allowed,
        "covenant scope '{}' disallows capability '{capability}'",
        cli.scope
    );

    match cli.command {
        Command::Init(args) => {
            ensure_covenant_version(&pool, args.covenant_version.as_str()).await?;
            println!(
                "initialized schema and covenant version {}",
                args.covenant_version
            );
        }
        Command::Log(args) => {
            let event_id = args.event_id.unwrap_or_else(|| Uuid::new_v4().to_string());
            let created_at = Utc::now().timestamp();
            sqlx::query(
                r#"
INSERT INTO events (id, created_at, description, domain_signature, status)
VALUES (?, ?, ?, ?, 'open')
                "#,
            )
            .bind(event_id.as_str())
            .bind(created_at)
            .bind(args.description)
            .bind(args.domain_signature)
            .execute(&pool)
            .await?;

            if let Some(goal) = args.intent_goal {
                let intent_id = Uuid::new_v4().to_string();
                sqlx::query(
                    r#"
INSERT INTO intent_tokens (id, event_id, goal, constraints, success_signal, confidence, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
                    "#,
                )
                .bind(intent_id.as_str())
                .bind(event_id.as_str())
                .bind(goal)
                .bind(args.intent_constraints.unwrap_or_default())
                .bind(args.intent_success_signal.unwrap_or_default())
                .bind(args.intent_confidence.unwrap_or(0.5))
                .bind(created_at)
                .execute(&pool)
                .await?;
            }

            println!("logged event {event_id}");
        }
        Command::Predict(args) => {
            ensure_event_exists(&pool, args.event_id.as_str()).await?;
            let hypothesis_id = Uuid::new_v4().to_string();
            let domain_signature = match args.domain_signature {
                Some(signature) => signature,
                None => event_domain_signature(&pool, args.event_id.as_str()).await?,
            };
            let falsifiers = serde_json::to_string(&args.falsifiers)?;
            sqlx::query(
                r#"
INSERT INTO hypotheses (id, event_id, model_type, probability, falsifiers, domain_signature)
VALUES (?, ?, ?, ?, ?, ?)
                "#,
            )
            .bind(hypothesis_id.as_str())
            .bind(args.event_id)
            .bind(args.model_type)
            .bind(args.probability)
            .bind(falsifiers)
            .bind(domain_signature)
            .execute(&pool)
            .await?;
            println!("added hypothesis {hypothesis_id}");
        }
        Command::Test(args) => {
            ensure_event_exists(&pool, args.event_id.as_str()).await?;
            ensure_hypothesis_exists(&pool, args.event_id.as_str(), args.hypothesis_id.as_str())
                .await?;
            let test_id = Uuid::new_v4().to_string();
            sqlx::query(
                r#"
INSERT INTO tests (id, event_id, hypothesis_id, description, result, evidence_ref, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
                "#,
            )
            .bind(test_id.as_str())
            .bind(args.event_id)
            .bind(args.hypothesis_id)
            .bind(args.description)
            .bind(args.result)
            .bind(args.evidence_ref)
            .bind(Utc::now().timestamp())
            .execute(&pool)
            .await?;
            println!("attached test {test_id}");
        }
        Command::Resolve(args) => {
            ensure_event_exists(&pool, args.event_id.as_str()).await?;
            anyhow::ensure!(
                !args.evidence_refs.is_empty(),
                "at least one evidence reference is required"
            );
            let outcome_id = Uuid::new_v4().to_string();
            let evidence_refs = serde_json::to_string(&args.evidence_refs)?;
            sqlx::query(
                r#"
INSERT INTO outcomes (id, event_id, summary, evidence_refs, created_at)
VALUES (?, ?, ?, ?, ?)
                "#,
            )
            .bind(outcome_id.as_str())
            .bind(args.event_id.as_str())
            .bind(args.summary)
            .bind(evidence_refs)
            .bind(Utc::now().timestamp())
            .execute(&pool)
            .await?;

            sqlx::query("UPDATE events SET status = 'closed' WHERE id = ?")
                .bind(args.event_id.as_str())
                .execute(&pool)
                .await?;
            println!("resolved event {}", args.event_id);
        }
        Command::PatternsAdd(args) => {
            let pattern_id = args
                .pattern_id
                .unwrap_or_else(|| Uuid::new_v4().to_string());
            let evidence_refs = serde_json::to_string(&args.evidence_refs)?;
            sqlx::query(
                r#"
INSERT INTO patterns (
    id,
    trigger,
    invariant,
    counterexample,
    best_response,
    domain_signature,
    evidence_refs,
    created_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    trigger = excluded.trigger,
    invariant = excluded.invariant,
    counterexample = excluded.counterexample,
    best_response = excluded.best_response,
    domain_signature = excluded.domain_signature,
    evidence_refs = excluded.evidence_refs
                "#,
            )
            .bind(pattern_id.as_str())
            .bind(args.trigger)
            .bind(args.invariant)
            .bind(args.counterexample)
            .bind(args.best_response)
            .bind(args.domain_signature)
            .bind(evidence_refs)
            .bind(Utc::now().timestamp())
            .execute(&pool)
            .await?;
            println!("upserted pattern {pattern_id}");
        }
    }

    Ok(())
}

fn default_state_db_path() -> PathBuf {
    if let Ok(codex_home) = std::env::var("CODEX_HOME") {
        return PathBuf::from(codex_home).join("state.sqlite");
    }
    if let Some(home) = home_dir() {
        return home.join(".codex/state.sqlite");
    }
    PathBuf::from(".codex/state.sqlite")
}

async fn open_sqlite_pool(path: &Path) -> anyhow::Result<SqlitePool> {
    if let Some(parent) = path.parent() {
        tokio::fs::create_dir_all(parent).await?;
    }

    let options = SqliteConnectOptions::new()
        .filename(path)
        .create_if_missing(true)
        .journal_mode(SqliteJournalMode::Wal)
        .synchronous(SqliteSynchronous::Normal)
        .foreign_keys(true);

    SqlitePoolOptions::new()
        .max_connections(1)
        .connect_with(options)
        .await
        .with_context(|| format!("open sqlite database at {}", path.display()))
}

async fn ensure_schema(pool: &SqlitePool) -> anyhow::Result<()> {
    sqlx::query(
        r#"
CREATE TABLE IF NOT EXISTS covenants (
    version TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    actor TEXT NOT NULL,
    action_type TEXT NOT NULL,
    scope TEXT NOT NULL,
    covenant_version TEXT NOT NULL,
    event_id TEXT,
    intent_id TEXT,
    FOREIGN KEY(covenant_version) REFERENCES covenants(version)
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL,
    description TEXT NOT NULL,
    domain_signature TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS intent_tokens (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    constraints TEXT NOT NULL,
    success_signal TEXT NOT NULL,
    confidence REAL NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hypotheses (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    model_type TEXT NOT NULL,
    probability REAL NOT NULL,
    falsifiers TEXT NOT NULL,
    domain_signature TEXT NOT NULL,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tests (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    hypothesis_id TEXT NOT NULL,
    description TEXT NOT NULL,
    result TEXT NOT NULL,
    evidence_ref TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY(hypothesis_id) REFERENCES hypotheses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS outcomes (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence_refs TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS patterns (
    id TEXT PRIMARY KEY,
    trigger TEXT NOT NULL,
    invariant TEXT NOT NULL,
    counterexample TEXT NOT NULL,
    best_response TEXT NOT NULL,
    domain_signature TEXT NOT NULL,
    evidence_refs TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
        "#,
    )
    .execute(pool)
    .await?;

    Ok(())
}

async fn ensure_covenant_version(pool: &SqlitePool, covenant_version: &str) -> anyhow::Result<()> {
    sqlx::query("INSERT OR IGNORE INTO covenants (version, created_at) VALUES (?, ?)")
        .bind(covenant_version)
        .bind(Utc::now().timestamp())
        .execute(pool)
        .await?;
    Ok(())
}

async fn insert_audit_action(
    pool: &SqlitePool,
    actor: &str,
    action_type: &str,
    scope: &str,
    covenant_version: &str,
    event_id: Option<&str>,
    intent_id: Option<&str>,
) -> anyhow::Result<()> {
    ensure_covenant_version(pool, covenant_version).await?;
    sqlx::query(
        r#"
INSERT INTO audit_actions (timestamp, actor, action_type, scope, covenant_version, event_id, intent_id)
VALUES (?, ?, ?, ?, ?, ?, ?)
        "#,
    )
    .bind(Utc::now().timestamp())
    .bind(actor)
    .bind(action_type)
    .bind(scope)
    .bind(covenant_version)
    .bind(event_id)
    .bind(intent_id)
    .execute(pool)
    .await?;
    Ok(())
}

async fn load_covenant(cwd: &Path) -> anyhow::Result<Covenant> {
    let covenant_path = find_covenant_path(cwd)
        .await
        .ok_or_else(|| anyhow::anyhow!("covenant.json not found from {}", cwd.display()))?;
    let contents = tokio::fs::read_to_string(covenant_path).await?;
    Ok(serde_json::from_str::<Covenant>(&contents)?)
}

async fn find_covenant_path(cwd: &Path) -> Option<PathBuf> {
    let mut current = Some(cwd);
    while let Some(path) = current {
        let candidate = path.join("covenant.json");
        if tokio::fs::try_exists(&candidate).await.unwrap_or(false) {
            return Some(candidate);
        }
        current = path.parent();
    }
    None
}

async fn ensure_event_exists(pool: &SqlitePool, event_id: &str) -> anyhow::Result<()> {
    let exists = sqlx::query_scalar::<_, i64>("SELECT COUNT(1) FROM events WHERE id = ?")
        .bind(event_id)
        .fetch_one(pool)
        .await?;
    anyhow::ensure!(exists > 0, "event {event_id} does not exist");
    Ok(())
}

async fn ensure_hypothesis_exists(
    pool: &SqlitePool,
    event_id: &str,
    hypothesis_id: &str,
) -> anyhow::Result<()> {
    let exists = sqlx::query_scalar::<_, i64>(
        "SELECT COUNT(1) FROM hypotheses WHERE id = ? AND event_id = ?",
    )
    .bind(hypothesis_id)
    .bind(event_id)
    .fetch_one(pool)
    .await?;
    anyhow::ensure!(
        exists > 0,
        "hypothesis {hypothesis_id} does not exist for event {event_id}"
    );
    Ok(())
}

async fn event_domain_signature(pool: &SqlitePool, event_id: &str) -> anyhow::Result<String> {
    let row = sqlx::query("SELECT domain_signature FROM events WHERE id = ?")
        .bind(event_id)
        .fetch_one(pool)
        .await?;
    row.try_get::<String, _>("domain_signature")
        .context("event missing domain_signature")
}

#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;

    #[test]
    fn covenant_check_works() {
        let covenant = Covenant {
            version: "1".to_string(),
            scopes: vec![CovenantScope {
                name: "default".to_string(),
                capabilities: vec!["event.log".to_string()],
            }],
        };

        assert_eq!(covenant.allows("default", "event.log"), true);
        assert_eq!(covenant.allows("default", "event.test"), false);
        assert_eq!(covenant.allows("missing", "event.log"), false);
    }

    #[test]
    fn evidence_refs_are_serialized() {
        let evidence_refs = vec!["test-1".to_string(), "test-2".to_string()];
        let serialized = serde_json::to_string(&evidence_refs).expect("serialize evidence refs");
        assert_eq!(serialized, json!(["test-1", "test-2"]).to_string());
    }
}
