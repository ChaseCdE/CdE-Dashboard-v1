"""
"Últimos datos" on the Portada: which headline indicators have a new observation, and when it
was first published on the site (site/data/releases.json).

Nothing here needs editing by hand to keep the section up to date. On every export the new
manifest is compared with the previous one: when the latest period of a highlighted series moves
forward, an event is logged with the date of that export (Spanish date). The daily refresh runs
after the INE (09:00) and Eurostat (11:00) releases, so in practice that is the publication date.

Event status:
  nuevo       a new period (definitive or provisional data)
  avance      a new period that is an INE flash estimate (see `provisional` in the data contract)
  definitivo  the flash estimate of a period has been replaced by the full release

To add or remove an indicator, edit HIGHLIGHTS. Each entry also defines the card (value and
change shown) and the chart drawn when the card is selected, so the site needs no JS changes.
scripts/backfill_releases.py rebuilds the log from the git history of manifest.json.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

MADRID = ZoneInfo("Europe/Madrid")
KEEP_DAYS = 400  # log length; the site shows the last weeks


def H(id, series, field, title, *, change=None, good=None, chart, years=3, chart_type="line", ref=None, page=None):
    """One highlighted indicator. chart: [(series, field, label or None), ...] of the same dataset
    unless a series is given as 'dataset:series'."""
    return {
        "id": id, "series": series, "field": field, "title_es": title,
        "change": change, "positive_is_good": good, "page": page,
        "chart": {
            "type": chart_type, "years": years, "ref": ref,
            "series": [{"dataset": s.split(":")[0] if ":" in s else id,
                        "series": s.split(":")[1] if ":" in s else s, "field": f, "label": lab}
                       for s, f, lab in chart],
        },
    }


HIGHLIGHTS = [
    H("ine.cpi_special_groups", "headline", "yoy", "Inflación (IPC)", good=False, page="pages/precios.html",
      chart=[("headline", "yoy", "General"), ("core", "yoy", "Subyacente")], years=3, ref={"y": 2, "label": "Objetivo BCE 2 %"}),
    H("eurostat.hicp", "es", "yoy", "Inflación armonizada (IPCA)", good=False, page="pages/precios.html",
      chart=[("es", "yoy", "España"), ("eu27", "yoy", "UE-27")], years=3),
    H("ine.gdp", "es", "qoq", "PIB, variación trimestral", change={"field": "yoy", "label": "interanual"}, good=True,
      page="pages/actividad.html", chart=[("es", "qoq", None)], chart_type="bar", years=5),
    H("ine.unemployment", "es", "value", "Tasa de paro (EPA)", change={"field": "yoy_pp", "label": "interanual"}, good=False,
      page="pages/laboral.html", chart=[("es", "value", "España"), ("eurostat.unemployment:eu27", "value", "UE-27")], years=5),
    H("bde.social_security_affiliates", "es", "value", "Afiliados a la Seguridad Social",
      change={"field": "mom_diff", "label": "en el mes"}, good=True, page="pages/laboral.html",
      chart=[("es", "mom_diff", None)], chart_type="bar", years=2),
    H("bde.registered_unemployment", "es", "value", "Paro registrado", change={"field": "mom_diff", "label": "en el mes"},
      good=False, page="pages/laboral.html", chart=[("es", "mom_diff", None)], chart_type="bar", years=2),
    H("ine.industrial_production", "es", "yoy", "Producción industrial", change={"field": "mom", "label": "mensual"},
      good=True, page="pages/sectores.html#industria", chart=[("es", "yoy", None)], years=3),
    H("ine.services_production", "es", "yoy", "Producción del sector servicios", change={"field": "mom", "label": "mensual"},
      good=True, page="pages/sectores.html#servicios", chart=[("es", "yoy", None)], years=3),
    H("ine.retail_sales", "es", "yoy", "Comercio minorista", change={"field": "mom", "label": "mensual"}, good=True,
      page="pages/actividad.html", chart=[("es", "yoy", None)], years=3),
    H("eurostat.economic_sentiment", "es", "value", "Sentimiento económico", change={"field": "yoy", "label": "interanual"},
      good=True, page="pages/actividad.html", chart=[("es", "value", "España"), ("eu27", "value", "UE-27")], years=3,
      ref={"y": 100, "label": "Media de largo plazo"}),
    H("ine.business_confidence", "ice", "value", "Confianza empresarial", change={"field": "yoy", "label": "interanual"},
      good=True, page="pages/empresas.html", chart=[("ice", "value", None)], years=5),
    H("eurostat.trade_balance", "es", "balance", "Saldo comercial de bienes", page="pages/sector-exterior.html",
      chart=[("es", "exports", "Exportaciones"), ("es", "imports", "Importaciones")], years=3),
    H("bde.current_account_balance", "es", "sum_12m", "Balanza por cuenta corriente (12 meses)",
      page="pages/sector-exterior.html", chart=[("es", "sum_12m", None)], years=5),
    H("ine.house_prices", "es", "yoy", "Precio de la vivienda (IPV)", page="pages/sectores.html#construccion-vivienda",
      chart=[("es", "yoy", None)], chart_type="bar", years=5),
    H("ine.housing_transactions", "total", "yoy", "Compraventa de viviendas", page="pages/sectores.html#construccion-vivienda",
      chart=[("total", "sum_12m", None)], years=5),
    H("ine.tourist_arrivals", "es", "yoy", "Turistas internacionales", change={"field": "sum_12m", "label": "en 12 meses"},
      good=True, page="pages/sectores.html#turismo", chart=[("es", "sum_12m", None)], years=5),
    H("eurostat.gov_deficit_quarterly", "es", "value", "Saldo de las Administraciones Públicas", good=True,
      page="pages/sector-publico.html", chart=[("es", "value", "España"), ("eu27", "value", "UE-27")], chart_type="bar", years=5),
    H("aeat.ome_totals", "sales", "yoy", "Ventas de las sociedades (AEAT)", good=True, page="pages/empresas.html",
      chart=[("sales", "yoy", "Ventas"), ("purchases", "yoy", "Compras"), ("wages", "yoy", "Masa salarial")], years=5),
]


def today_madrid(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.astimezone(MADRID).date().isoformat()


def _latest(manifest: dict | None, h: dict):
    """(date, is_flash) of the highlighted series/field in a manifest, or None."""
    if not manifest:
        return None
    entry = next((e for e in manifest.get("datasets", []) if e.get("id") == h["id"]), None)
    if not entry:
        return None
    ser = next((s for s in entry.get("series", []) if s.get("key") == h["series"]), None)
    point = ser and (ser.get("latest") or {}).get(h["field"])
    if not point:
        return None
    return point[0], point[0] in (entry.get("provisional") or [])


def update_events(events: list, previous: dict | None, current: dict, detected: str) -> list:
    """Return the event log after comparing two manifests (pure function)."""
    events = list(events or [])
    seen = {(e["id"], e["period"], e["status"]) for e in events}
    for h in HIGHLIGHTS:
        new, old = _latest(current, h), _latest(previous, h)
        if not new or not old:  # no baseline: nothing can be said about what is new
            continue
        status = None
        if new[0] > old[0]:
            status = "avance" if new[1] else "nuevo"
        elif new[0] == old[0] and old[1] and not new[1]:
            status = "definitivo"
        if status and (h["id"], new[0], status) not in seen:
            events.append({"id": h["id"], "period": new[0], "detected": detected, "status": status})
            seen.add((h["id"], new[0], status))
    cutoff = (date.fromisoformat(detected) - timedelta(days=KEEP_DAYS)).isoformat()
    events = [e for e in events if e["detected"] >= cutoff]
    order = {h["id"]: i for i, h in enumerate(HIGHLIGHTS)}
    events.sort(key=lambda e: (e["detected"], -order.get(e["id"], 99)), reverse=True)
    return events


def build(previous_manifest: dict | None, current_manifest: dict, previous_releases: dict | None,
          generated_at: str) -> dict:
    ids = {e["id"] for e in current_manifest.get("datasets", [])}
    missing = [h["id"] for h in HIGHLIGHTS for s in h["chart"]["series"] if s["dataset"] not in ids] + \
              [h["id"] for h in HIGHLIGHTS if h["id"] not in ids]
    if missing:
        raise ValueError(f"releases: highlighted datasets not exported: {sorted(set(missing))}")
    detected = today_madrid(datetime.fromisoformat(generated_at.replace("Z", "+00:00")))
    events = update_events((previous_releases or {}).get("events", []), previous_manifest, current_manifest, detected)
    return {"generated_at": generated_at, "highlights": HIGHLIGHTS, "events": events}


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except ValueError:
        return None
