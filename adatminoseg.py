"""
A hiányos és a jelölt adatok kezelése a megjelenítés során.

Az eredeti (beolvasott) adatot nem módosítjuk: ezek a függvények csak
összesítenek, illetve megmondják, mely értékek jelenjenek meg az ábrákon.
"""

from __future__ import annotations

import pandas as pd

# Közölt értéken előforduló jelölések, amelyeket a felhasználó elrejthet.
# (A "u" – kis megbízhatóság – ezekben a táblákban csak közöletlen cellán áll.)
ELREJTHETO_JELOLESEK = {"b": "idősortörés", "d": "eltérő definíció"}


def nem_kerdezett(adat: pd.DataFrame, eu_kod: str = "EU27_2020") -> pd.Series:
    """
    Szerkezeti hiány: a mutató abban az évben nem volt része az uniós
    kérdőívnek. Ennek jele, hogy az EU-átlag nincs közölve rá (legfeljebb
    néhány ország gyűjtötte saját döntésből). Ez nem az ország adathiánya,
    ezért a hiány-összesítésből kihagyjuk. Ha az adatban nincs EU-átlag
    (pl. feltöltött részhalmaz), akkor az számít szerkezetinek, amit
    egyetlen ország sem közölt.
    """
    kulcs = [adat[k] for k in ["indic_is", "unit", "size_emp", "nace_r2", "ev"]]
    van_eu = (adat["geo"] == eu_kod).any()
    kozolt = adat["ertek"].notna() & ((adat["geo"] == eu_kod) if van_eu else True)
    # Csoportonként (mutató, egység, méret, ágazat, év): van-e közölt alapérték.
    # A kategória-oszlopokon csoportosítunk, szöveggé alakítás nélkül (gyors).
    kerdezett = kozolt.groupby(kulcs, observed=True, sort=False).transform("any")
    return ~kerdezett.astype(bool)


def hiany_osszesites(adat: pd.DataFrame, szerint: list[str],
                     szerkezeti_nelkul: bool = True) -> pd.DataFrame:
    """
    Csoportonként: hány cella van, ebből hány hiányzik, hány bizalmas,
    és mekkora a hiány aránya (százalékban). Alapértelmezés szerint a
    nem kérdezett mutató–év párok nem számítanak hiánynak.
    """
    if szerkezeti_nelkul:
        adat = adat[~nem_kerdezett(adat)]
    csoport = adat.groupby(szerint, observed=True)
    eredmeny = pd.DataFrame({
        "cellak": csoport.size(),
        "hianyzo": csoport["hianyzik"].sum(),
        "bizalmas": csoport["bizalmas"].sum(),
    }).reset_index()
    eredmeny["hiany_szazalek"] = 100 * eredmeny["hianyzo"] / eredmeny["cellak"]
    return eredmeny


def jelolt_kozolt(adat: pd.DataFrame) -> pd.Series:
    """Közölt érték, amelyen elrejthető jelölés áll (pl. idősortörés)."""
    minta = "[" + "".join(ELREJTHETO_JELOLESEK) + "]"
    return adat["ertek"].notna() & adat["jelolesek"].str.contains(minta, regex=True)


def megjelenitheto(adat: pd.DataFrame, jelolt_is: bool = True) -> pd.Series:
    """
    Mely sorok kerüljenek az ábrákra: a közölt értékek, és – ha a felhasználó
    kéri – a jelölt értékek is. A hiányzó érték soha nem nulla: kimarad.
    """
    maszk = adat["ertek"].notna()
    if not jelolt_is:
        maszk &= ~jelolt_kozolt(adat)
    return maszk
