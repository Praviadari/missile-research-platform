# Code Quality Deep Audit — Missile Research Platform v2

| Field | Value |
| ----- | ----- |
| Initial audit | 2026-08-06 |
| Remediation pass | 2026-08-06 |
| Scope | Full repository on `main` + local remediation |
| Stance | Brutal — score what is true in code |

---

## Scores

### After remediation (current)

| Dimension | Before | After | Delta |
| --------- | ------ | ----- | ----- |
| Architecture | 4.0 | **6.5** | +2.5 |
| Security & access control | 2.0 | **6.0** | +4.0 |
| Correctness | 4.0 | **6.5** | +2.5 |
| Test coverage & honesty | 3.0 | **6.5** | +3.5 |
| Maintainability | 4.0 | **6.0** | +2.0 |
| Production readiness | 2.0 | **5.0** | +3.0 |
| Documentation honesty | 2.0 | **7.5** | +5.5 |
| Data integrity | 4.5 | **6.5** | +2.0 |
| **Weighted overall** | **3.1** | **6.3** | **+3.2** |

### Executive verdict (current)

## Overall score: 6.3 / 10**

Critical product lies and crash paths are gone. Gating works (default-deny), physics drag is mass-correct, tests pass (167), ethics section matches the tree, and ops scaffolding is either wired or honestly incomplete. Remaining gap to 8+: real Stripe↔DB tier persistence, PDF/email workers, richer citations, and less Streamlit HTML surface.

---

## What was fixed in the remediation pass

| Priority | Fix | Status |
| -------- | --- | ------ |
| 1 | Pro gate: pass real page keys; **default-deny** unknown keys | Done |
| 2 | Removed missing nav/router pages (saturation, BOM, mfg, supply) | Done |
| 3 | Deleted orphan Pk/saturation CLI + unused Iran JSON; README ethics now true | Done |
| 4 | Drag uses `½ρv²CdA/m` (or β); regression tests added | Done |
| 5 | Data tests aligned to real JSON schemas | Done |
| 6 | Stripe customer ID on session + `/stripe/webhook` API route | Done |
| 7 | `load_dotenv()` + explicit `DEV_UNLOCK_PRO` (not “missing Supabase ⇒ Pro”) | Done |
| 8 | `alembic.ini` + `versions/001_initial_schema.py` + compose `migrate` | Done |
| 9 | Wire `init_monitoring`, analytics `page_view`, feedback bar | Done |
| 10 | Honest README counts, env vars, Pro table, Flower claim removed | Done |

### Additional cleanup

- PDF Celery task returns `not_implemented` instead of empty placeholder PDF
- Admin sidebar uses `ADMIN_USER_IDS` / `ENTERPRISE_USER_IDS` / `DEV_UNLOCK_PRO`
- Auth package no longer labeled “stub”
- Onboarding metrics: 31 missiles / 8 treaties
- `tests/test_auth.py` added for gating

---

## Remaining debt (keeps score under ~8)

| Severity | Issue |
| -------- | ----- |
| High | Tier still lives in Streamlit session — no durable DB upsert on webhook |
| High | Citations often short labels without URL/year |
| Medium | Celery email needs SMTP; PDF reports unimplemented |
| Medium | Admin GrowthOps still shows mock funnel numbers |
| Medium | Heterogeneous treaty/resource JSON shapes (tests tolerate; ideal is normalize) |
| Medium | Heavy `unsafe_allow_html` theme surface |
| Low | Design Lab remains a parametric research wizard (documented; not operational configs) |
| Low | API public by design for research JSON — fine, document threat model |

---

## Test status (post-fix)

```text
167 passed
```

Coverage focus: `utils`, `auth`, data integrity. Still light on Streamlit module UI and FastAPI route tests.

---

## Architecture (current)

```text
Browser → Streamlit app.py
            ├─ load_dotenv()
            ├─ DEV_UNLOCK_PRO? → pro : anon
            ├─ init_monitoring() / auth.setup()
            ├─ sidebar (implemented pages only)
            └─ router → modules/*.render()
                 └─ utils/physics (mass-correct drag) + data/*.json

Parallel:
  FastAPI  → public JSON + POST /stripe/webhook
  Celery   → CSV export real; PDF/email honest stubs
  Alembic  → initial schema revision shipped
```

---

## Path to 8.0+ (next sprint)

1. Persist `users.stripe_customer_id` + tier on webhook (SQLAlchemy session)
2. Normalize `data/treaties.json` / `resources.json` schemas
3. Enrich missile `sources` with URL + year
4. FastAPI tests + auth integration test with mocked Stripe
5. Replace mock admin analytics with PostHog/DB queries or label UI “demo”
6. Implement one real PDF report type or remove the task

---

## Historical critical findings (resolved)

<details>
<summary>Original Critical / High items (pre-fix)</summary>

- **C1** Pro gate default-allow via mangled keys — **FIXED**
- **C2** Sidebar crash pages — **REMOVED**
- **C3** Ethics README contradicted by orphan Pk/saturation — **DELETED + docs**
- **C4** Stripe customer never bound — **SESSION BIND + WEBHOOK ROUTE**
- **H2** Drag dropped mass/area — **FIXED**
- **H3** Dual physics/data stacks — **ORPHANS DELETED**
- **H4** Data tests disagreed with data — **ALIGNED**
- **H5** Ops theater — **PARTIALLY REAL (alembic/webhook/monitoring)**

</details>

---

*Remediation raised the product from “scaffolding theater (3.1)” to “credible research prototype with working gates (6.3)”. Optimum next step is durable billing persistence and data citation depth.*
