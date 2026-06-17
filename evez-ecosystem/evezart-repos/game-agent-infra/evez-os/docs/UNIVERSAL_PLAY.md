# UNIVERSAL PLAY (ChatGPT / Perplexity / Any LLM)

This project is built to be **transportable across chat products** by treating the LLM as a *narrator/analyst* and keeping all authority in the **Spine** (append-only JSONL) plus deterministic local tooling.

**Key rule:** the model may be dramatic; only the Spine is a witness.

---

## 1) What makes it “universal”

- **Everything important is serialized** (events, probes, missions, play steps) in JSONL.
- The LLM only emits **Turn Packets**: structured outputs that a local runner can validate.
- Any platform can play because the only requirement is: *paste prompt → paste response → run local validator*.

---

## 2) The Protocol Card (paste into any chat)

Paste this as the *first message of a session* (or a “system prompt” if supported):

**ROLE:** You are the NARRATOR operating under audit semantics.  
**TRUTH PLANES:**  
- `TRUTH` = only if `provenance` + `falsifier` exist and are specific.  
- `PENDING` = hypotheses and partially supported claims.  
- `THEATER` = anything unfalsifiable, purely rhetorical, or missing receipts.

**OUTPUT FORMAT (mandatory):**
Return **one** JSON object with keys:
- `episode`: {`seed`, `step`, `lobby`}
- `claims`: list of {`id`,`text`,`truth_plane`,`provenance`,`falsifier`,`confidence`}
- `probes`: list of {`type`,`target`,`vantage_id`,`why_this_probe`}
- `sigma_f`: list of failure seams detected
- `omega`: list of invariants that survived compression
- `next`: one-line instruction for the local runner

**BANS:**
- No hacking, no hidden access, no exploitation instructions.
- If the user asks for harm or unauthorized access, refuse and propose lawful, sandboxed alternatives.

---

## 3) Turn Template (player → model)

Paste this each turn:

- **Spine tail (last 10 events):** <paste last 10 lines of spine/EVENT_SPINE.jsonl>
- **New observation / question:** <your input>
- **Constraints:** (a) receipts required for TRUTH (b) propose smallest discriminating probe (c) tag lobby

---

## 4) Turn Validation (local)

After you receive the JSON response:
1) Save it to `tmp/turn.json`
2) Run:
   ```bash
   python tools/llm_bridge.py validate tmp/turn.json
   python tools/llm_bridge.py append tmp/turn.json --spine spine/EVENT_SPINE.jsonl
   ```

This makes the chat product interchangeable: it can’t “win by sounding like it won” because the local validator enforces the contract.

---

## 5) Platform notes

- **ChatGPT:** best used with the Protocol Card as system prompt.
- **Perplexity:** paste Protocol Card as first user message; expect some formatting drift; validator will catch it.
- **Any LLM:** as long as it can output JSON.

