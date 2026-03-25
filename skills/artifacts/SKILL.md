---
name: artifacts
description: Load project context or save session work to the standard Obsidian artifact files (plan.md, design.md, problems.md, log.md, resources.md).
argument-hint: "[load | save | write <file> | description]"
---

# Artifacts

Load project context at session start, or save session work to the standard artifact files. The five primary artifacts are:

- **plan.md** - Project plan, phases, sprints, deliverables
- **design.md** - Technical architecture, schemas, data flows
- **problems.md** - Open issues, blockers, risk register
- **log.md** - Chronological session log (newest first)
- **resources.md** - Reference links, API docs, external material

## Arguments and Modes

`$ARGUMENTS` determines the mode:

| Invocation | Mode | Behavior |
|---|---|---|
| `/artifacts load` | load | Read targeted portions of artifacts to establish session context |
| `/artifacts save` | save | Update all artifacts that changed during the session |
| `/artifacts write log` | write | Update a single named artifact only |
| `/artifacts write plan` | write | Update a single named artifact only |
| `/artifacts added X, fixed Y` | save | Save with description as context hint |
| `/artifacts` (no arg, no prior work) | load | Auto-detect: no session work done yet = load |
| `/artifacts` (no arg, work done) | save | Auto-detect: session work exists = save |

## Steps: Load Mode

Goal: Establish project context with minimum reads. Do NOT read entire large files.

### 1. Locate the Artifacts folder

Find the project's `Artifacts/` folder. Check these locations in order:
- Any directory in the current workspace or additional working directories that contains an `Artifacts/` subfolder
- Look for sibling files like `plan.md`, `log.md`, `design.md` as confirmation

If multiple `Artifacts/` folders exist across working directories, identify which project is relevant from the current session's context. If ambiguous, ask the user.

### 2. Read the _Agents/README.md conventions

If `_Agents/README.md` exists in the Obsidian vault root (typically two levels above `Artifacts/`), read it - unless already read in this session.

### 3. Read artifacts (targeted)

Read each artifact using the minimum necessary to establish context:

**plan.md:**
- Read the first ~50 lines (frontmatter, objective, current state summary)
- Grep for the active sprint heading, then read just that section (typically 30-60 lines)
- Do NOT read completed sprints

**log.md:**
- Read frontmatter + header (first ~15 lines)
- Read the most recent 1-2 sessions only (use offset/limit). Typically the first 100-200 lines after the header.
- Do NOT read the full file

**problems.md:**
- Full read (typically small, <200 lines). If larger, read only "Decisions Needed" and "Technical Debt" sections.

**design.md:**
- Read frontmatter + architecture overview (first ~50 lines)
- Only read specific sections if the user's task requires them (use Grep to locate, then read that range)
- Do NOT read the full file by default

**resources.md:**
- Skip unless the user's task involves external references

### 4. Summarize context

Present a brief summary of the project state:
- Active sprint and its status (what's done, what's pending)
- Key open problems relevant to the session
- What the last 1-2 sessions accomplished
- Any pending next steps from the last session

## Steps: Save Mode

Goal: Record session work to the appropriate artifacts. Minimize reads - only read what you need to anchor edits.

### 1. Locate the Artifacts folder

Same as Load Mode step 1.

### 2. Read the _Agents/README.md conventions

Same as Load Mode step 2.

### 3. Determine what needs updating

Based on the current conversation context and any description in `$ARGUMENTS`:
- If a description was given, use it as a context hint for which files are affected
- Otherwise, review the session's work and identify which files have new information to record

**Skip files that don't need changes.** Not every session touches every artifact:
- If no new schema, architecture, or API changes: skip design.md
- If no new problems discovered or resolved: skip problems.md
- If no new external resources: skip resources.md
- log.md and plan.md almost always need updating after a working session

### 4. Read only what you need to edit

For each file that needs updating, read only the portion required to make the edit:

**log.md:** Read only the frontmatter + first heading (first ~15 lines) to anchor the prepend. Do NOT re-read the body.

**plan.md:** Grep for the active sprint section. Read just that range (offset/limit). Edit in place.

**design.md:** Grep for the section being modified. Read just that range. Edit in place.

**problems.md:** Full read is fine (small file). Add new entries or mark resolved.

**resources.md:** Full read is fine. Append new entries.

### 5. Apply updates

Edit each file. Preserve existing content. Follow the file-specific conventions below.

Ensure frontmatter is correct on every file touched:
- `status` reflects current state
- `summary` is accurate and under ~80 chars
- `editors` list is updated if a new agent has handled the file from what is already listed
- `last-modified` is set to today's date

If a file does not yet exist and the session produced content for it, create it with full frontmatter per the `_Agents/README.md` conventions. Check sibling files for the correct project tag.

### 6. Report

After updating, provide a summary:

**Updated artifacts:**
- `plan.md` - [what changed]
- `log.md` - [what changed]

**No changes needed:**
- `resources.md` - [why not]

## Steps: Write Mode

Goal: Update a single named artifact. Follows the same read and edit patterns as Save Mode, but only for the specified file.

Parse the file name from `$ARGUMENTS` (e.g. `write log`, `write plan`, `write design`). Apply the same targeted read and edit steps from Save Mode for that file only. Report what changed.

## File-Specific Conventions

### log.md entry structure

Entries use a strict two-level heading hierarchy:

```markdown
## YYYY-MM-DD

### Session N: Short Descriptor

Content...

### Session N-1: Short Descriptor

Content...

---

## YYYY-MM-DD (previous day)

### Session L: Short Descriptor

Content...

### Session L-1: Short Descriptor

Content...
```

Rules:
- `##` is the date heading. One per day. Newer days at top.
- `###` is the session heading under that date. Numbered, newest first within the day.
- `---` horizontal rule between days for visual separation.
- If today's date heading already exists, add the new session under it (as the first `###`). Do NOT create a duplicate `##` for the same date.
- A new day starts a new session count. 

### log.md entry content

Target length: 10-30 lines per session. Record at the feature/decision level, not the per-field level.

Include:
- What was built, fixed, or decided (feature-level, not line-level)
- Key decisions and their rationale
- Findings that affect future work
- Pending next steps

Each session entry ends with a `#### Completed Plan Items` subsection containing the exact text of any plan.md items completed during that session (see plan.md lifecycle below). This subsection is the archive mechanism for plan.md - it preserves the original planned work alongside the narrative of what actually happened, enabling auditability.

Do NOT include in the narrative:
- Exhaustive per-file or per-field change lists (that's what git diff is for)
- Routine steps that are obvious from the code
- Rehashing content already captured in plan.md or problems.md

### plan.md

plan.md is a living to-do list, not a historical record. It contains only incomplete and in-progress work.

**Formatting:**
- Use bullets (`-`) at appropriate indentation levels. No checkboxes (`- [ ]` / `- [x]`).
- Partially completed items stay in plan.md with notes on progress.

**Lifecycle:**
- When an item is completed during a session, **cut** it from plan.md and **paste** it into the log entry's `#### Completed Plan Items` subsection, preserving its exact original formatting (bullets, sub-bullets, indentation).
- When all items under a sprint/phase heading are completed and moved to the log, remove the heading itself. Empty structural headings are detritus.
- The "Current State" summary at the top of plan.md should be updated to reflect the new active work.

This keeps plan.md lean and scannable. The full history of what was planned and completed is recoverable from log.md entries.

### problems.md

Each entry has a P-number identifier (e.g. P49). Check existing entries to determine the next available number. Include: description, impact, priority, planned fix or resolution date.
