# MI-használat az európai vállalatoknál – interaktív dashboard

Streamlit-alkalmazás az Eurostat vállalati mesterségesintelligencia-használati adataihoz. A felületen szűrhető, hogyan használják az MI-t a vállalkozások, különösen a kis- és középvállalkozások, Magyarországon és az Európai Unióban.

Készült: PPKE ITK, Mesterséges Intelligencia Alkalmazásai szakirányú továbbképzés, Szkript nyelvek tárgy, a szakdolgozati portfólió részeként.

> **Állapot:** 2. lépés – rugalmas adatbeolvasás és adatminőség-kijelzés. A térkép, a grafikonok és a szűrők a következő lépésekben készülnek.

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

## Futtatás

```
pip install -r requirements.txt
python -m streamlit run app.py
```

Tesztek: `pip install -r requirements-dev.txt`, majd `python -m pytest -q tesztek`.
