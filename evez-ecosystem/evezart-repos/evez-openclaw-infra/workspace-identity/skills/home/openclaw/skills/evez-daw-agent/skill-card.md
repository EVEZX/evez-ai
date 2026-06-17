## Description: <br>
Autonomous music generation DAW - breakcore, dubstep, phonk, 404 architecture; synthesizes drums, bass, and FX from pure code with voice sample chopping and machine voice synthesis. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[evezart](https://clawhub.ai/user/evezart) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and music creators can use this skill to run a local audio-generation service that renders tracks, drumkits, chopped samples, presets, and health responses for experimental electronic music workflows. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill exposes an unauthenticated local HTTP audio service. <br>
Mitigation: Keep port 9112 off untrusted networks, bind the service to localhost before use where possible, and do not expose it where other users can send requests. <br>
Risk: The service can read caller-selected local audio paths and write output files without tight path controls. <br>
Mitigation: Run it from a disposable or limited-permission directory and review or patch filename and sample_path handling before using it with sensitive local files. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/evezart/evez-daw-agent) <br>


## Skill Output: <br>
**Output Type(s):** [Files, JSON, Shell commands, Guidance] <br>
**Output Format:** [Markdown guidance with bash commands and JSON API usage; the runtime service writes WAV audio files and returns JSON responses.] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Runs locally and exposes HTTP endpoints for rendering tracks, generating drumkits, chopping audio, listing presets, and health checks.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
