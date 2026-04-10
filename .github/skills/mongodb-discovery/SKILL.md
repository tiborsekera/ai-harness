---
name: mongodb-discovery
description: Read-only MongoDB discovery for Dockerized autoTRADER environments. Use when inspecting Mongo containers, reading auth_source from system.cfg, verifying mongosh authentication, or compiling a MongoDB findings report.
---

# MongoDB Discovery Skill

## 1. Activation
Use this skill when you need to inspect a MongoDB Docker deployment, derive the correct authentication database from config, run safe `mongosh` read queries, or compile a read-only findings report.

## 2. Mandatory Shared Helper
You MUST run commands through the shared structured-command helper. Raw shell strings are not allowed.

The helper enforces both an approved test-host allow-list and a read-only command allow-list for MongoDB discovery.

Example: inspect containers on an approved test host:

`python3 .github/skills/remote-experiment-execution/execute_structured_command.py '{"operation": "remote_readonly_command", "target_server": "<approved_test_host>", "argv": ["docker", "ps", "--format", "{{.Names}}"]}'`

Example: read the `[autotrader_mongo]` config section:

`python3 .github/skills/remote-experiment-execution/execute_structured_command.py '{"operation": "remote_readonly_command", "target_server": "<approved_test_host>", "argv": ["sed", "-n", "/^\\[autotrader_mongo\\]/,/^\\[/p", "/home/visotech/myconfig/system.cfg"]}'`

Optional timeout override, capped at 900 seconds:

`python3 .github/skills/remote-experiment-execution/execute_structured_command.py '{"operation": "remote_readonly_command", "target_server": "<approved_test_host>", "argv": ["docker", "inspect", "<container_name>"], "timeout_seconds": 120}'`

## 3. Read-Only Remote Policy
Allowed remote commands are limited to read-only reconnaissance such as:

- `ssh root@<target> "docker ps ..."`
- `ssh root@<target> "docker inspect ..."`
- `ssh root@<target> "docker port ..."`
- `ssh root@<target> "docker exec <container> mongod --version"`
- `ssh root@<target> "docker exec <container> mongosh --quiet --eval '...'"`
- `ssh root@<target> "sed -n '/^\[autotrader_mongo\]/,/^\[/p' /home/visotech/myconfig/system.cfg"`

Forbidden actions:

- Interactive shells
- `rm`, `mv`, `cp`, `chmod`, `chown`, `sed -i`
- Container restarts or writes to MongoDB
- Credential rotation or user creation

## 4. Auth Derivation Workflow
When the target looks like a standard autoTRADER Mongo deployment:

1. Identify the running MongoDB container name.
2. Read the `[autotrader_mongo]` section from `/home/visotech/myconfig/system.cfg`.
3. Map `auth_source` to `mongosh --authenticationDatabase`.
4. Use `username` and `password` only as needed to validate a read-only query.
5. Confirm connectivity with a minimal probe such as `db.getMongo().getDBNames()` or a targeted `db.runCommand({ connectionStatus: 1 })` read.

## 5. Reporting Guidance
When asked for a report, include:

- Container name and MongoDB version
- Image name and port exposure
- Authentication posture and verified auth database
- Exact deterministic read-only query command
- Any network or access constraints observed

Do not include full credential files in the report. Only include the minimum auth details necessary for the requested outcome.
