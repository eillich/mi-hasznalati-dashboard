"""Az ábrák tesztjei: helyes adat, a hiány nem nulla, a jelölt értékek kezelése."""

import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import abrak  # noqa: E402
import adatbetoltes as ab  # noqa: E402
import adatminoseg as am  # noqa: E402

ADAT, _ = ab.betoltes("meret", api=False)
FO = ADAT[(ADAT.indic_is == "E_AI_TANY") & (ADAT.unit == "PC_ENT") & (ADAT.size_emp == "GE10")]


def test_idosor_ertekei_es_hiany_hezag():
    sorok = FO[FO.geo.isin(["HU", "EU27_2020"])]
    abra = abrak.idosor(sorok, ["HU", "EU27_2020"], "")
    hu = abra.data[0]
    assert list(hu.x) == [2021, 2023, 2024, 2025]
    assert list(hu.y) == [2.98, 3.68, 7.41, 10.37]
    # hiányzó év: hézag (NaN), nem nulla
    abra2 = abrak.idosor(sorok[~((sorok.geo == "HU") & (sorok.ev == 2023))], ["HU", "EU27_2020"], "")
    assert math.isnan(abra2.data[0].y[1])


def test_terkep_orszagcsoportok_nelkul_es_kiemelessel():
    sorok = FO[FO.ev == 2025]
    abra = abrak.terkep(sorok, "Arány")
    helyek = set(abra.data[0].locations)
    assert "HUN" in helyek and len(helyek) == len(sorok) - 2  # EU27, EA nélkül
    assert list(abra.data[1].locations) == ["HUN"]


def test_savok_rendezese_es_kiemeles():
    meretek = {"10-49": "Kis", "50-249": "Közép", "GE250": "Nagy"}
    sorok = ADAT[(ADAT.indic_is == "E_AI_TANY") & (ADAT.unit == "PC_ENT") & (ADAT.ev == 2025)
                 & ADAT.size_emp.isin(meretek) & ADAT.geo.isin(["HU", "EU27_2020"])]
    rendezett = abrak.csoportositott_savok(sorok, ["HU", "EU27_2020"], "size_emp", meretek, "", "50-249")
    assert list(rendezett.data[0].y) == ["Nagy", "<b>Közép</b>", "Kis"]
    sorban = abrak.csoportositott_savok(sorok, ["HU", "EU27_2020"], "size_emp", meretek, "",
                                        rendezve=False)
    assert list(sorban.data[0].y) == ["Kis", "Közép", "Nagy"]


def test_jelolt_ertek_elrejtve_nem_jelenik_meg():
    lathato = ADAT[am.megjelenitheto(ADAT, jelolt_is=False)]
    assert not am.jelolt_kozolt(lathato).any()


def test_eu_szurke_orszagok_rogzitett_sorrendben():
    szinek = abrak.orszag_szinek(["HU", "EU27_2020", "AT"])
    assert szinek["EU27_2020"] == abrak.EU_SZIN
    assert szinek["HU"] == abrak.KATEGORIA[0] and szinek["AT"] == abrak.KATEGORIA[1]
