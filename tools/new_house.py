#!/usr/bin/env python3
"""Creates a new house from the template (houses/_mall) and fills it with open data for its address.

  python3 tools/new_house.py villa --address "Storgatan 5, Visby"            # Sweden is the default country
  python3 tools/new_house.py villa --address "…" --plot tomt.geojson          # the plot boundary from Lantmäteriet / your own drawing
  python3 tools/new_house.py villa --lat 57.63 --lng 18.29 --name "Villa Ek"   # no geocoding
  python3 tools/new_house.py exempel --demo                                    # the invented example house, no network

What it fetches (everything open, no account needed):
  • position            OpenStreetMap Nominatim (one request; the OSM usage policy allows this)
  • the house + neighbours, their heights, trees   OpenStreetMap Overpass (buildings within 90 m)
  • aerial photo under the model and the photos for the trip   Esri World Imagery export (see docs/OPPNA-DATA.md about terms)
  • plot boundary       --plot <GeoJSON>, or Lantmäteriet's Fastighetsindelning (open data, needs a free Geotorget
                        account: set LM_FASTIGHET_URL and LM_TOKEN), else a rectangle around the house marked 'approximate'
Then you add rooms, walls and openings from the floor plans (docs/NYTT-HUS.md, docs/PLAN-JSON.md) and build:
  python3 tools/build.py villa"""
import argparse, json, math, os, re, shutil, subprocess, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'husguiden/1.0 (open-source house guide builder; https://github.com/Biancanero/husguiden)'}
sys.path.insert(0, os.path.join(ROOT, 'tools'))


def http(url, data=None, headers=None, timeout=60, raw=False):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read()
    except urllib.error.URLError as e:
        # old macOS Pythons (LibreSSL) fail the TLS handshake with some servers: let curl fetch it instead
        if 'SSL' not in str(e.reason) or not shutil.which('curl'):
            raise
        cmd = ['curl', '-sS', '-f', '-m', str(timeout), url] + sum((['-H', f'{k}: {v}'] for k, v in {**UA, **(headers or {})}.items()), [])
        if data:
            cmd += ['--data-binary', '@-']
        b = subprocess.run(cmd, input=data, capture_output=True, check=True).stdout
    return b if raw else json.loads(b)


# ---------------------------------------------------------------- geometry: WGS84 ↔ local metres (x east, z south)
class Local:
    def __init__(self, lat, lng):
        self.lat, self.lng = lat, lng
        self.kx, self.kz = 111320 * math.cos(math.radians(lat)), 110540

    def xz(self, lng, lat):
        return [round((lng - self.lng) * self.kx, 2), round(-(lat - self.lat) * self.kz, 2)]


def inside(pt, poly):
    x, z = pt; c = False
    for i in range(len(poly)):
        x1, z1 = poly[i]; x2, z2 = poly[i - 1]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1) + x1:
            c = not c
    return c


def area(poly):
    return abs(sum(poly[i - 1][0] * p[1] - p[0] * poly[i - 1][1] for i, p in enumerate(poly))) / 2


def min_rect(poly):
    """The smallest rectangle around a footprint, as a plan.json building: x, z (corner), rot (degrees), w, d."""
    best = None
    for i in range(len(poly)):
        (x1, z1), (x2, z2) = poly[i - 1], poly[i]
        a = math.atan2(z2 - z1, x2 - x1)
        c, s = math.cos(a), math.sin(a)
        us = [x * c + z * s for x, z in poly]; vs = [-x * s + z * c for x, z in poly]
        A = (max(us) - min(us)) * (max(vs) - min(vs))
        if not best or A < best[0]:
            best = (A, a, min(us), min(vs), max(us) - min(us), max(vs) - min(vs))
    _, a, u0, v0, w, d = best
    # keep the long side along u and the angle small, so 'N' stays roughly north
    deg = math.degrees(a)
    while deg > 45:
        deg -= 90; u0, v0, w, d = -v0 - d, u0, d, w
    while deg < -45:
        deg += 90; u0, v0, w, d = v0, -u0 - w, d, w
    a = math.radians(deg)
    return {'x': round(u0 * math.cos(a) - v0 * math.sin(a), 2), 'z': round(u0 * math.sin(a) + v0 * math.cos(a), 2), 'rot': round(deg, 1), 'w': round(w, 2), 'd': round(d, 2)}


# ---------------------------------------------------------------- open data
def geocode(q, country):
    url = 'https://nominatim.openstreetmap.org/search?' + urllib.parse.urlencode({'q': q, 'format': 'jsonv2', 'limit': 1, 'countrycodes': country, 'addressdetails': 1})
    r = http(url)
    if not r:
        sys.exit(f'new_house: could not find {q!r} – give --lat/--lng instead')
    a = r[0]
    ad = a.get('address', {})
    town = ad.get('village') or ad.get('town') or ad.get('city') or ad.get('municipality') or ''
    return float(a['lat']), float(a['lon']), town, ad.get('county') or ad.get('state') or ''


def overpass(lat, lng, r=90):
    q = f'[out:json][timeout:40];(way["building"](around:{r},{lat},{lng});node["natural"="tree"](around:{r},{lat},{lng}););out geom tags;'
    for host in ('https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter'):
        try:
            return http(host, urllib.parse.urlencode({'data': q}).encode(), timeout=90)['elements']
        except Exception as e:
            print('  overpass', host, 'failed:', e)
            time.sleep(2)
    return []


def lm_plot(lat, lng, L):
    """Lantmäteriet Fastighetsindelning (OGC API Features) – the plot containing the point. Open data (CC BY 4.0) behind a free
    Geotorget account; check the current URL there. LM_FASTIGHET_URL = the collection's /items endpoint, LM_TOKEN = bearer token."""
    url, tok = os.environ.get('LM_FASTIGHET_URL'), os.environ.get('LM_TOKEN')
    if not url:
        return None
    d = .0015
    q = url + ('&' if '?' in url else '?') + urllib.parse.urlencode({'bbox': f'{lng - d},{lat - d},{lng + d},{lat + d}', 'f': 'json', 'limit': 50})
    try:
        fc = http(q, headers={'Authorization': 'Bearer ' + tok} if tok else {})
    except Exception as e:
        print('  Lantmäteriet failed:', e); return None
    return pick_plot(fc, L)


def pick_plot(gj, L):
    feats = gj.get('features', [gj]) if gj.get('type') == 'FeatureCollection' else [gj]
    rings = []
    for f in feats:
        g = f.get('geometry', f)
        if g['type'] == 'Polygon':
            rings.append((f.get('properties', {}), g['coordinates'][0]))
        elif g['type'] == 'MultiPolygon':
            rings += [(f.get('properties', {}), p[0]) for p in g['coordinates']]
    for props, ring in rings:
        poly = [L.xz(*c[:2]) for c in ring[:-1]]
        if inside([0, 0], poly):
            return {'polygon': poly, 'source': 'given', 'props': {k: v for k, v in props.items() if isinstance(v, (str, int, float))}}
    if rings:
        props, ring = rings[0]
        return {'polygon': [L.xz(*c[:2]) for c in ring[:-1]], 'source': 'given (point not inside – check)'}
    return None


def esri(lat, lng, half, px, path):
    """Esri World Imagery around the point, north up, `half` metres from the centre to the edge."""
    # bbox in degrees (the 3857 export answers 500 since 2026); the service draws it in Web Mercator, which is square here
    dlat, dlng = half / 110540, half / (111320 * math.cos(math.radians(lat)))
    # finer than the imagery has (≈0.3–0.6 m/px depending on the place) answers 500: step down until it works
    while True:
        url = ('https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/export?' +
               urllib.parse.urlencode({'bbox': f'{lng - dlng},{lat - dlat},{lng + dlng},{lat + dlat}', 'bboxSR': 4326, 'size': f'{px},{px}', 'format': 'jpg', 'f': 'image'}))
        try:
            open(path, 'wb').write(http(url, raw=True, timeout=90)); return px
        except urllib.error.HTTPError as e:
            if e.code != 500 or px <= 256:
                raise
            px = int(px * .7)


# ---------------------------------------------------------------- the new house
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('id', help='short id, a–z 0–9 (used in file names and database prefixes)')
    ap.add_argument('--address'); ap.add_argument('--name'); ap.add_argument('--lat', type=float); ap.add_argument('--lng', type=float)
    ap.add_argument('--country', default='se'); ap.add_argument('--plot', help='GeoJSON (WGS84) with the plot boundary')
    ap.add_argument('--demo', action='store_true', help='copy the invented example house as it is (no network)')
    ap.add_argument('--no-images', action='store_true'); ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9]{1,23}', a.id):
        sys.exit('new_house: id = 2–24 characters a–z and 0–9, starting with a letter')
    dst = os.path.join(ROOT, 'houses', a.id)
    if os.path.exists(dst) and not a.force:
        sys.exit(f'new_house: {dst} exists (use --force to overwrite)')
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, 'houses', '_mall'), dst)
    house = json.load(open(os.path.join(dst, 'house.json'), encoding='utf-8'))
    plan = json.load(open(os.path.join(dst, 'plan.json'), encoding='utf-8'))
    house.update(id=a.id, slug='husbok-' + a.id)
    if a.demo:
        json.dump(house, open(os.path.join(dst, 'house.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'houses/{a.id}: the invented example house. Build it: python3 tools/build.py {a.id}')
        return

    # 1. where
    town = county = ''
    if a.lat is None:
        if not a.address:
            sys.exit('new_house: give --address or --lat/--lng')
        lat, lng, town, county = geocode(a.address, a.country)
        print(f'  position {lat:.6f}, {lng:.6f} (OpenStreetMap Nominatim)')
    else:
        lat, lng = a.lat, a.lng
    L = Local(lat, lng)
    name = a.name or (a.address or f'{lat:.5f}, {lng:.5f}').split(',')[0]
    place = ' · '.join(x for x in [town, county.replace(' län', '')] if x) or name
    house.update(name=name, address=a.address or name, place=place, town=town or name, country=a.country, lat=round(lat, 6), lng=round(lng, 6),
                 type_line=('House · ' + place), about=f'a house at {a.address or name}', lang='sv' if a.country == 'se' else 'en',
                 currency={'se': 'SEK', 'es': 'EUR', 'no': 'NOK', 'dk': 'DKK', 'fi': 'EUR', 'de': 'EUR'}.get(a.country, 'EUR'))

    # 2. buildings and trees from OpenStreetMap
    els = overpass(lat, lng)
    blds = [(e.get('tags', {}), [L.xz(p['lon'], p['lat']) for p in e['geometry'][:-1]]) for e in els if e['type'] == 'way' and e.get('geometry')]
    trees = [L.xz(e['lon'], e['lat']) + [2.2, 7] for e in els if e['type'] == 'node']
    mine = next((b for b in blds if inside([0, 0], b[1])), None) or (min(blds, key=lambda b: min(math.hypot(*p) for p in b[1])) if blds else None)
    src = ['OpenStreetMap Nominatim (position)'] if a.lat is None else []
    if mine:
        tags, poly = mine
        r = min_rect(poly)
        levels = max(1, int(float(re.sub(r'[^0-9.]', '', tags.get('building:levels', '1')) or 1)))
        print(f'  the house: {r["w"]} × {r["d"]} m, turned {r["rot"]}°, {levels} storey(s), footprint {area(poly):.0f} m² (OpenStreetMap)')
        b = plan['buildings'][0]
        b.update(r)
        b['storeys'] = [{'rooms': [{'name': 'Ground floor' if k == 0 else 'Upper floor', 'x1': .3, 'x2': r['w'] - .3, 'z1': .3, 'z2': r['d'] - .3, 'furnish': False}],
                         'openings': [{'side': 'N', 'a': r['w'] / 2 - .5, 'w': 1.0, 'kind': 'door'}] if k == 0 else []} for k in range(levels)]
        b['terraces'] = []
        b['roof'] = {**b['roof'], 'ridge': 'x' if r['w'] >= r['d'] else 'z', 'pitch': 30}
        plan['buildings'] = [b]
        plan['slots'] = [{'name': 'Ground floor' if k == 0 else 'Upper floor' if k == 1 else f'Floor {k}', 'sub': f'{r["w"] * r["d"]:.0f} m²', 'type': 'storey', 'level': k} for k in range(min(levels, 3))] + [{'name': 'The plot', 'sub': '', 'type': 'plot'}]
        plan['neighbours'] = [{'polygon': p, 'h': round(3 * float(re.sub(r'[^0-9.]', '', t.get('building:levels', '2')) or 2) + 1.5, 1)} for t, p in blds if p is not poly]
        src.append('OpenStreetMap Overpass (buildings, levels, trees) – © OpenStreetMap contributors, ODbL')
        if tags.get('roof:shape'):
            b['roof']['type'] = {'gabled': 'gable', 'hipped': 'hip', 'flat': 'flat', 'skillion': 'mono'}.get(tags['roof:shape'], 'gable')
        if tags.get('start_date'):
            house['about'] += f', built {tags["start_date"]}'
    else:
        print('  no building found in OpenStreetMap at this point – the template house stays, move it by hand')
    plan['trees'] = trees[:60]
    plan['surfaces'] = []

    # 3. the plot
    plot = None
    if a.plot:
        plot = pick_plot(json.load(open(a.plot, encoding='utf-8')), L); src.append(f'Plot: {os.path.basename(a.plot)}')
    elif os.environ.get('LM_FASTIGHET_URL'):
        plot = lm_plot(lat, lng, L)
        if plot: src.append('Plot: Lantmäteriet Fastighetsindelning (CC BY 4.0)')
    if plot:
        plan['plot'] = {'polygon': plot['polygon']}
        print(f'  plot {area(plot["polygon"]):.0f} m² ({plot["source"]})')
    else:
        bx = plan['buildings'][0]
        cx, cz = bx['x'] + bx['w'] / 2, bx['z'] + bx['d'] / 2
        plan['plot'] = {'polygon': [[cx - 15, cz - 15], [cx + 15, cz - 15], [cx + 15, cz + 15], [cx - 15, cz + 15]], 'approximate': True}
        print('  plot: none given – a 30 × 30 m square marks it; replace it (docs/OPPNA-DATA.md → Tomtgräns)')
    pa = area(plan['plot']['polygon'])
    plan['slots'][-1]['sub'] = f'{pa:,.0f} m²'.replace(',', ' ')

    # 4. pictures: aerial photo under the model + the trip's satellite photos
    if not a.no_images:
        img, sat = os.path.join(dst, 'img'), os.path.join(dst, 'sat')
        os.makedirs(img, exist_ok=True); os.makedirs(sat, exist_ok=True)
        try:
            esri(lat, lng, 60, 2048, os.path.join(img, 'ortho.jpg'))
            plan['ground'] = {'image': 'img/ortho.jpg', 'size': 120}
            halves = [300000, 60000, 12000, 2500, 600, 120]
            for i, hw in enumerate(halves):
                esri(lat, lng, hw, 1024 if i < 4 else 1536, os.path.join(sat, f'{i + 1}.jpg')); time.sleep(.3)
            house['sat'] = halves
            src.append('Aerial photos: Esri World Imagery (Esri, Maxar, Earthstar Geographics)')
            print('  aerial photo + 6 satellite photos for the trip (Esri World Imagery)')
        except Exception as e:
            print('  aerial photos failed:', e)
    os.makedirs(os.path.join(dst, 'img'), exist_ok=True); os.makedirs(os.path.join(dst, 'underlag'), exist_ok=True)
    open(os.path.join(dst, 'img', 'KÄLLOR.txt'), 'w', encoding='utf-8').write('\n'.join(src) + '\n')
    b0 = plan['buildings'][0]
    house['c'] = [round(b0['x'] + b0['w'] / 2, 2), 0, round(b0['z'] + b0['d'] / 2, 2)]
    house['plans'] = []

    # 5. content: the overview article with what we know
    c = json.load(open(os.path.join(dst, 'content.json'), encoding='utf-8'))
    ov = c['articles'][0]
    ov.update(title='The house at a glance', body=f'{name}. Write about the house here.',
              facts=[{'k': 'Address', 'v': a.address or name}, {'k': 'Footprint', 'v': f'{b0["w"] * b0["d"]:.0f} m² (from the map, check)'}, {'k': 'Plot', 'v': f'{pa:.0f} m²' + (' (approximate)' if plan['plot'].get('approximate') else '')}],
              i18n={'sv': {'title': 'Huset i korthet', 'body': f'{name}. Skriv om huset här.', 'facts': [['Adress', a.address or name], ['Byggnadsyta', f'{b0["w"] * b0["d"]:.0f} m² (enligt kartan, kontrollera)'], ['Tomt', f'{pa:.0f} m²' + (' (ungefärlig)' if plan['plot'].get('approximate') else '')]]}})
    c['articles'] = [x for x in c['articles'] if x['id'] in ('overview', 'h-water', 's-welcome', 'doc-sources')]
    c['timeline'] = []
    json.dump(c, open(os.path.join(dst, 'content.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for f in os.listdir(os.path.join(dst, 'img')):
        if f.startswith('plan-auto-'):
            os.remove(os.path.join(dst, 'img', f))
    json.dump(plan, open(os.path.join(dst, 'plan.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(house, open(os.path.join(dst, 'house.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'\nhouses/{a.id} is ready for the floor plans. Next: docs/NYTT-HUS.md step 3, then  python3 tools/build.py {a.id}')


if __name__ == '__main__':
    main()
