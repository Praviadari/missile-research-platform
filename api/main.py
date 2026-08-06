"""
api/main.py
============
FastAPI read-only endpoints for the Missile Analysis & Research Platform.

Exposes the public database (missiles, events, treaties, resources)
as JSON endpoints. All data is from the static JSON files in data/.

Run:  uvicorn api.main:app --port 8001 --reload

Endpoints:
  GET /api/missiles              — full missile database
  GET /api/missiles/{name}       — single missile
  GET /api/events                — historical events
  GET /api/treaties              — treaty database
  GET /api/resources             — resource library
  GET /health                    — health check
"""

import json
import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Missile Research Platform API",
    description="Read-only API for publicly-sourced missile and arms control data.",
    version="2.0.0",
)

_cors_origins = [
    o.strip()
    for o in os.getenv(
        "API_CORS_ORIGINS", "http://localhost:8501,http://localhost:8502"
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(filename: str) -> list:
    path = os.path.join(DATA_DIR, filename)
    with open(path) as f:
        return json.load(f)


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# ── Missiles ───────────────────────────────────────────────────────────────────

@app.get("/api/missiles")
def get_missiles(
    country:  Optional[str] = Query(None, description="Filter by country"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_range: Optional[int] = Query(None, description="Minimum range (km)"),
    max_range: Optional[int] = Query(None, description="Maximum range (km)"),
):
    """Return missile database, with optional filters."""
    missiles = _load("missiles.json")
    if country:
        missiles = [m for m in missiles if m.get("country","").lower() == country.lower()]
    if category:
        missiles = [m for m in missiles if m.get("category","").lower() == category.lower()]
    if min_range is not None:
        missiles = [m for m in missiles if isinstance(m.get("range_km"),(int,float)) and m["range_km"] >= min_range]
    if max_range is not None:
        missiles = [m for m in missiles if isinstance(m.get("range_km"),(int,float)) and m["range_km"] <= max_range]
    return {"count": len(missiles), "missiles": missiles}


@app.get("/api/missiles/{name}")
def get_missile(name: str):
    """Return a single missile by name (case-insensitive)."""
    missiles = _load("missiles.json")
    match = next((m for m in missiles if m["name"].lower() == name.lower()), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Missile '{name}' not found.")
    return match


# ── Historical events ──────────────────────────────────────────────────────────

@app.get("/api/events")
def get_events(actor: Optional[str] = Query(None)):
    """Return historical strike events, with optional actor filter."""
    events = _load("historical_events.json")
    if actor:
        events = [e for e in events if actor.lower() in e.get("actor","").lower()]
    return {"count": len(events), "events": events}


@app.get("/api/events/{event_id}")
def get_event(event_id: str):
    events = _load("historical_events.json")
    match = next((e for e in events if e["id"] == event_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    return match


# ── Treaties ───────────────────────────────────────────────────────────────────

@app.get("/api/treaties")
def get_treaties(category: Optional[str] = Query(None)):
    treaties = _load("treaties.json")
    if category:
        treaties = [t for t in treaties if t.get("category","").lower() == category.lower()]
    return {"count": len(treaties), "treaties": treaties}


@app.get("/api/treaties/{treaty_id}")
def get_treaty(treaty_id: str):
    treaties = _load("treaties.json")
    match = next((t for t in treaties if t["id"] == treaty_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Treaty '{treaty_id}' not found.")
    return match


# ── Resources ──────────────────────────────────────────────────────────────────

@app.get("/api/resources")
def get_resources(resource_type: Optional[str] = Query(None, alias="type")):
    resources = _load("resources.json")
    if resource_type:
        resources = [r for r in resources if r.get("type","").lower() == resource_type.lower()]
    return {"count": len(resources), "resources": resources}


# ── Stripe webhook (billing lifecycle) ─────────────────────────────────────────

@app.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """Receive Stripe subscription lifecycle events."""
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
    try:
        from billing.stripe_billing import handle_webhook

        return handle_webhook(payload, stripe_signature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
