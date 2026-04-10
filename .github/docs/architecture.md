# Architecture Reference

## System Overview

The autoTRADER investigation harness is a multi-agent system built on GitHub Copilot's agent framework. It automates support investigations, bug reproduction, and ad hoc code exploration for the autoTRADER trading platform.

## Design Principles

1. **Single investigation per session** - The orchestrator handles one workflow at a time, persists state to `checkpoint.json`, and exits cleanly.
2. **Subagent isolation** - Each worker agent gets a focused context window with only the inputs it needs. Results flow back as condensed JSON, not raw data.
3. **Structured tool execution** - Remote commands are never generated as raw shell strings. All remote access goes through validated Python wrappers that enforce allow-lists and block injection.
4. **Checkpoint as system of record** - `checkpoint.json` is the single source of truth for investigation state. It must be updated after every subagent return, hypothesis pivot, or exit condition.
5. **Report as deliverable** - Every investigation produces a disk-persisted report (`RCA_handoff.md` or `Investigation_Report.md`), not chat-only output.

## Agent Layers

```
Layer 1: User Interface
  at-expert-orchestrator    -- Classifies, routes, and coordinates
  code-reviewer             -- Standalone code review (no orchestration)
  master-of-azure-devops    -- Standalone Azure DevOps extraction

Layer 2: Evidence Gathering
  pdf-extractor             -- PDF to text conversion
  incident-parser           -- Ticket text to structured parameters
  log-extractor             -- Remote log retrieval (read-only)
  master-of-legacy-jira     -- Jira ticket extraction
  master-of-legacy-gitlab   -- GitLab code/artifact extraction
  master-of-legacy-confluence -- Confluence documentation extraction
  master-of-mongodb         -- MongoDB read-only discovery

Layer 3: Analysis
  log-analyzer              -- Log forensics and timeline reconstruction
  code-investigator         -- Local code experiments and reproduction

Layer 4: Deployment (test environments only)
  remote-experiment-runner  -- Branch deployment to approved test hosts

Layer 5: Synthesis
  report-compiler           -- Final report generation from findings
```

## Data Flow

```
User Prompt
    |
    v
[at-expert-orchestrator]
    |
    |-- classify --> SUPPORT | BUG | ADHOC
    |
    |-- (if ticket) --> pdf-extractor --> incident-parser
    |                                         |
    |                                         v
    |-- (if logs needed) --------> log-extractor --> log-analyzer
    |
    |-- (if context needed) -----> master-of-legacy-jira
    |                              master-of-legacy-confluence
    |                              master-of-legacy-gitlab
    |
    |-- (if code proof needed) --> code-investigator
    |                                   |
    |                                   v (optional)
    |-- (if deploy needed) ------> remote-experiment-runner
    |
    |-- (finalize) --------------> report-compiler
    |
    v
checkpoint.json + reports/RCA_handoff.md or reports/Investigation_Report.md
```

## Skill Architecture

Skills are procedural runbooks stored in `.github/skills/<name>/`. Each skill folder contains:

- `SKILL.md` - The step-by-step procedure the agent must follow
- Helper scripts (optional) - Python wrappers that enforce security boundaries

Skills are loaded by agents at runtime, not injected upfront. This keeps agent instructions lean and follows the progressive disclosure pattern.

### Security Enforcement Stack

```
Agent instruction (NEVER generate raw shell)
    |
    v
SKILL.md (structured JSON template)
    |
    v
Python wrapper (Pydantic validation + forbidden-token blocklist)
    |
    v
subprocess.run(shell=False) with timeout
    |
    v
Remote server (read-only)
```

## Investigation Types

| Type | Trigger | Evidence Path | Final Report |
|------|---------|---------------|--------------|
| SUPPORT | Customer issue, ticket | Ticket -> logs -> analysis | `RCA_handoff.md` |
| BUG | Suspected code defect | Ticket -> logs -> code proof | `RCA_handoff.md` |
| ADHOC | User question, exploration | Code/docs -> targeted analysis | `Investigation_Report.md` |

## Repository Layout

```
.github/
  copilot-instructions.md          -- Entry point (~100 lines, navigation map)
  docs/
    architecture.md                -- This file (system of record)
  instructions/
    agent-conventions.instructions.md -- Agent file format standards
  agents/
    *.agent.md                     -- Individual agent definitions
  skills/
    <name>/
      SKILL.md                     -- Procedural runbook
      *.py                         -- Helper scripts (optional)
  workflows/
    copilot-setup-steps.yml        -- Environment bootstrap
```
