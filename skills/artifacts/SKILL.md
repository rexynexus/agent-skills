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

Walk up from the discovered `Artifacts/` folder until you find a sibling `_Agents/` folder. That folder lives at the Obsidian vault root (vault depth varies - the `_Agents/` folder is the anchor, not a fixed number of parents). Read `_Agents/README.md` from there - unless already read in this session.

Discovery fallback: If Glob does not find `_Agents/README.md` (Windows Glob behavior with underscore-prefixed folders is inconsistent), fall back to a Bash `ls`-based walk. List each parent directory level-by-level until a folder containing `_Agents/` appears. If you reach a drive root or the user's home directory without finding it, halt and ask the user to confirm the vault location. Do NOT proceed without the conventions doc - the skill's output schema depends on it.

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

Before writing the summary, compare plan.md's active headings against log.md's `#### Completed Plan Items` sections. If plan.md still contains items that log.md shows as completed, the plan has not been pruned per the lifecycle rules. Surface this as a "plan drift" note in the summary. Do not auto-fix - the user decides whether to clean up.

Present a brief summary of the project state:
- Active sprint and its status (what's done, what's pending)
- Key open problems relevant to the session
- What the last 1-2 sessions accomplished
- Any pending next steps from the last session
- Plan drift warning, if detected

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

Ensure frontmatter is correct on every file touched. Required fields per `_Agents/README.md`:
- `tags` - must include `project/<kebab-case-identifier>`. Check sibling files for the project's existing tag.
- `status` - one of `active`, `blocked`, `completed`, `superseded`. Reflects current state.
- `summary` - quoted string, max ~80 chars. Describes file contents, not the project.
- `editors` - list of agent names (e.g. `Claude-Opus-4.6`, `Codex-5.3`). Add your model if not already listed; do not remove prior entries.
- `created` - ISO date `YYYY-MM-DD`. Set on file creation, never changed afterward.
- `last-modified` - ISO date `YYYY-MM-DD`. Set to today's date on every edit.

If a file does not yet exist and the session produced content for it, create it with full frontmatter. Starter skeletons with the canonical headings are provided in `skills/artifacts/templates/` - copy the relevant template and fill in the content. Check sibling files in the Artifacts folder for the correct project tag.

If `_README.md` does not exist in the current Artifacts folder, create it with this exact content:

```
Agent workspace for this project. See [[_Agents/README]] for conventions.
```

This pointer note signals to any future agent reading the folder that the vault-level conventions doc is authoritative.

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

Entries use a letter-prefixed identifier scoped by type:

- `Q` - Open Questions (decisions needed, information gaps)
- `R` - Design Risks (known risks with severity, likelihood, mitigation)
- `P` - Problems (bugs, blockers, technical debt)

Each series numbers independently. Check existing entries to determine the next available number within the relevant series. Include: description, impact, priority, planned fix or resolution date. Risks additionally include severity, likelihood, and mitigation.

Move resolved items to a `## Resolved` section at the bottom with a one-line resolution note and date. Do not delete them - the record of how a question was answered or a risk was retired is load-bearing context for future agents.
