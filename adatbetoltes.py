"""
Az Eurostat vállalati MI-használati adatainak rugalmas beolvasása.

Három forrás, ebben a sorrendben:
  1. a felhasználó által feltöltött fájl (ha van),
  2. letöltés az Eurostat API-ról,
  3. a tárhelyen lévő, változatlan pillanatkép (adat/ mappa).

Ha egy forrás nem érhető el vagy hibás, a következőre vált, és a váltás okát
a betöltési jelentésben rögzíti, hogy a felület meg tudja mutatni.

Az eredeti adatot nem írjuk felül: a nyers cellaérték is megmarad (`nyers`),
a számérték és az Eurostat-jelölések ebből kerülnek szétválasztásra.
A modul nem hív Streamlit-függvényt; a hibák megjelenítése a felület dolga.
"""

from __future__ import annotations

import gzip
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# ── ÁLLANDÓK ────────────────────────────────────────────────────────────────

ADATKESZLETEK = {
    "meret": "isoc_eb_ai",     # MI-használat vállalatméret szerint
    "agazat": "isoc_eb_ain2",  # MI-használat ágazat (NACE Rev. 2) szerint
}

API_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/"
    "{kod}?format=TSV&compressed=true"
)
ADAT_MAPPA = Path(__file__).parent / "adat"
HELYI_FAJLNEV = "estat_{kod}.tsv.gz"

ELVART_DIMENZIOK = ["freq", "size_emp", "nace_r2", "indic_is", "unit", "geo"]

# Az Eurostat jelölései (flagek); a bizalmas érték külön kezelendő (": @C")
JELOLESEK = {
    "b": "idősortörés",
    "c": "bizalmas",
    "d": "eltérő definíció",
    "e": "becsült",
    "f": "előrejelzés",
    "n": "nem jelentős",
    "p": "előzetes",
    "r": "felülvizsgált",
    "s": "Eurostat-becslés",
    "u": "kis megbízhatóság",
    "z": "nem alkalmazható",
}

# A százalékos egységek kódja "PC_"-vel kezdődik; ezeknél 0 és 100 közötti érték várható
SZAZALEK_ELOTAG = "PC_"

# Egy cella: szám vagy ":", utána tetszőleges jelölés (betűk, "@C"), szóközökkel
CELLA_MINTA = re.compile(r"^\s*(?P<ertek>:|[-+]?\d+(?:[.,]\d+)?)\s*(?P<jel>[A-Za-z@ ]*?)\s*$")


class AdatHiba(Exception):
    """Olyan hiba, amely miatt az adott forrásból nem lehet adatot betölteni."""


@dataclass
class BetoltesiJelentes:
    """Mi történt a betöltéskor – ezt mutatja meg a felület."""

    adatkeszlet: str = ""
    forras: str = ""                 # "feltoltott", "api" vagy "helyi"
    forras_leirasa: str = ""
    tartalek_okai: list[str] = field(default_factory=list)  # miért nem az előző forrás
    sorok: int = 0                   # idősorok száma a fájlban
    cellak: int = 0                  # adatcellák (sor × év)
    hianyzo: int = 0                 # ":" cellák
    bizalmas: int = 0                # ": @C" cellák
    ervenytelen: int = 0             # nem értelmezhető cellák
    ervenytelen_peldak: list[str] = field(default_factory=list)
    tartomanyon_kivul: int = 0       # százalékos érték 0–100 kívül
    jelolesek: dict[str, int] = field(default_factory=dict)
    ismeretlen_jelolesek: list[str] = field(default_factory=list)
    evek: list[int] = field(default_factory=list)
    figyelmeztetesek: list[str] = field(default_factory=list)


# ── NYERS BÁJTOK → SZÖVEG ────────────────────────────────────────────────────

def nyers_szoveg(adat: bytes, jelentes: BetoltesiJelentes | None = None) -> str:
    """Tömörített (gzip) vagy sima fájl tartalmát szöveggé alakítja."""
    if not adat:
        raise AdatHiba("A fájl üres.")
    if adat[:2] == b"\x1f\x8b":  # gzip "varázsbájtok"
        try:
            adat = gzip.decompress(adat)
        except (OSError, EOFError) as hiba:
            raise AdatHiba(f"A tömörített fájl sérült, nem bontható ki ({hiba}).") from hiba
    try:
        szoveg = adat.decode("utf-8-sig")
    except UnicodeDecodeError:
        szoveg = adat.decode("latin-1")
        if jelentes is not None:
            jelentes.figyelmeztetesek.append(
                "A fájl nem UTF-8 kódolású; latin-1 kódolással olvastuk be.")
    if not szoveg.strip():
        raise AdatHiba("A fájl üres.")
    if szoveg.lstrip()[:1] == "<":
        raise AdatHiba("A fájl HTML-oldal, nem adatfájl "
                       "(például hibaoldal vagy átirányítás a letöltés helyett).")
    return szoveg


# ── EUROSTAT TSV FELDOLGOZÁSA ────────────────────────────────────────────────

def tsv_feldolgozas(szoveg: str, jelentes: BetoltesiJelentes) -> pd.DataFrame:
    """
    Az Eurostat széles TSV-formátumát hosszú táblává alakítja.

    Bemenet: első oszlop "freq,size_emp,...,geo\\TIME_PERIOD", majd évenként
    egy oszlop, a cellákban "érték jelölés" (pl. "8.70 u") vagy ":".
    Kimenet: soronként egy (dimenziók, év) érték, a nyers cellával együtt.
    """
    try:
        tabla = pd.read_csv(io.StringIO(szoveg), sep="\t", dtype=str,
                            keep_default_na=False, skipinitialspace=False)
    except pd.errors.EmptyDataError as hiba:
        raise AdatHiba("A fájl üres.") from hiba
    except pd.errors.ParserError as hiba:
        raise AdatHiba(f"A fájl nem olvasható tabulátorral tagolt táblaként ({hiba}).") from hiba

    tabla.columns = [str(o).strip() for o in tabla.columns]
    if tabla.shape[1] < 2:
        raise AdatHiba("A fájl nem tabulátorral tagolt Eurostat TSV "
                       "(csak egy oszlopot találtunk; lehet, hogy CSV vagy más formátum).")

    kulcs_oszlop = tabla.columns[0]
    if "\\" not in kulcs_oszlop:
        raise AdatHiba("Az első oszlop fejléce nem Eurostat-formátumú "
                       f"(várt: 'freq,...,geo\\TIME_PERIOD', kapott: '{kulcs_oszlop[:60]}').")
    dimenziok = [d.strip() for d in kulcs_oszlop.split("\\")[0].split(",")]
    hianyzo_dim = [d for d in ELVART_DIMENZIOK if d not in dimenziok]
    if hianyzo_dim:
        raise AdatHiba("Hiányzó dimenzió(k) a fájlban: " + ", ".join(hianyzo_dim)
                       + ". Nem az MI-használati adatkészlet?")
    tobblet_dim = [d for d in dimenziok if d not in ELVART_DIMENZIOK]
    if tobblet_dim:
        jelentes.figyelmeztetesek.append(
            "Ismeretlen dimenzió(k), figyelmen kívül hagyva: " + ", ".join(tobblet_dim))

    ev_oszlopok = [o for o in tabla.columns[1:] if re.fullmatch(r"\d{4}", o)]
    if not ev_oszlopok:
        raise AdatHiba("Nincs évszám-oszlop a fájlban.")
    egyeb = [o for o in tabla.columns[1:] if o not in ev_oszlopok]
    if egyeb:
        jelentes.figyelmeztetesek.append(
            "Nem évszám fejlécű oszlop(ok), figyelmen kívül hagyva: " + ", ".join(egyeb[:5]))

    # A kulcsoszlop szétbontása dimenziókra
    reszek = tabla[kulcs_oszlop].str.strip().str.split(",", expand=True)
    hibas_kulcs = reszek.notna().sum(axis=1) != len(dimenziok)
    if hibas_kulcs.any():
        jelentes.figyelmeztetesek.append(
            f"{int(hibas_kulcs.sum())} sor kulcsa nem bontható a(z) {len(dimenziok)} "
            "dimenzióra; ezeket a sorokat kihagytuk.")
        tabla, reszek = tabla[~hibas_kulcs], reszek[~hibas_kulcs]
    reszek = reszek.iloc[:, :len(dimenziok)]
    reszek.columns = dimenziok
    tabla = pd.concat([reszek[ELVART_DIMENZIOK], tabla[ev_oszlopok]], axis=1)

    # Ugyanaz az idősor kétszer?
    duplikalt = tabla.duplicated(subset=ELVART_DIMENZIOK)
    if duplikalt.any():
        jelentes.figyelmeztetesek.append(
            f"{int(duplikalt.sum())} ismétlődő sort kihagytunk (az első előfordulás maradt).")
        tabla = tabla[~duplikalt]
    jelentes.sorok = len(tabla)

    # Széles → hosszú tábla: egy sor = egy adatcella
    hosszu = tabla.melt(id_vars=ELVART_DIMENZIOK, value_vars=ev_oszlopok,
                        var_name="ev", value_name="nyers")
    hosszu["nyers"] = hosszu["nyers"].fillna("").str.strip()
    jelentes.cellak = len(hosszu)

    # Érték és jelölés szétválasztása
    reszlet = hosszu["nyers"].str.extract(CELLA_MINTA)
    ertek_szoveg = reszlet["ertek"]
    jel = reszlet["jel"].fillna("").str.replace(" ", "", regex=False)

    ures = hosszu["nyers"] == ""
    ervenytelen = ertek_szoveg.isna() & ~ures
    hosszu["hianyzik"] = (ertek_szoveg == ":") | ures
    hosszu["bizalmas"] = jel.str.contains("@C", regex=False)
    betuk = jel.str.replace("@C", "", regex=False).str.lower()
    hosszu["jelolesek"] = betuk

    szam = ertek_szoveg.where(ertek_szoveg != ":").str.replace(",", ".", regex=False)
    hosszu["ertek"] = pd.to_numeric(szam, errors="coerce")

    # Százalékos egységnél a 0–100 tartományon kívüli érték hibásnak tekintendő
    szazalekos = hosszu["unit"].str.startswith(SZAZALEK_ELOTAG)
    kivul = szazalekos & hosszu["ertek"].notna() & ~hosszu["ertek"].between(0, 100)
    hosszu.loc[kivul, "ertek"] = float("nan")

    # Jelentés
    jelentes.hianyzo = int((ertek_szoveg == ":").sum() + ures.sum())
    jelentes.bizalmas = int(hosszu["bizalmas"].sum())
    jelentes.ervenytelen = int(ervenytelen.sum())
    jelentes.ervenytelen_peldak = hosszu.loc[ervenytelen, "nyers"].head(5).tolist()
    jelentes.tartomanyon_kivul = int(kivul.sum())
    szamlalo: dict[str, int] = {}
    for betu_sor, db in betuk[betuk != ""].value_counts().items():
        for betu in betu_sor:
            szamlalo[betu] = szamlalo.get(betu, 0) + int(db)
    jelentes.jelolesek = dict(sorted(szamlalo.items(), key=lambda t: -t[1]))
    jelentes.ismeretlen_jelolesek = sorted(b for b in szamlalo if b not in JELOLESEK)
    if jelentes.ervenytelen:
        jelentes.figyelmeztetesek.append(
            f"{jelentes.ervenytelen} cella nem értelmezhető számként; hiányzónak tekintjük.")
    if jelentes.tartomanyon_kivul:
        jelentes.figyelmeztetesek.append(
            f"{jelentes.tartomanyon_kivul} százalékos érték 0 és 100 közé nem esik; "
            "hiányzónak tekintjük.")
    if jelentes.ismeretlen_jelolesek:
        jelentes.figyelmeztetesek.append(
            "Ismeretlen jelölés(ek): " + ", ".join(jelentes.ismeretlen_jelolesek))

    hosszu["ev"] = hosszu["ev"].astype(int)
    jelentes.evek = sorted(hosszu["ev"].unique().tolist())
    for oszlop in ELVART_DIMENZIOK:
        hosszu[oszlop] = hosszu[oszlop].astype("category")
    return hosszu[ELVART_DIMENZIOK + ["ev", "ertek", "jelolesek", "bizalmas", "hianyzik", "nyers"]]


def adatkeszlet_felismerese(adat: pd.DataFrame) -> str | None:
    """Melyik adatkészlet ez? 'meret', 'agazat', vagy None, ha egyik sem."""
    if "E_AI_TANY" not in set(adat["indic_is"].astype(str)):
        return None
    return "agazat" if adat["nace_r2"].nunique() > 1 else "meret"


# ── FORRÁSOK ─────────────────────────────────────────────────────────────────

def letoltes_apirol(kod: str, idokorlat: float = 30) -> bytes:
    """Letölti az adatkészletet az Eurostat API-ról (tömörített TSV)."""
    import requests  # csak itt kell; a tesztek kicserélhetik

    try:
        valasz = requests.get(API_URL.format(kod=kod), timeout=idokorlat)
        valasz.raise_for_status()
    except requests.Timeout as hiba:
        raise AdatHiba(f"Az Eurostat API nem válaszolt {idokorlat:.0f} másodpercen belül.") from hiba
    except requests.HTTPError as hiba:
        raise AdatHiba(f"Az Eurostat API hibát adott vissza (HTTP {hiba.response.status_code}).") from hiba
    except requests.RequestException as hiba:
        raise AdatHiba(f"Hálózati hiba az Eurostat API elérésekor ({type(hiba).__name__}).") from hiba
    return valasz.content


def helyi_fajl(kod: str) -> bytes:
    """A tárhelyen lévő pillanatkép beolvasása."""
    utvonal = ADAT_MAPPA / HELYI_FAJLNEV.format(kod=kod)
    try:
        return utvonal.read_bytes()
    except FileNotFoundError as hiba:
        raise AdatHiba(f"A helyi pillanatkép nem található: {utvonal.name}") from hiba
    except OSError as hiba:
        raise AdatHiba(f"A helyi pillanatkép nem olvasható ({hiba}).") from hiba


def _feldolgozas(adat: bytes, jelentes: BetoltesiJelentes, adatkeszlet: str) -> pd.DataFrame:
    tabla = tsv_feldolgozas(nyers_szoveg(adat, jelentes), jelentes)
    felismert = adatkeszlet_felismerese(tabla)
    if felismert is None:
        raise AdatHiba("A fájl nem az Eurostat MI-használati adatkészlete "
                       "(nincs benne az 'E_AI_TANY' mutató).")
    if felismert != adatkeszlet:
        raise AdatHiba(f"A fájl a(z) {ADATKESZLETEK[felismert]} adatkészlet, "
                       f"nem a várt {ADATKESZLETEK[adatkeszlet]}.")
    return tabla


def betoltes(adatkeszlet: str, feltoltott: bytes | None = None,
             feltoltott_nev: str = "", api: bool = True,
             idokorlat: float = 30) -> tuple[pd.DataFrame, BetoltesiJelentes]:
    """
    Betölti az adatkészletet a legjobb elérhető forrásból.

    adatkeszlet: "meret" vagy "agazat".
    feltoltott: a felhasználó által feltöltött fájl bájtjai (ha van).
    api: megpróbálja-e az Eurostat API-t.
    """
    if adatkeszlet not in ADATKESZLETEK:
        raise ValueError(f"Ismeretlen adatkészlet: {adatkeszlet}")
    kod = ADATKESZLETEK[adatkeszlet]
    okok: list[str] = []

    forrasok = []
    if feltoltott is not None:
        forrasok.append(("feltoltott", f"feltöltött fájl ({feltoltott_nev or 'névtelen'})",
                         lambda: feltoltott))
    if api:
        forrasok.append(("api", f"Eurostat API ({kod}, élő letöltés)",
                         lambda: letoltes_apirol(kod, idokorlat)))
    forrasok.append(("helyi", f"helyi pillanatkép ({HELYI_FAJLNEV.format(kod=kod)}, "
                              "letöltve 2026-11-01)", lambda: helyi_fajl(kod)))

    for forras, leiras, beolvaso in forrasok:
        jelentes = BetoltesiJelentes(adatkeszlet=kod, forras=forras, forras_leirasa=leiras)
        try:
            tabla = _feldolgozas(beolvaso(), jelentes, adatkeszlet)
        except AdatHiba as hiba:
            okok.append(f"{leiras}: {hiba}")
            continue
        jelentes.tartalek_okai = okok
        return tabla, jelentes

    raise AdatHiba("Egyik forrásból sem sikerült betölteni az adatot. " + " | ".join(okok))
