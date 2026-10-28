"""
Cross-source consistency: the same economic quantity published by two official
sources must agree. Catches a mislabelled series even when it matches its own API.

  - 10-year yields (BdE "Economía internacional" monthly series) vs Eurostat
    irt_lt_mcby_m (EMU convergence criterion bond yields), ES / DE / FR / IT.
  - HICP Spain: Eurostat prc_hicp_minr (site) vs INE IPCA8090 (IPCA, variación anual).
  - GDP Spain q/q: Eurostat namq_10_gdp (site) vs INE CNTR6653.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import Report, series  # noqa: E402
from check_eurostat import fetch as es_fetch  # noqa: E402
from check_ine import fetch as ine_fetch  # noqa: E402

YIELDS = {"bde.spain_10y_bond_monthly": ("es", "ES"), "bde.germany_10y_bond": ("de", "DE"),
          "bde.france_10y_bond": ("fr", "FR"), "bde.italy_10y_bond": ("it", "IT")}


def run(rep: Report):
    r = es_fetch("irt_lt_mcby_m", {"int_rt": "MCBY"}, [g for _, g in YIELDS.values()], since="2023")
    (sl,) = r["data"].keys()
    for ds, (skey, geo) in YIELDS.items():
        rep.compare(ds, "cross", series(ds, skey, "value"), r["data"][sl][geo], tol=0.011,
                    label=f"vs Eurostat irt_lt_mcby_m {geo}", last_n=24, require_latest=False)
    _, ipca = ine_fetch("IPCA8090", 30)
    rep.compare("eurostat.hicp", "cross", series("eurostat.hicp", "es", "yoy"), ipca, tol=1e-6,
                label="ES vs INE IPCA8090", last_n=24, require_latest=False)
    _, q = ine_fetch("CNTR6653", 12)
    rep.compare("eurostat.gdp_growth", "cross", series("eurostat.gdp_growth", "es", "qoq"), {k: round(v, 1) for k, v in q.items()},
                tol=0.11, label="ES vs INE CNTR6653 (rounded)", last_n=8, warn_only=True, require_latest=False)


if __name__ == "__main__":
    rep = Report()
    run(rep)
    rep.print()
    sys.exit(1 if rep.failed else 0)
