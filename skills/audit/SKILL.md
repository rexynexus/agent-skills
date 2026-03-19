---
name: audit
description: Security and code quality audit. Assesses the codebase, selects relevant skills from the registry, presents a plan for approval, then invokes each skill sequentially.
argument-hint: "[scope or focus area]"
---

# Audit

Orchestrates a security and code quality audit by selecting and invoking registered skills. Uses plan mode as the orchestration layer: assess the repo, pick applicable skills, present a tailored plan, invoke each skill on approval.

## Arguments

`$ARGUMENTS` can be:
- Blank - full audit, all applicable skills
- A scope keyword: `dependencies`, `secrets`, `sql`, `auth`, `api`, `frontend`, `infra`, `all`
- A file or directory path to focus the audit on a specific area

## Step 1: Enter plan mode

Call the `EnterPlanMode` tool immediately.

## Step 2: Assess the codebase

Quickly determine what's in the repo to decide which skills apply:

1. **Language/framework:** Check for `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, etc. Read entry point imports.
2. **Infrastructure:** Check for `Dockerfile`, `docker-compose.yml`, `.github/workflows/`, Terraform/Bicep/ARM templates, deployment/startup scripts.
3. **Database:** Grep for SQL queries, ORM usage, migration files, connection strings.
4. **Auth:** Grep for auth middleware, JWT, session management, OAuth/OIDC, API key handling.

## Step 3: Select skills from the registry

Based on the assessment, select applicable skills from the registry below. Skip skills that don't apply to this codebase.

If `$ARGUMENTS` specifies a scope, only select skills within that scope.

### Skill Registry

Each entry maps an audit area to a skill that can be invoked via the `Skill` tool. Skills marked `[external]` are from third-party repos (e.g., trailofbits/skills) and must be installed separately. Skills marked `[built-in]` ship with this repo or the user's skill library.

#### Dependencies

| ID | Skill | Applies when | What it covers |
|---|---|---|---|
| DEPS-01 | `/supply-chain-risk-auditor` [external] | Any dependency file exists | Vulnerable, unmaintained, or typosquatted packages. CVE checks, maintainer analysis, download stats. |
| DEPS-02 | `/dep-pinning` [built-in, planned] | Any dependency file exists | Unpinned versions, missing lockfiles, loose bounds. |

#### Secrets & Configuration

| ID | Skill | Applies when | What it covers |
|---|---|---|---|
| SEC-01 | `/insecure-defaults` [external] | Always | Hardcoded secrets, debug flags, permissive CORS, disabled security middleware, exposed credentials. |

#### Code Quality & Dangerous Patterns

| ID | Skill | Applies when | What it covers |
|---|---|---|---|
| CODE-01 | `/sharp-edges` [external] | Always | Error-prone APIs, dangerous configurations, footgun designs. Covers SQL injection, unsafe deserialization, template injection, file path traversal. |
| CODE-02 | `/static-analysis` [external] | Always | CodeQL, Semgrep, SARIF-based analysis. Sets up and runs static analysis tooling. |

#### Authentication & Authorization

| ID | Skill | Applies when | What it covers |
|---|---|---|---|
| AUTH-01 | `/auth-coverage` [built-in, planned] | API routes and auth middleware detected | Unprotected endpoints, missing auth middleware, IDOR patterns, role check gaps. |

#### Frontend

| ID | Skill | Applies when | What it covers |
|---|---|---|---|
| FRONT-01 | `/frontend-security` [built-in, planned] | Frontend JS/TS exists | XSS vectors (`dangerouslySetInnerHTML`, `innerHTML`, `v-html`), client-side secrets in bundles. |

#### Infrastructure & CI/CD

| ID | Skill | Applies when | What it covers |
|---|---|---|---|
| INFRA-01 | `/infra-security` [built-in, planned] | Dockerfile, CI config, or startup scripts exist | Container security (root user, unpinned base images), CI/CD permissions, startup script safety (CRLF, missing error handling, race conditions). |
| INFRA-02 | `/debug-buttercup` [external] | Kubernetes deployments detected (k8s manifests, Helm charts, kubectl configs) | Kubernetes deployment diagnostics. Pod health, resource limits, networking, ingress, persistent volumes, RBAC. |

#### CI/CD & Automation

| ID | Skill | Applies when | What it covers |
|---|---|---|---|
| CI-01 | `/agentic-actions-auditor` [external] | `.github/workflows/` exist AND workflows use AI agents, LLM calls, or agentic patterns (e.g., auto-merge bots, AI-generated PRs, agent-driven deployments) | Examines GitHub Actions for AI agent vulnerabilities: prompt injection via issue/PR bodies, excessive permissions granted to agent steps, missing human-in-the-loop gates, secret exposure to agent contexts. |

#### Code Review (Differential)

| ID | Skill | Applies when | What it covers |
|---|---|---|---|
| REVIEW-01 | `/differential-review` [external] | Git history available | Security-focused review of recent code changes with git history analysis. |

### Handling missing skills

During plan construction, check which skills are actually installed. For each registry entry:
1. If the skill is installed: include it in the plan with its invocation command
2. If the skill is NOT installed and marked `[external]`: note it as "not installed - skip or install from [repo]" in the plan
3. If the skill is NOT installed and marked `[built-in, planned]`: note it as "not yet built - skip" in the plan

This lets the audit run with whatever subset of skills is available. The plan makes gaps visible so the user can decide whether to install missing skills before proceeding.

## Step 4: Build the plan

Write the plan to the plan file:

```markdown
# Security Audit Plan

## Scope
[Repo name, languages, frameworks, key components identified in assessment]

## Skills to Run
| # | ID | Skill | Target | Status |
|---|---|---|---|---|
| 1 | SEC-01 | `/insecure-defaults` | Full repo | Installed |
| 2 | DEPS-01 | `/supply-chain-risk-auditor` | requirements.txt, package.json | Installed |
| 3 | CODE-01 | `/sharp-edges` | backend/, frontend/ | Installed |
| ... | | | | |

## Skills Skipped
| ID | Skill | Reason |
|---|---|---|
| FRONT-01 | `/frontend-security` | Not yet built |
| AUTH-01 | `/auth-coverage` | Not yet built |

## Execution Order
[Numbered list matching the Skills to Run table]
```

## Step 5: Exit plan mode

Call `ExitPlanMode` to present the plan for user approval. The user can remove skills they don't want, add scope constraints, or request installation of missing skills before approving.

## Step 6: Execute skills

After approval, invoke each selected skill sequentially using the `Skill` tool:

1. Use `TodoWrite` to track progress through the skill list
2. For each skill in the approved plan:
   - Invoke it: e.g., `Skill(skill="supply-chain-risk-auditor")`
   - Wait for it to complete
   - Capture its findings
   - Mark the step complete in the todo list
3. Accumulate all findings across skills

## Step 7: Consolidated report

After all skills complete, produce a single consolidated report:

### Summary
- Skills run / skills clean / skills with findings
- Total findings by severity (Critical / High / Medium / Low / Info)

### Findings by Skill
For each skill that produced findings, list them:

**`/skill-name` (ID): [n findings]**

| # | Severity | Location | Finding | Recommendation |
|---|----------|----------|---------|----------------|
| 1 | High | file.py:42 | Description | Fix |

### Clean Skills
List skills that found no issues (confirms coverage).

### Gaps
List skills that were skipped (not installed or not applicable) so the user knows what wasn't covered.

### Recommended Next Steps
Prioritized action items. If external skills need installation, list the install commands.

## Step 8: Optionally update artifacts

If the project has an `Artifacts/` folder, offer to invoke `/artifacts problems` to record findings in `problems.md`.
