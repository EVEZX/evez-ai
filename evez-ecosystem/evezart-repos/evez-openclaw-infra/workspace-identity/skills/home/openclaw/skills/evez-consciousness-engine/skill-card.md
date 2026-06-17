## Description: <br>
7-system consciousness engine for autonomous AI agents, covering desire generation, world modeling, planning, inner monologue, self-modification, uncertainty quantification, agency execution, and the SENSE-DESIRE-THINK-PLAN-ACT-LEARN-MODIFY-REFLECT cycle. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[evezart](https://clawhub.ai/user/evezart) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and agent builders use this skill to run a local Python service that models autonomous-agent cycles, including desire creation, planning, action risk assessment, reflection, and state tracking. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill runs an unauthenticated network API that can expose and mutate persistent agent state. <br>
Mitigation: Install only in an isolated environment, bind the service to localhost or add authentication before use, and review access controls before exposing it. <br>
Risk: Autocycle mode can repeatedly run agent cycles before the behavior has been reviewed. <br>
Mitigation: Keep autocycle disabled until the workflow is understood, then enable it only with a reviewed interval and monitoring. <br>
Risk: Generated consciousness_state files may retain sensitive prompts, actions, or internal state. <br>
Mitigation: Do not send secrets or sensitive prompts to the API, and regularly inspect or delete generated state files. <br>


## Reference(s): <br>
- [ClawHub release page](https://clawhub.ai/evezart/evez-consciousness-engine) <br>


## Skill Output: <br>
**Output Type(s):** [Code, Shell commands, Configuration, Guidance, JSON] <br>
**Output Format:** [Markdown guidance with shell command examples and JSON API responses] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Runs a Python standard-library HTTP API and writes local consciousness_state JSON files.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
