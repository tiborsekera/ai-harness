# GitHub Copilot Coding Agent Setup Guide

## Required Files

### 1. `.github/copilot-instructions.md`
Main instructions file read by Copilot for all tasks. Keep it concise (~100 lines) and use it as a table of contents pointing to deeper docs.

```markdown
# Project Name - Copilot Instructions

## Project Overview
One paragraph describing the project.

## Quick Reference
| Action | Command |
|--------|---------|
| Install | `...` |
| Test | `...` |
| Lint | `...` |

## Deep References
| Topic | Location |
|-------|----------|
| Architecture | `docs/architecture.md` |
| Conventions | `docs/conventions.md` |

## Key Rules
1. Most important rule
2. Second most important rule
```

### 2. `.github/workflows/copilot-setup-steps.yml`
Environment setup workflow. The job MUST be named `copilot-setup-steps`.

```yaml
name: Copilot Setup Steps
on: workflow_dispatch

jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup environment
        run: |
          # Install dependencies
      - name: Verify baseline
        run: |
          # Run tests/lints with remediation messages
          pytest || echo "REMEDIATION: Fix failing tests"
```

### 3. `.github/instructions/*.instructions.md`
Path-specific instructions with frontmatter glob patterns:

```markdown
---
applyTo: "**/*.py"
---
# Python Conventions
- Use type hints
- Line length: 100
```

### 4. `docs/` Directory
System of record for deep documentation:
- `docs/architecture.md` - Component map, dependency layers, data flow
- `docs/conventions.md` - Golden principles, code style rules
- `docs/contributing.md` - Session protocol, environment setup

## Checklist for New Repos

- [ ] Create `.github/copilot-instructions.md` with project overview and deep references
- [ ] Create `.github/workflows/copilot-setup-steps.yml` with environment setup
- [ ] Create path-specific instructions in `.github/instructions/`
- [ ] Create `docs/` directory with architecture, conventions, contributing docs
- [ ] Create `CLAUDE.md` for Claude Code (mirrors copilot-instructions.md structure)
- [ ] Ensure linter configs exist and are strict
- [ ] Add remediation messages to CI/lint error output
- [ ] Document dependency boundaries and enforce with structural tests
