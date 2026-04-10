# Copilot Instructions

This repository contains the GitHub Copilot agent harness for the autoTRADER investigation platform.

## Architecture

The system follows a hub-and-spoke orchestration model. See [docs/architecture.md](docs/architecture.md) for the full architecture reference.

- **Orchestrator**: `at-expert-orchestrator` classifies work as SUPPORT, BUG, or ADHOC and routes to specialized subagents.
- **Workers**: Single-purpose subagents (log-extractor, code-investigator, etc.) perform scoped tasks and return structured JSON handoffs.
- **Skills**: Reusable procedural runbooks in `.github/skills/` that agents load before executing domain-specific operations.

## Key Conventions

1. **Structured JSON contracts** - Every subagent returns a JSON object with a `status` field (`PASS`, `PARTIAL`, `FAIL`, `NEEDS_INFO`). Never return free-form prose as a final handoff.
2. **Checkpoint-driven state** - Investigation state lives in `checkpoint.json`, not in chat context. Always check for an existing checkpoint before starting work.
3. **Read-only remote access** - Remote servers are accessed only through the Python helper scripts in `.github/skills/`. Raw shell command generation is forbidden.
4. **Local working directory** - All artifacts (reports, logs, extracted data) are written to the local working directory. No remote writes are permitted.
5. **Progressive disclosure** - Agents start with this file and follow pointers to deeper docs, skills, and architecture references as needed.

## Agent Hierarchy

```
at-expert-orchestrator (user-invocable)
  |-- pdf-extractor
  |-- incident-parser
  |-- log-extractor --> skill: log-extraction
  |-- log-analyzer
  |-- code-investigator
  |-- remote-experiment-runner --> skill: remote-experiment-execution
  |-- report-compiler
  |-- master-of-legacy-jira --> skill: legacy-jira-extraction
  |-- master-of-legacy-gitlab
  |-- master-of-legacy-confluence --> skill: legacy-confluence-extraction
  |-- master-of-mongodb --> skill: mongodb-discovery

Standalone (user-invocable):
  |-- code-reviewer
  |-- master-of-azure-devops
```

## Security Boundaries

- **Approved test hosts only**: `j1-autotrader3`, `j1-autotrader4` (enforced by `execute_structured_command.py`)
- **No production writes**: Agents must never perform production remediation
- **Shell injection prevention**: All remote commands are routed through Pydantic-validated Python wrappers with forbidden-token blocklists
- **Credential hygiene**: Never print or persist PAT values; redact secrets in reports

## Where to Look Next

| Topic | Location |
|-------|----------|
| Full architecture and data flow | [docs/architecture.md](docs/architecture.md) |
| Agent file format and conventions | [instructions/agent-conventions.instructions.md](instructions/agent-conventions.instructions.md) |
| Environment setup for Copilot agent | [workflows/copilot-setup-steps.yml](workflows/copilot-setup-steps.yml) |
| Individual agent definitions | [agents/](agents/) |
| Skill runbooks and helper scripts | [skills/](skills/) |
