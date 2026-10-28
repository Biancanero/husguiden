# Lägga till ett nytt hus

Från adress till färdig husguide i sju steg. Räkna med en halv till en hel dag för ett vanligt hus; det mesta av tiden går till att mäta upp rummen och skriva artiklarna.

Allt för huset ligger i `houses/<id>/`:

| Fil | Innehåll |
|---|---|
| `house.json` | namn, adress, läge, språk, valuta, knapparna i 3D-panelen, översättningar |
| `plan.json` | byggnader, våningar, rum, väggar, dörrar, fönster, tak, tomt, grannar, träd ([PLAN-JSON.md](PLAN-JSON.md)) |
| `content.json` | artiklarna, de publika kontakterna, platser och tidslinjen ([DATAMODELL.md](DATAMODELL.md)) |
| `img/` | ritningar, foton och flygfoto |
| `sat/` | satellitbilderna för resan (`1.jpg` … `6.jpg`, från långt ut till nära) |

## 1. Samla underlaget

Se [UPPLADDNING.md](UPPLADDNING.md): planritningar, foton, adress, fastighetsbeteckning, tomtgräns, typskyltar och manualer.

## 2. Skapa huset från adressen

```bash
python3 tools/new_house.py villaek --address "Storgatan 5, Visby" --name "Villa Ek"
```

- `id` (här `villaek`) består av a–z och 0–9. Det används i filnamn och som databasprefix på familjesidan.
- Skriptet hämtar läget (OpenStreetMap Nominatim), husets fotavtryck, antal våningar och taktyp, grannhusen och deras höjd samt träden (OpenStreetMap Overpass), plus ett flygfoto under modellen och sex satellitbilder för resan (Esri World Imagery).
- Själva **tomtgränsen** finns inte i OpenStreetMap. Ge den med `--plot tomt.geojson`, eller ställ in Lantmäteriets tjänst (se [OPPNA-DATA.md](OPPNA-DATA.md#tomtgräns)). Annars ritas en 30 × 30 m ruta som är markerad som ungefärlig.
- Har adressen inget hus i OpenStreetMap? Ge koordinaterna direkt med `--lat 57.63 --lng 18.29` och rita huset själv i steg 3.
- Mallen utan nät: `python3 tools/new_house.py exempel --demo` skapar det påhittade exempelhuset, en villa i ett och ett halvt plan med garage.

Bygg direkt och titta:

```bash
python3 tools/build.py villaek
python3 server/server.py --site dist/husbok-villaek --db data/villaek.sqlite --seed houses/villaek
```

Öppna http://localhost:8080/. Huset står som en låda med rätt mått, vridning och takform på flygfotot, med grannarna omkring. Fotavtrycket kommer från kartan, så kontrollera måtten mot ritningen.

## 3. Mät upp rummen från planritningarna

Öppna `plan.json` och planritningen sida vid sida.

1. **Skalan:** mät en känd längd på ritningen i pixlar, till exempel husets bredd, och räkna ut meter per pixel. På Joan Miró 87:s ritningar (1130 px breda) är det cirka 0,0186 m/px.
2. **Byggnaden** är en rektangel `w` × `d` meter. Lokala koordinater: `x` åt öster längs `w` och `z` åt söder längs `d`, räknat från husets nordvästra hörn (före vridningen `rot`).
3. **Rummen:** ange `x1, x2, z1, z2` i meter från det hörnet. Ytan räknas ut automatiskt, men skriv `area` om ritningen anger en annan.
4. **Innerväggar:** `{x1, z1, x2, z2}` längs väggens mittlinje. Dörrar anges som `{a, w}`, alltså avstånd från väggens början och bredd. Använd `open: true` för en öppning utan dörr.
5. **Ytterväggarnas öppningar:** `side` är N, S, Ö eller V (skrivs `N`, `S`, `E`, `W`), `a` är avståndet från västra eller norra hörnet, `w` är bredden, `sill` är bröstningshöjden och `h` är höjden. Med `kind: "door"` blir öppningen en dörr man kan gå igenom.
6. **Trappor:** `{x1, x2, z1, z2, dir}`, där `dir` är riktningen trappan stiger åt.
7. **Knapparna** i 3D-panelen (`slots`, högst fyra): en per våning (`type: storey`), en per extra byggnad (`type: building`) och tomten (`type: plot`).

Kontrollera mot ritningen: `python3 tools/build.py villaek` ritar en plan per våning, `img/plan-auto-villaek-*.svg`, i samma skala. Den visas under Ritningar tills du lägger in de riktiga skanningarna i `house.json` → `plans`.

Rum vars namn innehåller sov, kök, bad, vardag, mat, tvätt eller kontor (även på engelska, spanska och tyska) möbleras automatiskt. Använd `furnish: false` för att stänga av det.

## 4. Färger, tak och detaljer

- `colors`: fasad, fönsterbågar, ytterdörr, tak och innerväggar. Färgen kan provtas från ett foto.
- `cladding: "boards"` ger stående panel (falurött hus och liknande). Utan den blir fasaden puts.
- `roof`: `gable` (sadeltak), `hip` (valmat), `mono` (pulpet) eller `flat` (platt med bröstning), med `pitch` i grader, `ridge` (`x` eller `z`), `overhang` och `material` (`tile`, `metal` eller `felt`).
- `terraces`, `pools`, `surfaces` (grus, sten, trall) och `trees`.

## 5. Skriv innehållet

`content.json` innehåller artiklarna. Kategorierna och fälten beskrivs i [DATAMODELL.md](DATAMODELL.md). Börja med de här:

- **Översikt:** huset i korthet, med fakta.
- **Rum:** en artikel per rum. `room: "0:Kitchen"` kopplar artikeln till rummet i modellen; siffran är knappens index och namnet är rummets namn i `plan.json`.
- **Så fungerar det:** värme, vatten, el, ventilation, larm, vitvaror. Använd `how` med fälten vad, var, hur, skötsel och vem man ringer.
- **Bo här:** sopor, nycklar (aldrig själva koden), avresa.
- **Ritningar och dokument** samt **Källor**.

Grundspråket är engelska, och översättningarna läggs i `i18n.sv/es/de`. Ett hus som bara finns på svenska kan ha svenska i grundfälten och `"lang": "sv"` i `house.json`. Listorna `facts` och `images` måste vara lika långa i alla språk.

Rumsnamn och knappnamn översätts via `house.json` → `i18n`, i formen `"Kitchen": ["Kök", "Cocina", "Küche"]`.

## 6. Kontrollera och bygg

```bash
python3 tools/check_public.py          # inga privata uppgifter
python3 tools/build.py villaek          # → dist/husbok-villaek/
```

Gå igenom varje knapp, Gå runt, Planritning, Ovanifrån och språkbytet. Logga in som ägare och kontrollera att ägarsidorna fungerar.

## 7. Familjesidan och resan (valfritt)

Lägg till huset i `family.json` → `homes`. Satellitbilderna i `sat/` och `house.json` → `sat` (bildernas halva bredd i meter) gör resan. `c` och `north` talar om var huset står i 3D-scenen och var norr är, så att dyket landar rakt ovanför huset. Skriptet `new_house.py` fyller i båda.

Driftsättning: [DEPLOY.md](DEPLOY.md).

## När plan.json inte räcker

`plan.json` beskriver hus som består av rätvinkliga byggnader. Det täcker de flesta villor, radhus och fritidshus. För ovanligare former finns två vägar, och båda finns som exempel i repot:

- **Egen scen** (`kind: "scene"`, som Hulehällar): en fristående 3D-sida (`scene.html`) och ett byggsteg (`build_book.py`/`build_steps.py`) som lyfter in scenen i skalet.
- **Skalets egen modell** (`kind: "shell"`, som Joan Miró 87): modellen skrivs direkt i `engine/shell.html`. Använd det bara för referenshuset.
