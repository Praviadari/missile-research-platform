# Code Quality Deep Audit — Missile Research Platform v2

| Field | Value |
| ----- | ----- |
| Initial audit | 2026-08-06 |
| Remediation pass 1 | 2026-08-06 → **6.3** |
| Remediation pass 2 | 2026-08-06 → **7.4** |
| Stance | Brutal — score what is true in code |

---

## Scores

### Current (after pass 2)

| Dimension | Start | Pass 1 | Pass 2 | Notes |
| --------- | ----- | ------ | ------ | ----- |
| Architecture | 4.0 | 6.5 | **7.0** | DB session layer + real workers |
| Security & access control | 2.0 | 6.0 | **6.5** | Gate solid; webhook persists tier |
| Correctness | 4.0 | 6.5 | **7.5** | Drag fixed; PDF/CSV real; sources structured |
| Test coverage & honesty | 3.0 | 6.5 | **8.0** | 184 tests: auth, API, billing/DB, workers, data |
| Maintainability | 4.0 | 6.0 | **7.0** | Normalized data contracts |
| Production readiness | 2.0 | 5.0 | **6.5** | Alembic + webhook→DB + migrate service |
| Documentation honesty | 2.0 | 7.5 | **8.0** | Demo analytics labeled; ethics true |
| Data integrity | 4.5 | 6.5 | **7.5** | Structured sources + treaty fields |
| **Weighted overall** | **3.1** | **6.3** | **7.4** | |

### Executive verdict

**Overall score: 7.4 / 10**

Credible research platform with working Pro gates, durable billing hooks, honest docs, and a meaningful automated test suite. Remaining gap to 8.5+: live PostHog admin metrics, SMTP email in CI, citation coverage closer to 100% URL, and Streamlit UI tests.

---

## Pass 2 changes

| Item | Status |
| ---- | ------ |
| `database/session.py` upsert/tier helpers | Done |
| Stripe webhook persists tier by `stripe_customer_id` | Done |
| Auth upserts user + DB tier fallback | Done |
| Missile sources → `{label, url, year}` objects | Done |
| Treaties → `origin_year` + `member_count` | Done |
| Resources locators for books without URL | Done |
| Real PDF reports (`missile_comparison`, `treaty_brief`) | Done |
| FastAPI + billing/DB + worker tests | Done |
| Admin GrowthOps marked DEMO; user tier counts from DB | Done |

### Test status

```text
184 passed
```

---

## Remaining debt (path to 8.5+)

| Severity | Issue |
| -------- | ----- |
| Medium | GrowthOps funnel still illustrative without PostHog API pulls |
| Medium | Some missile sources still lack resolved URLs (~target ≥80%) |
| Medium | No Streamlit UI / Playwright tests |
| Low | Email delivery requires SMTP; returns honest stub otherwise |
| Low | Supabase admin directory not implemented (service-role) |

---

## Architecture (current)

```text
Browser → Streamlit app.py
            ├─ load_dotenv / DEV_UNLOCK_PRO
            ├─ auth → Stripe + database.session upsert
            └─ modules → data/*.json (normalized) + utils/physics

API → public JSON + POST /stripe/webhook → update_tier_by_stripe_customer
DB  → alembic 001_initial + session helpers
Workers → CSV export + PDF comparison/treaty briefs
```

---

*From scaffolding theater (3.1) → working gates (6.3) → durable billing + real exports + honest data contracts (7.4).*
