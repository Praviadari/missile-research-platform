"""One-shot data normalizer for missiles / treaties / resources."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SOURCE_URLS = {
    "CSIS": "https://missilethreat.csis.org/",
    "CSIS Missile Defense Project": "https://missilethreat.csis.org/",
    "IISS": "https://www.iiss.org/publications/the-military-balance/",
    "IISS Military Balance": "https://www.iiss.org/publications/the-military-balance/",
    "IISS Military Balance 2024": "https://www.iiss.org/publications/the-military-balance/",
    "ISS Military Balance 2024": "https://www.iiss.org/publications/the-military-balance/",
    "NTI": "https://www.nti.org/countries/",
    "Janes": "https://www.janes.com/",
    "Janes Defence": "https://www.janes.com/",
    "Arms Control Association": "https://www.armscontrol.org/factsheets",
    "US DoD": "https://www.defense.gov/",
    "DoD": "https://www.defense.gov/",
}


def enrich_source(s: str) -> dict:
    label = s.strip()
    year = None
    m = re.search(r"(19|20)\d{2}", label)
    if m:
        year = int(m.group(0))
    url = SOURCE_URLS.get(label)
    if url is None:
        for key, u in SOURCE_URLS.items():
            if key.lower() in label.lower() or label.lower() in key.lower():
                url = u
                break
    return {"label": label, "url": url, "year": year}


def main() -> None:
    missiles = json.loads((DATA / "missiles.json").read_text(encoding="utf-8"))
    for m in missiles:
        new = []
        for s in m.get("sources", []):
            if isinstance(s, dict) and "label" in s:
                new.append(s)
            elif isinstance(s, str):
                new.append(enrich_source(s))
            else:
                new.append({"label": str(s), "url": None, "year": None})
        m["sources"] = new
    (DATA / "missiles.json").write_text(
        json.dumps(missiles, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("missiles sources enriched", len(missiles))

    treaties = json.loads((DATA / "treaties.json").read_text(encoding="utf-8"))
    for t in treaties:
        origin = t.get("signed", t.get("established", t.get("entered_into_force")))
        if origin is not None and str(origin)[:4].isdigit():
            t["origin_year"] = int(str(origin)[:4])
        if "parties" in t and isinstance(t["parties"], int):
            t["member_count"] = t["parties"]
            del t["parties"]
        elif "parties" in t and isinstance(t["parties"], list):
            t["members"] = t.get("members") or t["parties"]
            t["member_count"] = len(t["members"])
            del t["parties"]
        elif "members" in t and isinstance(t["members"], int):
            t["member_count"] = t["members"]
        elif "parties_original" in t:
            po = t["parties_original"]
            t["members"] = po if isinstance(po, list) else [po]
            t["member_count"] = len(t["members"])
        elif "subscribing_states" in t:
            ss = t["subscribing_states"]
            t["member_count"] = ss if isinstance(ss, int) else len(ss)
        t.setdefault("category", "other")
    (DATA / "treaties.json").write_text(
        json.dumps(treaties, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        "treaties normalized",
        [(t["id"], t.get("origin_year"), t.get("member_count")) for t in treaties],
    )

    resources = json.loads((DATA / "resources.json").read_text(encoding="utf-8"))
    for r in resources:
        r.setdefault("access", r.get("access") or "See publisher")
        if not r.get("url"):
            r["url"] = None
            r["locator"] = r.get("locator") or f"Bibliographic: {r.get('title')}"
    (DATA / "resources.json").write_text(
        json.dumps(resources, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        "resources normalized",
        sum(1 for r in resources if r.get("url")),
        "with url /",
        len(resources),
    )


if __name__ == "__main__":
    main()
