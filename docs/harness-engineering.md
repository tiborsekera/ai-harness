# Harness Engineering Reference

A harness is the full environment of scaffolding, constraints, and feedback loops that surrounds an AI coding agent and lets it perform stable work. This document captures key practices from OpenAI's harness engineering approach.

## Core Principles

1. **AGENTS.md as table of contents** (~100 lines) - not an encyclopedia. Points to deeper sources of truth in a structured `docs/` directory. A monolithic instruction file crowds out task context and rots quickly.

2. **Repository as system of record** - Anything the agent can't access in-context doesn't exist. Push all relevant knowledge into the repo in structured `docs/`.

3. **Dependency layers with mechanical enforcement** - Divide code into layers (Types -> Config -> Services -> Orchestration -> UI). Enforce with linters and structural tests, not documentation alone.

4. **Golden principles** - Opinionated, mechanical rules encoded directly into the repository. Examples:
   - Prefer shared utilities over hand-rolled helpers
   - Validate data at boundaries, not speculatively
   - Use instrumented concurrency utilities over third-party primitives

5. **Fast feedback loops** - Integrate type checkers, linters, tests into the agent's workflow. Slow verification reduces iteration count.

6. **Session protocol** - Orient, Setup, Verify baseline, Implement, Test, Update state. One task per session.

7. **Lint errors with remediation** - When a lint fails, the error message itself should contain remediation instructions the agent can act on.

8. **Continuous governance** - Run recurring cleanup tasks that scan for deviations, update quality grades, and open targeted refactoring PRs.

9. **Separate generation from evaluation** - Agents rate their own work too generously. Use independent verification.

## File Structure

```
.github/
  copilot-instructions.md              # Concise overview (~100 lines), table of contents
  instructions/
    python.instructions.md             # applyTo: "**/*.py"
    typescript.instructions.md         # applyTo: "**/*.ts,**/*.tsx"
    testing.instructions.md            # applyTo: "**/tests/**"
  workflows/
    copilot-setup-steps.yml            # Agent environment setup with verification
docs/
  architecture.md                      # System of record for architecture & dependency layers
  conventions.md                       # Golden principles & code conventions
  contributing.md                      # Session protocol & environment setup
CLAUDE.md                             # Claude Code instructions (also concise, points to docs/)
```

## Key Patterns

### Progressive Disclosure
Agents start with a small, stable entry point and are taught where to look next, rather than being overwhelmed with all context up front.

### Structural Tests
Tests that verify architectural constraints rather than business logic:
- Import boundary enforcement (no cross-layer violations)
- Model layer purity (no internal dependencies)
- Naming convention compliance

### Copilot Setup Steps
The `copilot-setup-steps.yml` workflow runs before the coding agent starts work. Include:
- Environment setup (language, dependencies, system packages)
- Baseline verification (tests pass, lints clean)
- Remediation messages on failure (so the agent knows how to fix issues)

### Agent-Legible Code
- Favor stable, well-documented technologies over cutting-edge ones
- Structure code so agents can understand the full domain from the repository
- Cross-link documentation and enforce links mechanically

## Sources

- OpenAI "Harness engineering: leveraging Codex in an agent-first world"
- Harness Engineering Best Practices (Anthropic + OpenAI compilation)
