# Vad ska laddas upp? Checklista för husägaren

Allt nedan används för att bygga husguiden. **Fet** = krävs. Resten gör guiden bättre, men den fungerar utan.

Skicka filerna i en mapp per kategori. Vi lägger dem i `houses/<id>/underlag/`, som aldrig checkas in, och bara det som är tänkt att visas går vidare till `img/` eller `content.json`.

## 1. Adress och fastighet

- [ ] **Gatuadress** med postnummer och ort.
- [ ] **Fastighetsbeteckning**, till exempel *Visby Ekan 5* (i Spanien *referencia catastral*). Den står i köpekontraktet, på lagfartsbeviset och på fastighetsskattebeskedet.
- [ ] Tomtgränsen, något av följande:
  - Lantmäteriets karta: en skärmbild från *Min fastighet*, eller filen från Geotorget.
  - Situationsplanen ur bygglovshandlingarna.
  - Ett eget utkast i [geojson.io](https://geojson.io), sparat som `tomt.geojson`.
- [ ] Byggår och tillbyggnadsår.

## 2. Ritningar (viktigast för 3D-modellen)

- [ ] **Planritning för varje våning**, även källare och vind, som PDF eller fotografi rakt uppifrån med hela papperet synligt.
- [ ] Fasadritningar (fönster, dörrar och takform) och en sektion (takhöjd och bjälklag).
- [ ] Situationsplan (byggnadernas läge på tomten).
- [ ] Ritningar för tillbyggnader, garage, gäststuga och attefallshus.

Var hittar man dem? I Sverige hos kommunens bygglovsarkiv (beställs ofta via e-post, i regel gratis eller billigt), hos förra ägaren eller i mäklarens objektsbeskrivning. I Spanien hos *Ajuntament*, arkitekten eller *Catastro* (*croquis*).

## 3. Foton

- [ ] **Huset utifrån** från gatan, trädgården och alla fyra sidorna, i dagsljus.
- [ ] **Varje rum** sett från dörren och från motsatt hörn, med 1–2 bilder per rum.
- [ ] Detaljer: golv, kakel, bänkskivor, fönster, trappa, eldstad.
- [ ] Trädgård, uteplatser och utsikt.

Regler för foton som ska visas:

- Inga personer, inte heller i speglar, fönster eller TV-skärmar.
- Inga koder, nycklar, larmpaneler med kod, post eller papper med namn.
- Liggande format och minst 2000 px på bredden. Fotografera med telefonens vanliga lins, inte vidvinkel.

## 4. Typskyltar och manualer (för "Så fungerar det")

Ta ett foto av typskylten och ladda upp manualen (PDF eller länk) för:

- [ ] värmesystemet (värmepump, panna, golvvärme) och varmvattenberedaren
- [ ] ventilationen (FTX- eller frånluftsaggregat) och luftvärmepump eller AC
- [ ] vitvarorna: spis, ugn, mikro, kyl, frys, disk-, tvätt- och torkmaskin
- [ ] elcentralen (foto på gruppförteckningen), huvudkranen för vatten och golvbrunnar
- [ ] larm, brandvarnare, eventuell solcellsanläggning och laddbox
- [ ] pool, bastu, kamin, markiser och persienner

Skriv också var sakerna finns, hur man stänger av dem och vem man ringer.

## 5. Färger och material

- [ ] Kulörbeskrivning (NCS eller RAL) för fasad, snickerier och invändigt, om den finns.
- [ ] Golv, kakel och bänkskivor (fabrikat och modell), för reparationer.

## 6. Kontakter

- [ ] Hantverkare som har arbetat i huset (rör, el, bygg, trädgård).
- [ ] Serviceavtal (pool, hiss, larm) och nödnummer.
- [ ] Bocka för vilka kontakter **gäster** får se. Resten blir privata.

## 7. Historik

- [ ] Köp, renoveringar, installationer och service, med datum. Kostnader kan anges, men de syns bara för ägaren.

## Det här laddas INTE upp till guiden

Det här skriver ägaren själv in efteråt, i ägarläget i webbläsaren. Det sparas i guidens egen databas och aldrig i git.

- Wifi-lösenord, larmkoder, portkoder och var nyckeln ligger. Skriv dem i en privat artikel eller skicka dem till gästerna.
- Kostnader, räkningar, avtals-, kund- och mätarnummer, bankkonton och försäkringsnummer.
- Id-handlingar, personnummer och NIE/DNI.
- Köpekontrakt och andra dokument med personuppgifter (som underlag går de bra, men de visas inte).

## Vad vi hämtar själva (öppna data)

Läge, byggnadens fotavtryck och höjd, grannhus, träd, flygfoto, satellitbilder, solens bana och klimatzon. I Sverige kan även tomtgränsen hämtas från Lantmäteriet. Källorna står i [OPPNA-DATA.md](OPPNA-DATA.md) och i husets artikel *Källor*.
