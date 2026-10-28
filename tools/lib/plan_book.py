"""A house book for a NEW house, built from data alone:

  engine/shell.html        the house-book shell (header, 3D panel, pages, search, Ask the house, owner/guest views)
  engine/plan-scene.js     the generic 3D scene
  houses/<id>/house.json   name, place, position, language, currency, the four floor/building buttons …
  houses/<id>/plan.json    buildings, storeys, rooms, walls, openings, roofs, plot, neighbours, trees (see docs/PLAN-JSON.md)
  houses/<id>/content.json articles, public contacts, places, timeline (the snapshot signed-out visitors see)

The same patches the Gotland book uses (houses/hulehallar/build_book.py), with every number taken from the plan."""
import json, math
from .common import rep, between, emb, i18n_block

ENGINE_EXPORTS = 'groups, roofs, ceilings, HROOMS, plannedG, glassG, site, canopy, yard, plotG, nbG, furniture, BIKES, POOLS, setGarage, STOREYS, BASEY'


def bounds(plan):
    """World-space bounding box of all buildings (and the plot), for cameras and the shadow camera."""
    xs, zs = [], []
    for b in plan['buildings']:
        a = math.radians(b.get('rot', 0))
        for (u, v) in [(0, 0), (b['w'], 0), (b['w'], b['d']), (0, b['d'])]:
            xs.append(b.get('x', 0) + u * math.cos(a) - v * math.sin(a))
            zs.append(b.get('z', 0) + u * math.sin(a) + v * math.cos(a))
    bx = (min(xs), max(xs), min(zs), max(zs))
    pts = (plan.get('plot') or {}).get('polygon') or []
    px = (min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)) if pts else bx
    return bx, px


def storey_h(plan, b, k):
    st = b['storeys'][k]
    return st.get('height', plan.get('storey_height', 2.7))


def slot_info(plan):
    """For each of the shell's four buttons: base height, the building(s) it shows and where it looks."""
    slots = plan['slots']
    assert 1 <= len(slots) <= 4, 'plan.slots: one to four buttons'
    bx, px = bounds(plan)
    out = []
    for i, s in enumerate(slots):
        kind = s.get('type', 'storey')
        if kind == 'plot':
            cx, cz = (px[0] + px[1]) / 2, (px[2] + px[3]) / 2
            span = max(px[1] - px[0], px[3] - px[2], 12)
            out.append(dict(kind=kind, base=0, tgt=[cx, 0, cz], pos=[cx, span * 1.25, cz + span * .9], bld=None))
            continue
        if kind == 'building':
            b = next(b for b in plan['buildings'] if b['id'] == s['building'])
            base, level = b.get('floor', .15), 0
        else:
            level = s.get('level', i)
            own = [x['building'] for x in slots if x.get('type') == 'building']
            b = next((b for b in plan['buildings'] if b['id'] not in own and len(b.get('storeys', [])) > level), plan['buildings'][0])
            base = b.get('floor', .15) + sum(storey_h(plan, b, k) + .2 for k in range(level))
        a = math.radians(b.get('rot', 0))
        cu, cv = b['w'] / 2, b['d'] / 2
        cx, cz = b.get('x', 0) + cu * math.cos(a) - cv * math.sin(a), b.get('z', 0) + cu * math.sin(a) + cv * math.cos(a)
        span = max(b['w'], b['d'])
        # walking starts in the first room of that floor, facing into the house
        st = (b.get('storeys') or [{}])[level] if kind == 'storey' else (b.get('storeys') or [{}])[0]
        r = (st.get('rooms') or [{'x1': 1, 'x2': 2, 'z1': 1, 'z2': 2}])[0]
        ru, rv = (r['x1'] + r['x2']) / 2, (r['z1'] + r['z2']) / 2
        sx, sz = b.get('x', 0) + ru * math.cos(a) - rv * math.sin(a), b.get('z', 0) + ru * math.sin(a) + rv * math.cos(a)
        out.append(dict(kind=kind, base=round(base, 3), tgt=[cx, base, cz], pos=[cx + span * .15, base + span * 1.5 + 6, cz + span * 1.1 + 4],
                        bld=b['id'], start=[round(sx, 2), round(sz, 2), round(math.atan2(cx - sx, cz - sz), 3)]))
    while len(out) < 4:   # the shell always has four buttons: unused ones are hidden
        out.append(dict(kind='none', base=0, tgt=out[0]['tgt'], pos=out[0]['pos'], bld=None, start=out[0].get('start', [0, 0, 0])))
    return out


def build(shell, house, plan, content, engine_js):
    s = shell
    SL = slot_info(plan)
    bx, px = bounds(plan)
    cx, cz = (bx[0] + bx[1]) / 2, (bx[2] + bx[3]) / 2
    span = max(px[1] - px[0], px[3] - px[2], bx[1] - bx[0], bx[3] - bx[2], 16)
    own = [x['building'] for x in plan['slots'] if x.get('type') == 'building']   # buildings with a button of their own
    psl = [{'type': x['kind'], 'bld': x['bld'], 'level': plan['slots'][n].get('level', n) if n < len(plan['slots']) else n} for n, x in enumerate(SL)]

    glue = f'''
// ---------- glue between the generic scene and the house-book shell ----------
const H = {plan.get('storey_height', 2.7) + .2}, D0 = Math.PI / 180;
const PSL = {json.dumps(psl)};
const garden = site, street = new THREE.Group(), neighbours = nbG;
neighbours.visible = {str(bool(plan.get('show_neighbours', True))).lower()};
// the shell's four buttons: storeys (stacked), buildings (side by side) or the plot
const floors = [new THREE.Group(), new THREE.Group(), new THREE.Group(), new THREE.Group()];
floors.forEach(f => world.add(f));
world.updateMatrixWorld(true);
const OWN = {json.dumps(own)};
PSL.forEach((p, i) => {{
  if (p.type === 'storey') for (const [k, g] of Object.entries(STOREYS)) {{ const [bid, lv] = k.split(':'); if (+lv === p.level && !OWN.includes(bid)) floors[i].attach(g); }}
  else if (p.type === 'building') floors[i].attach(groups[p.bld]);
  else if (p.type === 'plot') floors[i].add(site, canopy, yard, plotG);
}});
if (!PSL.some(p => p.type === 'plot')) floors[3].add(site, canopy, yard, plotG);
// roofs ride with the top storey of their building
for (const [k, r] of Object.entries(roofs)) {{ if (OWN.includes(k)) continue; const top = PSL.map((p, i) => p.type === 'storey' && STOREYS[k + ':' + p.level] ? i : -1).filter(i => i >= 0).pop(); if (top !== undefined) floors[top].attach(r); }}
const BASE = {json.dumps([x['base'] for x in SL])};
const SHOWN = (i, lvl) => lvl < 0 || PSL[lvl].type !== 'storey' || PSL[i].type !== 'storey' || i <= lvl;
const CUT = lvl => BASE[lvl] + 1.45;
const frontDoor = null, garageDoor = null;
const shutterState = {{ open: 0, target: 0, t: 0 }};
function placeShutters() {{ }}
function updateFuture() {{ plannedG.visible = !!document.getElementById('t-future')?.checked; }}
function relabel3D() {{ labels.forEach(l => {{ l.o.element.firstChild.textContent = t(l.name); }}); }}
let compassEl = null;
'''
    scene_code = ('// ---------- the scene from plan.json (engine/plan-scene.js), in its own scope ----------\n'
                  'const world = new THREE.Group(); scene.add(world);\nconst trees = new THREE.Group(); world.add(trees);\n'
                  'const PLAN = ' + json.dumps(plan, ensure_ascii=False) + ';\n'
                  'const { ' + ENGINE_EXPORTS + ' } = (() => {\n' + engine_js + '\nreturn { ' + ENGINE_EXPORTS + ' };\n})();\n' + glue)

    i, j = between(s, '// ---------- textures ----------', '// ---------- room labels ----------')
    s = s[:i] + scene_code + '\n' + s[j:]

    i, j = between(s, '// ---------- room labels ----------', '// ---------- light & sun ----------')
    s = s[:i] + f'''// ---------- room labels ----------
const labels = [];
const ROOMS = [];
function label(floor, name, area, x, z, dy = 1.4) {{
  const key = `${{floor}}:${{name}}`;
  const el = document.createElement('div'); el.className = 'lbl'; el.title = 'Open in the wiki';
  el.append(t(name)); if (area) {{ const s = document.createElement('span'); s.textContent = `${{String(area).replace('.', LANG === 'en' ? '.' : ',')}} m²`; el.append(s); }}
  el.addEventListener('click', () => dispatchEvent(new CustomEvent('room-click', {{ detail: {{ key, name, floor }} }})));
  const o = new CSS2DObject(el); o.position.set(x, BASE[floor] + dy, z); o.visible = false;
  world.add(o); labels.push({{ o, floor, key, name }}); if (!ROOMS.some(r => r.key === key)) ROOMS.push({{ key, name, floor, area }});
}}
world.updateMatrixWorld(true);
for (const r of HROOMS) {{ const p = r.g.localToWorld(new THREE.Vector3(r.x, 0, r.z)); label(r.b, r.name, r.area, p.x, p.z, 1.1); }}
{{
  const el = document.createElement('div'); el.className = 'lbl compass'; el.textContent = 'N';
  el.title = 'North'; compassEl = el;
  const o = new CSS2DObject(el); o.position.set({cx:.2f}, .2, {px[2] - 3:.2f}); scene.add(o);
}}

''' + s[j:]

    # sun: the house's own latitude; x east, z south
    lat, lng, tz = house['lat'], house['lng'], house.get('tz', 1)
    noon_w = 12 + tz - lng / 15
    ext = round(span * .8, 1)
    s = rep(s, "Object.assign(sun.shadow.camera, { left: -18, right: 18, top: 18, bottom: -18, near: 1, far: 100 });",
            f"sun.shadow.mapSize.set(4096, 4096); Object.assign(sun.shadow.camera, {{ left: -{ext}, right: {ext}, top: {ext}, bottom: -{ext}, near: 1, far: {round(span * 4)} }});")
    s = rep(s, "const center = new THREE.Vector3(3.2, 4, 9);", f"const center = new THREE.Vector3({cx:.2f}, 0, {cz:.2f});")
    s = rep(s, "  // Palma 39.57°N. Avinguda de Joan Miró runs ~N–S: world +z (towards the garden) points to bearing 79°, world +x to 349°.",
            f"  // {lat:.3f}°N, {lng:.3f}°E: world +x points east (90°), world +z south (180°).")
    s = rep(s, "const noon = (m >= 3 && m <= 9) ? 13.82 : 12.82;", f"const noon = (m >= 3 && m <= 9) ? {noon_w + 1:.2f} : {noon_w:.2f};")
    s = rep(s, "const Hh = (hr - noon) * 15 * D, lat = 39.57 * D;", f"const Hh = (hr - noon) * 15 * D, lat = {lat:.3f} * D;")
    s = rep(s, "const dir = new THREE.Vector3(Math.cos((bearing - 349) * D) * Math.cos(e), Math.sin(e), Math.cos((bearing - 79) * D) * Math.cos(e));",
            "const dir = new THREE.Vector3(Math.cos((bearing - 90) * D) * Math.cos(e), Math.sin(e), Math.cos((bearing - 180) * D) * Math.cos(e));")
    s = rep(s, "sun.position.copy(center).addScaledVector(dir, 50);", f"sun.position.copy(center).addScaledVector(dir, {round(span * 2)});")

    views = {'all': {'pos': [round(cx + span * .9, 1), round(span * .85, 1), round(cz + span * 1.15, 1)], 'tgt': [round(cx, 1), 0, round(cz, 1)]}}
    for n, x in enumerate(SL):
        views[str(n)] = {'pos': [round(v, 2) for v in x['pos']], 'tgt': [round(v, 2) for v in x['tgt']]}
    i, j = between(s, '// ---------- views ----------', "document.querySelectorAll('.floors button').forEach(b => b.addEventListener('click', () => applyView(b.dataset.view)));")
    s = s[:i] + f'''// ---------- views ----------
const views = {json.dumps(views)};
let current = 'all';
const showLabels = document.getElementById('t-labels');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
let tween = null;
function applyView(v, animate = true) {{
  current = v;
  if (walk) {{
    document.querySelectorAll('.floors button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === v)));
    dispatchEvent(new CustomEvent('view-change', {{ detail: v }}));
    walkStart(v === 'all' ? 0 : +v); return;
  }}
  const lvl = v === 'all' ? -1 : +v;
  floors.forEach((f, i) => f.visible = SHOWN(i, lvl));
  for (const [k, r] of Object.entries(roofs)) {{ const open = lvl >= 0 && ((PSL[lvl].type === 'storey' && !OWN.includes(k)) || PSL[lvl].bld === k); r.visible = !open; if (ceilings[k]) ceilings[k].visible = !open; }}
  document.querySelectorAll('.floors button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === v)));
  labels.forEach(l => l.o.visible = showLabels.checked && v !== 'all' && l.floor === lvl);
  if (typeof updateFuture === 'function') updateFuture();
  dispatchEvent(new CustomEvent('view-change', {{ detail: v }}));
  const {{ pos, tgt }} = views[v];
  const to = {{ p: new THREE.Vector3(...pos), t: new THREE.Vector3(...tgt) }};
  if (!animate || reduce) {{ camera.position.copy(to.p); controls.target.copy(to.t); return; }}
  tween = {{ from: {{ p: camera.position.clone(), t: controls.target.clone() }}, to, start: performance.now(), dur: 900 }};
}}
''' + s[j:]

    front = plan.get('front', 'N')   # the street side: the "Street" camera looks from there
    d = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}[front]
    far = span * .9
    s = rep(s, '''const CAMS = {
  street: () => ({ p: new THREE.Vector3(3.4, 6.5, -15), t: new THREE.Vector3(3.4, 4, 5) }),
  garden: () => ({ p: new THREE.Vector3(3.4, 9, 31), t: new THREE.Vector3(3.4, 3.5, 12) }),
  top: () => { const y = current === 'all' ? 3 * H : +current * H; return { p: new THREE.Vector3(3.45, y + 22, 9.7), t: new THREE.Vector3(3.4, y, 9.6) }; },
};''', f'''const CAMS = {{
  street: () => ({{ p: new THREE.Vector3({cx + d[0] * far:.2f}, 4, {cz + d[1] * far:.2f}), t: new THREE.Vector3({cx:.2f}, 2.5, {cz:.2f}) }}),
  garden: () => ({{ p: new THREE.Vector3({cx - d[0] * far:.2f}, 5, {cz - d[1] * far:.2f}), t: new THREE.Vector3({cx:.2f}, 2.5, {cz:.2f}) }}),
  top: () => {{ const t0 = new THREE.Vector3(...views[current].tgt); return {{ p: t0.clone().add(new THREE.Vector3(0, current === 'all' ? {round(span * 2.2)} : {round(span * 1.4)}, .1)), t: t0 }}; }},
}};''')
    s = rep(s, "  floors.forEach((f, i) => f.visible = i <= lvl);\n  if (lvl < 3) { cutPlane.constant = lvl * H + 1.45; renderer.clippingPlanes = [cutPlane]; } else renderer.clippingPlanes = [];",
            "  floors.forEach((f, i) => f.visible = SHOWN(i, lvl));\n  if (PSL[lvl] && PSL[lvl].type !== 'plot') { cutPlane.constant = CUT(lvl); renderer.clippingPlanes = [cutPlane]; } else renderer.clippingPlanes = [];")
    s = rep(s, '''    for (const lvl of [0, 1, 2, 3]) {
      const y = lvl * H, c = new THREE.Vector3(3.4, y, lvl === 0 ? 10 : 7.5);
      thumbs.floor[lvl] = snapView(lvl, new THREE.Vector3(-3.5, y + 13, c.z - 4), c);
    }''', '''    for (const lvl of [0, 1, 2, 3]) thumbs.floor[lvl] = snapView(lvl, new THREE.Vector3(...views[lvl].pos), new THREE.Vector3(...views[lvl].tgt));''')
    s = rep(s, "const t0 = new THREE.Vector3(); l.o.getWorldPosition(t0); t0.y = l.floor * H + .4;", "const t0 = new THREE.Vector3(); l.o.getWorldPosition(t0); t0.y = BASE[l.floor] + .4;")
    s = rep(s, "const t = new THREE.Vector3(); l.o.getWorldPosition(t); t.y = +current * H + .9; flyTo(t, 4.2, 4.2);", "const t = new THREE.Vector3(); l.o.getWorldPosition(t); t.y = BASE[+current] + .9; flyTo(t, 4.2, 4.2);")
    s = rep(s, "  const on = document.getElementById('t-cut').checked && current !== 'all' && +current < 3;\n  if (on) { cutPlane.constant = +current * H + 1.45; renderer.clippingPlanes = [cutPlane]; } else renderer.clippingPlanes = [];",
            "  const on = document.getElementById('t-cut').checked && current !== 'all' && PSL[+current]?.type !== 'plot';\n  if (on) { cutPlane.constant = CUT(+current); renderer.clippingPlanes = [cutPlane]; } else renderer.clippingPlanes = [];")
    starts = {str(n): x.get('start', [cx, cz + span / 2, math.pi]) for n, x in enumerate(SL)}
    for n, x in enumerate(SL):
        if x['kind'] == 'plot':
            starts[str(n)] = [round(cx, 2), round(px[3] - 2, 2), math.pi]
    s = rep(s, "const STARTS = { 0: [4.3, 1.0], 1: [3.6, 1.0], 2: [4.4, 3.0], 3: [3.4, 10.6] };   // model x, z per floor; you start looking towards the garden",
            f"const STARTS = {json.dumps(starts)};   // world x, z and heading per button")
    s = rep(s, "const toWorld = (x, z) => new THREE.Vector3(world.position.x + world.scale.x * x, 0, z);", "const toWorld = (x, z) => new THREE.Vector3(x, 0, z);")
    s = rep(s, "  const [x, z] = STARTS[lvl], p = toWorld(x, z); p.y = lvl * H + EYE;\n  camera.position.copy(p); walk.yaw = 0; walk.pitch = -.05;",
            "  const [x, z, yaw] = STARTS[lvl], p = toWorld(x, z); p.y = BASE[lvl] + EYE;\n  camera.position.copy(p); walk.yaw = yaw; walk.pitch = -.05;")
    s = rep(s, "    if (b.max.x - b.min.x < 30) walk.boxes.push({ b, o });", "    if (b.max.x - b.min.x < 30 && b.max.z - b.min.z < 30) walk.boxes.push({ b, o });")
    s = rep(s, "Object.assign(window, { camera, controls, applyView, world, THREE, walkState", "Object.assign(window, { camera, controls, applyView, world, THREE, labels, walkState")

    # ---------------------------------------------------------------- texts of this house
    name, place = house['name'], house['place']
    s = rep(s, '<title>Townhouse El Terreno</title>', f'<title>{name}</title>')
    s = rep(s, "const HOME_ID = 'jm87';", f"const HOME_ID = {json.dumps(house['id'])};")
    s = rep(s, '<span class="addr">Joan Miró 87</span><small>Avinguda de Joan Miró 87 · El Terreno · Palma</small>', f'<span class="addr">{name}</span><small>{house.get("address", place)}</small>')
    s = rep(s, '<div class="addrtag" aria-hidden="true"><b>Joan Miró 87</b><span>Avinguda de Joan Miró 87 · El Terreno · Palma</span></div>',
            f'<div class="addrtag" aria-hidden="true"><b>{name}</b><span>{place}</span></div>')
    i, j = between(s, '<div class="floors" data-stack role="group" aria-label="Choose floor">', '</div>')
    btns = ''.join(f'\n    <button id="v-{n}" data-view="{n}" aria-pressed="false"{" hidden" if n >= len(plan["slots"]) else ""}>{plan["slots"][n]["name"] if n < len(plan["slots"]) else ""}<small>{plan["slots"][n].get("sub", "") if n < len(plan["slots"]) else ""}</small></button>' for n in range(4))
    stacked = all(x.get('type', 'storey') != 'building' for x in plan['slots'])
    s = s[:i] + f'''<div class="floors"{" data-stack" if stacked else ""} role="group" aria-label="Choose floor">
    <button id="v-all" data-view="all" aria-pressed="true">{house.get('whole', 'Whole')}<small>{house.get('whole_sub', 'house')}</small></button>{btns}
  ''' + s[j:]
    s = rep(s, '<label><input type="checkbox" id="t-trees"> Street trees</label>', '<label><input type="checkbox" id="t-trees" checked> Trees</label>')
    s = rep(s, "trees.visible = e.target.checked);", "trees.visible = e.target.checked);")
    hide = ['.vacbtn', '#t-plan', '#t-laundry', '.plannote', '.futuretoggle']
    if not house.get('buyer', False):
        hide += ['.bookbtn', '.bookbar', '[data-view-mode="buyer"]']
        s = rep(s, "if (v === 'guest' || v === 'buyer') viewMode = v;", "if (v === 'guest') viewMode = v;")
    s = rep(s, '</style>', ', '.join(hide) + ' { display: none !important; }\n</style>', 1)
    for a, b in [("'jm87-lang'", f"'{house['id']}-lang'"), ("'jm87-view'", f"'{house['id']}-view'")]:
        s = s.replace(a, b)
    s = rep(s, "let LANG = 'en';", f"let LANG = {json.dumps(house.get('lang', 'en'))};")
    names = [x['name'] for x in plan['slots']] + [''] * (4 - len(plan['slots']))
    s = rep(s, "const FLOOR_NAMES = ['Ground floor', 'First floor', 'Second floor', 'Roof'];", f"const FLOOR_NAMES = {json.dumps(names, ensure_ascii=False)};")
    if house.get('about_cats'):
        s = rep(s, "const ABOUT_CATS = ['Overview', 'Facades & exterior', 'Garden & pool', 'Materials & finishes', 'Dimensions & data'];", f"const ABOUT_CATS = {json.dumps(house['about_cats'], ensure_ascii=False)};")
    i, j = between(s, 'const PLANS = [', '];\n')
    s = s[:i] + 'const PLANS = [\n' + ''.join(f'  {json.dumps(p, ensure_ascii=False)},\n' for p in house.get('plans', [])) + s[j:]
    line = house.get('type_line', place)
    s = s.replace("t('Townhouse · El Terreno · Palma')", f"t({json.dumps(line, ensure_ascii=False)})").replace("h('b', {}, 'Joan Miró 87')", f"h('b', {{}}, {json.dumps(name, ensure_ascii=False)})").replace("h('h2', {}, 'Joan Miró 87')", f"h('h2', {{}}, {json.dumps(name, ensure_ascii=False)})")
    s = rep(s, "'You are the house book of Joan Miró 87, a townhouse in El Terreno, Palma de Mallorca. The person asking is '",
            json.dumps(f"You are the house book of {name}, {house.get('about', 'a house in ' + place)}. The person asking is ", ensure_ascii=False).replace('"', "'"))
    s = rep(s, "const AGENCY = { name: 'Your Agency',", f"const AGENCY = {{ name: {json.dumps(house.get('agency', ''), ensure_ascii=False)},")
    cur = house.get('currency', 'EUR')
    if cur != 'EUR':
        s = rep(s, "const eur = n => Number(n).toLocaleString(LOC(), { style: 'currency', currency: 'EUR' });",
                f"const eur = n => Number(n).toLocaleString(LOC(), {{ style: 'currency', currency: '{cur}', maximumFractionDigits: 0 }});")
        s = s.replace("label: 'Amount (€)'", "label: 'Amount (kr)'" if cur == 'SEK' else f"label: 'Amount ({cur})'")
    s = i18n_block(s, house.get('i18n', {}))
    return s
