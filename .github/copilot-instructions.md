# AI Harness - Copilot Instructions

## Project Overview

AI Harness is a reference implementation for AI coding agent setup patterns, capturing harness engineering practices from OpenAI's Codex approach and GitHub Copilot configuration best practices.

## Deep References

| Topic | Location |
|-------|----------|
| Harness engineering principles | `docs/harness-engineering.md` |
| Copilot setup guide & checklist | `docs/copilot-setup-guide.md` |

## Key Concepts

1. **AGENTS.md / copilot-instructions.md as table of contents** - Keep concise, point to `docs/`
2. **Structured `docs/` as system of record** - Architecture, conventions, contributing docs
3. **Path-specific instructions** - `.github/instructions/*.instructions.md` with `applyTo` globs
4. **copilot-setup-steps.yml** - Environment setup with baseline verification and remediation messages
5. **Dependency layers** - Enforce with structural tests and linters
6. **Golden principles** - Opinionated mechanical rules encoded in the repo

## Note

Once you finish work, output a potential commit message. DO NOT COMMIT unless explicitly told to do so.
