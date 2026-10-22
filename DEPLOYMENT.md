# Intern publicering

Detta paket är självbärande: alla Three.js-moduler finns i `vendor/` och inga Google Fonts eller andra CDN-resurser laddas. Kartlänkar och WhatsApp-länkar är fortfarande externa användarval.

## Docker på PorscheHunter

Kopiera paketet till mål-VM:n, packa upp det och starta den isolerade webbcontainern:

```sh
tar -xzf Westman-intern.tar.gz
cd Westman-intern
docker compose up -d --build
```

`compose.yaml` binder enbart `10.108.0.5:80` på värden; port 80 blir därmed inte tillgänglig via andra värdadresser. Containern kör filservern skrivskyddat med endast `NET_BIND_SERVICE`, vilket krävs för att Caddy ska kunna lyssna på port 80, och utan externa applikationsberoenden efter att imagen har byggts. Öppna inte någon port vidare utanför det interna nätet.

Verifiering efter publicering:

```sh
curl -I http://10.108.0.5/
curl -I http://10.108.0.5/husbok-palma/
curl -I http://10.108.0.5/vendor/three/build/three.module.js
docker compose ps
```

Detta är fortfarande en statisk demo. Ändringar i familjeportalen sparas inte, och redigerings-/inloggningsdelarna i husböckerna kräver en separat backend som ersätter den plattformsspecifika `claude`-integrationen.
