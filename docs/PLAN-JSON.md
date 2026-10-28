# plan.json och house.json – referens

Ett fullständigt exempel finns i `houses/_mall/plan.json`: en villa i ett och ett halvt plan med fristående garage. Alla mått anges i meter.

## Koordinater

- Origo är punkten `lat`/`lng` i `house.json`, alltså husets läge på kartan.
- `x` pekar åt **öster**, `z` åt **söder** och `y` uppåt.
- En byggnad är en rektangel `w` (längs x) × `d` (längs z). Den placeras med sitt nordvästra hörn i (`x`, `z`) och vrids `rot` grader medurs sett ovanifrån.
- Allt inuti byggnaden (rum, väggar, öppningar) mäts från byggnadens hörn i dess egen ram, före vridningen.

## plan.json

```jsonc
{
  "storey_height": 2.5,            // normal takhöjd (väggarnas höjd); en våning kan ha egen "height"
  "front": "N",                    // gatusidan: kameran "Gatan" tittar därifrån
  "colors": { "facade": "#8e3b2c", "frames": "#f3f0e8", "door": "#2f3a35", "roof": "#3b3d3f", "inner": "#efebe3" },
  "show_neighbours": true,
  "slots": [                       // 3D-panelens knappar, 1–4 st, i den ordning de ska stå
    { "name": "Ground floor", "sub": "84 m²", "type": "storey", "level": 0 },   // en våning i huvudbyggnaden/-erna
    { "name": "Garage", "sub": "24 m²", "type": "building", "building": "garage" }, // en hel byggnad
    { "name": "The plot", "sub": "1 050 m²", "type": "plot" }                     // tomten
  ],
  "buildings": [ … ],
  "plot": { "polygon": [[x, z], …] },
  "neighbours": [{ "polygon": [[x, z], …], "h": 7 }],
  "trees": [[x, z, kronradie, höjd], …],
  "pools": [{ "x1": 0, "x2": 8, "z1": 12, "z2": 16, "depth": 1.4 }],
  "surfaces": [{ "kind": "gravel | stone | deck", "polygon": [[x, z], …] }],
  "ground": { "image": "img/ortho.jpg", "size": 120 }   // flygfoto, norr upp, size = meter från kant till kant
}
```

### En byggnad

```jsonc
{
  "id": "main",                    // unikt, a–z
  "x": 0, "z": 0, "rot": 0, "w": 11, "d": 8,
  "wall": 0.3,                     // ytterväggens tjocklek
  "floor": 0.45,                   // golvet över mark (sockel)
  "cladding": "boards",            // stående panel; utan = puts
  "roof": { "type": "gable", "pitch": 38, "ridge": "x", "overhang": 0.45, "material": "metal" },
  "terraces": [{ "side": "S", "a": 5.5, "w": 5.2, "depth": 3.2, "kind": "deck" }],
  "storeys": [ { … }, { … } ]      // nedifrån och upp
}
```

Taktyper:

| `type` | Tak | Övriga fält |
|---|---|---|
| `gable` | sadeltak | `pitch`, `ridge` (`"x"` eller `"z"`, nockens riktning) |
| `hip` | valmat tak | `pitch` |
| `mono` | pulpettak | `pitch`, `high`: `"n"`/`"w"` (standard) eller `"s"`/`"e"` – sidan som är hög |
| `flat` | platt tak | `parapet`: bröstningens höjd (standard 0,5) |

`material` kan vara `tile` (tegel), `metal` (plåt) eller `felt` (papp).

### En våning

```jsonc
{
  "height": 2.4,
  "rooms": [{ "name": "Kitchen", "x1": 3.1, "x2": 6.6, "z1": 0.3, "z2": 3.9, "floor": "oak", "kind": "kitchen", "area": 12.6, "furnish": true }],
  "walls": [{ "x1": 3.05, "z1": 0.3, "x2": 3.05, "z2": 7.7, "t": 0.1, "doors": [{ "a": 1.6, "w": 0.9 }, { "a": 5.4, "w": 1.6, "open": true }] }],
  "openings": [
    { "side": "N", "a": 1.0, "w": 1.0, "kind": "door", "h": 2.1 },
    { "side": "S", "a": 6.6, "w": 1.8, "kind": "door", "h": 2.2, "glass": true },
    { "side": "E", "a": 1.6, "w": 1.2, "sill": 0.9, "h": 1.2 }
  ],
  "stairs": [{ "x1": 1.9, "x2": 2.9, "z1": 0.4, "z2": 3.1, "dir": "n" }]
}
```

- **Rumsnamn** är nycklar och skrivs helst på engelska (Kitchen, Bedroom, Bathroom …). De översätts via `house.json` → `i18n`, och möbleringen väljs efter namnet. `kind` styr möbleringen direkt: `bed`, `bath`, `kitchen`, `living`, `dining`, `laundry` eller `study`.
- **floor** kan vara `oak`, `tile` eller `concrete`. Badrum och tvättstuga får klinker automatiskt.
- **Öppningar** i ytterväggen: `side` är `N`, `S`, `E` eller `W`. `a` mäts från västra hörnet på N- och S-sidorna och från norra hörnet på E- och W-sidorna. Ett fönster har `sill` (bröstning) och `h`. En dörr (`kind: "door"`) börjar vid golvet och går att gå igenom; `glass: true` ger glasdörr och `slide: true` skjutdörr.
- **Innerväggar** går längs mittlinjen från (`x1`, `z1`) till (`x2`, `z2`) och måste vara raka i x- eller z-led. Dörrarna mäts från väggens början.

## house.json

| Fält | |
|---|---|
| `id`, `slug` | id: a–z 0–9 (databasprefix på familjesidan). slug: mappen i `dist/` |
| `kind` | `plan` (nya hus), `scene` (egen scen, som Hulehällar), `shell` (referenshuset Joan Miró 87) |
| `name`, `place`, `address`, `town`, `type_line`, `about` | texter i sidhuvud, översikt och "Fråga huset" (`about` = en mening om huset på engelska) |
| `lat`, `lng`, `tz` | läge; `tz` = tidszon vintertid (1 i Sverige och Spanien), för solens bana |
| `lang`, `currency` | startspråk (`en`, `sv`, `es`, `de`) och valuta (`SEK`, `EUR` …) |
| `whole`, `whole_sub` | knappen "Hela" |
| `buyer` | `true` = köparvy och "Boka visning" (för hus till salu) |
| `agency` | namn i sidhuvudet (mäklare eller familj), tomt = inget |
| `plans` | ritningar: `[{"name", "src": "img/plan-0.jpg", "note"}]`. Tomt = ritas automatiskt från plan.json |
| `i18n` | översättningar för rum och knappar: `"Kitchen": ["Kök", "Cocina", "Küche"]` |
| `sat`, `c`, `north`, `url` | resan: satellitbildernas halva bredd i meter (en per bild i `sat/`), husets mitt i scenen, norr i scenen (`[0, -1]` för plan-hus), och guidens egen adress om den körs fristående |
| `about_cats` | valfritt: kategorierna på översiktssidan |
