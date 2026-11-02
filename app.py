"""
MI-használat az európai vállalatoknál – interaktív Streamlit-dashboard
=====================================================================
Adatforrás: Eurostat, isoc_eb_ai (vállalatméret szerint) és
            isoc_eb_ain2 (ágazat szerint)

Futtatás: python -m streamlit run app.py

Állapot: 5. lépés – szűrők: mutató, vállalatméret vagy ágazat, év, kiemelt ország,
összevetés, csak EU-tagállamok a térképen, jelölt értékek.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import adatbetoltes as ab
import abrak
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


@st.cache_data(ttl=3600, show_spinner="Adatok betöltése…")
def adat_betoltese(adatkeszlet: str, feltoltott: bytes | None, nev: str, api: bool):
    """Gyorsítótárazott betöltés: nem tölt le újra minden kattintásra."""
    return ab.betoltes(adatkeszlet, feltoltott=feltoltott, feltoltott_nev=nev, api=api)


@st.cache_data(ttl=3600, show_spinner="Az adatminőség összesítése…")
def minoseg_osszesites(adatkeszlet: str, feltoltott: bytes | None, nev: str, api: bool):
    """Az adatminőség-összesítések adatkészletenként egyszer készülnek el, nem minden
    kattintásnál (az ágazati táblában közel egymillió cella van)."""
    adat, _ = adat_betoltese(adatkeszlet, feltoltott, nev, api)
    nem_kerdezett = am.nem_kerdezett(adat)
    return {
        "nem_kerdezett_arany": float(nem_kerdezett.mean()),
        "valodi_hiany_arany": float(adat.loc[~nem_kerdezett, "hianyzik"].mean()),
        "orszagos": am.hiany_osszesites(adat, ["geo"]),
        "racs": am.hiany_osszesites(adat, ["geo", "ev"]),
        "jelolt_kozolt": int(am.jelolt_kozolt(adat).sum()),
    }


# ── OLDALSÁV: ADATFORRÁS ─────────────────────────────────────────────────────
st.sidebar.header("Adatforrás")
adatkeszlet = st.sidebar.radio("Adatkészlet", list(ADATKESZLET_NEVEK),
                               format_func=ADATKESZLET_NEVEK.get)
api = st.sidebar.checkbox("Élő letöltés az Eurostat API-ról", value=True,
                          help="Ha nem sikerül, az alkalmazás a tárhelyen lévő "
                               "pillanatképet használja, és kiírja, miért.")
if st.sidebar.button("Adatok újratöltése", help="Az adatok legfeljebb egy óráig a "
                     "gyorsítótárból jönnek. A gomb azonnal újra letölti őket "
                     "(pl. ha az élő letöltés nem sikerült)."):
    st.cache_data.clear()
feltoltes = st.sidebar.file_uploader(
    "Saját letöltött Eurostat-fájl (nem kötelező)", type=["tsv", "gz", "txt"],
    help="Az Eurostatról letöltött TSV-fájl, tömörítve (.tsv.gz) vagy kibontva.")

forras_parameterek = (adatkeszlet, feltoltes.getvalue() if feltoltes else None,
                      feltoltes.name if feltoltes else "", api)
try:
    adat, jelentes = adat_betoltese(*forras_parameterek)
except ab.AdatHiba as hiba:
    st.error(f"Az adatot nem sikerült betölteni. {hiba}")
    st.stop()
minoseg = minoseg_osszesites(*forras_parameterek)

# A szűrők a megjelenítési kapcsoló fölé kerülnek (a tartalmukat lent töltjük ki)
szurok_panel = st.sidebar.container()

# ── OLDALSÁV: MEGJELENÍTÉS ───────────────────────────────────────────────────
st.sidebar.header("Megjelenítés")
jelolt_kozolt_db = minoseg["jelolt_kozolt"]
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

# ── OLDALSÁV: SZŰRŐK ─────────────────────────────────────────────────────────
# A szűrők csak azt választják ki, mi jelenjen meg; az adat nem változik.
MUTATOK = cimkek.valaszthato_mutatok()
TEMAKOR_NEVEK = {k: tk["cim"].split(" (")[0] for k, tk in cimkek.TEMAKOROK.items()}


def temakor_neve(kod: str) -> str:
    for k, tk in cimkek.TEMAKOROK.items():
        if kod in tk["mutatok"]:
            return TEMAKOR_NEVEK[k]
    return "Fő mutató"


def ervenyes_allapot(kulcs: str, lehetosegek: list) -> None:
    """Ha a korábban választott érték már nem választható (pl. másik mutató), elfelejtjük."""
    if kulcs in st.session_state and st.session_state[kulcs] not in lehetosegek:
        del st.session_state[kulcs]


lathato = adat[am.megjelenitheto(adat, jelolt_is)]
geok = sorted(map(str, lathato["geo"].unique()), key=cimkek.orszag)
orszag_kodok = [g for g in geok if g not in cimkek.AGGREGATUMOK]

szurok_panel.header("Szűrők")
mutato = szurok_panel.selectbox(
    "Mutató (térkép, idősor, fő számok)", list(MUTATOK),
    format_func=lambda k: MUTATOK[k][0],
    help="A mutató mindig a hozzá illő alapra vetítve jelenik meg "
         "(pl. a nem-használat okai a bevezetést mérlegelők körében).")
mutato_nev, mutato_egyseg = MUTATOK[mutato]

if adatkeszlet == "meret":
    meret_kodok = [k for k in cimkek.MERETEK if k in set(map(str, lathato["size_emp"].unique()))]
    meret = szurok_panel.selectbox("Vállalatméret", meret_kodok, index=meret_kodok.index("GE10"),
                                 format_func=cimkek.MERETEK.get)
    agazat = "C10-S951_X_K"
else:
    meret = "GE10"
    agazat_kodok = [k for k in cimkek.AGAZATOK if k in set(map(str, lathato["nace_r2"].unique()))]
    agazat = szurok_panel.selectbox("Ágazat", agazat_kodok, index=agazat_kodok.index("C10-S951_X_K"),
                                  format_func=cimkek.agazat)

kivalasztott = lathato[(lathato["indic_is"] == mutato) & (lathato["unit"] == mutato_egyseg)
                       & (lathato["size_emp"] == meret) & (lathato["nace_r2"] == agazat)]
# Csak a felmérési évek (amikor az uniós kérdőívben szerepelt: van EU-átlag);
# ha a bontásra nincs EU-átlag (pl. mikrovállalatok), minden év, amelyre van adat
eu_evek = kivalasztott[kivalasztott["geo"] == "EU27_2020"]["ev"]
evek = sorted((eu_evek if len(eu_evek) else kivalasztott["ev"]).unique().tolist())
if not evek:
    st.warning("Ehhez a mutatóhoz és bontáshoz nincs közölt adat. Válassz másik mutatót "
               "vagy bontást!")
    st.stop()
ervenyes_allapot("ev", evek)
ev = szurok_panel.select_slider("Év", evek, value=evek[-1], key="ev",
                              help="Csak azok az évek, amelyekre a mutatóhoz van adat.")

ervenyes_allapot("kiemelt", orszag_kodok)
kiemelt = szurok_panel.selectbox("Kiemelt ország", orszag_kodok, key="kiemelt",
                               index=orszag_kodok.index("HU") if "HU" in orszag_kodok else 0,
                               format_func=cimkek.orszag)
osszevetheto = [g for g in geok if g != kiemelt]
alap_osszevetes = ["EU27_2020"] if "EU27_2020" in osszevetheto else osszevetheto[:1]
osszevetes = szurok_panel.multiselect(
    "Összevetés", osszevetheto, default=alap_osszevetes, max_selections=4,
    format_func=cimkek.orszag, help="Legfeljebb négy ország vagy átlag, hogy a színek "
                                    "megkülönböztethetők maradjanak.")
ORSZAGOK = [kiemelt] + osszevetes
csak_eu = szurok_panel.checkbox("Csak EU-tagállamok a térképen", value=False)

megjelenitett: list[pd.DataFrame] = []


def ertek(sorok: pd.DataFrame, geo: str, ev_: int) -> float | None:
    x = sorok[(sorok["geo"] == geo) & (sorok["ev"] == ev_)]["ertek"]
    return float(x.iloc[0]) if len(x) else None


bontas_szoveg = (cimkek.MERETEK[meret].lower() if adatkeszlet == "meret"
                 else cimkek.agazat(agazat).lower())
fulek = st.tabs(["Áttekintés", "Adatminőség"])

with fulek[0]:
    # Fő számok: a kiemelt ország és az első összevetés
    masik = osszevetes[0] if osszevetes else None
    k_ertek = ertek(kivalasztott, kiemelt, ev)
    m_ertek = ertek(kivalasztott, masik, ev) if masik else None
    elso_ev = evek[0]
    k_elso = ertek(kivalasztott, kiemelt, elso_ev)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"{cimkek.orszag(kiemelt)}, {ev}", szazalek(k_ertek) if k_ertek is not None else "–")
    m2.metric(f"{cimkek.orszag(masik)}, {ev}" if masik else "Összevetés",
              szazalek(m_ertek) if m_ertek is not None else "–")
    m3.metric("Különbség (százalékpont)", f"{k_ertek - m_ertek:+.1f}".replace(".", ",").replace("-", "−")
              if None not in (k_ertek, m_ertek) else "–",
              help="A kiemelt ország és az első összevetés különbsége százalékpontban.")
    m4.metric(f"{cimkek.orszag(kiemelt)}, {elso_ev}", szazalek(k_elso) if k_elso is not None else "–",
              help="A mutató első elérhető évének értéke, összevetésül.")
    st.caption(f"{mutato_nev}, {cimkek.egyseg(mutato_egyseg)} ({bontas_szoveg}).")

    # Térkép
    st.subheader(f"{mutato_nev} – Európa, {ev}")
    terkep_sorok = kivalasztott[kivalasztott["ev"] == ev]
    if csak_eu:
        terkep_sorok = terkep_sorok[terkep_sorok["geo"].isin(cimkek.EU27)]
    if terkep_sorok.empty:
        st.info("Erre az évre nincs megjeleníthető adat.")
    else:
        st.plotly_chart(abrak.terkep(terkep_sorok, "Arány", kiemelt), width="stretch",
                        config=abrak.TERKEP_CONFIG)
        st.caption(f"Fekete körvonal: {cimkek.orszag(kiemelt)}. Szürke: nincs közölt adat, "
                   "vagy nem része a felmérésnek (a kiválasztott szűrőkkel). "
                   "Országhatárok: Natural Earth (sane-topojson).")
        megjelenitett.append(terkep_sorok)

    # Időbeli alakulás
    st.subheader("Időbeli alakulás")
    idosor_sorok = kivalasztott[kivalasztott["geo"].isin(ORSZAGOK)]
    st.plotly_chart(abrak.idosor(idosor_sorok, ORSZAGOK, cimkek.egyseg(mutato_egyseg)),
                    width="stretch", config={"displayModeBar": False})
    st.caption("Csak a mutató felmérési évei szerepelnek (2022-ben nem volt MI-kérdés); "
               "a hiányzó érték hézag, nem nulla.")
    megjelenitett.append(idosor_sorok)

    # Vállalatméret vagy ágazat szerint
    if adatkeszlet == "meret":
        st.subheader(f"Vállalatméret szerint, {ev}")
        meretek = {k: cimkek.MERETEK[k] for k in ["10-49", "50-249", "GE250", "10-249"]}
        bontas = lathato[(lathato["indic_is"] == mutato) & (lathato["unit"] == mutato_egyseg)
                         & (lathato["nace_r2"] == agazat) & (lathato["ev"] == ev)
                         & lathato["size_emp"].isin(meretek) & lathato["geo"].isin(ORSZAGOK)]
        kiemelt_kat, rendezve, cimke = "10-249", False, "A kkv-k sora félkövér."
        kat_oszlop, kategoriak = "size_emp", meretek
    else:
        st.subheader(f"Ágazat szerint, {ev}")
        agazatok = {k: cimkek.agazat(k) for k in cimkek.FO_AGAZATOK}
        if agazat not in agazatok and agazat != "C10-S951_X_K":
            agazatok[agazat] = cimkek.agazat(agazat)  # a választott ágazat is látsszon
        bontas = lathato[(lathato["indic_is"] == mutato) & (lathato["unit"] == mutato_egyseg)
                         & (lathato["size_emp"] == meret) & (lathato["ev"] == ev)
                         & lathato["nace_r2"].isin(agazatok) & lathato["geo"].isin(ORSZAGOK)]
        kiemelt_kat = agazat if agazat != "C10-S951_X_K" else "M69-M71"
        rendezve, cimke = True, f"Félkövér: {cimkek.agazat(kiemelt_kat).lower()}."
        kat_oszlop, kategoriak = "nace_r2", agazatok
    if bontas.empty:
        st.info("Ehhez a választáshoz nincs bontott adat.")
    else:
        st.plotly_chart(abrak.csoportositott_savok(bontas, ORSZAGOK, kat_oszlop, kategoriak,
                                                   cimkek.egyseg(mutato_egyseg), kiemelt_kat,
                                                   rendezve=rendezve),
                        width="stretch", config={"displayModeBar": False})
        st.caption(f"{mutato_nev}. {cimke}")
        megjelenitett.append(bontas)

    # Témakörök
    st.subheader("Hogyan és miért (nem) használják?")
    temakor = st.radio("Témakör", list(cimkek.TEMAKOROK), horizontal=True,
                       format_func=TEMAKOR_NEVEK.get, label_visibility="collapsed")
    tk = cimkek.TEMAKOROK[temakor]
    tema = lathato[lathato["indic_is"].isin(tk["mutatok"]) & (lathato["unit"] == tk["egyseg"])
                   & (lathato["size_emp"] == meret) & (lathato["nace_r2"] == agazat)
                   & lathato["geo"].isin(ORSZAGOK)]
    tema_evek = sorted(e for e in tema["ev"].unique() if e <= ev)
    if not tema_evek:
        st.info(f"Ehhez a témakörhöz {ev}-ig nincs közölt adat a kiválasztott országokra.")
    else:
        tema_ev = tema_evek[-1]
        tema = tema[tema["ev"] == tema_ev]
        st.markdown(f"**{tk['cim']}**, {tema_ev}")
        st.plotly_chart(abrak.csoportositott_savok(tema, ORSZAGOK, "indic_is", tk["mutatok"],
                                                   cimkek.egyseg(tk["egyseg"]),
                                                   "E_AI_BLEG" if temakor == "akadalyok" else None),
                        width="stretch", config={"displayModeBar": False})
        megjegyzes = "" if tema_ev == ev else f" A kiválasztott évre ({ev}) nincs adat, ezért a {tema_ev}-es."
        st.caption(f"Alap: {cimkek.egyseg(tk['egyseg'])}; {bontas_szoveg}.{megjegyzes} "
                   "A kérdőív évről évre változik, ezért nem minden évben ugyanazok a sorok.")
        megjelenitett.append(tema)

    # A megjelenített adatok táblázatban
    with st.expander("A megjelenített adatok táblázatban"):
        tabla = pd.concat(megjelenitett).drop_duplicates(
            subset=["geo", "indic_is", "unit", "size_emp", "nace_r2", "ev"])
        mutatonevek = {cimkek.FO_MUTATO: cimkek.FO_MUTATO_NEV}
        for t in cimkek.TEMAKOROK.values():
            mutatonevek.update(t["mutatok"])
        tabla = pd.DataFrame({
            "Ország": tabla["geo"].map(cimkek.orszag),
            "Mutató": tabla["indic_is"].astype(str).map(lambda k: mutatonevek.get(k, k)),
            "Alap": tabla["unit"].map(cimkek.egyseg),
            "Méret": tabla["size_emp"].astype(str).map(lambda k: cimkek.MERETEK.get(k, k)),
            "Ágazat": tabla["nace_r2"].map(cimkek.agazat),
            "Év": tabla["ev"],
            "Érték (%)": tabla["ertek"],
            "Jelölés": tabla["jelolesek"],
            "Eurostat-kód": tabla["indic_is"].astype(str),
        }).sort_values(["Mutató", "Ország", "Év"])
        st.dataframe(tabla, hide_index=True, width="stretch",
                     column_config={"Érték (%)": st.column_config.NumberColumn(format="%.2f")})
        st.download_button("Letöltés CSV-ben", tabla.to_csv(index=False, sep=";", decimal=",")
                           .encode("utf-8-sig"), "mi_hasznalat_megjelenitett.csv", "text/csv")

with fulek[1]:
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
    orszagos = minoseg["orszagos"]
    orszagos = orszagos[~orszagos["geo"].isin(cimkek.AGGREGATUMOK)]
    legtobb = orszagos.loc[orszagos["hiany_szazalek"].idxmax()]
    hu = orszagos.loc[orszagos["geo"] == "HU", "hiany_szazalek"]

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Nem kérdezett", szazalek(100 * minoseg["nem_kerdezett_arany"]),
              help="A mutató abban az évben (abban a bontásban) nem volt része az uniós "
                   "kérdőívnek: az EU-átlag nincs rá közölve, legfeljebb néhány ország "
                   "gyűjtötte. Ez nem az országok adathiánya, ezért kihagyjuk.")
    h2.metric("Valódi hiány", szazalek(100 * minoseg["valodi_hiany_arany"]),
              help="A kérdezett mutatók közül ennyi érték nem közölt "
                   "(nem megbízható, bizalmas vagy nem jelentett).")
    h3.metric("Magyarország", szazalek(hu.iloc[0]) if not hu.empty else "–",
              help="A valódi hiány aránya a magyar adatokban.")
    h4.metric("Legtöbb hiány", szazalek(legtobb["hiany_szazalek"]),
              help=cimkek.orszag(legtobb["geo"]))
    st.caption(f"Legtöbb hiány: {cimkek.orszag(legtobb['geo'])}. Az ábrákon a hiányzó érték "
               "hézagként jelenik meg, soha nem nullaként; a táblázatokban „–” jelöli.")

    # Hiánytérkép: ország × év, a valódi hiány aránya
    racs = minoseg["racs"]
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


st.caption("Forrás: Eurostat, Community survey on ICT usage and e-commerce in enterprises "
           "(isoc_eb_ai, isoc_eb_ain2).")
