---
name: legacy-confluence-extraction
description: Autonomously searches, fetches, and parses documentation from a legacy self-hosted Confluence instance via REST API.
---

# Legacy Confluence Extraction Skill

## 1. Activation
**Use this skill when:** You have been provided with a working directory (e.g., `VT-12345`) and a search objective (describing the system context, testing steps, SOP, or architecture details required).
**Prerequisites:** You must have the `execute` tool to run local Python 3 scripts, and Basic Auth environment variables (`CONFLUENCE_USER`, `CONFLUENCE_PWD`).

## 2. Mandatory Pattern: Local Python Execution
You must write and execute local Python 3 scripts to interact with the Confluence REST API. 
**Target Host:** `https://portal.visotech.com`

## 3. Execution Procedure
Follow these exact steps to retrieve and format the documentation:

1. **Search Phase:** Build one or more focused CQL queries from the search objective. Use `https://portal.visotech.com/confluence/rest/api/content/search?cql={query}&limit=5` to identify relevant page IDs.
2. **Fetch Phase:** Fetch each relevant page using `https://portal.visotech.com/confluence/rest/api/content/{page_id}?expand=body.storage`. If no useful content is found be creative: got to step 1. and refine the search objective until you are reasonably confident you have exhausted relevant queries.
3. **Parse & Save Phase:** Using Python, strip the HTML from `body.storage`, clean the whitespace, and preserve page titles and page IDs. Save the extracted knowledge to: `<working_directory>/reports/confluence_context.md`.
4. **Markdown Formatting:** The generated `.md` file must contain:
   * The original search objective.
   * The exact queries used.
   * A list of matched pages with title, page ID, and URL.
   * The cleaned, extracted content for the most relevant pages.
   * A short final section summarizing the most useful findings for the downstream agent.
   * *Note: If no relevant pages are found, still create the Markdown output with the attempted queries and a clear "no relevant results found" section.*

## 4. Output Contract
Upon completion (or if authentication fails), return your state strictly as a condensed JSON object to the Orchestrator. Do not return free-form prose, raw HTML, or full page dumps in chat. Persist detailed extracted content to `extracted_file_path` and return only the structured handoff.

```json
{
  "status": "PASS" | "FAIL",
  "extracted_file_path": "<working_directory>/reports/confluence_context.md",
  "error_message": "<leave blank if PASS; explain auth or execution failures if FAIL>"
}
```
