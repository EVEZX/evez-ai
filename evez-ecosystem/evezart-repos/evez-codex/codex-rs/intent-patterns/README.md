# Codex Intent Patterns

This crate captures intent-driven troubleshooting flows and compiles them into reusable patterns.

## End-to-end example: pressed play -> audio routed to Bluetooth

### 1) Intent token

```
IntentToken { text: "pressed play" }
```

### 2) Hypotheses

```
Hypothesis { summary: "Bluetooth output not selected" }
Hypothesis { summary: "Media player still using built-in speakers" }
```

### 3) Test

```
CaptureTest { description: "Switch system output to Bluetooth headphones" }
```

### 4) Outcome

```
Outcome { summary: "audio routed to Bluetooth", success: true }
```

### 5) Compiled pattern

```
CompiledPattern {
  intent: "pressed play",
  outcome: "audio routed to Bluetooth",
  tokens: ["pressed", "play"],
}
```

### 6) Pattern match on a similar query

Query:

```
"hit play and still no sound in my Bluetooth headset"
```

Match result:

```
PatternMatch {
  pattern: CompiledPattern { intent: "pressed play", ... },
  score: 1,
  rationale: "matched tokens: play",
}
```
