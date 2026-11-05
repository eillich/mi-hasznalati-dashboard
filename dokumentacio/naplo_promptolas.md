# Napló – MI-használat az európai vállalatoknál (interaktív Eurostat-dashboard)
## Szkript nyelvek – a promptolás érdekes részletei

Az alkalmazás: https://mi-hasznalati-dashboard.streamlit.app
A kód és az adat: https://github.com/eillich/mi-hasznalati-dashboard

Az MI-eszköz: Claude (claude.ai, a szakdolgozati projektben), amely a kódot írta, futtatta és tesztelte, a GitHub-tárhelyen dolgozott, a naplót vezette. Én határoztam meg a feladatot és a sorrendet, én döntöttem minden javaslatról, és én próbáltam ki az élő változatot. A teljes, szó szerinti napló a szakdolgozat MI-mellékletében van; itt a lényeges részek.

---

## A feladat

Egy komplex adatforrás interaktív megjelenítése: több száz sor és oszlop, rugalmas beolvasás adathibák kezelésével, az adatra jellemző megjelenítés, és a megjelenítés befolyásolása a felületen (szűrés), az adat előfeldolgozása nélkül.

A téma a szakdolgozatomhoz kapcsolódik (MI-alapú asszisztens a kkv-k MI-szabályozási megfelelésének ügyvédi előkészítéséhez): mennyire használnak MI-t a vállalkozások, különösen a kis- és középvállalkozások, és mi tartja vissza azokat, amelyek nem.

## Az adat

**Eurostat**, a vállalatok IKT-használatáról szóló uniós felmérés két táblája:

| Adatkészlet | Tartalom | Méret |
| --- | --- | --- |
| `isoc_eb_ai` | MI-használat vállalatméret szerint | 25 263 idősor, 101 052 adatcella |
| `isoc_eb_ain2` | MI-használat ágazat szerint (50 ágazat) | 236 998 idősor, 947 992 adatcella |

36 ország és átlag, 2021, 2023, 2024, 2025 (2022-ben nem volt MI-kérdés), 63 mutató. Az adatcellák kb. harmada üres, és négyféle Eurostat-jelölés fordul elő (kis megbízhatóság, idősortörés, eltérő definíció, bizalmas). Részletesen: [`README.md`](../README.md), az adat eredete és ellenőrzőösszegei: [`adat/LETOLTES.md`](../adat/LETOLTES.md).

---

## Előzmény: a bolygós (exoplanet) projekt – és ami kiderült róla

A tárgyból korábban a NASA exobolygó-adataiból készítettem Streamlit-dashboardot. Ugyanezzel a módszerrel indultunk, ezért feltöltöttem a régi kódot, naplót és képernyőképeket.

**Az első prompt** (rövidítve): *„Készítsük el a szakdolgozathoz a projektet a Szkript nyelvek tárgyhoz. A téma: keresd meg a projekten belül, hogy mit választottunk ehhez a tárgyhoz. A feladat: ugyanazt fogjuk megcsinálni mint az exoplanet projektnél, Streamlit-et használtunk. […] Ehhez a projekthez külön fájlokat készítünk és külön naplózzuk. Először írd meg a projekt megvalósítási lépéseit.”*

Az MI a régi anyag átnézésekor észrevette, amit akkor nem vettünk észre: **a beadott bolygós alkalmazás nem a NASA adataiból dolgozott.** A NASA API-ról való letöltés nem sikerült, az alkalmazás csendben a helyi fájlra váltott, a helyi fájl pedig generált adatsor volt (csillagnevek „Star-0001”-től „Star-5250”-ig, egyetlen ismert bolygó sincs benne, a „Kepler-0001 b” felfedezési éve 1995, holott a Kepler-misszió 2009-ben indult). Ezt az MI a fájlon futtatott ellenőrzéssel mutatta ki.

Ebből lett az új projekt hét alapelve, például:
- a felület **mindig kiírja a forrást**, és ha tartalékra vált, azt is, miért;
- a mentett adat **a valódi forrásból letöltött, változatlan pillanatkép**, letöltési dátummal és ellenőrzőösszeggel;
- nincs mindent elkapó hibakezelés (`except Exception`) és elnémított figyelmeztetés, mert ezek rejtették el a hibát.

---

## A munka menete

A munkát az MI által javasolt lépésekre bontottuk, és lépésenként haladtunk: minden lépés végén átnéztem az eredményt, és csak utána mondtam, hogy jöhet a következő. Emiatt a promptok többsége rövid (*„Jöhet a 3. lépés.”*) – a feladatleírás, a terv és a korábbi döntések a projekt dokumentumaiban voltak, ezekre épült minden lépés.

| Lépés | Tartalom | Kulcsprompt |
| --- | --- | --- |
| 0–1. | Tárhely, az adatforrás ellenőrzése, a pillanatkép letöltése | *„Mielőtt továbbmegyünk: 2026-os évre vonatkozó adat nincs?”* |
| 2. | Rugalmas beolvasás, hibakezelés | *„Jöhet a 2. lépés.”* |
| 3. | Hiányos adatok kezelése | *„Jöhet a 3. lépés.”* |
| 4. | Térkép, grafikonok, táblázat | *„Jöhet a 4. lépés.”* |
| 5. | Szűrők | *„Jöhet az 5. lépés.”* |
| 6. | Közzététel, kipróbálás, javítások | *„Amit nem értek, magyarázd el: …”* |
| 7. | Képernyőképek | – |

Az adatot én töltöttem le böngészőből (a fejlesztői környezet nem érte el az Eurostatot), az MI változatlanul feltöltötte a tárhelyre.

---

## Sikeres utak

**1. Az elsődleges forrás ellenőrzése.** A szakdolgozat témaleadásához korábban egy Eurostat-összefoglalóból vettem át számokat. Az MI a letöltött fájlból ellenőrizte őket: a méret szerinti adatok stimmeltek, de a „jogi következmények tisztázatlansága” mint ok (52,52%) a **2024-es** érték volt, nem a 2025-ös (53,61%).

**2. A Python nyelvi elemek.** A feladatkiírás szerint érdemes ellenőrizni a hibakezelés Python nyelvi elemeit; a moodle-oldal már nem volt elérhető. Kérdésemre (*„Pontosan mi a feladatkiírás?”*) az MI szó szerint visszaadta a vonatkozó pontot, és a Python hivatalos dokumentációjához mérve táblázatot készített: melyik elem hol van a kódban és mire szolgál, és melyiket hagytuk ki szándékosan, miért ([`python-nyelvi-elemek.md`](python-nyelvi-elemek.md)).

**3. A mértékegységek csapdája.** Az adatban hat különböző alap van. Ugyanaz a mutató egészen mást mond: a jogi bizonytalanságot 2025-ben az összes vállalat 5,86%-a, de a bevezetést mérlegelők 53,61%-a jelölte meg. Az alkalmazás ezért minden mutatót a hozzá illő alapra vetít, és mindig kiírja, mihez képest.

**4. Automatikus tesztek.** Az MI minden lépéshez teszteket írt (a végén 47-et), köztük hibás fájlokra (üres, sérült, HTML-hibaoldal, CSV a TSV helyett), hálózati hibára és a szűrőkre. A GitHub minden változtatásnál lefuttatta őket.

**5. Kérdezni, ha valamit nem értek.** A kipróbáláskor megkérdeztem, mire való három elem a felületen (*„Csak EU-tagállamok a térképen jelölés, ennek van értelme úgy, hogy eurostat adatokat nézünk? […] jelölt értékek az ábrákon mező, ha ki-be kapcsolom, minek kellene változni?”*). A válaszokból kiderült, hogy a felület hibája volt: a jelölt értékek kapcsolója például Magyarország és az EU-átlag nézetében semmit nem változtatott, mert ezekben nincs jelölt érték. Javítás: a kapcsoló alatt mindig látszik, mit érint az aktuális nézetben. A további kérdéseimből (*„az összes mutatót beraktad, amit az eurostat vizsgált? […] Az ágazatok abc sorrendben nem lennének könnyebben kereshetők?”*) új mutatók kerültek be, és kiderült, hogy két ágazat kétszer szerepelt a listában.

---

## Sikertelen utak és javításuk

| Mi nem sikerült | Hogyan derült ki | A megoldás | Tanulság |
| --- | --- | --- | --- |
| **A hiány első szabálya.** „Szerkezeti a hiány, ha egy mutatót egyetlen ország sem közölt.” | A hiánytérképen 2024-ben minden ország 25–40%-os hiányt mutatott – gyanús. Néhány ország saját döntésből gyűjtött nem uniós kérdéseket is. | Szerkezeti a hiány, ha az EU-átlag nincs közölve. Így a valódi hiány 6,1%, illetve 18,3%; Magyarország adatai gyakorlatilag teljesek. | A hiányt nem elég megszámolni, meg kell érteni, honnan jön. |
| **Üres térkép.** A térkép nem jelent meg. | Képernyőképen. A Plotly a határokat futás közben egy külső szerverről tölti le. | Első javítás (saját határfájl) nem segített. Végül a határfájlok a tárhelyre kerültek, és az alkalmazás maga szolgálja ki őket. | Ne legyen rejtett külső függőség – ugyanaz a hiba, mint a bolygós projektnél. |
| **Levágott és elrontott feliratok** („−9,6 százalék…”, „sz,pont”) | Képernyőképen. | Rövidebb feliratok; a mértékegység a címkébe került. | A bolygós projekt egyik hibája („0.0% hián…”) visszatért – a felületet meg kell nézni, nem elég a kód. |
| **Lassú ágazati nézet:** egy kattintás 20 másodperc. | Közzététel előtti mérés. Fejlesztés közben a tízszer kisebb táblával dolgoztunk. | Profilozás; a teljes tábla átalakítása és a hiányszámítás nem fut minden kattintásnál. Kb. 2 másodperc, azonos eredménnyel. | A sebességet a legnagyobb adatkészleten kell mérni. |
| **Az élő Eurostat-letöltés nem működött** a közzétett változatban; az üzenet csak „ConnectionError” volt. | Az első közzétett változaton. A tartalékra váltás működött és látszott. | A hibaüzenet a pontos okot is kiírja; a letöltő bemutatkozik a szervernek, és egyszer újrapróbálkozik. Utána működött. | A hibaüzenetnek az okot is meg kell mondania. Hogy a két javítás közül melyik oldotta meg, nem választható szét. |
| **Hiba a frissítés után** (`AttributeError`) | Az élő változaton. A tesztek sikeresek voltak, a kód helyes. | A felhő a régi modult tartotta a memóriában: újraindítás. | Frissítés után az élő változatot is meg kell nézni. |
| **Az év csúszkán** | Az én kipróbálásom: négy különálló év, nem tartomány. | Gombsor. Az oldalsávban két sorba tört, ezért a főoldalra került. | – |

---

## Tanulságok a promptolásról

- **A rövid prompt akkor működik, ha a kontextus megvan.** A terv, a döntések és a korábbi munka a projekt dokumentumaiban volt; így elég volt annyi, hogy *„Jöhet a 4. lépés.”*
- **Lépésenként, jóváhagyással.** Minden lépés után átnéztem az eredményt; a javaslatok közül én döntöttem (pl. *„A kódok nem kellenek, a többi mehet egyben.”*). Az észrevételeket egy körben javíttattam.
- **A kérdés is prompt.** Amikor csak magyarázatot kértem, abból derültek ki a felület hibái.
- **Az elsődleges forrás számít.** Az összefoglalóból átvett szám évét is a letöltött adatból kellett ellenőrizni; a régi projekt adatairól is így derült ki, hogy generáltak.
- **Az MI saját ellenőrzései sokat megfogtak** (tesztek, képernyőképek, mérés), de nem mindent: az élő változat két hibája csak a közzététel után, az én kipróbálásomban látszott.

---

## Képernyőképek a működő programról

A közzétett változatról, 2026. november 2. Leírás: [`kepernyokepek.md`](kepernyokepek.md).

1. [Nyitóoldal élő forrással](kepernyokepek/01-nyitooldal-elo-forras.png)
2. [Térkép, jelölt értékkel (Franciaország, idősortörés)](kepernyokepek/02-terkep-jelolt-ertek.png)
3. [Összevetés több országgal](kepernyokepek/03-osszevetes-tobb-orszag.png)
4. [Mutató: a jogi következmények tisztázatlansága](kepernyokepek/04-mutato-jogi-bizonytalansag.png)
5. [Ágazat: jogi, számviteli, tanácsadási tevékenység](kepernyokepek/05-agazat-jogi-tanacsadasi.png)
6. [Témakör: MI-technológiák](kepernyokepek/06-temakor-technologiak.png)
7. [Adatminőség fül](kepernyokepek/07-adatminoseg-ful.png)
8. [Hibás fájl feltöltése](kepernyokepek/08-hibas-fajl-feltoltese.png)
9. [Élő letöltés nélkül: a pillanatkép](kepernyokepek/09-pillanatkep-elo-letoltes-nelkul.png)
10. [Táblázat CSV-letöltéssel](kepernyokepek/10-tablazat-csv.png)

---

## Fájlok

| Fájl | Tartalom |
| --- | --- |
| `app.py` | Az alkalmazás (Streamlit-felület) |
| `adatbetoltes.py` | Rugalmas beolvasás, hibakezelés |
| `adatminoseg.py` | Hiányos és jelölt adatok |
| `abrak.py` | Ábrák (térkép, idősor, sávdiagramok) |
| `cimkek.py` | Magyar feliratok, mutatók, ágazatok |
| `adat/` | Az Eurostat-pillanatkép (két TSV-fájl) és eredete |
| `static/` | A térkép országhatárai |
| `tesztek/` | 47 automatikus teszt |
| `dokumentacio/` | Python nyelvi elemek, közzététel, képernyőképek, ez a napló |
| `README.md` | Az adat leírása, futtatás |

Futtatás: `pip install -r requirements.txt`, majd `python -m streamlit run app.py`.
