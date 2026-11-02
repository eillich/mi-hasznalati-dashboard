"""Magyar feliratok az Eurostat-kódokhoz. Ismeretlen kódnál maga a kód jelenik meg."""

ORSZAGOK = {
    "AL": "Albánia", "AT": "Ausztria", "BA": "Bosznia-Hercegovina", "BE": "Belgium",
    "BG": "Bulgária", "CY": "Ciprus", "CZ": "Csehország", "DE": "Németország",
    "DK": "Dánia", "EE": "Észtország", "EL": "Görögország", "ES": "Spanyolország",
    "FI": "Finnország", "FR": "Franciaország", "HR": "Horvátország", "HU": "Magyarország",
    "IE": "Írország", "IT": "Olaszország", "LT": "Litvánia", "LU": "Luxemburg",
    "LV": "Lettország", "ME": "Montenegró", "MK": "Észak-Macedónia", "MT": "Málta",
    "NL": "Hollandia", "NO": "Norvégia", "PL": "Lengyelország", "PT": "Portugália",
    "RO": "Románia", "RS": "Szerbia", "SE": "Svédország", "SI": "Szlovénia",
    "SK": "Szlovákia", "TR": "Törökország",
}

# Országcsoportok: a térképen és az országos rangsorokban külön kezelendők
AGGREGATUMOK = {"EU27_2020": "EU-27 átlag", "EA": "Euróövezet"}

MERETEK = {
    "GE10": "Összes (10+ fő)",
    "10-49": "Kisvállalat (10–49 fő)",
    "50-249": "Középvállalat (50–249 fő)",
    "GE250": "Nagyvállalat (250+ fő)",
    "10-249": "Kkv (10–249 fő)",
    "0-9": "Mikrovállalat (0–9 fő)",
    "0_1": "0–1 fő",
    "2-9": "2–9 fő",
}


def orszag(kod: str) -> str:
    kod = str(kod)
    return AGGREGATUMOK.get(kod) or ORSZAGOK.get(kod) or kod

# Az Eurostat 2 betűs országkódja → ISO 3166-1 alpha-3 (a térképhez)
ISO3 = {
    "AL": "ALB", "AT": "AUT", "BA": "BIH", "BE": "BEL", "BG": "BGR", "CY": "CYP",
    "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "EL": "GRC", "ES": "ESP",
    "FI": "FIN", "FR": "FRA", "HR": "HRV", "HU": "HUN", "IE": "IRL", "IT": "ITA",
    "LT": "LTU", "LU": "LUX", "LV": "LVA", "ME": "MNE", "MK": "MKD", "MT": "MLT",
    "NL": "NLD", "NO": "NOR", "PL": "POL", "PT": "PRT", "RO": "ROU", "RS": "SRB",
    "SE": "SWE", "SI": "SVN", "SK": "SVK", "TR": "TUR",
}

EGYSEGEK = {
    "PC_ENT": "az összes vállalat %-a",
    "PC_ENT_AI_TANY": "az MI-t használó vállalatok %-a",
    "PC_ENT_AI_EC": "a bevezetést mérlegelő vállalatok %-a",
    "PC_ENT_AI_TX": "az MI-t nem használó vállalatok %-a",
    "PC_ENT_AI_PDI": "a személyes adatot MI-vel kezelő vállalatok %-a",
    "PC_ENT_IUSE": "az internetet használó vállalatok %-a",
}

# A mutatók témakörönként; a témakörhöz illő egységgel (az alapra vonatkoztatva)
TEMAKOROK = {
    "technologiak": {
        "cim": "Milyen MI-technológiát használnak?",
        "egyseg": "PC_ENT",
        "mutatok": {
            "E_AI_TTM": "Szövegelemzés (szövegbányászat)",
            "E_AI_TNLG": "Szöveg-, beszéd- vagy kódgenerálás",
            "E_AI_TPVSG": "Kép-, videó- vagy hanggenerálás",
            "E_AI_TSR": "Beszédfelismerés",
            "E_AI_TML": "Gépi tanulás adatelemzésre",
            "E_AI_TPA": "Munkafolyamat-automatizálás, döntéstámogatás",
            "E_AI_TIR": "Kép- és személyfelismerés",
            "E_AI_TAR": "Gépek autonóm mozgatása",
        },
    },
    "celok": {
        "cim": "Mire használják az MI-t?",
        "egyseg": "PC_ENT_AI_TANY",
        "mutatok": {
            "E_AI_PMS": "Marketing, értékesítés",
            "E_AI_PBAM": "Üzleti adminisztráció, vezetés",
            "E_AI_PBA": "Üzleti adminisztráció",
            "E_AI_PME": "Vállalatirányítás",
            "E_AI_PFIN": "Számvitel, kontrolling, pénzügy",
            "E_AI_PRDI": "Kutatás-fejlesztés, innováció",
            "E_AI_PPP": "Termelési folyamatok",
            "E_AI_PITS": "Informatikai biztonság",
            "E_AI_PHR": "Emberierőforrás-gazdálkodás, toborzás",
            "E_AI_PLOG": "Logisztika",
        },
    },
    "forras": {
        "cim": "Honnan származik az MI-megoldás?",
        "egyseg": "PC_ENT_AI_TANY",
        "mutatok": {
            "E_AI_ARDY": "Kész kereskedelmi szoftver",
            "E_AI_AMOWN": "Saját munkatársak által módosított kereskedelmi szoftver",
            "E_AI_AOS": "Saját munkatársak által módosított nyílt forrású szoftver",
            "E_AI_AEXT": "Külső fejlesztő fejlesztette vagy módosította",
            "E_AI_ADOWN": "Saját munkatársak fejlesztették",
        },
    },
    "felelos": {
        "cim": "Személyes adatok és torzítás-ellenőrzés (2024, 12–13 ország, EU-átlag nélkül)",
        "egyseg": "PC_ENT_AI_TANY",
        "mutatok": {
            "E_AI_PDI": "Személyes adatot kezel MI-vel",
            "E_AI_BIAS": "Ellenőrzi az MI-eredmények esetleges torzítását",
        },
    },
    "akadalyok": {
        "cim": "Miért nem vezették be? (a bevezetést mérlegelők körében)",
        "egyseg": "PC_ENT_AI_EC",
        "mutatok": {
            "E_AI_BLE": "Nincs meg a szükséges szakértelem",
            "E_AI_BLEG": "Nem világosak a jogi következmények",
            "E_AI_BCDP": "Adatvédelmi aggályok",
            "E_AI_BDDT": "A szükséges adatok hiánya vagy minősége",
            "E_AI_BINC": "Nem illeszkedik a meglévő rendszerekhez",
            "E_AI_BCST": "Túl magas költség",
            "E_AI_BEC": "Etikai megfontolások",
            "E_AI_BNU": "Nem hasznos a vállalkozásnak",
        },
    },
}

FO_MUTATO = "E_AI_TANY"
FO_MUTATO_NEV = "Legalább egy MI-technológiát használ"

# Témakörön kívüli, külön választható mutatók: kód → (név, alap)
KULON_MUTATOK = {
    "E_AI_EC": ("Mérlegelte az MI bevezetését (az MI-t nem használók körében)", "PC_ENT_AI_TX"),
}

# A fő ágazatok (az ágazati ábrához); a teljes lista a szűrőkhöz: AGAZATOK
FO_AGAZATOK = ["C", "D_E", "F", "G", "H", "I", "J", "L", "M", "M69-M71", "N"]

AGAZATOK = {
    "C10-S951_X_K": "Összes vizsgált ágazat (mezőgazdaság, bányászat, pénzügy nélkül)",
    "C-F": "Ipar és építőipar", "C-E": "Ipar (feldolgozóipar, energia, víz)",
    "C": "Feldolgozóipar", "C10-C18": "Élelmiszer-, textil-, fa-, papíripar, nyomdaipar",
    "C10-C12": "Élelmiszer, ital, dohány", "C13-C15": "Textil, ruházat, bőr",
    "C16-C18": "Fa, papír, nyomdaipar", "C19-C23": "Kőolaj, vegyi anyag, gyógyszer, gumi, műanyag",
    "C19": "Kokszgyártás, kőolaj-feldolgozás", "C20": "Vegyi anyag", "C21": "Gyógyszergyártás",
    "C22_C23": "Gumi, műanyag, nemfém ásványi termék", "C24_C25": "Fémalapanyag, fémfeldolgozás",
    "C26-C33": "Számítógép, elektronika, gép, jármű, bútor, javítás",
    "C26": "Számítógép, elektronikai, optikai termék", "C27_C28": "Villamos berendezés, gépgyártás",
    "C27": "Villamos berendezés", "C28": "Gépgyártás", "C29_C30": "Járműgyártás",
    "C31-C33": "Bútor, egyéb feldolgozóipar, javítás",
    "D_E": "Energia-, víz- és hulladékgazdálkodás", "D": "Villamosenergia-, gáz-, gőzellátás",
    "E": "Víz, szennyvíz, hulladékgazdálkodás",
    "F": "Építőipar", "G": "Kereskedelem, gépjárműjavítás", "G45": "Gépjármű-kereskedelem, -javítás",
    "G45-S951_X_K": "Szolgáltatások (pénzügyi szektor nélkül)", "G46": "Nagykereskedelem",
    "G47": "Kiskereskedelem", "H": "Szállítás, raktározás", "I": "Szálláshely, vendéglátás",
    "I55": "Szálláshely-szolgáltatás", "J": "Információ, kommunikáció",
    "J58-J60": "Kiadói, film-, műsorszolgáltatás", "J61": "Távközlés",
    "J62_J63": "Informatikai szolgáltatás", "L_M": "Ingatlanügyek; szakmai, tudományos tevékenység",
    "L": "Ingatlanügyek",
    "M": "Szakmai, tudományos, műszaki tevékenység",
    "M69-M71": "Jogi, számviteli, tanácsadási, mérnöki tevékenység",
    "M72": "Tudományos kutatás-fejlesztés", "M73-M75": "Reklám, piackutatás, egyéb szakmai tevékenység",
    "N": "Adminisztratív és szolgáltatást támogató tevékenység",
    "N77-N82_X_N79": "Kölcsönzés, munkaerő-piaci, biztonsági, irodai szolgáltatás",
    "N79": "Utazásszervezés", "S951": "Számítógép, kommunikációs eszköz javítása",
    "ICT": "Infokommunikációs ágazat összesen",
}


def agazat(kod: str) -> str:
    return AGAZATOK.get(str(kod), str(kod))


def egyseg(kod: str) -> str:
    return EGYSEGEK.get(str(kod), str(kod))


EU27 = {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR", "HR", "HU",
        "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"}


def valaszthato_mutatok() -> dict[str, tuple[str, str]]:
    """A térképen és az idősoron választható mutatók: kód → (név, a hozzá illő alap)."""
    valasztek = {FO_MUTATO: (FO_MUTATO_NEV, "PC_ENT"), **KULON_MUTATOK}
    for tk in TEMAKOROK.values():
        for kod, nev in tk["mutatok"].items():
            valasztek[kod] = (nev, tk["egyseg"])
    return valasztek


_EKEZET = str.maketrans("áéíóöőúüűÁÉÍÓÖŐÚÜŰ", "aeiooouuuAEIOOOUUU")


def abc_kulcs(szoveg: str) -> tuple:
    """Magyar ábécérendhez közelítő rendezési kulcs (ékezetes betű az alapbetű után)."""
    return (szoveg.lower().translate(_EKEZET), szoveg.lower())


def agazatok_abc_sorrendben(kodok) -> list[str]:
    """Az „összes” elöl, a többi ágazat a magyar neve szerint ábécérendben."""
    kodok = [k for k in kodok if k in AGAZATOK]
    elol = [k for k in ("C10-S951_X_K",) if k in kodok]
    return elol + sorted((k for k in kodok if k not in elol), key=lambda k: abc_kulcs(agazat(k)))
