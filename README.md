# agent-skills

Custom skills for Claude Code. Each subdirectory contains a `SKILL.md` that defines the skill's name, trigger conditions, and instructions.

## Skills

| Skill | Description |
|-------|-------------|
| [artifacts](artifacts/) | Update standard Obsidian project artifact files (plan.md, design.md, problems.md, log.md, resources.md) based on the current session's work |
| [audit](audit/) | Security and code quality audit orchestrator. Assesses the codebase, selects applicable skills from a registry, presents a plan, then invokes each sequentially. Depends on external skills from [trailofbits/skills](https://github.com/trailofbits/skills) (see [audit/README.md](audit/README.md) for install instructions and the full skill registry) |
| [inspect-twenty](inspect-twenty/) | Inspect a Twenty CRM object type by querying the live API for metadata and data analysis |
| [obsidian-charts](obsidian-charts/) | Create and edit charts in Obsidian using the Charts plugin (bar, line, pie, doughnut, radar, polarArea, scatter, bubble, sankey) |

## Installation

Copy a skill directory into `~/.claude/skills/` (user-global) or `<project>/.claude/skills/` (project-scoped):

```bash
cp -r obsidian-charts ~/.claude/skills/
```

Or install all:

```bash
cp -r */ ~/.claude/skills/
```

## Structure

Each skill follows the [Agent Skills specification](https://agentskills.io/specification):

```
skill-name/
  SKILL.md      # Frontmatter (name, description) + full skill prompt
  README.md     # Optional usage docs
```
