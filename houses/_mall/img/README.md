# img/ – bilderna i husboken

Lägg här:

- `plan-0.jpg`, `plan-1.jpg` … planritningar per våning (de visas under "Ritningar" och används när du mäter upp rummen till `plan.json`).
- `hero.jpg` – en bild på huset utifrån (används av artikeln "overview" om du lägger den i dess `images`).
- Rumsbilder, t.ex. `kok.jpg`, `vardagsrum.jpg` – peka på dem från artiklarna i `content.json` (`"images": [{"src": "img/kok.jpg", "caption": "…"}]`).
- `ortho.jpg` – flygfotot under 3D-modellen (skapas av `tools/new_house.py`).

Regler: inga bilder med personer, inga speglingar med personer i, inga koder eller nycklar i bild. Max ca 2000 px på längsta sidan, JPG.
Filnamnen måste vara unika över alla hus som ska ligga på samma familjesida.
