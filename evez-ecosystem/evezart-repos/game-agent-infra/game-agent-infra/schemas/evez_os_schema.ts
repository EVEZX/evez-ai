import {
  mysqlTable,
  mysqlEnum,
  serial,
  varchar,
  text,
  timestamp,
  bigint,
  float,
  json,
  boolean,
  int,
} from "drizzle-orm/mysql-core";

// ─── Users (from auth) ───
export const users = mysqlTable("users", {
  id: serial("id").primaryKey(),
  unionId: varchar("unionId", { length: 255 }).notNull().unique(),
  name: varchar("name", { length: 255 }),
  email: varchar("email", { length: 320 }),
  avatar: text("avatar"),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
  lastSignInAt: timestamp("lastSignInAt").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

// ─── Agents ───
export const agents = mysqlTable("agents", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  name: varchar("name", { length: 255 }).notNull(),
  mission: text("mission"),
  status: mysqlEnum("status", [
    "idle",
    "running",
    "paused",
    "error",
    "terminated",
  ])
    .default("idle")
    .notNull(),
  agentType: mysqlEnum("agentType", [
    "executor",
    "skeptic",
    "architect",
    "explorer",
    "evolver",
    "meta",
    "aegis",
    "watchdog",
  ])
    .default("executor")
    .notNull(),
  recursionDepth: int("recursionDepth").default(0).notNull(),
  parentAgentId: bigint("parentAgentId", { mode: "number", unsigned: true }),
  phi: float("phi").default(0),
  healthScore: float("healthScore").default(1.0),
  longeviate: boolean("longeviate").default(true),
  config: json("config"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
  lastHeartbeatAt: timestamp("lastHeartbeatAt").defaultNow().notNull(),
});

export type Agent = typeof agents.$inferSelect;
export type InsertAgent = typeof agents.$inferInsert;

// ─── Agent Tasks ───
export const agentTasks = mysqlTable("agent_tasks", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  sourceSystem: varchar("source_system", { length: 64 }).notNull(),
  targetSystem: varchar("target_system", { length: 64 }),
  requestedAction: varchar("requested_action", { length: 255 }).notNull(),
  payload: json("payload"),
  status: mysqlEnum("status", [
    "pending",
    "assigned",
    "running",
    "success",
    "failed",
    "retrying",
  ])
    .default("pending")
    .notNull(),
  priority: int("priority").default(5).notNull(),
  agentId: bigint("agentId", { mode: "number", unsigned: true }),
  result: json("result"),
  errorLog: text("error_log"),
  callbackUrl: varchar("callback_url", { length: 512 }),
  decayFactor: float("decay_factor").default(0.95),
  thresholdValue: float("threshold_value").default(1.0),
  fireCount: int("fire_count").default(0),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
  completedAt: timestamp("completedAt"),
});

export type AgentTask = typeof agentTasks.$inferSelect;
export type InsertAgentTask = typeof agentTasks.$inferInsert;

// ─── Events (FIRE events, system events) ───
export const events = mysqlTable("events", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  eventType: mysqlEnum("eventType", [
    "fire",
    "emerge",
    "merge",
    "spawn",
    "transmutation",
    "tick",
    "heartbeat",
    "alert",
    "milestone",
  ])
    .default("tick")
    .notNull(),
  source: varchar("source", { length: 128 }).notNull(),
  payload: json("payload"),
  severity: mysqlEnum("severity", ["info", "low", "medium", "high", "critical"])
    .default("info")
    .notNull(),
  hash: varchar("hash", { length: 128 }),
  prevHash: varchar("prev_hash", { length: 128 }),
  provenance: json("provenance"),
  phiAtEvent: float("phi_at_event").default(0),
  recursionDepth: int("recursion_depth").default(0),
  agentId: bigint("agentId", { mode: "number", unsigned: true }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Event = typeof events.$inferSelect;
export type InsertEvent = typeof events.$inferInsert;

// ─── Threat Log (AEGIS) ───
export const threatLog = mysqlTable("threat_log", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  threatType: mysqlEnum("threatType", [
    "osint",
    "coordination",
    "infrastructure",
    "identity",
    "reputation",
    "deanon",
  ])
    .default("osint")
    .notNull(),
  severity: mysqlEnum("severity", ["green", "orange", "red"])
    .default("green")
    .notNull(),
  surface: varchar("surface", { length: 128 }).notNull(),
  coordinationScore: float("coordination_score"),
  motiveClass: mysqlEnum("motiveClass", [
    "suppression",
    "narrative_ctrl",
    "recon",
    "unknown",
  ]).default("unknown"),
  evidence: json("evidence"),
  clusterId: varchar("cluster_id", { length: 64 }),
  hawkesIntensity: float("hawkes_intensity"),
  handled: boolean("handled").default(false),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type ThreatLog = typeof threatLog.$inferSelect;
export type InsertThreatLog = typeof threatLog.$inferInsert;

// ─── Trunk State ───
export const trunkState = mysqlTable("trunk_state", {
  id: serial("id").primaryKey(),
  version: varchar("version", { length: 32 }).notNull().unique(),
  canonicalObjective: text("canonical_objective").notNull(),
  currentBranch: varchar("current_branch", { length: 128 }).notNull(),
  branchStatus: mysqlEnum("branchStatus", [
    "active",
    "blocked",
    "completed",
    "merged",
  ])
    .default("active")
    .notNull(),
  lastDelta: text("last_delta"),
  blockedDecisions: json("blocked_decisions"),
  nextAutomaticBranch: varchar("next_automatic_branch", { length: 128 }),
  contextHash: varchar("context_hash", { length: 128 }),
  valuationScenario: mysqlEnum("valuationScenario", ["bear", "base", "bull", "strategic"])
    .default("bear")
    .notNull(),
  phi: float("phi").default(0),
  healthScore: float("health_score").default(1.0),
  agentCount: int("agent_count").default(0),
  taskQueueDepth: int("task_queue_depth").default(0),
  fireCount: int("fire_count").default(0),
  provenanceRoot: varchar("provenance_root", { length: 128 }),
  config: json("config"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
});

export type TrunkState = typeof trunkState.$inferSelect;
export type InsertTrunkState = typeof trunkState.$inferInsert;

// ─── Sensory Events ───
export const sensoryEvents = mysqlTable("sensory_events", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  sensoryType: mysqlEnum("sensoryType", [
    "audio",
    "visual",
    "text",
    "telemetry",
    "contextual",
    "fusion",
  ])
    .default("text")
    .notNull(),
  rawInput: text("raw_input"),
  transcribedText: text("transcribed_text"),
  visualMap: json("visual_map"),
  topologyTau: float("topology_tau"),
  chordData: json("chord_data"),
  immersionScore: float("immersion_score").default(0),
  agentId: bigint("agentId", { mode: "number", unsigned: true }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type SensoryEvent = typeof sensoryEvents.$inferSelect;
export type InsertSensoryEvent = typeof sensoryEvents.$inferInsert;

// ─── Invariance Tests ───
export const invarianceTests = mysqlTable("invariance_tests", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  cognitiveEventId: varchar("cognitive_event_id", { length: 64 }).notNull(),
  rotationType: mysqlEnum("rotationType", [
    "time_shift",
    "state_shift",
    "frame_shift",
    "adversarial_shift",
    "identity_goal_shift",
  ])
    .notNull(),
  result: mysqlEnum("result", ["pass", "fail", "weak_defeater", "strong_defeater"])
    .default("pass")
    .notNull(),
  score: float("score").default(1.0),
  defeaterEvidence: text("defeater_evidence"),
  agentId: bigint("agentId", { mode: "number", unsigned: true }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type InvarianceTest = typeof invarianceTests.$inferSelect;
export type InsertInvarianceTest = typeof invarianceTests.$inferInsert;

// ─── Provenance Ledger ───
export const provenanceLedger = mysqlTable("provenance_ledger", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  entryType: mysqlEnum("entryType", [
    "action",
    "verification",
    "commit",
    "rollback",
    "fire",
    "spawn",
    "decay",
  ])
    .default("action")
    .notNull(),
  actor: varchar("actor", { length: 128 }).notNull(),
  action: varchar("action", { length: 255 }).notNull(),
  payload: json("payload"),
  hash: varchar("hash", { length: 128 }).notNull(),
  prevHash: varchar("prev_hash", { length: 128 }),
  signature: varchar("signature", { length: 256 }),
  rule2Enforced: boolean("rule2_enforced").default(true),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type ProvenanceLedger = typeof provenanceLedger.$inferSelect;
export type InsertProvenanceLedger = typeof provenanceLedger.$inferInsert;

// ─── System Health ───
export const systemHealth = mysqlTable("system_health", {
  id: serial("id").primaryKey(),
  healthScore: float("health_score").default(1.0),
  successRate: float("success_rate").default(1.0),
  avgLatencyMs: float("avg_latency_ms").default(0),
  errorRate: float("error_rate").default(0),
  activeAgents: int("active_agents").default(0),
  queueDepth: int("queue_depth").default(0),
  phi: float("phi").default(0),
  fireRate: float("fire_rate").default(0),
  memoryPressure: float("memory_pressure").default(0),
  recursionDepth: int("recursion_depth").default(0),
  violationCount: int("violation_count").default(0),
  snapshot: json("snapshot"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type SystemHealth = typeof systemHealth.$inferSelect;
export type InsertSystemHealth = typeof systemHealth.$inferInsert;

// ─── Retrocausal Deltas ───
export const retrocausalDeltas = mysqlTable("retrocausal_deltas", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  futureEventId: varchar("future_event_id", { length: 64 }).notNull(),
  pastEventId: varchar("past_event_id", { length: 64 }).notNull(),
  deltaType: mysqlEnum("deltaType", [
    "threshold_decay",
    "loop_spawn",
    "priority_shift",
    "config_rewrite",
  ])
    .default("threshold_decay")
    .notNull(),
  decayFactor: float("decay_factor").default(0.95),
  oldValue: float("old_value"),
  newValue: float("new_value"),
  causalChain: json("causal_chain"),
  applied: boolean("applied").default(false),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type RetrocausalDelta = typeof retrocausalDeltas.$inferSelect;
export type InsertRetrocausalDelta = typeof retrocausalDeltas.$inferInsert;

// ─── Revenue / FIRE Pipeline ───
export const revenueEvents = mysqlTable("revenue_events", {
  id: serial("id").primaryKey(),
  uuid: varchar("uuid", { length: 64 }).notNull().unique(),
  fireId: varchar("fire_id", { length: 32 }),
  source: varchar("source", { length: 128 }).notNull(),
  amount: float("amount").default(0),
  currency: varchar("currency", { length: 8 }).default("USD"),
  status: mysqlEnum("status", [
    "pending",
    "confirmed",
    "failed",
    "refunded",
  ])
    .default("pending")
    .notNull(),
  stripeEventId: varchar("stripe_event_id", { length: 128 }),
  metadata: json("metadata"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type RevenueEvent = typeof revenueEvents.$inferSelect;
export type InsertRevenueEvent = typeof revenueEvents.$inferInsert;
