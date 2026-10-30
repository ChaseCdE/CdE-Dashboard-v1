"""
Release calendars of the statistics shown on the site ("Calendario" page and the Portada box).

Sources and formats:
- INE: official iCalendar feed with every release of the current year (date, time, title with
  the reference period). Robust.
- Eurostat: the JSON behind its release calendar page (euro indicators only). Not a documented
  API: it is checked on every run.
- Banco de España: an annual PDF table (one row per statistic, one column per month, each cell
  with the reference period and the release date), revised during the year.
- Ministerio de Trabajo / Inclusión (MTES-MISSM): an annual one-page PDF calendar, the source for
  Seguridad Social affiliation (AFI) and registered unemployment (MLR). Its server does not send
  the intermediate certificate, so the FNMT intermediate is bundled (src/fetchers/certs/) and
  added to the trusted roots: the connection is still verified.

Each source is parsed into events {date, time, source, title, period, flash} and saved to
data/raw/calendar/<source>.json. The PDF parsers check their own output (every release date
must fall in its month column, a minimum number of rows); on any failure the previous file is
kept and a warning is logged, so a layout change never publishes a wrong calendar.
"""

from __future__ import annotations

import io
import json
import logging
import re
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .http_session import make_session

logger = logging.getLogger(__name__)

MADRID = ZoneInfo("Europe/Madrid")
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
CERTS = Path(__file__).resolve().parent / "certs"

INE_ICS = "https://www.ine.es/dynt3/Calendario/calendario.ics"
EUROSTAT_JSON = "https://ec.europa.eu/eurostat/o/calendars/eventsJson"
BDE_PDF = "https://www.bde.es/webbe/es/estadisticas/compartido/calendario/pdf/calendario-bde-{year}.pdf"
MITES_PDF = ("https://www.mites.gob.es/ficheros/ministerio/estadisticas/calendario/"
             "Calendario_Estadisticas_Coyunturales_MITES-MISSM.pdf")

MONTHS_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MONTHS_LONG = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
               "septiembre", "octubre", "noviembre", "diciembre"]


def _event(d: date, time: str | None, source: str, title: str, period: str | None, flash=False, **extra) -> dict:
    return {"date": d.isoformat(), "time": time, "source": source, "title": title.strip(),
            "period": (period or "").strip() or None, "flash": bool(flash), **extra}


# ---------------------------------------------------------------------------------------- INE
def parse_ine_ics(text: str) -> list:
    text = text.replace("\r\n", "\n").replace("\n ", "")  # unfold lines
    out = []
    for block in re.findall(r"BEGIN:VEVENT\n(.*?)END:VEVENT", text, re.S):
        m = re.search(r"^DTSTART(?:;TZID=([^:]+))?:(\d{8})(?:T(\d{4}))?", block, re.M)
        s = re.search(r"^SUMMARY:(.*)$", block, re.M)
        if not m or not s:
            continue
        d = datetime.strptime(m.group(2), "%Y%m%d").date()
        time = f"{m.group(3)[:2]}:{m.group(3)[2:]}" if m.group(3) else None
        summary = s.group(1).replace("\\,", ",").replace("\\;", ";").strip()
        # "Índice de Precios de Consumo. Avance. Octubre 2026" -> title, flash, period
        parts = [p.strip() for p in summary.split(". ")]
        flash = "Avance" in parts[1:]
        period = parts[-1] if len(parts) > 1 and re.search(r"\d{4}", parts[-1]) else None
        title_parts = [p for p in (parts[:-1] if period else parts) if p != "Avance"]
        out.append(_event(d, time, "INE", ". ".join(title_parts), period, flash))
    return out


def fetch_ine(session) -> list:
    r = session.get(INE_ICS, timeout=60)
    r.raise_for_status()
    events = parse_ine_ics(r.content.decode("utf-8", errors="replace"))
    if len(events) < 200:
        raise ValueError(f"INE calendar: only {len(events)} events")
    return events


# ----------------------------------------------------------------------------------- Eurostat
def fetch_eurostat(session, start: date, end: date) -> list:
    """Euro-indicator releases between start and end (the page shows them in Luxembourg time;
    the 'Z' in the JSON is the page's local time, as on the site: 11:00 for most releases)."""
    params = {"start": f"{start.isoformat()}T00:00:00+01:00", "end": f"{end.isoformat()}T00:00:00+01:00", "theme": 0, "category": 0, "keywords": "",
              "isEuroindicator": "true", "authorInclude": "", "authorExclude": ""}
    r = session.get(EUROSTAT_JSON, params=params, timeout=60,
                    headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"})
    r.raise_for_status()
    rows = r.json()
    if not isinstance(rows, list):
        raise ValueError("Eurostat calendar: unexpected response")
    out = []
    for e in rows:
        m = re.match(r"(\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}))?", str(e.get("start", "")))
        if not m or not e.get("title"):
            continue
        out.append(_event(date.fromisoformat(m.group(1)), m.group(2), "Eurostat", e["title"], e.get("period"),
                          bool(e.get("preliminary")) or "flash" in e["title"].lower(),
                          codes=e.get("datasetCodes") or None))
    if len(out) < 20:
        raise ValueError(f"Eurostat calendar: only {len(out)} events")
    return out


# ------------------------------------------------------------------------------ Banco de España
DATE_RE = re.compile(r"^(\d{2})/(\d{2})$")
PERIOD_RE = re.compile(r"^(?:(?:Ene|Feb|Mar|Abr|May|Jun|Jul|Ago|Sep|Oct|Nov|Dic)/\d{2}|[IV]{1,3}-\d{4}|\d{4})$")


def _lines(words, tol=2.5):
    """Group words into text lines by their top coordinate."""
    lines = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(lines[-1]["top"] - w["top"]) <= tol:
            lines[-1]["words"].append(w)
        else:
            lines.append({"top": w["top"], "bottom": w["bottom"], "words": [w]})
        lines[-1]["bottom"] = max(lines[-1]["bottom"], w["bottom"])
    for ln in lines:
        ln["text"] = " ".join(w["text"] for w in sorted(ln["words"], key=lambda w: w["x0"]))
    return lines


def parse_bde_pdf(content: bytes) -> tuple[int, list]:
    """(year, [{name, date, period}]) for every statistic row of the BdE calendar."""
    import pdfplumber

    rows, year = [], None
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            text = " ".join(w["text"] for w in words)
            m = re.search(r"\(AÑO:\s*(\d{4})\)", text)
            year = year or (int(m.group(1)) if m else None)
            heads = {w["text"]: w for w in words if w["text"] in [x.upper() for x in MONTHS_ES]}
            datos = next((w for w in words if w["text"] == "DATOS"), None)
            if len(heads) != 12 or not datos:
                continue
            centers = [(heads[mm.upper()]["x0"] + heads[mm.upper()]["x1"]) / 2 for mm in MONTHS_ES]
            col_left = centers[0] - (centers[1] - centers[0]) / 2
            body_top = heads["ENE"]["bottom"] + 2
            label_limit = datos["x0"] - 3

            def col(x):
                return min(range(12), key=lambda i: abs(centers[i] - x))

            body = [w for w in words if w["top"] > body_top]
            label_lines = _lines([w for w in body if w["x1"] < label_limit])
            data = [w for w in body if w["x0"] >= col_left - 5]
            # Statistic labels: merge continuation lines; skip all-caps section headers.
            stats = []
            for ln in label_lines:
                t = ln["text"].strip()
                if not t or t.startswith("(a)") or t.startswith("(b)"):
                    continue
                letters = re.sub(r"[^A-Za-zÁÉÍÓÚÑáéíóúñ]", "", t)
                if letters and letters.isupper() and len(letters) > 3:
                    stats.append({"name": None, "top": ln["top"], "bottom": ln["bottom"]})  # section break
                    continue
                prev = stats[-1] if stats else None
                # A wrapped label continues right below its first line (gap ~2 pt); a new
                # statistic can start almost as close, so a line ending in ")" closes a label
                # unless the next line is a footnote mark like "(a) (b)".
                cont = prev and prev["name"] and ln["top"] - prev["bottom"] <= 3.5 and (
                    not prev["name"].endswith(")") or t.startswith("("))
                if cont:
                    prev["name"] += " " + t
                    prev["bottom"] = ln["bottom"]
                else:
                    stats.append({"name": t, "top": ln["top"], "bottom": ln["bottom"]})
            # Vertical extent of each statistic: halfway to its neighbours.
            for i, s in enumerate(stats):
                c = (s["top"] + s["bottom"]) / 2
                s["lo"] = (c + (stats[i - 1]["top"] + stats[i - 1]["bottom"]) / 2) / 2 if i else body_top
                s["hi"] = (c + (stats[i + 1]["top"] + stats[i + 1]["bottom"]) / 2) / 2 if i + 1 < len(stats) else page.height
            for s in stats:
                if not s["name"]:
                    continue
                toks = [w for w in data if s["lo"] <= (w["top"] + w["bottom"]) / 2 < s["hi"]]
                for w in toks:
                    m = DATE_RE.match(w["text"])
                    if not m:
                        continue
                    c = col((w["x0"] + w["x1"]) / 2)
                    periods = [p for p in toks if PERIOD_RE.match(p["text"]) and col((p["x0"] + p["x1"]) / 2) == c
                               and p["top"] < w["top"]]
                    period = max(periods, key=lambda p: p["top"])["text"] if periods else None
                    rows.append({"name": re.sub(r"\s+", " ", s["name"]), "day": int(m.group(1)),
                                 "month": int(m.group(2)), "column": c + 1, "period": period})
    if not year:
        raise ValueError("BdE calendar: year not found")
    bad = [r for r in rows if r["month"] != r["column"]]
    if len(rows) < 100 or len(bad) > 0.05 * len(rows):
        raise ValueError(f"BdE calendar: {len(rows)} dates, {len(bad)} outside their month column; layout changed?")
    out = []
    for r in rows:
        if r["month"] != r["column"]:
            continue
        out.append({"name": r["name"], "date": date(year, r["month"], r["day"]).isoformat(), "period": r["period"]})
    return year, out


def fetch_bde(session, today: date) -> list:
    events = []
    for year in sorted({today.year, (today + timedelta(days=60)).year}):
        r = session.get(BDE_PDF.format(year=year), timeout=60)
        if r.status_code == 404 and year != today.year:
            continue  # next year's calendar not published yet
        r.raise_for_status()
        _, rows = parse_bde_pdf(r.content)
        for x in rows:
            events.append(_event(date.fromisoformat(x["date"]), None, "Banco de España", x["name"], x["period"]))
    return events


# ---------------------------------------------------------------------- Trabajo / Inclusión
MITES_CODES = {"AFI": "Afiliación de trabajadores a la Seguridad Social",
               "MLR": "Paro registrado y contratos"}


def parse_mites_pdf(content: bytes) -> list:
    """AFI and MLR releases from the one-page MTES-MISSM calendar: each month block lists
    'day: CODE (ref month), CODE (ref month)'."""
    import pdfplumber

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
        text = " ".join(w["text"] for w in words)
        m = re.search(r"Calendario (\d{4})", text)
        if not m:
            raise ValueError("MITES calendar: year not found")
        year = int(m.group(1))
        titles = [w for w in words if w["text"].lower() in MONTHS_LONG]
        if len(titles) != 12:
            raise ValueError(f"MITES calendar: {len(titles)} month titles")
        out = []
        for t in titles:
            month = MONTHS_LONG.index(t["text"].lower()) + 1
            same_row = sorted([o for o in titles if abs(o["top"] - t["top"]) < 8], key=lambda o: o["x0"])
            below = sorted({round(o["top"]) for o in titles if o["top"] > t["top"] + 8})
            x1 = next((o["x0"] for o in same_row if o["x0"] > t["x0"] + 5), page.width)
            y1 = below[0] - 2 if below else page.height
            region = page.crop((max(0, t["x0"] - 60), t["top"] - 2, min(page.width, x1 - 60 if x1 < page.width else x1), y1))
            block = region.extract_text() or ""
            # Text after "N:" up to the next "N:" belongs to day N.
            for dm in re.finditer(r"(?<![\d/])(\d{1,2}):\s*(.*?)(?=(?<![\d/])\d{1,2}:|\Z)", block, re.S):
                day, items = int(dm.group(1)), dm.group(2)
                for code, ref in re.findall(r"\b(AFI|MLR)\s*\(([^)]+)\)", items):
                    out.append(_event(date(year, month, day), None, "Ministerios de Trabajo e Inclusión",
                                      MITES_CODES[code], ref.strip(), code=code))
    # Validation: a release each month for both statistics, early in the month.
    for code in MITES_CODES:
        months = {e["date"][:7] for e in out if e.get("code") == code}
        if len(months) < 11 or any(int(e["date"][8:]) > 10 for e in out if e.get("code") == code):
            raise ValueError(f"MITES calendar: {code} found in {len(months)} months; layout changed?")
    return out


def fetch_mites(session) -> list:
    r = session.get(MITES_PDF, timeout=60, verify=_bundle_with_fnmt())
    r.raise_for_status()
    return parse_mites_pdf(r.content)


def _bundle_with_fnmt() -> str:
    """The default trusted roots plus the FNMT intermediate the mites.gob.es server omits."""
    import certifi
    import os

    base = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE") or certifi.where()
    path = Path(tempfile.gettempdir()) / "cde_ca_bundle_fnmt.pem"
    path.write_text(Path(base).read_text() + "\n" + (CERTS / "fnmt_ac_componentes_informaticos.pem").read_text())
    return str(path)


# ------------------------------------------------------------------------------------- driver
class CalendarFetcher:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fetch_all(self) -> dict:
        today = datetime.now(MADRID).date()
        session = make_session(user_agent=BROWSER_UA)
        jobs = {
            "ine": lambda: fetch_ine(session),
            "eurostat": lambda: fetch_eurostat(session, today - timedelta(days=45), today + timedelta(days=120)),
            "bde": lambda: fetch_bde(session, today),
            "mites": lambda: fetch_mites(session),
        }
        result = {}
        for name, job in jobs.items():
            try:
                events = job()
            except Exception as e:  # noqa: BLE001 - one source failing must not stop the others
                logger.warning(f"Calendar {name}: download or parsing failed, keeping the previous file: {e}")
                result[name] = 0
                continue
            (self.output_dir / f"{name}.json").write_text(
                json.dumps({"fetched": today.isoformat(), "events": events}, ensure_ascii=False, indent=0), encoding="utf-8")
            logger.info(f"Calendar {name}: {len(events)} events")
            result[name] = len(events)
        return result
