---
description: 'Conventions for writing and maintaining GitHub Copilot agent and skill files in this repository.'
applyTo: '.github/agents/**/*.agent.md,.github/skills/**/SKILL.md'
---

# Agent and Skill File Conventions

## Agent File Format (*.agent.md)

Every agent file must follow this structure:

### Required YAML Frontmatter

```yaml
---
name: <lowercase-hyphenated-name>
description: <one-sentence purpose statement>
tools: ['execute', 'edit', 'read', 'agent']  # only what is needed
user-invocable: true | false
disable-model-invocation: false
model: GPT-5.4
---
```

### Required Sections

1. **Title** (`# Agent Name`) - Clear, descriptive heading
2. **Always Do** - Numbered list of mandatory behaviors
3. **Ask First** - Conditions requiring user confirmation before proceeding
4. **Never Do** - Hard constraints and forbidden actions
5. **Output Contract** - JSON schema for the structured handoff

### Section Ordering Rules

- "Always Do" comes before "Ask First" which comes before "Never Do"
- Domain-specific execution protocols follow the constraint sections
- Output Contract is always the last section

## Skill File Format (SKILL.md)

### Required YAML Frontmatter

```yaml
---
name: <lowercase-hyphenated-name matching folder>
description: <one-sentence purpose statement>
---
```

### Required Sections

1. **Activation** - When to use this skill and prerequisites
2. **Mandatory Pattern** - Required execution method (structured tool execution)
3. **Execution Procedure** - Numbered step-by-step protocol
4. **Output Contract** - JSON schema for the structured handoff

## Naming Conventions

- Agent files: `<name>.agent.md` (lowercase, hyphen-separated)
- Skill folders: `<name>/` (lowercase, hyphen-separated)
- Skill files: `SKILL.md` (uppercase)
- Helper scripts: `<verb>_<noun>.py` (snake_case)

## Tool Assignment Rules

- `read` - Agents that only inspect local files
- `execute` - Agents that run local commands or Python scripts
- `edit` - Agents that create or modify local files
- `agent` - Only the orchestrator (for subagent coordination)

Assign the minimum set of tools needed. A log-analyzer that only reads files should not have `execute`.

## Output Contract Rules

- Every agent and skill must define an Output Contract
- The contract is always a JSON object with a `status` field
- Status values: `PASS`, `PARTIAL`, `FAIL`, `NEEDS_INFO`
- `NEEDS_INFO` must include a `data_request` object with `missing_context` and `suggested_source`
- Error details go in `error_message`, left blank on success
- Never return raw data dumps in chat; persist to files and return paths

## Security Constraints for All Agents

- Remote access is read-only unless the agent is explicitly `remote-experiment-runner`
- Shell metacharacters are forbidden in tool arguments
- Credentials must never be printed or persisted in reports
- All remote commands must go through the Python helper scripts in `.github/skills/`
