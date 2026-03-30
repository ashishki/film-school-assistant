# Film School Assistant — Non-Functional Requirements

Version: 1.0
Last updated: 2026-03-30
Status: Initial retrofit baseline

---

## 1. Operational NFRs

| Metric | Target / Guardrail | Baseline Status |
|--------|---------------------|-----------------|
| Authorized-user enforcement | 100% of sensitive flows guarded | Expected by design; re-verify in tests |
| Reminder delivery reliability | Failed sends are logged and retryable | Measurement path exists; baseline not yet refreshed |
| Weekly summary uniqueness | At most one summary per intended period | Known gap under hardening; baseline pending |
| Service recovery | Recoverable by restart and DB restore | Operational posture only; no fresh drill recorded |

---

## 2. AI / Inference NFRs

| Metric | Target / Guardrail | Baseline Status |
|--------|---------------------|-----------------|
| Cost per routine chat exchange | Keep low-cost model on default chat/tool path | Exact current cost not recorded yet |
| Strong-model escalation rate | Limited to explicit review flows | Not yet measured explicitly |
| AI-path latency | Chat path should feel responsive; review path may be slower | Not yet measured explicitly |
| Failed AI call rate | Failures should degrade safely, not corrupt state | Error handling exists; baseline pending |
| Unnecessary inference rate | Avoid summary or review calls when deterministic guard can exit early | Known gap tracked in T62 |

---

## 3. Measurement Procedure

Until automated telemetry is added, record baselines manually:

1. run the relevant test or script in the project environment
2. capture whether the deterministic guard prevented unnecessary work
3. record measured latency or a bounded observation where feasible
4. note model class used and the pricing source/date when cost estimates are updated

Approved comparison sources may include vendor docs and model-pricing aggregators, but the
accepted decision must be written back into `docs/ARCHITECTURE.md`.

---

## 4. Current Gaps

- no explicit refreshed latency baseline was captured during this retrofit pass
- no explicit per-path cost estimate is recorded yet
- local verification was blocked in the current shell because project dependencies are absent

These gaps are acceptable for the retrofit baseline, but they should be closed before making
claims about operational cost or reliability improvements.
