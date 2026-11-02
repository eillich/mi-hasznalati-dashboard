# Közzététel a Streamlit Community Cloudon, kipróbálás, képernyőképek

## Előtte: a privát tárhely korlátja

A Streamlit Community Cloudon egyszerre **csak egy olyan alkalmazás lehet, amely privát tárhelyről fut**. Ha egy már működik (például a szakdolgozati asszisztens a `mi-megfelelesi-asszisztens` tárhelyről), egy második privát tárhelyes alkalmazást csak akkor enged létrehozni, ha az elsőt nyilvánossá teszed vagy törlöd ([Streamlit: Share your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)).

Lehetőségek:

- **A) Ennek a tárhelynek a nyilvánossá tétele most** (javasolt). A tárhelyben nincs semmi bizalmas: kód, az Eurostat nyilvános adatai, dokumentáció. A beadás előtt amúgy is nyilvános lesz. Így az alkalmazás is nyilvános, és a link meghívás nélkül megnyílik.
  GitHub → `mi-hasznalati-dashboard` → *Settings* → lap alja, *Danger Zone* → *Change visibility* → *Change to public* → megerősítés.
- **B) A tárhely privát marad**, és a meglévő privát alkalmazást (az asszisztenst) nyilvánossá teszed vagy törlöd a Streamlit-felületen. Ekkor ez az alkalmazás privát lesz: csak a meghívottak látják (*Share* → e-mail-cím), amíg nyilvánossá nem teszed.

## 1. Bejelentkezés

1. Nyisd meg: https://share.streamlit.io
2. *Continue with GitHub*, a GitHub-fiókoddal (`eillich`).
3. Ha kéri, engedélyezd a Streamlitnek a tárhelyeid elérését. Privát tárhelynél (B) a privát tárhelyek elérését is engedélyezni kell.

## 2. Az alkalmazás létrehozása

1. Jobb felül *Create app* → *Deploy a public app from GitHub* (vagy *Yup, I have an app*).
2. Kitöltés:
   - **Repository:** `eillich/mi-hasznalati-dashboard`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** javaslat: `mi-hasznalat-dashboard` (így a cím `https://mi-hasznalat-dashboard.streamlit.app` lesz; ha foglalt, válassz mást)
3. *Advanced settings* → **Python version: 3.12** (ezen futnak a GitHub-ellenőrzések is). Titkos kulcs (*Secrets*) nem kell.
4. *Deploy*.

Az első indítás 2–5 percig tart (a csomagok telepítése). Ha hibát ír, másold be ide a naplóját (jobb alul *Manage app* → a napló alja).

## 3. Kipróbálás (ellenőrzőlista)

Az élő változaton ellenőrizendő, ami a fejlesztői környezetben nem volt kipróbálható:

- [ ] A fejlécben a forrás **„🌐 Eurostat API (élő letöltés)”**, és nincs sárga figyelmeztetés. (A fejlesztői környezetben az API nem volt elérhető.)
- [ ] A **térkép megjelenik** (országhatárok a saját `static/` mappából). Ha üres, szólj.
- [ ] Az **ágazati adatkészletre** váltás után a kattintások néhány másodpercen belül frissülnek.
- [ ] Az *Élő letöltés* kikapcsolása után a forrás „💾 helyi pillanatkép”, sárga figyelmeztetés nélkül.
- [ ] Hibás fájl feltöltése (pl. egy tetszőleges `.txt`): sárga figyelmeztetés az okkal, az alkalmazás tovább működik.
- [ ] A szűrők: más kiemelt ország, összevetés 2–3 országgal, másik mutató, év, vállalatméret és ágazat.
- [ ] A *Jelölt értékek az ábrákon* kapcsoló.
- [ ] *A megjelenített adatok táblázatban* → *Letöltés CSV-ben*, és a fájl megnyílik Excelben.
- [ ] Egy kijelentkezett (inkognitó) böngészőablakban is megnyílik a link (A esetben).

Minden észrevétel jöhet egyben, egy körben javítom.

## 4. Képernyőképek a beadandóhoz

A feladatkiírás a működő program bemutatását kéri képernyőképekkel. Javasolt sorrend, az élő változatról:

1. **Nyitóoldal** az élő forrással (fejléc, fő számok, térkép).
2. **Térkép**, egérrel egy ország fölött (a buborékban az érték).
3. **Szűrés:** kiemelt ország és összevetés több országgal (idősor, méret szerinti ábra).
4. **Mutatóváltás:** „Nem világosak a jogi következmények” (térkép és fő számok).
5. **Ágazati nézet:** a jogi, számviteli, tanácsadási ágazat kiválasztva.
6. **Témakör:** „Miért nem vezették be?”.
7. **Adatminőség fül:** a hiánymutatók és a hiánytérkép.
8. **Hibakezelés:** hibás fájl feltöltése után a figyelmeztetés.
9. **Tartalékra váltás:** az *Élő letöltés* kikapcsolva, a forrás „helyi pillanatkép”.
10. **A táblázat** a CSV-letöltés gombbal.

Teljes képernyős böngészőablakban, 100%-os nagyításon készüljenek, hogy az oldalsáv is látsszon.
