# Databasen

Varje driftsatt guide har en egen SQLite-fil (`/data/husguiden.sqlite` i containern). Den består av dokument i samlingar, på samma sätt som claude.ai:s artefaktdatabas som husboken först byggdes på. Därför fungerar samma sida både som claude.ai-artefakt och fristående.

Det fullständiga schemat, alla fält och åtkomstreglerna finns i **[`db/schema.json`](../db/schema.json)**. Här följer en sammanfattning.

## Samlingar

| Samling | Vem läser | Vem skriver | Innehåll |
|---|---|---|---|
| `wiki` | alla (`view`) | redaktör, ägare | publika artiklar plus dokumenten `contacts`, `places` och `timeline` (`{rows: […]}`) |
| `private` | ägaren | ägaren | privata artiklar, `contacts` (alla), `costs`, `payments`, `upcoming`, `timeline`, `equipment`, `checklist`, `utilities`, `account`, `rental` |
| `leads` | ägaren | var och en sitt eget dokument `leads/<id>` | visningsförfrågningar (bara när `buyer: true`) |

På familjesidan har varje hus utom det första sina samlingar under `<husets id>-`, till exempel `hamra-wiki` och `hamra-private`. Reglerna gäller namnet utan prefix.

## Roller

| Roll | Hur | Nivå |
|---|---|---|
| besökare | inte inloggad (bara när `PUBLIC=1`) | `view` |
| gäst | `GUEST_PASSWORD` | `interact` |
| redaktör | `EDITOR_PASSWORD` | `admin` |
| ägare | `OWNER_PASSWORD` | `owner` |

## Förifylld data

- **Publikt:** `houses/<hus>/content.json` → `wiki`. Servern läser in den första gången den startar mot en tom databas (`--seed houses/<hus>[:prefix]`). Samma innehåll bäddas också in i sidan, så att en sida som öppnas utan server fortfarande visar husboken.
- **Privat:** startar tomt och fylls av ägaren i webbläsaren. För demo: `--example-private db/examples/private.example.json` (påhittade rader), eller `EXAMPLE_PRIVATE=1` i Docker.

## Artikel (wiki/<id> och private/<id>)

```json
{
  "title": "Kitchen", "cat": "Rooms", "room": "0:Kitchen", "sort": 2,
  "body": "Text. Tomrad = nytt stycke, '## ' = rubrik, '- ' = lista.",
  "facts": [{ "k": "Oven", "v": "Küppersbusch BP6350.0S" }],
  "how": { "what": "", "where": "", "use": "", "maintenance": "", "call": "" },
  "images": [{ "src": "img/kitchen.jpg", "caption": "From the dining table" }],
  "colors": [{ "name": "Walls", "code": "RAL 9010", "hex": "#f1ece1", "where": "All rooms" }],
  "i18n": { "sv": { "title": "Kök", "body": "…", "facts": [["Ugn", "Küppersbusch BP6350.0S"]], "captions": ["Från matbordet"] } }
}
```

Regler:

- `i18n.<språk>.facts` och `.captions` ligger i samma ordning som de engelska och ska ha samma längd. `tools/build.py` stoppar bygget om de inte har det.
- Under `wiki` får aldrig koder, wifi-lösenord, nyckelns plats, belopp eller avtalsnummer stå. Sådant hör hemma i `private`.

## Säkerhetskopia

Hela guidens data ligger i en enda fil. Säkerhetskopiera volymen, eller kör `sqlite3 husguiden.sqlite ".backup kopia.sqlite"`. Allt som är publikt kan alltid återskapas från `content.json`.

## API (för den som vill bygga vidare)

`server/server.py` har följande endpoints:

- `GET /api/session`
- `POST /api/login` och `/api/logout`
- `GET /api/col?path=` och `/api/doc?path=`
- `PUT` (ersätt), `PATCH` (slå ihop) och `DELETE /api/doc?path=`
- `GET /api/watch?path=` (server-sent events: en ny ögonblicksbild vid varje ändring)
- `POST /api/sample` (Fråga huset)
- `GET /health`

`runtime/husguiden-runtime.js` gör om dem till `claude.use('db' | 'user' | 'sample')`.
