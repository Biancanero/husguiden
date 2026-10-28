# Driftsättning – en guide eller tusen

En guide består av en container och en volym (SQLite) och har ett eget lösenord. Alla guider använder samma image. De delar ingenting: varje guide är ett eget Compose-projekt med egen container, eget nät och egen volym.

## Bygg imagen

```bash
git clone git@github.com:Biancanero/husguiden.git && cd husguiden
docker build -t husguiden .
```

Bygget kör `tools/build.py` och kräver inget nätverk. three.js finns i repot.

## En guide

```bash
cp deploy/instance.env.example instances/palma.env   # SITE, SEED, PORT, BIND, OWNER_PASSWORD …
docker compose -p palma --env-file instances/palma.env up -d
curl -s http://127.0.0.1:8081/health
```

| Variabel | |
|---|---|
| `SITE` | vilken byggd guide som serveras: `family` (båda exempelhusen med resan), `husbok-palma`, `husbok-gotland`, `husbok-<id>` eller `.` (allt, med portalen) |
| `SEED` | fyller en **tom** databas vid första starten: `houses/<mapp>[:prefix]`, med mellanslag mellan flera |
| `BIND`, `PORT` | adress och port på värden. `127.0.0.1` bakom en omvänd proxy med TLS, eller en intern IP som `10.108.0.5` |
| `OWNER_PASSWORD` | krävs. Ägaren ser och ändrar allt |
| `EDITOR_PASSWORD`, `GUEST_PASSWORD` | valfria |
| `PUBLIC` | `1` = husboken kan läsas utan inloggning. `0` = allt kräver inloggning, även själva sidan |
| `ANTHROPIC_API_KEY` | slår på "Fråga huset" (servern anropar Claude; nyckeln stannar på servern). Modell: `HUSGUIDEN_MODEL`, standard `claude-sonnet-5-5` |
| `EXAMPLE_PRIVATE` | `1` = påhittade privata rader för demo |

## Tusen guider

```bash
sh deploy/new-instance.sh villa-ek husbok-villaek houses/villaek 8102
```

Skriptet skriver `instances/villa-ek.env` med ett slumpat ägarlösenord, som visas en gång, och startar projektet. Varje guide får en egen port. Låt en omvänd proxy koppla domän till port, till exempel med Caddy:

```
villa-ek.husguiden.se {
    reverse_proxy 127.0.0.1:8102
}
```

Så här lägger du till ett hus i en befintlig installation:

1. `git pull`
2. Lägg till `houses/<id>/` och kör `python3 tools/check_public.py`.
3. Kör `docker build -t husguiden .`
4. Kör `new-instance.sh`.

Befintliga guider påverkas inte förrän de startas om med den nya imagen. Deras data ligger kvar i volymerna.

Uppdatera alla guider till en ny version: bygg imagen och kör sedan, för varje fil i `instances/*.env`, `docker compose -p <namn> --env-file <fil> up -d`.

## Utan Docker

```bash
python3 tools/build.py
OWNER_PASSWORD=… python3 server/server.py --site dist/husbok-palma --db data/palma.sqlite --seed houses/joanmiro87 --port 8081
```

Servern har inga beroenden utöver Pythons standardbibliotek. Kör den med systemd eller supervisord om den ska startas automatiskt.

## Som claude.ai-artefakt (familjens nuvarande sätt)

```bash
python3 tools/build.py --target claude
```

Det ger sidor utan runtime, där three.js hämtas från CDN. `dist/family/index.html` publiceras som artefakt med `img/*`, `trip/*` och eventuellt `car/` som filer. Databasen är då artefaktens egen, och reglerna står i `db/schema.json`.

## Säkerhet

- Cookien är HMAC-signerad och HttpOnly. Hemligheten skapas per databas (`*.sqlite.secret`), eller sätts med `SECRET`.
- Statiska filer serveras bara inifrån `SITE`. Punktfiler och sökvägar som `../` ger 404.
- Containern körs som en vanlig användare, med skrivskyddat filsystem (utom `/data`), utan capabilities och med `no-new-privileges`.
- Lägg TLS framför (Caddy eller nginx). Lösenord skickas inte okrypterat om sidan nås via https.
- Ta backup av volymen. Se [DATAMODELL.md](DATAMODELL.md#säkerhetskopia).
