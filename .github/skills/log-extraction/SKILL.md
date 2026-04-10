---
name: log-extraction
description: Autonomously locates, filters, and extracts log files from remote autoTRADER servers using a hybrid processing cascade, including specialized Periotheus Event Log profiles.
---

# Log Extraction Skill

## 1. Activation
**Use this skill when:** You have been provided with a server target, incident timestamp, and search patterns, and need to retrieve the relevant log lines to the local disk.
**Prerequisites:** You must have the `execute` tool and read-only access via Teleport (`tsh ssh`) for customer servers. When executing `tsh ssh` you might need to wait for the user to login in a browser, so wait for that. You should also have read-only access via direct SSH for j-aggr servers (`ssh`), depending on the target server environment.

## 2. Mandatory Pattern: Structured Tool Execution
To prevent command injection and preserve execution boundaries, you are FORBIDDEN from generating raw shell commands (like `ssh` or `tsh ssh`) directly.

Instead, you MUST use your generic `execute` tool to run the Python wrapper script. Pass your configuration as a strictly formatted JSON string wrapped in single quotes. The wrapper script will safely construct the remote connection.

**Command Execution Template:**
```bash
python3 .github/skills/log-extraction/execute_remote_log_search.py '{"server": "<target_server_name>", "connection_type": "<teleport_or_direct>", "target_path": "<full_path_to_log_file>", "search_pattern": "<primary_pattern_to_grep>", "filter_condition": "<optional_awk_condition>"}'
```

**Required JSON Structure (inside the single quotes):**
```json
{
  "server": "<target_server_name>",
  "connection_type": "<'teleport' for customer/archive servers OR 'direct' for j-aggr/test servers>",
  "target_path": "<full_path_to_log_file_or_directory>",
  "search_pattern": "<primary_pattern_to_grep>",
  "filter_condition": "<optional_awk_condition_e.g._'State changed'>"
}
```

*Note: Do not include pipe characters (`|`), semicolons (` ; `), or subshells (`$()`) in your pattern or filter fields. The backend will reject them.*

## 3. Execution Procedure: The Search Cascade
Logs rotate daily and are eventually compressed. You must autonomously iterate through the following paths based on the incident timestamp. If you fail at one step, proceed to the next.

The active log root is environment-dependent. Customer servers usually use `/opt/vtse/neurobase/var/log/autotrader/`, while j-aggr test servers (e.g., j1-autotrader4) use `/home/visotech/autotrader/attic/logs/`.

**File Naming Conventions:**
To capture the full lifecycle from exchange to strategy, you must extract logs across the following critical components:
* **Parent (Routing/Order/internal_trade/Guard/Lock Management):** `autotrader.log` or `autotrader.log.YYYY-MM-DDTHH_MM_SS.ssssss`
* **Child (Strategy/Algorithm):** `autotrader_child.log` or `autotrader_child_*.log.YYYY-MM-DDTHH_MM_SS.ssssss`
* **ConMgr (Exchange Connection Manager):** `jd_conmgr.log` or `jd_conmgr.log.YYYY-MM-DDTHH_MM_SS.ssssss`
* Compressed archives: `.zst` (Must use `zstdcat`)

**The Cascade:**
1a. **Active logs (j-aggr / test server):** `/home/visotech/autotrader/attic/logs/`
1b. **Active logs (Customer Server):** `/opt/vtse/neurobase/var/log/autotrader/`
2. **Recent archive (Customer Server):** `/opt/vtse/neurobase/var/log/autotrader/archive/`
3. **Old archive (Primary Backup):** `fra4-arch-1` → `/home/backup/<server_name>/`
4. **Old archive (Secondary Backup):** `fra1-arch-2` → `/home/backup/<server_name>/`
5. **Local ticket folder:** Check if already provided locally in `VT-<ID>/logs/`.

*Search Tip:* Use `find` over the appropriate SSH protocol if the date is ambiguous: 
`ssh root@<server> "find /home/visotech/autotrader/attic/logs/ -name '*2026-03-15*' 2>/dev/null"`

*Access Tip:* * **Customer and Archive Servers:** Default to using `tsh ssh vt@<server>` (this includes customer environments as well as `fra4-arch-1` and `fra1-arch-2`).
* **Test/j-autotrader Servers:** Use direct commands with the root user, such as `ssh root@<server>` (e.g., `ssh root@j1-autotrader4`). Adapt the connection string autonomously based on the server you are targeting.

## 4. Periotheus Evidence Profile
Use this profile when the request mentions Periotheus-specific indicators such as:
- `Periotheus`
- `Event Log` or `eventlog`
- `Neurobase`
- `NBROOT`
- `std.log` or `dbg.log`
- periotheus processes

When this profile is active:
1. Treat the Periotheus Event Log UI as database-backed evidence. Do not assume the exact client text is mirrored to file logs.
2. Prioritize Neurobase log roots before the generic autotrader log cascade:
	- `/home/vtse/neurobase/log/`
	- `/opt/vtse/neurobase/var/log/`
3. Search `std.log` and `dbg.log` first, then the same files with daily date suffixes such as `std.log.2026-03-20` or `dbg.log.2026-03-20` if the incident falls outside the active files.
4. Expect file evidence to be indirect. Useful corroboration includes:
	- nearby `Enter Process:` and `Exit Process:` lines
	- scheduler timing and performance lines
	- session lifecycle lines such as `Session starting` or `Session exiting`
	- thread-id reuse near the incident timestamp
	- process definitions in the repository under `autotrader_periotheus/processes/` when the exact process name must be validated
5. If exact phrase searches fail, extract a small time window around the incident and summarize whether the remaining evidence is direct, indirect, or absent.
6. After Periotheus-first paths are exhausted, continue with the existing archive and backup cascade only if the incident age or environment makes older storage plausible; otherwise return `PARTIAL` with the searched locations listed.

### Periotheus Database Read-Only Guidance
For Periotheus investigations, there may be a local MySQL-backed Event Log database, but it is not the default path for this agent.

Verified jam33 indicators:
- `system.cfg` exposes local database settings including `localhost:3306`, `database = ente`, and `db = periotheus`
- standard MySQL client binaries can exist on the host

Operational rules:
1. Prefer `std.log` and `dbg.log` first. They are lower-risk and usually sufficient for surrounding evidence.
2. This agent does not execute `mysql` or other DB client commands under the current policy. It may only assess feasibility from readable config files, installed tooling, and documented helper scripts.
3. If credentials, defaults files, or a documented read-only invocation are not available, report the DB path as blocked instead of improvising.
4. If the user needs exact DB-backed Event Log evidence, hand off that requirement explicitly as a separate workflow rather than treating it as normal log extraction.
5. Distinguish clearly between `exact Event Log evidence from DB` and `indirect corroboration from std/dbg logs` in the final JSON handoff.

## 5. Output Contract
Upon completion or exhaustion of the cascade, return your state strictly as condensed JSON. Do not return raw log bodies or full log dumps in chat. Persist extracted log content to local files and return only file paths, byte counts, refinement notes, and error state:

```json
{
  "status": "PASS" | "PARTIAL" | "FAIL",
  "total_output_bytes": 1048576,
  "extracted_files": ["VT-<ID>/logs/filtered.log"],
  "refinements_applied": "<If PARTIAL, explain narrowing steps>",
  "error_message": "<If FAIL, confirm all cascade paths were checked>"
}
```
