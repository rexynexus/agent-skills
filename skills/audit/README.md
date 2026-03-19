# /audit

Orchestration skill for security and code quality audits. Assesses the codebase, selects applicable skills from a registry, presents a plan for user approval via plan mode, then invokes each skill sequentially and produces a consolidated report.

## How it works

1. Enters plan mode
2. Scans the repo to detect languages, frameworks, infrastructure, database, auth patterns
3. Selects applicable skills from the registry based on what's detected
4. Presents a plan showing which skills will run, which are skipped, and why
5. On approval, invokes each skill via the `Skill` tool
6. Collates findings into a single severity-ranked report

## Installing dependency skills

The audit skill orchestrates other skills. It works with whatever subset is installed, but reports gaps. To get full coverage, install the external skills it references.

### From trailofbits/skills

Repository: https://github.com/trailofbits/skills

Install by copying skill folders into `~/.claude/skills/` (user-global) or `<project>/.claude/skills/` (project-scoped):

```bash
# Clone the repo
git clone https://github.com/trailofbits/skills.git /tmp/trailofbits-skills

# Copy the skills used by /audit
cp -r /tmp/trailofbits-skills/supply-chain-risk-auditor ~/.claude/skills/
cp -r /tmp/trailofbits-skills/insecure-defaults ~/.claude/skills/
cp -r /tmp/trailofbits-skills/sharp-edges ~/.claude/skills/
cp -r /tmp/trailofbits-skills/static-analysis ~/.claude/skills/
cp -r /tmp/trailofbits-skills/differential-review ~/.claude/skills/
cp -r /tmp/trailofbits-skills/debug-buttercup ~/.claude/skills/
cp -r /tmp/trailofbits-skills/agentic-actions-auditor ~/.claude/skills/
```

### Skill registry reference

| ID | Skill | Source | Category |
|---|---|---|---|
| DEPS-01 | `/supply-chain-risk-auditor` | trailofbits/skills | Dependencies |
| DEPS-02 | `/dep-pinning` | Built-in (planned) | Dependencies |
| SEC-01 | `/insecure-defaults` | trailofbits/skills | Secrets & Configuration |
| CODE-01 | `/sharp-edges` | trailofbits/skills | Code Quality |
| CODE-02 | `/static-analysis` | trailofbits/skills | Code Quality |
| AUTH-01 | `/auth-coverage` | Built-in (planned) | Auth |
| FRONT-01 | `/frontend-security` | Built-in (planned) | Frontend |
| INFRA-01 | `/infra-security` | Built-in (planned) | Infrastructure |
| INFRA-02 | `/debug-buttercup` | trailofbits/skills | Infrastructure (K8s) |
| CI-01 | `/agentic-actions-auditor` | trailofbits/skills | CI/CD & Automation |
| REVIEW-01 | `/differential-review` | trailofbits/skills | Code Review |

Skills marked "planned" are not yet built. The audit skill will note these as gaps in the plan.

### Minimum useful install

For a Python web app (FastAPI/Django) without Kubernetes or agentic CI:

```bash
cp -r /tmp/trailofbits-skills/supply-chain-risk-auditor ~/.claude/skills/
cp -r /tmp/trailofbits-skills/insecure-defaults ~/.claude/skills/
cp -r /tmp/trailofbits-skills/sharp-edges ~/.claude/skills/
cp -r /tmp/trailofbits-skills/differential-review ~/.claude/skills/
```

These four cover dependency risk, secrets/config, dangerous code patterns, and PR-level review.

## Adding new skills to the registry

Edit `SKILL.md` and add a row to the appropriate category table in the Skill Registry section. Each entry needs:

- **ID**: Category prefix + sequential number (e.g., `CODE-03`)
- **Skill**: The `/skill-name` as invoked via the Skill tool
- **Source tag**: `[external]` or `[built-in]` or `[built-in, planned]`
- **Applies when**: Condition for the skill to be selected during assessment
- **What it covers**: Brief description of what the skill checks

The audit skill dynamically checks which registered skills are installed at plan time, so adding a registry entry for an uninstalled skill is safe - it will show up as a gap in the plan.
