# Kundportal – ren Docker-mall

En fristående intern portal för en kunds hus och bilar. Varje kund får en egen Compose-projektmapp, container och Docker-volym; inga data delas mellan kunder.

## Funktioner

- Lösenordsskyddat administrationsgränssnitt.
- Lägg till och ta bort hus och bilar.
- SQLite-databas i den namngivna volymen `customer_portal_data`.
- Ingen extern databas, CDN eller tredjepartstjänst krävs vid drift. Varje portal får ett separat Docker-nät.
- Porten är parameterstyrd och binds endast till `10.108.0.5`.

## Ny kund

```sh
cp .env.example .env
# Sätt ett unikt ADMIN_PASSWORD och en ledig CUSTOMER_PORTAL_PORT.
docker compose -p kundnamn up -d --build
```

För nästa kund: kopiera den här katalogen till en ny katalog, välj nytt Compose-projektnamn och en ny port. Det ger egen container, eget nät och en egen namngiven datavolym per kund.
