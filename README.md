# Husguiden

En husbok i 3D för ett hus: modell av varje våning, rum, ritningar, artiklar ("hur fungerar det", "bo här"), kontakter, tidslinje, en ägardel med kostnader och uppgifter, och "Fråga huset". Allt finns i en enda HTML-sida per hus, och en liten server ger varje hus en egen databas.

Repot innehåller **två exempelhus** och en **mall för fler**:

| Hus | Typ | Mapp |
|---|---|---|
| Joan Miró 87, Palma | radhus i fyra plan, modellen skriven för hand (referenshuset) | `houses/joanmiro87/` |
| Hulehällar 418D, Hamra, Gotland | tomt med fyra byggnader, scenen skriven för hand | `houses/hulehallar/` |
| *ditt hus* | byggs från **data**: plan.json + öppna data för adressen | `houses/_mall/` → `houses/<id>/` |

Familjesidan (`dist/family/`) lägger husen i samma sida. Där kan man **resa** mellan dem: över en jordglob och sedan ned genom satellitbilder rakt in i 3D-modellen. Ett tredje hus läggs till i `family.json`.

## Snabbstart (Linux eller Mac, bara Python 3.9+)

```bash
python3 tools/build.py
OWNER_PASSWORD=hemligt python3 server/server.py --site dist --db data/test.sqlite \
  --seed houses/joanmiro87 --seed houses/hulehallar:hamra-
```

Öppna sedan:

- http://localhost:8080/family/ – båda husen, med resan
- http://localhost:8080/husbok-palma/ – ett hus
- http://localhost:8080/ – exempelportalen

Logga in som ägare med knappen nere till vänster.

Med Docker:

```bash
docker build -t husguiden .
cp deploy/instance.env.example instances/demo.env      # fyll i
docker compose -p demo --env-file instances/demo.env up -d
```

## Ett nytt hus på tre steg

```bash
python3 tools/new_house.py villaek --address "Storgatan 5, Visby"    # öppna data: läge, byggnad, grannar, träd, flygfoto
#  … mät upp rummen från planritningarna i houses/villaek/plan.json, skriv artiklar i content.json …
python3 tools/build.py villaek
```

Läs **[docs/NYTT-HUS.md](docs/NYTT-HUS.md)** och **[docs/UPPLADDNING.md](docs/UPPLADDNING.md)** (vad ägaren ska ladda upp). Vill du provköra mallen utan nät: `python3 tools/new_house.py exempel --demo`.

## Vad som finns var

```
engine/shell.html        husbokens skal: sidor, 3D-panel, sök, Fråga huset, ägar-/gästläge, resan (+ Joan Miró 87:s modell)
engine/plan-scene.js     3D-scenen för nya hus, byggd från plan.json
engine/vendor/           three.js 0.160 (lokalt: guiden kräver inget CDN)
engine/trip/             världskarta + d3 för resan
houses/<hus>/            house.json (fakta), plan.json (byggnader/rum), content.json (artiklar), img/, sat/
tools/build.py           bygger dist/<slug>/ per hus, dist/family/ och portalen
tools/new_house.py       nytt hus från mallen + öppna data
tools/plan_svg.py        ritar planer från plan.json (för kontroll mot riktiga ritningar)
tools/check_public.py    stoppar privata uppgifter innan de hamnar i git – kör före varje push
tools/vendor.py          hämtar three.js till engine/vendor (redan gjort)
server/server.py         en guide + dess databas (SQLite), inloggning, live-uppdatering, Fråga huset
runtime/                 ersätter claude.ai:s window.claude (db, user, sample) utanför claude.ai
db/schema.json           databasschemat och åtkomstreglerna
db/examples/             påhittade privata rader för demo
portal/                  exempelportalen WESTMAN (påhittade siffror, ingen riktig ekonomi)
deploy/, compose.yaml    en container + en volym per guide – samma image för tusen guider
customer-portal/         separat Docker-mall för en kundportal (oförändrad)
docs/                    guiderna
```

## Viktigt

- **Repot kan vara publikt.** Lägg aldrig in kostnader, konton, avtals- eller kundnummer, koder, wifi-lösenord eller var nyckeln ligger. Sådant matas in i guidens databas efter driftsättningen, i ägarläget. Kör `python3 tools/check_public.py` före varje push. Lägg dina egna känsliga ord i `.private-words` (den checkas aldrig in).
- **Bilder:** inga personer och inga speglingar med personer i, varken i gäst- eller köparvyn.
- **Bilmodellen** i familjens egna husbok är licensierad CC BY-NC och finns därför **inte** här. Använd aldrig den i något som säljs.
- **Satellitbilderna** kommer från Esri World Imagery. Läs villkoren i [docs/OPPNA-DATA.md](docs/OPPNA-DATA.md) innan du använder dem kommersiellt.

Mer: [docs/DEPLOY.md](docs/DEPLOY.md) · [docs/PLAN-JSON.md](docs/PLAN-JSON.md) · [docs/DATAMODELL.md](docs/DATAMODELL.md) · [docs/OPPNA-DATA.md](docs/OPPNA-DATA.md) · [docs/3D-KONVENTIONER.md](docs/3D-KONVENTIONER.md)
