"""
MI-használat az európai vállalatoknál – interaktív Streamlit-dashboard
=====================================================================
Adatforrás: Eurostat, isoc_eb_ai (vállalatméret szerint) és
            isoc_eb_ain2 (ágazat szerint)

Futtatás: python -m streamlit run app.py

Állapot: 3. lépés – adatbetöltés, adatminőség, a hiányos adatok kezelése.
A térkép, a grafikonok és a szűrők a következő lépésekben kerülnek bele.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import adatbetoltes as ab
import adatminoseg as am
import cimkek

st.set_page_config(page_title="MI-használat a vállalatoknál", page_icon="📊", layout="wide")

ADATKESZLET_NEVEK = {
    "meret": "Vállalatméret szerint (isoc_eb_ai)",
    "agazat": "Ágazat szerint (isoc_eb_ain2)",
}
FORRAS_IKON = {"api": "🌐", "helyi": "💾", "feltoltott": "📄"}

# Egyszínű (kék) sorozat a mennyiséghez: világos = kevés, sötét = sok
KEK_SKALA = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def szazalek(x: float, tizedes: int = 1) -> str:
    return f"{x:.{tizedes}f}%".replace(".", ",")


@st.cache_data(ttl=24 * 3600, show_spinner="Adatok betöltése…")
def adat_betoltese(adatkeszlet: str, feltoltott: bytes | None, nev: str, api: bool):
    """Gyorsítótárazott betöltés: nem tölt le újra minden kattintásra."""
    return ab.betoltes(adatkeszlet, feltoltott=feltoltott, feltoltott_nev=nev, api=api)


# ── OLDALSÁV: ADATFORRÁS ─────────────────────────────────────────────────────
st.sidebar.header("Adatforrás")
adatkeszlet = st.sidebar.radio("Adatkészlet", list(ADATKESZLET_NEVEK),
                               format_func=ADATKESZLET_NEVEK.get)
api = st.sidebar.checkbox("Élő letöltés az Eurostat API-ról", value=True,
                          help="Ha nem sikerül, az alkalmazás a tárhelyen lévő "
                               "pillanatképet használja, és kiírja, miért.")
feltoltes = st.sidebar.file_uploader(
    "Saját letöltött Eurostat-fájl (nem kötelező)", type=["tsv", "gz", "txt"],
    help="Az Eurostatról letöltött TSV-fájl, tömörítve (.tsv.gz) vagy kibontva.")

try:
    adat, jelentes = adat_betoltese(
        adatkeszlet,
        feltoltes.getvalue() if feltoltes else None,
        feltoltes.name if feltoltes else "",
        api,
    )
except ab.AdatHiba as hiba:
    st.error(f"Az adatot nem sikerült betölteni. {hiba}")
    st.stop()

# ── OLDALSÁV: MEGJELENÍTÉS ───────────────────────────────────────────────────
st.sidebar.header("Megjelenítés")
jelolt_kozolt_db = int(am.jelolt_kozolt(adat).sum())
jelolt_is = st.sidebar.checkbox(
    "Jelölt értékek az ábrákon", value=True,
    help="Idősortörés (b) vagy eltérő definíció (d) jelölésű, de közölt értékek. "
         "Kikapcsolva ezek nem jelennek meg az ábrákon; az adat nem változik.")
st.sidebar.caption(f"{jelolt_kozolt_db:,} közölt érték jelölt.".replace(",", " "))

# ── FEJLÉC ───────────────────────────────────────────────────────────────────
st.title("MI-használat az európai vállalatoknál")
st.markdown(
    f"**Adatkészlet:** {ADATKESZLET_NEVEK[adatkeszlet]} · "
    f"**Forrás:** {FORRAS_IKON[jelentes.forras]} {jelentes.forras_leirasa} · "
    f"**Évek:** {', '.join(map(str, jelentes.evek))}"
)

if jelentes.tartalek_okai:
    st.warning(
        "Nem az elsődleges forrásból töltöttünk be, mert:\n\n"
        + "\n".join(f"- {ok}" for ok in jelentes.tartalek_okai)
    )
for figyelmeztetes in jelentes.figyelmeztetesek:
    st.info(figyelmeztetes)

# ── ADATMINŐSÉG ──────────────────────────────────────────────────────────────
st.subheader("Adatminőség")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Idősorok", f"{jelentes.sorok:,}".replace(",", " "))
k2.metric("Adatcellák", f"{jelentes.cellak:,}".replace(",", " "))
k3.metric("Üres cella", f"{jelentes.hianyzo / jelentes.cellak:.1%}".replace(".", ","),
          help="A „:” jelű cellák aránya, a bizalmas és a nem kérdezett értékekkel együtt. "
               "A valódi hiányt lásd lent.")
k4.metric("Bizalmas", f"{jelentes.bizalmas:,}".replace(",", " "),
          help="Az Eurostat nem közli („: @C”).")
k5.metric("Jelölt cella", f"{sum(jelentes.jelolesek.values()):,}".replace(",", " "),
          help="Jelöléssel ellátott cellák (pl. kis megbízhatóság); a jelölés hiányzó "
               "értéken is állhat („: u”).")

if jelentes.jelolesek:
    jelolestabla = pd.DataFrame(
        [(betu, ab.JELOLESEK.get(betu, "ismeretlen jelölés"), db)
         for betu, db in jelentes.jelolesek.items()],
        columns=["Jelölés", "Jelentés", "Cellák száma"],
    )
    st.dataframe(jelolestabla, hide_index=True, width="content")

# ── MINTA: A NYERS CELLA ÉS A SZÉTVÁLASZTOTT ÉRTÉK ──────────────────────────
with st.expander("Hogyan olvassuk be a cellákat? (minta a beolvasott adatból)"):
    st.caption("A „Nyers cella” az Eurostat-fájl eredeti tartalma; ebből választjuk szét "
               "a számértéket és a jelöléseket. Az eredeti adatot nem írjuk felül.")
    # Minden fajta cellából egy példa: sima szám, jelölt szám, hiányzó, jelölt hiányzó, bizalmas
    kozolt = adat["ertek"].notna()
    jelolt = adat["jelolesek"].ne("")
    esetek = [kozolt & ~jelolt, kozolt & adat["jelolesek"].str.contains("u"),
              kozolt & adat["jelolesek"].str.contains("b"), adat["hianyzik"] & ~jelolt & ~adat["bizalmas"],
              adat["hianyzik"] & jelolt, adat["bizalmas"]]
    minta = pd.concat([adat[eset].head(1) for eset in esetek])
    minta["ertek"] = minta["ertek"].map(lambda x: "–" if pd.isna(x) else f"{x:g}".replace(".", ","))
    st.dataframe(
        minta.rename(columns={
            "geo": "Ország", "indic_is": "Mutató", "unit": "Egység", "size_emp": "Méret",
            "nace_r2": "Ágazat", "ev": "Év", "nyers": "Nyers cella", "ertek": "Érték",
            "jelolesek": "Jelölés", "bizalmas": "Bizalmas", "hianyzik": "Hiányzik",
        })[["Ország", "Mutató", "Egység", "Méret", "Ágazat", "Év",
            "Nyers cella", "Érték", "Jelölés", "Bizalmas", "Hiányzik"]],
        hide_index=True, width="stretch",
    )

# ── HIÁNYZÓ ADATOK ───────────────────────────────────────────────────────────
st.subheader("Hiányzó adatok")
nem_kerdezett = am.nem_kerdezett(adat)
valodi = adat[~nem_kerdezett]
orszagos = am.hiany_osszesites(adat, ["geo"])
orszagos = orszagos[~orszagos["geo"].isin(cimkek.AGGREGATUMOK)]
legtobb = orszagos.loc[orszagos["hiany_szazalek"].idxmax()]
hu = orszagos.loc[orszagos["geo"] == "HU", "hiany_szazalek"]

h1, h2, h3, h4 = st.columns(4)
h1.metric("Nem kérdezett", szazalek(100 * nem_kerdezett.mean()),
          help="A mutató abban az évben (abban a bontásban) nem volt része az uniós "
               "kérdőívnek: az EU-átlag nincs rá közölve, legfeljebb néhány ország "
               "gyűjtötte. Ez nem az országok adathiánya, ezért kihagyjuk.")
h2.metric("Valódi hiány", szazalek(100 * valodi["hianyzik"].mean()),
          help="A kérdezett mutatók közül ennyi érték nem közölt "
               "(nem megbízható, bizalmas vagy nem jelentett).")
h3.metric("Magyarország", szazalek(hu.iloc[0]) if not hu.empty else "–",
          help="A valódi hiány aránya a magyar adatokban.")
h4.metric("Legtöbb hiány", szazalek(legtobb["hiany_szazalek"]),
          help=cimkek.orszag(legtobb["geo"]))
st.caption(f"Legtöbb hiány: {cimkek.orszag(legtobb['geo'])}. Az ábrákon a hiányzó érték "
           "hézagként jelenik meg, soha nem nullaként; a táblázatokban „–” jelöli.")

# Hiánytérkép: ország × év, a valódi hiány aránya
racs = am.hiany_osszesites(adat, ["geo", "ev"])
racs = racs[~racs["geo"].isin(cimkek.AGGREGATUMOK)]
sorrend = orszagos.sort_values("hiany_szazalek", ascending=False)["geo"].astype(str).tolist()
evek = sorted(racs["ev"].unique())
matrix = (racs.assign(geo=racs["geo"].astype(str))
          .pivot(index="geo", columns="ev", values="hiany_szazalek").reindex(sorrend))
reszlet = (racs.assign(geo=racs["geo"].astype(str))
           .pivot(index="geo", columns="ev", values=["hianyzo", "cellak", "bizalmas"]))
nevek = [cimkek.orszag(k) for k in sorrend]
hover = [[f"<b>{cimkek.orszag(g)}, {e}</b><br>"
          f"Hiányzik: {szazalek(matrix.loc[g, e])}<br>"
          f"{int(reszlet.loc[g, ('hianyzo', e)])} / {int(reszlet.loc[g, ('cellak', e)])} cella"
          f", ebből bizalmas: {int(reszlet.loc[g, ('bizalmas', e)])}"
          if pd.notna(matrix.loc[g, e]) else f"{cimkek.orszag(g)}, {e}: nincs adat"
          for e in evek] for g in sorrend]
abra = go.Figure(go.Heatmap(
    z=matrix.values, x=[str(e) for e in evek], y=nevek,
    zmin=0, zmax=100, colorscale=[[i / (len(KEK_SKALA) - 1), c] for i, c in enumerate(KEK_SKALA)],
    xgap=2, ygap=2, hovertext=hover, hoverinfo="text",
    colorbar=dict(title="Hiányzik", ticksuffix="%", thickness=12),
))
abra.update_layout(
    height=24 * len(sorrend) + 90, margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#52514e"), yaxis=dict(autorange="reversed"),
    xaxis=dict(side="top", type="category"),
)
st.markdown("**A valódi hiány aránya országonként és évenként** "
            "(a nem kérdezett mutatók nélkül; az EU- és az euróövezeti átlag nélkül)")
st.plotly_chart(abra, width="stretch", config={"displayModeBar": False})

st.caption("Forrás: Eurostat, Community survey on ICT usage and e-commerce in enterprises. "
           "A térkép, a grafikonok és a szűrők a következő fejlesztési lépésben készülnek.")
