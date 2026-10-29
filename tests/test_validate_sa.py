import unittest

from src.fetchers.ine_indicators import SeriesError, validate_series
from src.fetchers.ine_series import SA


def item(name):
    return {"COD": "X1", "Nombre": name, "Data": [{"Fecha": 0, "Valor": 1.0}]}


class ValidateSeasonalAdjustment(unittest.TestCase):
    def test_adjusted_series_passes(self):
        validate_series("X1", [SA], item("Total Nacional. Datos ajustados de estacionalidad y calendario. PIB."))

    def test_unadjusted_series_declared_adjusted_fails(self):
        # "ajustados de estacionalidad" is a substring of "no ajustados de estacionalidad".
        with self.assertRaises(SeriesError):
            validate_series("X1", [SA], item("Total Nacional. Datos no ajustados de estacionalidad y calendario. PIB."))

    def test_unadjusted_series_without_sa_token_passes(self):
        validate_series("X1", ["PIB"], item("Total Nacional. Datos no ajustados de estacionalidad y calendario. PIB."))


if __name__ == "__main__":
    unittest.main()
