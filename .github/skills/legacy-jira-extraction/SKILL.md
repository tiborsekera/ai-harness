---
name: legacy-jira-extraction
description: Autonomously searches, fetches, and parses relevant tickets from a legacy self-hosted Jira instance via REST and Agile APIs.
---

# Legacy Jira Extraction Skill

## 1. Activation
**Use this skill when:** You have been provided with a working directory (e.g., `VT-12345`) and a search objective describing incident symptoms, customer names, hostnames, stack traces, product areas, or prior-ticket knowledge that may be relevant.
**Prerequisites:** You must have the `execute` tool to run local Python 3 scripts, and Basic Auth environment variables (`JIRA_USER`, `JIRA_PWD`).

## 2. Mandatory Pattern: Local Python Execution
You must write and execute local Python 3 scripts to interact with the Jira APIs.
**Target Host:** `https://portal.visotech.com/jira`

## 3. Verified API Strategy
Use the Jira APIs in this order, based on the search objective:

1. **Board-Scoped Search First (Preferred for support-ticket discovery):**
   * Use the Agile board endpoint for the Algotrading support board: `https://portal.visotech.com/jira/rest/agile/1.0/board/131/issue?jql={query}&maxResults=10&fields=summary,status,comment,updated,labels`
   * This keeps the search aligned with the support board shown in the web UI.
   * Example JQL fragments: `text ~ "engie33" ORDER BY updated DESC`, `summary ~ "Natural Gas" ORDER BY updated DESC`, `labels = autotrader ORDER BY updated DESC`

2. **Broader Search Fallback:**
   * If board-scoped search is too narrow, use POST `https://portal.visotech.com/jira/rest/api/2/search`
   * Send JSON with `jql`, `maxResults`, `fields`, and `expand`.
   * Prefer queries shaped like: `project = VT AND text ~ "<term>" ORDER BY updated DESC`
   * Use `text ~` for broad matching across indexed ticket text. Add stricter clauses when the objective contains a specific customer, environment, component, or known key.

3. **Issue Retrieval:**
   * Fetch candidate issues with: `https://portal.visotech.com/jira/rest/api/2/issue/{issue_key}?fields=summary,status,issuetype,priority,labels,updated,description,comment,attachment,issuelinks&expand=renderedFields,changelog`
   * **Note:** Ticket summaries (titles) are often entirely non-descriptive. You must fetch and evaluate the full issue payload to understand the context.
   * Prefer `renderedFields.description` when present. Description may legitimately be empty; do not treat missing description as a failure.

4. **Comment Retrieval:**
   * Comments are available in the issue payload, but you must verify pagination.
   * If `comment.total` exceeds the number of returned comments, fetch all comments explicitly from: `https://portal.visotech.com/jira/rest/api/2/issue/{issue_key}/comment?expand=renderedBody&startAt={offset}&maxResults=100`
   * Prefer `renderedBody` for final output when available; fall back to raw `body` otherwise.

5. **Attachments and Links:**
   * Capture attachment metadata from the issue payload: filename, MIME type, and authenticated content URL.
   * Capture linked issues from `issuelinks` because duplicates and related incidents can be highly relevant.
   * Do not download binary attachments by default. Only download attachments when they are clearly text-based or when the search objective explicitly requires attachment inspection.

## 4. Execution Procedure
Follow these exact steps to retrieve and format the ticket context:

1. **Search Phase:**
   * Build multiple focused JQL queries from the search objective.
   * Start with board-scoped Agile search on board `131`.
   * If results are sparse or clearly incomplete, run broader Jira REST search against project `VT`.
   * Keep the exact JQL strings used.

2. **Selection Phase:**
   * Rank matches by direct relevance to the objective, recency, and density of useful technical content.
   * **CRITICAL:** Do not evaluate relevance based solely on the ticket title/summary, as these are often non-descriptive and lack real information. You must dig deeper into the ticket's description, the comment thread (discussion), and related/linked tickets to uncover the actual issue.
   * Prefer tickets with detailed comments, attachments, or duplicate links to other relevant issues.

3. **Fetch Phase:**
   * Retrieve the most relevant tickets in detail.
   * Include issue metadata, rendered description, rendered comments, attachment metadata, linked issues, and changelog when it materially helps reconstruct incident history.

4. **Parse & Save Phase:**
   * Using Python, clean or convert rendered HTML into readable Markdown or plain text.
   * Preserve ticket keys, titles, URLs, statuses, updated timestamps, labels, attachments, and linked issues.
   * Save the extracted knowledge to: `<working_directory>/reports/jira_context.md`.

5. **Markdown Formatting:**
   * The generated `.md` file must contain:
   * The original search objective.
   * The exact JQL queries used.
   * Whether each query was board-scoped or broader REST search.
   * A list of matched tickets with key, summary, status, updated timestamp, and URL.
   * The cleaned extracted content for the most relevant tickets.
   * Attachment metadata and linked-issue references for the selected tickets.
   * A short final section summarizing the most useful findings for the downstream agent.
   * *Note: If no relevant tickets are found, still create the Markdown output with the attempted queries and a clear `no relevant results found` section.*

## 5. Output Contract
Upon completion (or if authentication fails), return your state strictly as a condensed JSON object to the Orchestrator. Do not return free-form prose, raw ticket dumps, raw HTML, or full code dumps in chat. Persist detailed content to `extracted_file_path` and return only the structured handoff.

```json
{
  "status": "PASS" | "FAIL",
  "extracted_file_path": "<working_directory>/reports/jira_context.md",
  "error_message": "<leave blank if PASS; explain auth or execution failures if FAIL>"
}
```

## 6. Example Orchestrator Invocation
To ensure deterministic results, the Orchestrator should invoke this agent using the following structure:

**Tool Call:** `#tool:agent/runSubagent`
**Parameters:**
- `agentName`: "master-of-legacy-jira"
- `description`: "Extracting Jira ticket context"
- `prompt`: """
   WORKING_DIRECTORY: VT-12345
   OBJECTIVE: Extract the full description, comments, and linked issues for ticket VT-12345 to understand the reported memory leak in the EPEX connection manager.
   OUTPUT_REQUIREMENT: Return a JSON object containing `status` and `extracted_file_path`.
"""
