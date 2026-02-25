---
name: artifacts
description: Update the standard Obsidian project artifact files (plan.md, design.md, problems.md, log.md, resources.md) based on the current session's work.
argument-hint: "[file-or-description]"
disable-model-invocation: true
---

Update the standard project artifact files based on the current session's work. The five primary artifacts are:

- **plan.md** - Project plan, phases, sprints, deliverables
- **design.md** - Technical architecture, schemas, data flows
- **problems.md** - Open issues, blockers, risk register
- **log.md** - Chronological session log (newest first)
- **resources.md** - Reference links, API docs, external material

## Arguments

`$ARGUMENTS` can be:
- A specific file name (e.g. `log`, `plan`, `design`)
- A description of what changed (e.g. "added contract sync, fixed date bug")
- Blank or "all" to review and update whichever files need it based on the current session

## Steps

### 1. Locate the Artifacts folder

Find the project's `Artifacts/` folder. Check these locations in order:
- Any directory in the current workspace or additional working directories that contains an `Artifacts/` subfolder
- Look for sibling files like `plan.md`, `log.md`, `design.md` as confirmation

If multiple `Artifacts/` folders exist across working directories, identify which project is relevant from the current session's context. If ambiguous, ask the user.

### 2. Read the _Agents/README.md conventions

If `_Agents/README.md` exists in the Obsidian vault root (typically two levels above `Artifacts/`), read it. Follow all conventions for frontmatter, naming, status, and file lifecycle.

### 3. Read existing artifacts

Read the frontmatter and content of each artifact file that exists in the folder. Note:
- Current frontmatter fields (tags, status, created, agent, summary)
- Last entry dates in log.md
- Current state of plan.md phases/sprints
- Open items in problems.md

### 4. Determine what needs updating

Based on the current conversation context and `$ARGUMENTS`:
- If a specific file was named, focus on that file
- If a description was given, determine which files are affected
- If "all" or blank, review the session's work and update every file that has new information to record

For each file, the appropriate update type:

**plan.md**: Update phase status, sprint progress, add new phases/sprints, mark completed items, update dependencies and deliverables summary.

**design.md**: Update schemas, add new tables/fields, revise data flows, update API documentation, correct inaccuracies found during implementation.

**problems.md**: Add new issues discovered, mark resolved issues, update risk assessments, add blockers. Each entry: description, impact, status (open/resolved/accepted), date.

**log.md**: Prepend a new dated entry summarizing the session's work. Include: what was done, decisions made, findings, next steps. Concise but complete enough that a future reader understands what happened and why.

**resources.md**: Add new reference links, API documentation, external resources discovered during the session.

### 5. Apply updates

Edit each file that needs changes. Preserve existing content. Append or prepend as appropriate (log.md is newest-first, others are structured by topic).

Ensure frontmatter is correct on every file touched:
- `status` reflects current state
- `summary` is accurate and under ~80 chars
- `agent` field is set (use `Claude` for Claude Code sessions)
- `editors` list is updated if a different agent originally created the file
- `last-modified` is set to today's date

If a file does not yet exist and the session produced content for it, create it with full frontmatter per the `_Agents/README.md` conventions. Check sibling files for the correct project tag.

### 6. Report

After updating, provide a summary:

**Updated artifacts:**
- `plan.md` - [what changed]
- `log.md` - [what changed]

**No changes needed:**
- `resources.md` - [why not]
