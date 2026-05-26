# Cognition Manifest - Film School Assistant

---
artifact_kind: retrieval_manifest
project: film-school-assistant
source_repo: film-school-assistant
status: active
canonical: false
generated: false
tags: [private-assistant, sqlite-memory, cognition]
---

Version: 1.0
Last updated: 2026-05-25

## Purpose

Repo-local engineering cognition map for a private creative workflow assistant. This separates product memory about the user and projects from engineering governance memory.

## Authority Rules

- Canonical repo artifacts win over this manifest.
- User/project memory stored in SQLite is product data, not cross-project engineering cognition.
- Obsidian and generated indexes are optional navigation layers.

## Project Identity

| Field | Value |
|-------|-------|
| Primary shape | Private Telegram assistant with deterministic persistence and bounded LLM extraction/reflection |
| Governance level | Lean/Standard |
| Runtime tier | T1 private systemd service |
| Active profiles | Operational memory, bounded LLM extraction, private-data controls |

## Canonical Truth

| Surface | Path | Notes |
|---------|------|-------|
| Architecture | `docs/ARCHITECTURE.md` | System architecture |
| Contract | `docs/IMPLEMENTATION_CONTRACT.md` | Implementation rules |
| Task graph | `docs/tasks.md` | Current backlog |
| Session state | `docs/CODEX_PROMPT.md` | Workflow state |
| Decisions | `docs/DECISIONS.md` | Existing decision surface |
| Memory architecture | `docs/MEMORY_ARCHITECTURE.md` | Product memory model |
| Workflow boundaries | `docs/WORKFLOW_BOUNDARIES.md` | Deterministic vs LLM ownership |
| Deployment | `docs/DEPLOY.md`, `systemd/` | Runtime operations |
| Archive | `docs/archive/` | Historical reviews/evals |

## Retrieval Scopes

| Scope | Start here | Include next |
|-------|------------|--------------|
| Memory schema change | `docs/MEMORY_ARCHITECTURE.md`, migrations | schema, tests, decisions |
| LLM extraction/reflection | `docs/WORKFLOW_BOUNDARIES.md` | prompts, handlers, archived evals |
| Deployment issue | `docs/DEPLOY.md` | systemd units, ops-security, scripts |
| Reviewer packet | task ACs and contract | memory architecture, decisions, relevant tests |
| Product/private data boundary | memory architecture | ops-security and workflow boundaries |

## Local/VPS Agent Context Workflow

Agents do not automatically discover the cognition vault. The operator or orchestrator must pass a repo-local manifest, vault project map, or generated context packet path into the agent task.

Expected sibling layout on any machine that runs agents:

```text
ai-stack/
|-- projects/<repo>/
`-- engineering-cognition-vault/
```

Local project work:

```bash
cd ai-stack/engineering-cognition-vault
./scripts/sync_from_projects.sh --no-pull --commit --push
```

VPS project work:

1. Commit and push code, docs, evals, ADRs, findings, or postmortems in this repo.
2. Refresh the vault on the machine that owns vault sync:

```bash
cd ai-stack/engineering-cognition-vault
git pull --ff-only
./scripts/sync_from_projects.sh --commit --push
```

If an agent runs on the VPS, clone the vault next to `projects/` and pass packet paths explicitly:

```text
../engineering-cognition-vault/10-projects/<project>.md
../engineering-cognition-vault/90-context-packets/<role>-<project>-<scope>.md
```

Do not write canonical decisions, eval results, or findings directly into the vault. Write them into this repo first, then regenerate the vault.

---

## Known Gaps

| Gap | Impact | Migration step |
|-----|--------|----------------|
| Uses `docs/DECISIONS.md` instead of playbook `DECISION_LOG.md` | Decision retrieval is project-specific | Keep existing file; add decision log only for future major changes |
| No evidence index | Archived eval proof requires manual search | Add `docs/EVIDENCE_INDEX.md` if recurring findings resume |
| No ADR directory | Supersession lineage is weak | Add ADRs only for future architecture/runtime changes |

## Generated Artifacts

| Artifact | Path | Policy |
|----------|------|--------|
| Cognition index | `generated/cognition/index.json` | Optional generated artifact; exclude private DB exports |
| Context packets | `docs/context-packets/` | Commit only major review/regression packets |

