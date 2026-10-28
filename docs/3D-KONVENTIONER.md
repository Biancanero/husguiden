# 3D – hur modellerna är byggda

Allt bygger på three.js 0.160 med samma skal (`engine/shell.html`). Skalet innehåller:

- kamera, OrbitControls, skuggor och miljöljus
- HQ-läge med ambient occlusion: EffectComposer, RenderPass, GTAOPass och OutputPass. Sidan startar i snabbläge och växlar upp efter cirka 2,5 s.
- etiketter (CSS2DRenderer) och snittplanet vid våningsval
- gåläget (kollisionslådor i världskoordinater) och solreglaget
- resan mellan husen

Själva huset kommer från en av tre källor.

## Nya hus: `engine/plan-scene.js` (kind `plan`)

Huset byggs helt från `plan.json`, enligt [PLAN-JSON.md](PLAN-JSON.md). Byggsteget (`tools/lib/plan_book.py`) gör tre saker:

1. Lägger scenen i ett eget scope.
2. Kopplar knapparna (`slots`) till skalets fyra "våningar" (`floors[0..3]`). En våningsknapp visar den våningen och de under, och döljer taket. En byggnadsknapp tar bara bort den byggnadens tak. Tomtknappen visar allt.
3. Räknar ut kameravyer, gåstartpunkter, skuggkamerans storlek och solens bana från husets mått och läge.

Hjälpfunktionerna i plan-scene.js kan användas i egna tillägg:

| Funktion | Gör |
|---|---|
| `box`, `tbox` | lådor; `tbox` med textur per meter |
| `cyl` | cylinder |
| `tris` | fria trianglar |
| `wall(g, axis, a1, a2, c1, c2, h, ops, mats)` | vägg med öppningar |
| `roof` | tak |
| `furnish` | möblering |
| `F(mesh)` | markerar möbler (knappen "Möbler") |

`userData.pass = true` gör en del genomgånglig i gåläget. Det gäller till exempel trappsteg, dörrblad och golv.

## Hulehällar 418D: egen scen (kind `scene`)

`houses/hulehallar/scene.html` är en fristående 3D-sida som går att öppna för sig. `build_steps.py` lyfter ut scenen (från `// ---------- helpers ----------` till `// ---------- sun: Gotland`) och patchar skalet:

- skalets fyra "våningar" blir husets byggnader (huvudhus, gäststuga med garage, attefallshus) och tomten
- den valda byggnaden tappar sitt tak och snittas vid 1,65 m
- egna rader under Visningsalternativ: cykelförråd 1–9, trall och pool 1–5, garageportar, glashuset

Varje `rep()` kontrollerar sitt ankare. Ändras skalet så att ett ankare försvinner stoppas bygget med ett tydligt fel i stället för att bli fel i tysthet.

## Joan Miró 87: skalets egen modell (kind `shell`)

Referenshuset är skrivet direkt i `engine/shell.html`, mellan `// ---------- textures ----------` och `// ---------- room labels ----------`. Konventioner som är lätta att göra fel på:

- **Koordinater:** modellens x går från 0 (norra brandväggen) till 6,45. `world`-gruppen är **speglad** (`scale.x = -6.83/6.45`, `position.x = 6.83`), så världens x = 6,83 − 1,059 × modellens x. z = 0 vid gatufasaden och ökar mot trädgården. +z pekar mot ONO (79°).
- **Våningar:** H = 2,8 m från golv till golv och C = 2,5 m i takhöjd. `y0 = nivå × H`. Takterrassen ligger på 3H.
- **Strålkastning mot väggar fungerar inte** på grund av speglingen. Gåläget använder lådor i världskoordinater.
- `wall(g, axis, a1, a2, c1, c2, y0, h, openings)`: axis `'x'` betyder att väggen löper längs x vid z c1–c2. Öppningar med `lo: 0` går att gå igenom.
- Kontrollera planritningarna i `houses/joanmiro87/img/plan-*.jpg` innan layouten ändras. Skalan är cirka 0,0186 m/px på de 1130 px breda planerna. Titta också på dörrarnas slagbågar innan en dörr ändras.
- Hiss (`liftG`, `callLift`), skjutpartier (`t: 'slide'`), trappor (`walkStairs`) och förrådsidén i hisschaktet finns bara här. Listorna deklareras **en gång** direkt efter importerna (`let liftDoors = [], slideDoors = [] …`), eftersom Gotland-bygget tar bort Joan Miró 87:s modell. Ladda båda husen efter varje ändring i skalet.

## Testa

```bash
python3 tools/build.py
python3 server/server.py --site dist --db data/test.sqlite --seed houses/joanmiro87 --seed houses/hulehallar:hamra-
```

Öppna `/family/`, `/husbok-palma/` och `/husbok-gotland/`, och dessutom ett plan-hus (`new_house.py exempel --demo`). Kolla konsolen. Gå igenom varje knapp, gåläget, planritningen och resan (logga in som ägare: växlaren syns bara för den som får redigera).
