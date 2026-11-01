# MI-használat az európai vállalatoknál – interaktív dashboard

Streamlit-alkalmazás az Eurostat vállalati mesterségesintelligencia-használati adataihoz. A felületen szűrhető, hogyan használják az MI-t a vállalkozások, különösen a kis- és középvállalkozások, Magyarországon és az Európai Unióban.

Készült: PPKE ITK, Mesterséges Intelligencia Alkalmazásai szakirányú továbbképzés, Szkript nyelvek tárgy, a szakdolgozati portfólió részeként.

> **Állapot:** 5. lépés – a térkép, a grafikonok és a táblázat a felületről szűrhető.

## Az adat

| Adatkészlet | Tartalom | Méret (2026-11-01) |
| --- | --- | --- |
| [`isoc_eb_ai`](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ai/default/table) | MI-használat vállalatméret szerint | 25 263 idősor, 101 052 adatcella |
| [`isoc_eb_ain2`](https://ec.europa.eu/eurostat/databrowser/view/isoc_eb_ain2/default/table) | MI-használat ágazat (NACE Rev. 2) szerint | 236 998 idősor, 947 992 adatcella |

- Forrás: Eurostat, Community survey on ICT usage and e-commerce in enterprises; legalább 10 fős vállalkozások, 36 ország és aggregátum, 2021, 2023, 2024, 2025.
- 63 mutató: MI-technológiák, felhasználási célok, az MI-megoldás forrása, a nem-használat okai (köztük a jogi következmények tisztázatlansága).
- Az adatok kb. harmada hiányzik (`:`), részben bizalmas (`: @C`); a közölt értékek egy része jelölt (`b` idősortörés, `d` eltérő definíció, `u` kis megbízhatóság).
- A pillanatkép eredete és ellenőrzőösszegei: [`adat/LETOLTES.md`](adat/LETOLTES.md).

## A beolvasás

Az alkalmazás az adatot nem módosítja előre (nincs Excel- vagy kézi előfeldolgozás); minden a beolvasáskor és a megjelenítéskor történik (`adatbetoltes.py`):

1. **Forrás, sorrendben:** feltöltött fájl (ha van) → élő letöltés az Eurostat API-ról → a tárhelyen lévő pillanatkép. Ha egy forrás nem érhető el vagy hibás, a következőre vált, és a felületen kiírja, miért.
2. **Formátum:** tömörített vagy sima TSV; UTF-8, szükség esetén latin-1; a HTML-hibaoldalt felismeri.
3. **Cellák:** a számérték és az Eurostat-jelölés szétválasztása (`8.70 u`, `: @C`, tizedesvessző is), a nyers cella megmarad.
4. **Ellenőrzések:** hiányzó dimenziók, évszám-oszlopok, hibás kulcsú és ismétlődő sorok, értelmezhetetlen cellák, 0–100 % közé nem eső százalékok, ismeretlen jelölések, rossz adatkészlet.

A hibakezelés Python nyelvi elemei, a hivatalos dokumentációhoz mérve: [`dokumentacio/python-nyelvi-elemek.md`](dokumentacio/python-nyelvi-elemek.md).

## A hiányos adatok

- **Nem kérdezett:** ha a mutató abban az évben és bontásban nem volt része az uniós kérdőívnek (az EU-átlag nincs közölve), a hiány szerkezeti, nem az országé; az összesítés ezeket kihagyja (`adatminoseg.py`). Ez a cellák kb. harmada.
- **Valódi hiány:** a kérdezett mutatók közül a nem közölt értékek (nem megbízható, bizalmas, nem jelentett). A felület országonként és évenként mutatja (hiánytérkép).
- **Jelölt értékek:** az idősortöréses (`b`) és eltérő definíciójú (`d`) közölt értékek a megjelenítésből kikapcsolhatók; az adat nem változik.
- A hiányzó érték az ábrákon hézag, soha nem nulla; a táblázatokban „–”.

## A megjelenítés

Két fül: **Áttekintés** és **Adatminőség**.

- Fő számok: Magyarország és az EU-átlag, különbség százalékpontban.
- Európa-térkép az MI-t használó vállalatok arányáról (egyszínű skála, Magyarország kiemelve).
- Időbeli alakulás (a hiányzó év hézag, nem nulla).
- Vállalatméret, illetve ágazat szerinti összevetés (a kkv-k, illetve a jogi és tanácsadási ágazat kiemelve).
- Témakörök: technológiák, felhasználási célok, az MI-megoldás forrása, a nem-használat okai; mindig a témakörhöz illő alapra vetítve (pl. az okok a bevezetést mérlegelők körében).
- A megjelenített adatok táblázatban, CSV-letöltéssel.

A térkép országhatárait (Natural Earth, a [`sane-topojson`](https://github.com/etpinard/sane-topojson) csomagból, MIT-licenc) az alkalmazás a saját `static/` mappájából szolgálja ki, így nem függ külső letöltéstől.

## A szűrők (oldalsáv)

A szűrők csak azt választják ki, mi jelenjen meg; az adat nem változik.

- **Mutató:** az MI-használat, a technológiák, a célok, az MI-megoldás forrása vagy a nem-használat egyik oka; mindig a hozzá illő alapra vetítve.
- **Vállalatméret** (méret szerinti adatkészlet) vagy **ágazat** (ágazati adatkészlet, 50 ágazat).
- **Év:** csak a mutató felmérési évei (amikor az uniós kérdőívben szerepelt).
- **Kiemelt ország** (a fő számokban, kék színnel, a térképen körvonallal) és **összevetés** (legfeljebb négy ország vagy átlag, rögzített színsorrendben; az EU-átlag mindig szürke).
- **Csak EU-tagállamok a térképen**, és a **jelölt értékek** (idősortörés, eltérő definíció) ki-be kapcsolása.
- A témakörábra a kiválasztott évet követi; ha arra az évre nincs adat a témakörben, a legutóbbi korábbit mutatja, és ezt kiírja.

## Futtatás

```
pip install -r requirements.txt
python -m streamlit run app.py
```

Tesztek: `pip install -r requirements-dev.txt`, majd `python -m pytest -q tesztek`.
