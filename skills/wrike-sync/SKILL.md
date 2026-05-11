---
name: wrike-sync
description: Sync Obsidian artifact files (problems.md, plan.md) to Wrike kanban board for Mission Control development visibility. Detects changes via Obsidian sync history, creates/updates/resolves Wrike tasks. Designed for hourly scheduled invocation via Sonnet.
---

# Wrike Artifact Sync

Sync problems.md and plan.md artifacts from the Obsidian Elevate vault to the Mission Control Development Wrike project. This skill is designed to run cheaply and autonomously - exit as early as possible when there's nothing to do.

## Configuration

```
Wrike Project ID: MQAAAAEJjPTJ
Wrike Space: D&I Development (MQAAAABqaDqV)
Tim's Contact ID: KUAWJIMO

Custom Fields:
  Feature Area (Multiple): IEAGTA7VJUAMKLOK
  Type (Dropdown): IEAGTA7VJUAMKLOO

Statuses (Default Workflow):
  Not Started: IEAGTA7VJMAAAAAA
  In Progress: IEAGTA7VJMF3QJM6
  Blocked: IEAGTA7VJMF3UAEK
  Completed: IEAGTA7VJMAAAAAB
  On Hold: IEAGTA7VJMAAAAAC
  Cancelled: IEAGTA7VJMAAAAAD

Obsidian Vault: Elevate
State File: 03 - Projects/Personal/Wrike Development Board/Artifacts/.wrike-sync-state.json

Tracked Files:
  Role Control:
    problems: 03 - Projects/Corporate/01024 - IMIT/Role Control/Artifacts/problems.md
    plan: 03 - Projects/Corporate/01024 - IMIT/Role Control/Artifacts/plan.md
    feature_area: Role Control
  Revenue Insights:
    problems: 03 - Projects/Corporate/01024 - IMIT/Revenue Insights/Artifacts/problems.md
    plan: 03 - Projects/Corporate/01024 - IMIT/Revenue Insights/Artifacts/plan.md
    feature_area: Revenue Insights
  Workplanning:
    problems: 03 - Projects/Corporate/01024 - IMIT/Workplanning/Artifacts/problems.md
    plan: 03 - Projects/Corporate/01024 - IMIT/Workplanning/Artifacts/plan.md
    feature_area: Workplanning
```

## Step 0: Obsidian Gate

Run:
```
obsidian vault="Elevate" sync:status
```

If this command fails (exit code != 0), Obsidian is not running. Log the following to the Wrike Dev Board log.md and exit immediately:

```
Wrike sync skipped: Obsidian not running.
```

Do NOT attempt any file reads or Wrike operations.

## Step 1: Load State

Read the state file at the full path:
`C:\Users\TimothyCrockett\Documents\Obsidian\Elevate\03 - Projects\Personal\Wrike Development Board\Artifacts\.wrike-sync-state.json`

If it does not exist, treat all files as new (no previous sync). The state file structure:

```json
{
  "last_sync": "2026-05-11T17:00:00",
  "files": {
    "<vault-relative-path>": {
      "last_synced_timestamp": "2026-05-08 13:18",
      "last_synced_size": "14.59 KB"
    }
  },
  "task_map": {
    "RC-P10": "WRIKE_TASK_ID",
    "RC-R1": "WRIKE_TASK_ID",
    "RC-Sprint-1": "WRIKE_TASK_ID"
  }
}
```

## Step 2: Change Detection

For each tracked file, run:
```
obsidian vault="Elevate" history path="<vault-relative-path>"
```

This returns output like:
```
<path>
1    2026-05-08 13:18    14.59 KB
2    2026-05-08 13:13    14.59 KB
3    2026-05-04 15:34    13.37 KB
```

Version 1 is always the most recent. Compare version 1's timestamp against the stored `last_synced_timestamp` for that file. If the timestamp is different (newer), the file changed.

**If NO files changed across all tracked paths, exit immediately.** No Wrike API calls needed. This is the common case and should cost minimal tokens.

**If a file has no history** (new file, never synced by Obsidian), treat it as changed.

## Step 3: Parse Changed Files

For each changed file, read it using the Read tool. Parse based on file type:

### Parsing problems.md

Extract structured items from these sections:

**Active items** (items NOT under `## Resolved`):
- `### P<N>:` or `### P<N> -` entries under any heading (Open Issues, Open Questions, Active Risks, Technical Debt, Data Quality, etc.)
- `### R<N>:` or `### R<N> -` entries (risks)
- `### Q<N>:` or `### Q<N> -` entries (questions) - only if they represent actionable work, not pure design decisions

For each active item, extract:
- **ref**: `<feature-prefix>-<ID>` (e.g., `RC-P10`, `RI-P66`, `WP-R1`)
  - Feature prefixes: `RC` = Role Control, `RI` = Revenue Insights, `WP` = Workplanning
- **title**: The text after the ID prefix (e.g., "Pages show broken UI instead of access-denied")
- **priority**: Extract from `**Priority:**` line if present, else derive from `**Severity:**` for risks
- **description**: The body text of the item (first ~500 chars, truncated cleanly at sentence boundary)
- **type**: Map the item prefix to a Wrike Type value:
  - P items: examine content - if it describes broken behavior, Type = Bug; if it describes missing capability, Type = Feature; if it describes improvement to existing, Type = Enhancement; otherwise Type = Task
  - R items: Type = Task (risk mitigation)
  - Q items: Type = Task (design decision)

**Resolved items** (items under `## Resolved`):
- Match by their ID prefix (P/R/Q + number)
- Extract the resolution text (one-liner after `**Resolution:**`)

**Stakeholder filter**: Skip items that are purely internal engineering concerns with no user-visible impact. Indicators of internal-only items:
- Severity Low AND Likelihood Low with no user-facing symptom described
- Items about code organization, test infrastructure, or developer tooling
- Items explicitly marked as "acceptable for Phase N" with no planned fix

When in doubt, include rather than exclude.

### Parsing plan.md

Extract items at the `###` heading level (sprint/section headings). These are the right granularity for Wrike tasks.

For each `###` heading:
- **ref**: `<feature-prefix>-<normalized-heading>` (e.g., `RC-Sprint-1`, `WP-Phase-2-Wrike-API`)
  - Normalize: lowercase, replace spaces with hyphens, remove special chars, truncate at 40 chars
- **title**: The heading text (e.g., "Sprint 1: Plugin Skeleton + Query Execution")
- **status**: Determine from context:
  - If the heading contains "(completed" or "(COMPLETE": Completed
  - If it's under `## Active Work` or `## Current State` references it: In Progress
  - If it's under `## Future Phases`: Not Started
  - Otherwise: Not Started
- **description**: Concatenate the bullets under this heading into an HTML list for the Wrike task description. Use `<ul><li>` format. Include first-level and second-level bullets only. Truncate at 2000 chars.
- **type**: Feature (for sprint/phase headings) or Task (for standalone items like Quick Wins)

**Standalone bullets** outside sprint headings (e.g., under `### Quick Wins` or `### Phase 1 Remaining`):
- Each top-level bullet (`- `) becomes its own task
- **ref**: `<feature-prefix>-<first-5-words-hyphenated>`
- **title**: The bullet text (first line only)
- **type**: Enhancement or Task based on content

**Heading-level items to SKIP:**
- `## Goal`, `## Scope Context`, `## Current State` - structural, not work items
- `## Key Decisions Outstanding` - tracked via problems.md Q items
- `### Scoping Rules`, `### Twenty CRM Setup` and similar design documentation headings within a sprint - context, not separate deliverables

## Step 4: Query Existing Wrike Tasks

Use `wrike_search_tasks` to fetch all tasks in the project:
```
folderId: MQAAAAEJjPTJ
pageSize: 200
fields: ["briefDescription", "customFields", "responsibleIds"]
descendants: true
```

Build a lookup map: for each task, check if its title contains a `[REF]` tag (e.g., `[RC-P10]`). Map ref -> Wrike task ID.

Also load the `task_map` from the state file as a secondary lookup.

## Step 5: Diff and Sync

For each parsed item from Step 3, determine the action:

### New item (ref not in Wrike or state map)

Create a Wrike task:
- **title**: `<title> [<ref>]` (e.g., `Pages show broken UI instead of access-denied [RC-P10]`)
- **folderId**: `MQAAAAEJjPTJ`
- **description**: HTML-formatted description from parsing
- **customFields**: Set Feature Area and Type
  - Feature Area value format for Multiple select: `"[\"<value>\"]"` (e.g., `"[\"Role Control\"]"`)
  - Type value: the determined type string
- **importance**: Map priority to Wrike importance (High -> High, Medium -> Normal, Low -> Low)
- **responsibles**: `["KUAWJIMO"]`
- **customStatusId**: Based on determined status

Record the new Wrike task ID in the task_map.

### Item resolved (ref exists in Wrike, item now in Resolved section)

Update the Wrike task:
- Set status to Completed (`IEAGTA7VJMAAAAAB`)
- Append resolution text to the task description:
  ```html
  <br/><br/><b>Resolution:</b> <resolution text>
  ```

### Item still active, task exists (ref in Wrike, item still in active section)

Check if anything material changed:
- Priority/severity changed -> update importance
- Title changed -> update title (preserve the [ref] tag)
- Description content materially different -> update description

Only call `wrike_update_task` if something actually changed. Don't update for whitespace or formatting-only changes.

### Plan item disappeared (ref was in task_map but heading no longer in plan.md)

The item was likely completed and moved to log.md. Check the relevant log.md for a `#### Completed Plan Items` section containing text that matches the heading. If found:
- Mark the Wrike task as Completed
- Add the session narrative from the log entry as a completion note in the description

If NOT found in log.md either, do NOT auto-complete. Leave the task as-is. It may have been restructured rather than completed.

## Step 6: Update State

Write the updated state file with:
- `last_sync`: current ISO timestamp
- `files`: updated timestamps from Step 2 (version 1 timestamp for each file)
- `task_map`: all ref -> Wrike task ID mappings (existing + newly created)

Write to:
`C:\Users\TimothyCrockett\Documents\Obsidian\Elevate\03 - Projects\Personal\Wrike Development Board\Artifacts\.wrike-sync-state.json`

## Step 7: Report

If any changes were made, output a brief summary:
```
Wrike sync complete:
- Created: N tasks (list refs)
- Updated: N tasks (list refs)
- Completed: N tasks (list refs)
- Skipped: N items (internal-only)
```

If running as a routine (not manual invocation), keep the report minimal.

## Error Handling

- If any single Wrike API call fails, log the error and continue with remaining items. Do not abort the entire sync for one failed task.
- If Obsidian history commands fail for a specific file, skip that file and continue with others.
- If the state file is corrupted or unparseable, log a warning and treat it as a fresh sync (no previous state). This will create duplicate tasks if tasks already exist - accept this as preferable to losing sync state silently.

## Manual Invocation

When invoked manually (not via routine), the skill accepts optional arguments:
- `force` - Skip change detection, re-sync all files regardless of history timestamps
- `dry-run` - Parse and diff but don't create/update any Wrike tasks. Report what would change.
- `<feature>` - Only sync files for the named feature (e.g., `role-control`, `revenue-insights`)
