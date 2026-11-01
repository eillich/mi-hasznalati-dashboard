"""A hiányos és jelölt adatok kezelésének tesztjei."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import adatbetoltes as ab  # noqa: E402
import adatminoseg as am  # noqa: E402


def tabla(sorok):
    """sorok: (geo, indic, ev, ertek, jelolesek, bizalmas)"""
    t = pd.DataFrame(sorok, columns=["geo", "indic_is", "ev", "ertek", "jelolesek", "bizalmas"])
    t["unit"], t["size_emp"], t["nace_r2"] = "PC_ENT", "GE10", "C10-S951_X_K"
    t["hianyzik"] = t["ertek"].isna()
    return t


NAN = float("nan")


def test_nem_kerdezett_az_eu_atlag_szerint():
    t = tabla([
        ("EU27_2020", "A", 2024, 10.0, "", False), ("HU", "A", 2024, NAN, "", False),
        ("EU27_2020", "B", 2024, NAN, "", False), ("HU", "B", 2024, NAN, "", False),
        ("DE", "B", 2024, 5.0, "", False),  # csak egy ország gyűjtötte
    ])
    assert am.nem_kerdezett(t).tolist() == [False, False, True, True, True]


def test_nem_kerdezett_eu_atlag_nelkul():
    t = tabla([("HU", "A", 2024, 1.0, "", False), ("HU", "B", 2024, NAN, "", False),
               ("DE", "B", 2024, NAN, "", False)])
    assert am.nem_kerdezett(t).tolist() == [False, True, True]


def test_hiany_osszesites_szerkezeti_nelkul():
    t = tabla([
        ("EU27_2020", "A", 2024, 10.0, "", False),
        ("HU", "A", 2024, 3.0, "", False), ("ME", "A", 2024, NAN, "", True),
        ("HU", "B", 2024, NAN, "", False),  # nem kérdezett: nem számít
    ])
    o = am.hiany_osszesites(t, ["geo"]).set_index("geo")
    assert o.loc["HU", "hiany_szazalek"] == 0 and o.loc["HU", "cellak"] == 1
    assert o.loc["ME", "hiany_szazalek"] == 100 and o.loc["ME", "bizalmas"] == 1


def test_jelolt_ertekek_elrejtese_csak_a_megjelenitesben():
    t = tabla([("HU", "A", 2024, 3.0, "b", False), ("HU", "A", 2025, 4.0, "", False),
               ("HU", "A", 2023, NAN, "u", False)])
    eredeti = t.copy()
    assert am.megjelenitheto(t, jelolt_is=True).tolist() == [True, True, False]
    assert am.megjelenitheto(t, jelolt_is=False).tolist() == [False, True, False]
    pd.testing.assert_frame_equal(t, eredeti)  # az adat nem változott


def test_valodi_adat_magyarorszag_teljes():
    adat, _ = ab.betoltes("meret", api=False)
    o = am.hiany_osszesites(adat, ["geo"]).set_index("geo")
    assert o.loc["HU", "hiany_szazalek"] == pytest.approx(0)
    assert o.loc["MK", "hiany_szazalek"] > 70
    assert am.jelolt_kozolt(adat).sum() == 890
