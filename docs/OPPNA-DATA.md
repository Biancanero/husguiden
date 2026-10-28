# Öppna data – Sverige först, Spanien som andra land

`tools/new_house.py` använder bara källor som är öppna och som inte kräver konto. Lantmäteriet är ett tillval för tomtgränsen. Alla källor som används för ett hus skrivs i `img/KÄLLOR.txt` och bör nämnas i artikeln *Källor*.

| Vad | Källa | Konto | Licens | I verktyget |
|---|---|---|---|---|
| Läge från adress | OpenStreetMap Nominatim | nej | ODbL | ja (ett anrop per hus, följ användarvillkoren) |
| Husets fotavtryck, våningar, takform, byggår | OpenStreetMap (Overpass) | nej | ODbL | ja |
| Grannhus och deras höjd, träd | OpenStreetMap (Overpass) | nej | ODbL | ja |
| Flygfoto under modellen, satellitbilder för resan | Esri World Imagery (export) | nej | Esris villkor, se nedan | ja |
| **Tomtgräns (Sverige)** | Lantmäteriet *Fastighetsindelning* | ja, gratis konto på Geotorget | CC BY 4.0 | ja, med `LM_FASTIGHET_URL` och `LM_TOKEN` |
| Byggnader och adresser (Sverige) | Lantmäteriet *Byggnad*, *Belägenhetsadress* | ja, Geotorget | CC BY 4.0 | inte än (OSM används) |
| Ortofoto (Sverige) | Lantmäteriet *Ortofoto* | ja, Geotorget | CC BY 4.0 | inte än (Esri används) |
| Markhöjd | Lantmäteriet *Markhöjdmodell* | ja, Geotorget | CC BY 4.0 | inte än |
| Solens bana | beräknas i sidan från `lat`, `lng` och `tz` | – | – | ja |
| Solinstrålning | EU JRC PVGIS (API) | nej | fri användning | inte än |

Sedan februari 2025 är Lantmäteriets "värdefulla datamängder" avgiftsfria under CC BY 4.0. De hämtas via API eller nedladdning från **Geotorget** efter att man har skapat ett konto. Data som innehåller fastighetsregisteruppgifter kan kräva en ansökan i Geotorgets beställningsflöde. Kontrollera aktuella villkor och adresser på lantmateriet.se.

## Tomtgräns

Tomtgränsen finns inte i OpenStreetMap. Det finns tre sätt, i den här ordningen:

1. **`--plot tomt.geojson`**, en polygon i WGS84 (lng, lat). Den kan tas fram så här:
   - Exportera fastigheten från Geotorget (Fastighetsindelning, nedladdning).
   - Rita den i [geojson.io](https://geojson.io) ovanpå en karta med fastighetsgränser, till exempel med kommunens eller Lantmäteriets kartbild bredvid. Spara som `tomt.geojson`.
   - Situationsplanen: mät hörnen och skriv in dem direkt som `plot.polygon` i `plan.json` (meter, x öster, z söder).
2. **Lantmäteriets API.** Ange de här variablerna, så hämtar `new_house.py` den fastighet som adresspunkten ligger i:

   ```bash
   export LM_FASTIGHET_URL="https://…/collections/<fastighetsytor>/items"
   export LM_TOKEN="…"
   ```

   - `LM_FASTIGHET_URL` är *items*-adressen för Fastighetsindelningens fastighetsytor (OGC API Features), som den står i Geotorget.
   - `LM_TOKEN` är en giltig access token från Geotorget (Bearer).
   - Verktyget frågar med `bbox` runt punkten och väljer den yta som innehåller den. Adressen kan ändras hos Lantmäteriet, så kontrollera den i Geotorgets produktbeskrivning.
3. **Inget av ovanstående.** Då markeras en ruta på 30 × 30 m som ungefärlig, `"approximate": true` i `plan.json`, och tomtens yta visas med "(ungefärlig)".

## Esri World Imagery

Satellitbilderna hämtas från Esris öppna `export`-tjänst. Den ger cirka 0,3–0,6 m per pixel beroende på plats. Ber man om skarpare än vad som finns svarar tjänsten med fel, och då stegar verktyget ned upplösningen tills det fungerar.

**Villkor:** bilderna får visas med källangivelsen "Imagery © Esri, Maxar, Earthstar Geographics", som visas under resan. För kommersiell användning i stor skala kräver Esri ett ArcGIS-konto. Kontrollera Esris villkor innan guider säljs, eller byt till Lantmäteriets ortofoto (CC BY 4.0). Bildernas filnamn och format är detsamma oavsett källa, så det enda som behöver ändras är `esri()` i `tools/new_house.py`.

## Spanien

Exempelhuset Joan Miró 87 i Palma bygger på följande, med uppgifterna inmatade för hand:

- **Catastro** (ovc.catastro.meh.es): referencia catastral, ytor, byggår och fasadfoto.
- **INSPIRE**: parcell- och byggnadspolygoner via WFS och nedladdning per kommun, öppet.
- **PNOA**: ortofoto från IGN, WMS, öppet.
- **IDEIB** (Balearerna): planering och översvämningszoner.

Catastro begränsar antalet anrop per timme. Hämta långsamt och spara svaren lokalt.

## Andra länder

Nominatim, Overpass och Esri fungerar i hela världen. Ange `--country` med en tvåbokstavskod, till exempel `no`, `dk`, `fi` eller `de`. Tomtgränsen kommer från landets lantmäteri eller anges med `--plot`.
