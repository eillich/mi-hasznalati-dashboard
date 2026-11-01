# Az adat-pillanatkép eredete

A mappában lévő fájlok az Eurostat-ról letöltött, **változatlan** eredeti fájlok. Nincs rajtuk kézi vagy Excel-előfeldolgozás; minden tisztítás az alkalmazásban, beolvasáskor történik.

| Fájl | Adatkészlet | Letöltés |
| --- | --- | --- |
| `estat_isoc_eb_ai.tsv.gz` | Mesterséges intelligencia vállalatméret szerint | https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/isoc_eb_ai?format=TSV&compressed=true |
| `estat_isoc_eb_ain2.tsv.gz` | Mesterséges intelligencia ágazat (NACE Rev. 2) szerint | https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/isoc_eb_ain2?format=TSV&compressed=true |

- Letöltés ideje: 2026. november 1., böngészőből (Illich Éva).
- Az adatok közlése: Eurostat, 2025. december (felmérési évek: 2021, 2023, 2024, 2025).
- SHA-256 ellenőrzőösszegek:
  - `estat_isoc_eb_ai.tsv.gz`: `69d74017968d4bcfbe5bfadcda5945d358a5dcbabaf1e6664e18ccb21845a8d3`
  - `estat_isoc_eb_ain2.tsv.gz`: `717d8ce23d78b2e36e3365201035878b94bff4171c1b67820067fb7eba8b3557`

Forrás: Eurostat, Community survey on ICT usage and e-commerce in enterprises. Az Eurostat adatai szabadon újrafelhasználhatók a forrás megjelölésével.
