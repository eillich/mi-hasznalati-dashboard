"""A rugalmas beolvasás tesztjei: valódi pillanatkép, hibás fájlok, forrásváltás."""

import gzip
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import adatbetoltes as ab  # noqa: E402

FEJLEC = "freq,size_emp,nace_r2,indic_is,unit,geo\\TIME_PERIOD\t2024 \t2025 \n"


def tsv(*sorok: str, fejlec: str = FEJLEC) -> bytes:
    return (fejlec + "".join(s + "\n" for s in sorok)).encode("utf-8")


def sor(geo="HU", indic="E_AI_TANY", unit="PC_ENT", meret="GE10", nace="C10-S951_X_K",
        ertekek=("7.41 ", "10.37 ")) -> str:
    return f"A,{meret},{nace},{indic},{unit},{geo}\t" + "\t".join(ertekek)


def feldolgoz(adat: bytes):
    j = ab.BetoltesiJelentes()
    return ab.tsv_feldolgozas(ab.nyers_szoveg(adat, j), j), j


# ── Valódi pillanatkép ─────────────────────────────────────────────────────

def test_valodi_meret_szerinti_pillanatkep():
    tabla, j = ab.betoltes("meret", api=False)
    assert j.forras == "helyi"
    assert (j.sorok, j.cellak) == (25263, 101052)
    assert j.bizalmas == 682
    assert j.jelolesek == {"u": 1089, "b": 888, "d": 29}
    assert j.evek == [2021, 2023, 2024, 2025]
    hu = tabla[(tabla.geo == "HU") & (tabla.indic_is == "E_AI_TANY") & (tabla.unit == "PC_ENT")
               & (tabla.size_emp == "GE10") & (tabla.ev == 2025)]
    assert hu["ertek"].item() == pytest.approx(10.37)


def test_valodi_agazati_pillanatkep():
    tabla, j = ab.betoltes("agazat", api=False)
    assert (j.sorok, j.cellak) == (236998, 947992)
    jogi = tabla[(tabla.geo == "HU") & (tabla.indic_is == "E_AI_TANY") & (tabla.unit == "PC_ENT")
                 & (tabla.nace_r2 == "M69-M71") & (tabla.ev == 2025)]
    assert jogi["ertek"].item() == pytest.approx(22.51)


# ── Cellák értelmezése ─────────────────────────────────────────────────────

def test_jeloles_hiany_es_bizalmas_szetvalasztasa():
    tabla, j = feldolgoz(tsv(sor(ertekek=("8.70 u", ": ")), sor(geo="ME", ertekek=(": @C", "3 bd"))))
    hu = tabla[tabla.geo == "HU"].set_index("ev")
    assert hu.loc[2024, "ertek"] == pytest.approx(8.70) and hu.loc[2024, "jelolesek"] == "u"
    assert hu.loc[2025, "hianyzik"] and pd.isna(hu.loc[2025, "ertek"])
    me = tabla[tabla.geo == "ME"].set_index("ev")
    assert me.loc[2024, "bizalmas"] and pd.isna(me.loc[2024, "ertek"])
    assert me.loc[2025, "ertek"] == 3 and me.loc[2025, "jelolesek"] == "bd"
    assert j.jelolesek == {"u": 1, "b": 1, "d": 1} and j.bizalmas == 1


def test_tizedesvesszo_es_felesleges_szokozok():
    tabla, _ = feldolgoz(tsv(sor(ertekek=("  12,5  ", " 7 "))))
    assert sorted(tabla["ertek"]) == [7, 12.5]


def test_ertelmezhetetlen_cella_figyelmeztetessel():
    tabla, j = feldolgoz(tsv(sor(ertekek=("abc", "n/a"))))
    assert tabla["ertek"].isna().all()
    assert j.ervenytelen == 2 and j.ervenytelen_peldak == ["abc", "n/a"]
    assert any("nem értelmezhető" in f for f in j.figyelmeztetesek)


def test_szazalek_tartomanyon_kivul():
    tabla, j = feldolgoz(tsv(sor(ertekek=("150", "-3"))))
    assert tabla["ertek"].isna().all() and j.tartomanyon_kivul == 2


def test_ismeretlen_jeloles():
    _, j = feldolgoz(tsv(sor(ertekek=("5 x", "6"))))
    assert j.ismeretlen_jelolesek == ["x"]


def test_ismetlodo_sor_es_hibas_kulcs():
    tabla, j = feldolgoz(tsv(sor(), sor(), "A,GE10,HU\t1\t2"))
    assert j.sorok == 1 and len(tabla) == 2
    assert any("ismétlődő" in f for f in j.figyelmeztetesek)
    assert any("nem bontható" in f for f in j.figyelmeztetesek)


def test_tomoritett_es_sima_fajl_egyformán():
    sima = tsv(sor())
    a, _ = feldolgoz(sima)
    b, _ = feldolgoz(gzip.compress(sima))
    pd.testing.assert_frame_equal(a, b)


# ── Hibás fájlok ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("adat, uzenet", [
    (b"", "üres"),
    (b"   \n", "üres"),
    (b"<!DOCTYPE html><html>Sorry</html>", "HTML"),
    (b"\x1f\x8bnem gzip", "sérült"),
    (b"pl_name,hostname,disc_year\nKepler-1 b,Kepler-1,2006\n", "egy oszlopot"),
    (b"a\tb\n1\t2\n", "nem Eurostat"),
    (b"freq,geo\\TIME_PERIOD\t2025\nA,HU\t1\n", "Hiányzó dimenzió"),
    (b"freq,size_emp,nace_r2,indic_is,unit,geo\\TIME_PERIOD\tmegj\nA,a,b,c,d,HU\tx\n", "évszám"),
])
def test_hibas_fajl_ertheto_uzenettel(adat, uzenet):
    with pytest.raises(ab.AdatHiba, match=uzenet):
        feldolgoz(adat)


def test_nem_mi_adatkeszlet_feltoltve():
    adat = tsv(sor(indic="E_CC"))
    _, j = ab.betoltes("meret", feltoltott=adat, feltoltott_nev="mas.tsv", api=False)
    assert j.forras == "helyi"
    assert "nem az Eurostat MI-használati" in j.tartalek_okai[0]


def test_rossz_adatkeszlet_feltoltve():
    adat = tsv(sor(nace="C"), sor(nace="J"))
    with pytest.raises(ab.AdatHiba, match="isoc_eb_ain2"):
        ab._feldolgozas(adat, ab.BetoltesiJelentes(), "meret")


# ── Forrásváltás ───────────────────────────────────────────────────────────

class _Valasz:
    def __init__(self, content=b"", status=200):
        self.content, self.status_code = content, status

    def raise_for_status(self):
        import requests
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


def test_api_idotullepes_utan_helyi_pillanatkep(monkeypatch):
    import requests

    def lassu(*a, **k):
        raise requests.Timeout()
    monkeypatch.setattr(requests, "get", lassu)
    _, j = ab.betoltes("meret")
    assert j.forras == "helyi"
    assert len(j.tartalek_okai) == 1 and "nem válaszolt" in j.tartalek_okai[0]


def test_api_html_hibaoldalt_ad(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **k: _Valasz(b"<html>sorry</html>"))
    _, j = ab.betoltes("meret")
    assert j.forras == "helyi" and "HTML" in j.tartalek_okai[0]


def test_api_http_hiba(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **k: _Valasz(status=503))
    _, j = ab.betoltes("meret")
    assert "HTTP 503" in j.tartalek_okai[0]


def test_api_sikeres(monkeypatch):
    import requests
    valodi = ab.helyi_fajl("isoc_eb_ai")
    monkeypatch.setattr(requests, "get", lambda *a, **k: _Valasz(valodi))
    _, j = ab.betoltes("meret")
    assert j.forras == "api" and j.tartalek_okai == []


def test_hibas_feltoltes_utan_api_helyett_helyi(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "get", lambda *a, **k: _Valasz(status=500))
    _, j = ab.betoltes("meret", feltoltott=b"rossz", feltoltott_nev="valami.csv")
    assert j.forras == "helyi" and len(j.tartalek_okai) == 2
    assert "valami.csv" in j.tartalek_okai[0]


def test_minden_forras_hibas(monkeypatch, tmp_path):
    monkeypatch.setattr(ab, "ADAT_MAPPA", tmp_path)
    with pytest.raises(ab.AdatHiba, match="Egyik forrásból sem"):
        ab.betoltes("meret", api=False)
