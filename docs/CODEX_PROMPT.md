# Film School Assistant — Codex Session State

**Last updated:** 2026-05-29

## Project

- Root: `/home/ashishki/Documents/dev/ai-stack/projects/film-school-assistant`
- Product state: operational private Telegram assistant; paused as an active
  product and maintained as a creative-professions portfolio case
- Historical roadmap: Phase 0-11 complete and archived
- Current execution model: maintenance backlog in `docs/tasks.md`

## Current System

- Single authorized Telegram user.
- Python service on private VPS.
- SQLite as canonical state.
- Local Whisper for transcription.
- LLMs used only for bounded extraction, review, reflection, and summaries.
- Project-first memory with explicit cross-project access.
- Verbatim evidence stored in `memory_items` with provenance.

## Current Priorities

1. Keep README and case-study framing aligned with runtime behavior.
2. Preserve privacy and inspectability.
3. Do not add new product scope while usage is paused.
4. Run production smoke checks only when docs/deploy/runtime changes are made.
5. Convert still-relevant archived audit findings into explicit backlog items before implementation.

## Rules For Future Work

- Read `docs/tasks.md` before choosing work.
- Read `docs/MEMORY_ARCHITECTURE.md` for memory, retrieval, continuity, recall, or reflection changes.
- Read `docs/COGNITION_MANIFEST.md` and `docs/VPS_COGNITION_VAULT.md` before cross-project cognition or vault-sync work.
- Keep structured SQLite state as source of truth.
- Treat `/srv/codex-entropy/repos/product-3/engineering-cognition-vault` as downstream navigation only; write canonical findings, evals, and decisions in this repo first.
- Keep retrieval project-first by default.
- Do not add web, multi-user, external calendar, vector search, or broad RAG behavior unless a current backlog item explicitly says so.
- Do not resume feature development unless `docs/tasks.md` resume criteria are met.
- Do not treat archived phase plans, audit reports, or eval packs as active instructions.
- Do not claim checks that were not run.

## Active Docs

- `README.md`
- `docs/README.md`
- `docs/COGNITION_MANIFEST.md`
- `docs/VPS_COGNITION_VAULT.md`
- `docs/tasks.md`
- `docs/PRODUCT_OVERVIEW.md`
- `docs/ARCHITECTURE.md`
- `docs/MEMORY_ARCHITECTURE.md`
- `docs/WORKFLOW_BOUNDARIES.md`
- `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/spec.md`
- `docs/DEPLOY.md`

## Archive

Historical task graphs, phase plans, review packs, audits, and old architecture
snapshots live under `docs/archive/`.
