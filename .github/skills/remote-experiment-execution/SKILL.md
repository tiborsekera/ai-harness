---
name: remote-experiment-execution
description: Autonomously executes long-running deployment and automation scripts with extended timeouts.
---

# Remote Experiment Execution Skill

## 1. Activation
**Use this skill when:** You need to run deployment shell scripts or automation Python scripts that are expected to take longer than 60 seconds, up to 15 minutes.

## 2. Mandatory Pattern: Structured Tool Execution
You MUST use your generic `execute` tool to run the shared structured-command helper. Pass a structured JSON payload wrapped in single quotes. Raw `command_string` payloads are not allowed.

The helper enforces a hardcoded allow-list of approved test hosts for every remote action. If the host is not approved, the tool will reject the request before any SSH command is attempted.

**Deployment Step Templates:**

Deploy a branch to an approved test host:
`python3 .github/skills/remote-experiment-execution/execute_structured_command.py '{"operation": "remote_git_deploy", "target_server": "<approved_test_host>", "branch_name": "<branch_name>"}'`

Restart the approved `autotrader` container, optionally with a settle delay:
`python3 .github/skills/remote-experiment-execution/execute_structured_command.py '{"operation": "remote_docker_restart", "target_server": "<approved_test_host>", "settle_seconds": 240}'`

Run the fixed customer portal automation script locally:
`python3 .github/skills/remote-experiment-execution/execute_structured_command.py '{"operation": "run_customer_portal_automation"}'`

Optional timeout override, capped at 900 seconds:
`python3 .github/skills/remote-experiment-execution/execute_structured_command.py '{"operation": "remote_docker_restart", "target_server": "<approved_test_host>", "settle_seconds": 240, "timeout_seconds": 300}'`

Backward compatibility: `execute_long_command.py` remains as a thin alias for older entry points, but it uses the same structured-operation payloads.

## 3. Constraints
Do not use this for infinite processes. The helper enforces a maximum timeout of 15 minutes.
Only the following operations are supported: `remote_git_deploy`, `remote_docker_restart`, `run_customer_portal_automation`, and `remote_readonly_command`.
