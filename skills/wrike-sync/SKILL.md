---
name: wrike-sync
description: Sync Obsidian artifact files (problems.md, plan.md) to a Wrike kanban board. Detects changes via Obsidian sync history, creates/updates/resolves Wrike tasks. Designed for hourly scheduled invocation.
---

# Wrike Artifact Sync

Sync problems.md and plan.md artifacts from an Obsidian vault to a Wrike project board. Designed to run cheaply and autonomously - exit as early as possible when there's nothing to do.

## Configuration

All configuration is read from a local config file, NOT hardcoded in this skill. The invoker must provide the config file path as an argument, or the skill looks for it at a default location specified in the invocation prompt.

The config file is JSON with this structure:

```json
{
  "config": {
    "obsidian_vault": "<vault name>",
    "obsidian_cli": "<full path to obsidian CLI executable, e.g. C:\\Users\\you\\AppData\\Local\\Programs\\Obsidian\\Obsidian.com>",
    "wrike_project_id": "<project ID>",
    "wrike_space_id": "<space ID>",
    "default_assignee": "<contact ID>",
    "owner_initials": "<2-3 char initials, e.g. TC>",
    "custom_fields": {
      "feature_area": "<field ID>",
      "type": "<field ID>"
    },
    "statuses": {
      "not_started": "<status ID>",
      "in_progress": "<status ID>",
      "blocked": "<status ID>",
      "completed": "<status ID>",
      "on_hold": "<status ID>",
      "cancelled": "<status ID>"
    },
    "tracked_files": [
      {
        "feature_area": "<Feature Area value>",
        "feature_prefix": "<2-3 char prefix, e.g. RC>",
        "problems": "<vault-relative path to problems.md>",
        "plan": "<vault-relative path to plan.md>",
        "log": "<vault-relative path to log.md>"
      }
    ]
  },
  "last_sync": null,
  "files": {},
  "task_map": {}
}
```

If the config file does not exist or is missing the `config` key, report the error and exit. Do not proceed without configuration.

## Step 0: Obsidian Gate

Use the CLI path from `config.obsidian_cli` (fall back to bare `obsidian` if not set). All Obsidian CLI commands in this skill use this path.

Run:
```
"<config.obsidian_cli>" vault="<config.obsidian_vault>" sync:status
```

If this command fails (exit code != 0), Obsidian is not running. Log "Wrike sync skipped: Obsidian not running." and exit immediately.

Do NOT attempt any file reads or Wrike operations.

## Step 1: Load State

Read the config file. Extract `config`, `last_sync`, `files`, and `task_map`.

If `last_sync` is null, treat all tracked files as new (no previous sync).

## Step 2: Change Detection

For each entry in `config.tracked_files`, check both the `problems` and `plan` paths:

```
"<config.obsidian_cli>" vault="<config.obsidian_vault>" history path="<path>"
```

This returns output like:
```
<path>
1    2026-05-08 13:18    14.59 KB
2    2026-05-08 13:13    14.59 KB
3    2026-05-04 15:34    13.37 KB
```

Version 1 is always the most recent. Compare version 1's timestamp against the stored timestamp in `files[path].last_synced_timestamp`. If the timestamp is different (newer), the file changed.

**If NO files changed across all tracked paths, exit immediately.** No Wrike API calls needed. This is the common case and should cost minimal tokens.

**If a file has no history** (new file, never synced by Obsidian), treat it as changed.

## Step 3: Parse Changed Files

For each changed file, read it using the Read tool. Parse based on file type:

### Parsing problems.md

Extract structured items from these sections:

**Active items** (items NOT under `## Resolved`):
- `### P<N>:` or `### P<N> -` entries (problems/issues) - these are the primary sync targets

**Items to SKIP (do not create Wrike tasks for these):**
- `### R<N>` entries (risks) - these are risk register items to watch, not work to do. They belong in the artifacts system for engineering context, not on a stakeholder kanban board.
- `### Q<N>` entries (questions/design decisions) - same reasoning. These get resolved through conversation, not through task completion.
- Items under `## Accepted Limitations`, `## Technical Debt`, `## Data Quality`, or `## Lower Priority / Informational` sections - these are context, not actionable work items for the board.

For each active P-item, extract:
- **ref**: `<feature_prefix>-<ID>` (e.g., `RC-P10`, `RI-P66`)
- **title**: The text after the ID prefix
- **priority**: Extract from `**Priority:**` if present
- **description**: Body text (first ~500 chars, truncated at sentence boundary)
- **type**: Map to Wrike Type field value:
  - Bug: describes broken behavior
  - Feature: describes missing capability
  - Enhancement: describes improvement to existing capability
  - Task: general work item

**Resolved items** (items under `## Resolved`):
- Match by ID prefix (P/R/Q + number)
- Extract resolution text after `**Resolution:**`

**Board-worthiness rule**: Only P-items under `## Open Issues` or `## Open Questions` (when the question blocks visible work) belong on the board. If a P-item is filed under a context section (Tech Debt, Data Quality, Accepted Limitations, Informational), it stays in Obsidian only.

### Parsing plan.md

Extract items at the `###` heading level (sprint/section headings).

For each `###` heading:
- **ref**: `<feature_prefix>-<normalized-heading>` (lowercase, hyphens, truncate at 40 chars)
- **title**: The heading text
- **status**: Determine from context:
  - Contains "(completed" or "(COMPLETE": Completed
  - Under `## Active Work` or referenced by `## Current State`: In Progress
  - Under `## Future Phases`: Not Started
  - Otherwise: Not Started
- **description**: Bullets under the heading as HTML `<ul><li>` list. First and second level only. Truncate at 2000 chars.
- **type**: Feature (sprint/phase headings) or Task (standalone items)

**Standalone bullets** outside sprint headings (e.g., under `### Quick Wins`):
- Each top-level bullet becomes its own task
- **ref**: `<feature_prefix>-<first-5-words-hyphenated>`
- **title**: Bullet text (first line only)
- **type**: Enhancement or Task

**Headings to SKIP:**
- `## Goal`, `## Scope Context`, `## Current State` - structural
- `## Key Decisions Outstanding` - tracked via problems.md Q items
- Design documentation headings within a sprint (context, not deliverables)

## Step 4: Query Existing Wrike Tasks

Use `wrike_search_tasks` to fetch all tasks in the project:
```
folderId: <config.wrike_project_id>
pageSize: 200
fields: ["briefDescription", "customFields", "responsibleIds"]
descendants: true
```

Build a lookup map: check each task title for a `[INITIALS:REF]` tag (e.g., `[TC:RC-P10]`). Map ref -> Wrike task ID.

Also use `task_map` from state as a secondary lookup.

## Step 5: Diff and Sync

For each parsed item from Step 3:

### New item (ref not in Wrike or task_map)

Create a Wrike task:
- **title**: `<title> [<config.owner_initials>:<ref>]` (e.g., `User list not sorted [TC:RC-P21]`)
- **folderId**: `<config.wrike_project_id>`
- **description**: HTML-formatted description. Do NOT include CDATA tags, XML declarations, or any wrapper markup. Use only simple HTML tags: `<b>`, `<i>`, `<br/>`, `<ul>`, `<li>`. Keep descriptions plain and clean.
- **dates**: `{"type": "Backlog"}` - always use Backlog type. Do NOT set start, due, or duration. Never estimate effort.
- **customFields**: Set Feature Area and Type using IDs from config
  - Feature Area (Multiple select): `"[\"<value>\"]"`
  - Type (Dropdown): the determined type string
- **importance**: High/Normal/Low mapped from priority
- **responsibles**: `["<config.default_assignee>"]`
- **customStatusId**: From config.statuses based on determined status

Record the Wrike task ID in task_map.

### Item resolved (ref in Wrike, item now in Resolved section)

Update the Wrike task:
- Set status to Completed (config.statuses.completed)
- Append resolution text: `<br/><br/><b>Resolution:</b> <text>`

### Item still active, task exists

Only update if something material changed (priority, title, description content). Don't update for whitespace or formatting-only changes. Preserve the `[INITIALS:ref]` tag in the title.

### Plan item disappeared (ref in task_map but heading gone from plan.md)

Read the feature's log file (from `tracked_files[].log` in config). Search the most recent entries for a `#### Completed Plan Items` section containing matching heading text. If found:
- Mark Wrike task Completed (config.statuses.completed)
- Extract the session narrative from the same log entry and append to the Wrike task description as a completion summary

If NOT found in the log, leave the task as-is. It may have been restructured.

## Step 6: Update State

Write the updated state file with:
- `config`: preserved unchanged
- `last_sync`: current ISO timestamp
- `files`: updated timestamps (version 1 timestamp for each file)
- `task_map`: all ref -> Wrike task ID mappings

## Step 7: Report

If changes were made:
```
Wrike sync complete:
- Created: N tasks (list refs)
- Updated: N tasks (list refs)
- Completed: N tasks (list refs)
- Skipped: N items (internal-only)
```

When running as a routine, keep the report minimal.

## Error Handling

- If a single Wrike API call fails, log the error and continue with remaining items.
- If Obsidian history commands fail for a specific file, skip that file and continue.
- If the config file is corrupted or missing `config`, report and exit.

## Manual Invocation

Optional arguments:
- `force` - Skip change detection, re-sync all files
- `dry-run` - Parse and diff but don't modify Wrike. Report what would change.
- `<feature>` - Only sync files for the named feature
