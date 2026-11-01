"""
MI-használat az európai vállalatoknál – interaktív Streamlit-dashboard
=====================================================================
Adatforrás: Eurostat, isoc_eb_ai (vállalatméret szerint) és
            isoc_eb_ain2 (ágazat szerint)

Futtatás: python -m streamlit run app.py

Állapot: 2. lépés – adatbetöltés és adatminőség. A megjelenítések
(térkép, grafikonok, szűrők) a következő lépésekben kerülnek bele.
"""

import pandas as pd
import streamlit as st

import adatbetoltes as ab

st.set_page_config(page_title="MI-használat a vállalatoknál", page_icon="📊", layout="wide")

ADATKESZLET_NEVEK = {
    "meret": "Vállalatméret szerint (isoc_eb_ai)",
    "agazat": "Ágazat szerint (isoc_eb_ain2)",
}
FORRAS_IKON = {"api": "🌐", "helyi": "💾", "feltoltott": "📄"}


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
k3.metric("Hiányzó", f"{jelentes.hianyzo / jelentes.cellak:.1%}".replace(".", ","),
          help="A „:” jelű cellák aránya; ebben benne vannak a bizalmas értékek is.")
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

st.caption("Forrás: Eurostat, Community survey on ICT usage and e-commerce in enterprises. "
           "A térkép, a grafikonok és a szűrők a következő fejlesztési lépésben készülnek.")
