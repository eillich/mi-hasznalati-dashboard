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
