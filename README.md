Agent skills by rexynexus.

These skills follow the [Agent Skills specification](https://agentskills.io/specification) so they can be used by any skills-compatible agent, including Claude Code and Codex CLI.

## Installation

### Marketplace

```
/plugin marketplace add rexynexus/agent-skills
/plugin install agent-skills@rexynexus
```

### Manually

#### Claude Code

Copy a skill directory into `~/.claude/skills/` (user-global) or `<project>/.claude/skills/` (project-scoped). See more in the [official Claude Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

#### Codex CLI

Copy the skill directories into your Codex skills path (typically `~/.codex/skills`). See the [Agent Skills specification](https://agentskills.io/specification) for the standard skill format.

## Skills

| Skill | Description |
|-------|-------------|
| [artifacts](skills/artifacts/) | Update standard Obsidian project artifact files (plan.md, design.md, problems.md, log.md, resources.md) based on the current session's work |
| [audit](skills/audit/) | Security and code quality audit orchestrator. Depends on external skills from [trailofbits/skills](https://github.com/trailofbits/skills) (see [audit/README.md](skills/audit/README.md)) |
| [inspect-twenty](skills/inspect-twenty/) | Inspect a Twenty CRM object type by querying the live API for metadata and data analysis |
| [obsidian-charts](skills/obsidian-charts/) | Create and edit charts in Obsidian using the Charts plugin (bar, line, pie, doughnut, radar, polarArea, scatter, bubble, sankey) |
