"""
Az ábrák. Minden függvény a már kiválasztott (szűrt) sorokat kapja meg, és egy
Plotly-ábrát ad vissza; az adatot nem módosítja.

Színek: a kiemelt ország kék, az EU-átlag szürke (összehasonlítási alap);
további országok a kategóriapaletta következő színeit kapják, rögzített sorrendben.
A mennyiséget (térkép) egyszínű kék skála mutatja.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import cimkek

KEK_SKALA = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
EU_SZIN = "#898781"
KATEGORIA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SZOVEG = "#52514e"
RACS = "#e8e7e3"

# A térkép országhatárai (topojson) a saját szerverről jönnek, nem a Plotly
# CDN-jéről: így a térkép külső letöltés nélkül is működik (static/ mappa,
# Streamlit statikus kiszolgálás). A st.plotly_chart config-jába kell átadni.
TERKEP_CONFIG = {"displayModeBar": False, "topojsonURL": "app/static/"}


def orszag_szinek(orszagok: list[str]) -> dict[str, str]:
    """Az EU-átlag mindig szürke; az országok a választás sorrendjében kapnak színt."""
    szinek, i = {}, 0
    for kod in orszagok:
        if kod in cimkek.AGGREGATUMOK:
            szinek[kod] = EU_SZIN
        else:
            szinek[kod] = KATEGORIA[i % len(KATEGORIA)]
            i += 1
    return szinek


def _alap(abra: go.Figure, magassag: int, y_cim: str | None = None,
          x_cim: str | None = None) -> go.Figure:
    abra.update_layout(
        template="plotly_white", height=magassag, separators=", ",
        font=dict(color=SZOVEG, size=13),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        hoverlabel=dict(bgcolor="white", font_color="#0b0b0b"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    abra.update_xaxes(gridcolor=RACS, zeroline=False, title_text=x_cim)
    abra.update_yaxes(gridcolor=RACS, zeroline=False, title_text=y_cim)
    return abra


def _jeloles_szoveg(jelolesek: pd.Series) -> pd.Series:
    nevek = {"b": "idősortörés", "d": "eltérő definíció"}
    return jelolesek.map(lambda j: "<br><i>" + ", ".join(nevek[b] for b in j if b in nevek) + "</i>"
                         if any(b in nevek for b in j) else "")


# ── TÉRKÉP ──────────────────────────────────────────────────────────────────

def terkep(sorok: pd.DataFrame, cim: str, kiemelt: str | None = "HU") -> go.Figure:
    """Európa-térkép: az érték országonként (az országcsoportok nélkül)."""
    adat = sorok[~sorok["geo"].astype(str).isin(cimkek.AGGREGATUMOK)].copy()
    adat["geo"] = adat["geo"].astype(str)
    adat["iso3"] = adat["geo"].map(cimkek.ISO3)
    adat = adat.dropna(subset=["iso3"])
    adat["nev"] = adat["geo"].map(cimkek.orszag)
    adat["jel"] = _jeloles_szoveg(adat["jelolesek"])
    abra = go.Figure(go.Choropleth(
        locations=adat["iso3"], z=adat["ertek"], locationmode="ISO-3",
        zmin=0, zmax=max(10, float(adat["ertek"].max() or 0)),
        colorscale=[[i / (len(KEK_SKALA) - 1), c] for i, c in enumerate(KEK_SKALA)],
        marker_line_color="white", marker_line_width=0.6,
        customdata=adat[["nev", "jel"]],
        hovertemplate="<b>%{customdata[0]}</b><br>%{z:.1f}%%{customdata[1]}<extra></extra>",
        colorbar=dict(title=cim, ticksuffix="%", thickness=12, len=0.75),
    ))
    if kiemelt and kiemelt in set(adat["geo"]):
        abra.add_trace(go.Choropleth(
            locations=[cimkek.ISO3[kiemelt]], z=[0], locationmode="ISO-3",
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
            marker_line_color="#0b0b0b", marker_line_width=2, hoverinfo="skip",
        ))
    abra.update_geos(scope="europe", resolution=50, projection_type="mercator",
                     lonaxis_range=[-11, 42], lataxis_range=[34, 70.5],
                     showcountries=True, countrycolor="white", showland=True,
                     landcolor="#e8e7e3", showocean=False, showlakes=False,
                     showframe=False, showcoastlines=False, bgcolor="rgba(0,0,0,0)")
    return _alap(abra, 520).update_layout(margin=dict(l=0, r=0, t=10, b=0))


# ── IDŐSOR ──────────────────────────────────────────────────────────────────

def idosor(sorok: pd.DataFrame, orszagok: list[str], y_cim: str) -> go.Figure:
    """Vonaldiagram évek szerint; a hiányzó év hézag (nem nulla)."""
    szinek = orszag_szinek(orszagok)
    abra = go.Figure()
    evek = sorted(sorok["ev"].unique())
    for kod in orszagok:
        o = sorok[sorok["geo"].astype(str) == kod].set_index("ev").reindex(evek)
        jel = _jeloles_szoveg(o["jelolesek"].fillna(""))
        abra.add_trace(go.Scatter(
            x=evek, y=o["ertek"], name=cimkek.orszag(kod), mode="lines+markers",
            line=dict(color=szinek[kod], width=2.5 if kod not in cimkek.AGGREGATUMOK else 2,
                      dash="dot" if kod in cimkek.AGGREGATUMOK else None),
            marker=dict(size=8), connectgaps=False, customdata=jel,
            hovertemplate="%{y:.1f}%%{customdata}<extra>" + cimkek.orszag(kod) + "</extra>",
        ))
    abra = _alap(abra, 380, y_cim)
    abra.update_xaxes(tickmode="array", tickvals=evek, ticktext=[str(e) for e in evek])
    abra.update_yaxes(ticksuffix="%", rangemode="tozero")
    abra.update_layout(hovermode="x unified")
    return abra


# ── OSZLOP- ÉS SÁVDIAGRAMOK ─────────────────────────────────────────────────

def csoportositott_savok(sorok: pd.DataFrame, orszagok: list[str], kategoria_oszlop: str,
                         kategoriak: dict[str, str], x_cim: str,
                         kiemelt_kategoria: str | None = None,
                         rendezve: bool = True) -> go.Figure:
    """
    Vízszintes, csoportosított sávok: kategóriánként (pl. méret, ágazat, cél)
    egy-egy sáv országonként. A kategóriák sorrendje az első ország értéke
    szerint csökkenő; a hiányzó érték üresen marad.
    """
    szinek = orszag_szinek(orszagok)
    kodok = [k for k in kategoriak if k in set(sorok[kategoria_oszlop].astype(str))]
    elso = sorok[sorok["geo"].astype(str) == orszagok[0]].set_index(
        sorok[sorok["geo"].astype(str) == orszagok[0]][kategoria_oszlop].astype(str))["ertek"]
    if rendezve:
        kodok.sort(key=lambda k: (pd.isna(elso.get(k)), -(elso.get(k) or 0)))
    feliratok = [f"<b>{kategoriak[k]}</b>" if k == kiemelt_kategoria else kategoriak[k]
                 for k in kodok]
    abra = go.Figure()
    for kod in orszagok:
        o = sorok[sorok["geo"].astype(str) == kod]
        o = o.set_index(o[kategoria_oszlop].astype(str)).reindex(kodok)
        abra.add_trace(go.Bar(
            y=feliratok, x=o["ertek"], name=cimkek.orszag(kod), orientation="h",
            marker=dict(color=szinek[kod], line_width=0, cornerradius=4),
            customdata=_jeloles_szoveg(o["jelolesek"].fillna("")),
            hovertemplate="%{y}<br><b>%{x:.1f}%</b>%{customdata}<extra>"
                          + cimkek.orszag(kod) + "</extra>",
        ))
    abra = _alap(abra, 70 + 28 * len(kodok) * max(1, len(orszagok)) ** 0.6, None, x_cim)
    abra.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
    abra.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
    abra.update_xaxes(ticksuffix="%", rangemode="tozero")
    return abra
