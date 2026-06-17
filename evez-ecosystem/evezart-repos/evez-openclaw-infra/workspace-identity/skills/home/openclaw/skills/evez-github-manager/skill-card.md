## Description: <br>
Manage GitHub repositories, pull requests, issues, and workflows from OpenClaw. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[evezart](https://clawhub.ai/user/evezart) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and engineering teams use this skill to inspect GitHub repositories, pull requests, issues, branches, and organization repositories from an agent workflow. It supports PR review, issue triage, branch management, release coordination, workflow status checks, and multi-repo coordination. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: A GitHub token can allow repository-changing actions such as merge, branch deletion, issue closure, release creation, workflow changes, or multi-repo operations. <br>
Mitigation: Use a fine-grained, least-privilege token, prefer read-only scopes unless writes are required, and require explicit human confirmation before repository-changing operations. <br>
Risk: The skill does not clearly spell out safety limits for broad GitHub operations. <br>
Mitigation: Review the requested repository, operation, and token scopes before installation or execution, especially in organization or multi-repo contexts. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/evezart/evez-github-manager) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Markdown and command-line text with inline shell commands and GitHub API results] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May require a GITHUB_TOKEN or configured Composio integration for authenticated GitHub operations.] <br>

## Skill Version(s): <br>
1.0.0 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
