"""
Seasonal and calendar adjustment statements for field notes (`note_es`).

Rule (docs/audit/seasonal-adjustment.md): every published field states its adjustment,
using exactly one of these phrases, alongside any other note text.
"""

SCA = "Datos corregidos de efectos estacionales y de calendario"
SA = "Datos corregidos de efectos estacionales"  # the source adjusts for seasonality only
NSA = "Datos originales (sin corregir de estacionalidad)"
ANNUAL = "Dato anual: la corrección de estacionalidad no procede"

PHRASES = (SCA, SA, NSA, ANNUAL)


def note(adjustment: str, text: str | None = None) -> str:
    """`text. adjustment` (or just the adjustment statement)."""
    if adjustment not in PHRASES:
        raise ValueError(f"unknown adjustment statement: {adjustment!r}")
    return f"{text.rstrip('. ')}. {adjustment}" if text else adjustment
