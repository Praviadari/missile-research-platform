# 🚀 Missile Analysis & Research Platform v2

Open-source defense research platform built with Streamlit, ported from the
Drone Design Platform v3 architecture. All missile data sourced exclusively
from public, academic, and declassified governmental references.

---

## Architecture

```text
missile_platform_v2/
├── app.py                   # Entry point — session init, router
│
├── ui/
│   ├── theme.py             # Design system — all CSS tokens, card builders, Plotly helpers
│   ├── sidebar.py           # Navigation sidebar component
│   └── charts.py            # Reusable Plotly chart builders
│
├── modules/                 # Streamlit page renderers (one per page)
│   ├── onboarding.py        # Home / landing page [FREE]
│   ├── missile_database.py  # Read-only missile browser [FREE]
│   ├── historical_timeline.py # Strike event history [FREE]
│   ├── treaty_guide.py      # Arms control policy browser [FREE]
│   ├── learning_center.py   # Physics education modules [FREE]
│   └── resource_library.py  # Curated bibliography [FREE]
│
├── data/                    # Static JSON data files
│   ├── missiles.json        # 32+ systems — specs, sources, categories
│   ├── historical_events.json # 8 documented strike events with sources
│   ├── treaties.json        # 7 major arms control frameworks
│   └── resources.json       # 17 curated academic/government sources
│
├── auth/
│   ├── auth.py              # Supabase auth integration
│   ├── auth_guard.py        # Feature-gate decorator + upgrade walls
│   └── auth_modal.py        # Sign-in / sign-up / upgrade dialog
│
├── database/
│   └── models.py            # SQLAlchemy ORM (User, SavedSearch, ResearchNote, Analytics)
│
├── api/
│   └── main.py              # FastAPI read-only REST endpoints
│
├── analytics/
│   └── tracker.py           # PostHog event tracking (privacy-preserving)
│
├── billing/
│   └── stripe_billing.py    # Stripe subscription management
│
├── feedback/
│   └── feedback_widget.py   # In-app thumbs-up/down feedback collection
│
├── monitoring/
│   └── health.py            # Sentry, structured logging, health checks
│
├── workers/
│   └── celery_app.py        # Celery async tasks (PDF export, CSV, email)
│
├── abtest/
│   └── experiments.py       # A/B testing framework (deterministic variant assignment)
│
├── admin/
│   ├── admin_dashboard.py   # Admin health + data integrity page
│   └── admin_ops.py         # GrowthOps — funnel analytics, experiment control
│
├── utils/
│   └── units.py             # Unit conversions + ISA atmosphere + rocket equation
│
├── tests/
│   └── test_units.py        # 30 unit tests — all passing
│
├── alembic/
│   ├── env.py               # Database migration configuration
│   └── versions/            # Schema revisions
├── docs/
│   └── CODE_QUALITY_AUDIT.md
│
├── .streamlit/config.toml   # Streamlit dark theme config
├── .github/workflows/ci.yml # GitHub Actions CI
├── .env.example             # Required environment variables
├── Dockerfile               # Production container
├── docker-compose.yml       # Full stack (app + api + worker + db + redis)
└── requirements.txt         # Python dependencies
```

---

## Quick Start

### Development (local Pro unlock)

```bash
cp .env.example .env
# DEV_UNLOCK_PRO=true unlocks Pro locally without Supabase/Stripe
pip install -r requirements.txt
streamlit run app.py
```

Without `DEV_UNLOCK_PRO=true`, the app starts as anonymous/free and Pro pages show the upgrade wall.

### Production (Docker)

```bash
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_ANON_KEY, STRIPE_* as needed
# Set DEV_UNLOCK_PRO=false for production
docker-compose up -d
docker-compose run --rm migrate   # alembic upgrade head
# App: http://localhost:8501
# API: http://localhost:8001/docs
```

### Run Tests

```bash
pytest tests/ -v --cov=utils --cov=auth --cov-report=term-missing
```

---

## Public Pages (Free, No Login Required)

| Page | Key | Description |
| ---- | --- | ----------- |
| 🏠 Home | `home` | Platform overview and navigation guide |
| 📋 Missile Database | `missile_database` | 31 systems — table, card, and chart views |
| 📅 Historical Timeline | `historical_timeline` | 8 documented strike events with intercept data |
| 📜 Treaty Guide | `treaty_guide` | NPT, INF, New START, MTCR + related frameworks |
| 🎓 Learning Center | `learning_center` | Physics education: ballistics, propulsion, guidance, defense |
| 📖 Resource Library | `resource_library` | Curated bibliography of 17 public sources |

## Pro Pages (Require Subscription)

| Page | Key | Description |
| ---- | --- | ----------- |
| 📈 Trajectory Simulator | `trajectory` | 2D physics-based trajectory with ISA atmosphere |
| 🔥 Propulsion Analysis | `propulsion` | Isp curves, rocket equation explorer, staging |
| 🌡️ Reentry Analysis | `reentry` | Atmospheric reentry heating and deceleration |
| ⚡ Hypersonic Lab | `hypersonic` | HGV, scramjet, Mach regime comparisons |
| 🛡️ Defense Systems Lab | `defense_lab` | Engagement envelopes, intercept geometry |
| 🌐 3D Visualizer | `visualizer` | Three-dimensional trajectory visualizer |
| 🛠️ Design Lab | `design_lab` | 7-step guided research workflow |

---

## Data Sources

All missile specifications drawn from this source hierarchy:

1. **US DoD Annual Reports** — China, Russia, Iran military power assessments
2. **CSIS Missile Defense Project** — missilethreat.csis.org
3. **IISS Military Balance** — annual edition
4. **Janes Defence Intelligence** — professional reference database
5. **NTI Country Profiles** — nti.org
6. **Arms Control Association** — armscontrol.org
7. **Peer-reviewed literature** — Nonproliferation Review, RAND studies

Entries with uncertain specifications are marked `_uncertain: true` in the
JSON and displayed with ⚠️ in the UI.

---

## Environment Variables

See `.env.example` for full list. Required for production:

| Variable | Purpose |
| -------- | ------- |
| `DEV_UNLOCK_PRO` | Local Pro unlock (`true`/`false`) |
| `SUPABASE_URL` | Auth provider |
| `SUPABASE_ANON_KEY` | Supabase public key |
| `STRIPE_SECRET_KEY` | Billing |
| `STRIPE_PRO_PRICE_ID` | Pro tier price |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification |
| `DATABASE_URL` | PostgreSQL connection |
| `REDIS_URL` | Celery broker |

Optional:

| Variable | Purpose |
| -------- | ------- |
| `POSTHOG_API_KEY` | Product analytics |
| `SENTRY_DSN` | Error tracking |
| `STRIPE_PAYMENT_LINK` | Hosted checkout URL |
| `ADMIN_USER_IDS` | Comma-separated admin Supabase UUIDs |
| `ENTERPRISE_USER_IDS` | Enterprise tier allow-list |

---

## What Is NOT in This Codebase

The following capabilities are intentionally absent (research/education scope only):

- ❌ Defense saturation calculator that outputs "missiles needed to overwhelm"
- ❌ Attack planning optimizer / target sequencing
- ❌ Intercept probability calculator tied to specific real-world defense deployments
- ❌ Weapon design wizard outputting operational missile configurations
- ❌ BOM / manufacturing / supply-chain tooling (removed from nav; not product scope)

Pro modules (trajectory, propulsion, defense lab, design lab) provide engineering
insight for research without targeting or saturation-planning functionality.

---

## License

MIT License. All data from public sources — see data files for per-entry citations.
