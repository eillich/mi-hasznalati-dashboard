# A beolvasás hibakezelése és a Python nyelvi elemei

A feladatkiírás szerint érdemes ellenőrizni az adatbeolvasás hibakezeléséhez tartozó Python nyelvi elemeket. A kurzus moodle-oldala már nem érhető el, ezért az ellenőrzés mércéje a Python hivatalos oktatóanyagának hibakezelési fejezete: [The Python Tutorial, 8. Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html). A kód: `adatbetoltes.py` (és a felület hibakijelzése: `app.py`).

## Nyelvi elemek

| Nyelvi elem (fejezet) | Hol a kódban | Mire szolgál |
| --- | --- | --- |
| `try` / `except` egy konkrét kivétellel (8.3) | `nyers_szoveg()`: `except UnicodeDecodeError` | Ha a fájl nem UTF-8 kódolású, latin-1 kódolással próbálja újra, és figyelmeztet. |
| Több `except` ág, a konkrétabbtól az általánosabb felé (8.3) | `letoltes_apirol()`: `requests.Timeout` → `requests.HTTPError` → `requests.RequestException`; `helyi_fajl()`: `FileNotFoundError` → `OSError` | Minden hibatípus saját, érthető üzenetet kap (időtúllépés, HTTP-hibakód, hálózati hiba; hiányzó vagy olvashatatlan fájl). Az alosztály-kivételt előbb kell elkapni, különben az általános ág nyelné el. |
| `except` kivételtípusok csoportjával (8.3) | `nyers_szoveg()`: `except (OSError, EOFError)` | A sérült és a csonka tömörített fájl ugyanúgy kezelendő. |
| `except … as` (8.3) | minden `except` ág | A kivétel adatai bekerülnek az üzenetbe (pl. a HTTP-státuszkód: `hiba.response.status_code`). |
| `else` ág (8.3) | `betoltes()`: a forrásokon végigmenő ciklus | A sikeres betöltés utáni lépés csak akkor fut, ha a `try` blokkban nem volt hiba; hiba esetén az ok rögzül, és a ciklus a következő forrásra lép. |
| `raise` (8.4) | `nyers_szoveg()`, `tsv_feldolgozas()`, `_feldolgozas()` | A tartalmi hibák (üres fájl, HTML-oldal, hiányzó dimenzió, nincs évszám-oszlop, rossz adatkészlet) jelzése, mielőtt rossz adat jutna a megjelenítésbe. |
| Kivételláncolás: `raise … from` (8.5) | `letoltes_apirol()`, `helyi_fajl()`, `nyers_szoveg()`, `tsv_feldolgozas()` | A technikai kivétel (pl. `ParserError`) a felhasználónak szóló `AdatHiba` közvetlen okaként megmarad, így hibakereséskor is visszakövethető. |
| Saját kivételosztály (8.6) | `class AdatHiba(Exception)` | Egy közös típus minden olyan hibára, amely miatt egy forrásból nem tölthető be az adat. A forrásváltás és a felület csak ezt az egy típust kezeli. |
| Előre definiált takarítás (8.8) | `helyi_fajl()`: `Path.read_bytes()` | A fájl megnyitását és bezárását a könyvtári függvény végzi (belül `with` blokkal), ezért kézi `finally` nem kell. |

## Szándékosan nem használt elemek

- **`except Exception` (mindent elkapó ág):** nem használjuk, mert elfedné a hibák okát. Itt csak a várt kivételeket kapjuk el; minden más programhiba látható marad.
- **`warnings.filterwarnings("ignore")`:** nem használjuk, hogy az elavult paraméterekre figyelmeztető üzenetek ne rejtőzzenek el (a bolygós projekt tanulsága).
- **`finally` (8.7), kivételcsoportok és `except*` (8.9), megjegyzések: `add_note()` (8.10):** a feladatban nincs párhuzamos hibaforrás és kézzel lezárandó erőforrás, ezért nem indokoltak.

## Hibatűrés a pandas szintjén

| Elem | Hol | Mire szolgál |
| --- | --- | --- |
| `pd.read_csv(..., dtype=str, keep_default_na=False)` | `tsv_feldolgozas()` | Mindent szövegként olvas be, így semmi nem vész el és nem alakul át csendben; a hiányt a kód maga értelmezi (`:`). |
| Reguláris kifejezés (`re`, `str.extract`) | `CELLA_MINTA`, `tsv_feldolgozas()` | A szám és az Eurostat-jelölés szétválasztása egy cellán belül (`5.88 b`, `: @C`, tizedesvessző is). |
| `pd.to_numeric(..., errors="coerce")` | `tsv_feldolgozas()` | Ami nem szám, hiányzó lesz, nem állítja le a programot; a jelentés megszámolja és példákat mutat. |
| Ellenőrzés `if` + `raise` / figyelmeztetés | `tsv_feldolgozas()` | Hiányzó dimenziók, évszám-oszlopok, hibás kulcsú és ismétlődő sorok, 0–100 közé nem eső százalékok, ismeretlen jelölések. |

## Ellenőrzés

A hibakezelést 27 automatikus teszt fedi le (`tesztek/test_adatbetoltes.py`), köztük: üres fájl, HTML-hibaoldal, sérült tömörítés, CSV a TSV helyett, hiányzó dimenzió, értelmezhetetlen cella, időtúllépés, HTTP-hiba, rossz adatkészlet, és ha minden forrás hibás.
