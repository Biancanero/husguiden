# Hulehällar 418D – the build steps (run by build_book.py with `shell` = engine/shell.html and `hdir` = this folder).
# Leaves the finished page in `s`. Every rep() asserts its anchor in the shell.
import json, os, re, sys

model = open(os.path.join(hdir, 'scene.html'), encoding='utf-8').read()
content = json.load(open(os.path.join(hdir, 'content.json'), encoding='utf-8'))

def rep(s, a, b, n=1):
    c = s.count(a)
    if c != n: sys.exit(f'expected {n}× but found {c}×: {a[:90]!r}')
    return s.replace(a, b)

def between(s, start, end):
    i = s.index(start); j = s.index(end, i)
    return i, j

# ---------------------------------------------------------------- the Gotland scene, without its own page around it
mjs = model[model.index('<script type="module">'):]
mjs = mjs[mjs.index('// ---------- helpers ----------'):mjs.index('// ---------- sun: Gotland')]
# its registries: the shell owns `labels`, so the model's room labels are collected separately and drawn by the shell
mjs = rep(mjs, 'const groups = {}, cuttable = [], colliders = [], furniture = [], labels = [], roofs = {}, ceilings = {};',
          'const groups = {}, cuttable = [], colliders = [], furniture = [], roofs = {}, ceilings = {}, HROOMS = [];')
mjs = rep(mjs, "g.userData.key = key; scene.add(g); groups[key] = g;", "g.userData.key = key; world.add(g); groups[key] = g;")
i, j = between(mjs, '// labels\nfunction label(', 'const fmt = ')
mjs = mjs[:i] + '''// labels: the model names its rooms in Swedish; the house book keys rooms by an English name and translates it
const SV2EN = { 'Arbets-/gästrum': 'Study / guest room', 'Förråd': 'Storage', 'Kapprum': 'Cloakroom', 'Tvätt/apparatrum': 'Laundry & plant room',
  'Passage': 'Passage', 'Kök': 'Kitchen', 'Matplats': 'Dining', 'Vardagsrum': 'Living room', 'Dusch/toa': 'Shower & WC', 'Sovrum': 'Bedroom',
  'Glasveranda': 'Glazed veranda', 'Gäststuga': 'Guest cottage', 'Arbetsrum/bod': 'Workshop', 'Förråd/garage': 'Storage & garage',
  'Toa/dusch': 'Shower & WC', 'Dusch & WC': 'Shower & WC', 'Sovrum norr': 'North bedroom', 'Sovrum söder': 'South bedroom', 'Hall & pentry': 'Hall & kitchenette', 'Grillplats': 'Grill place', 'Studsmatta': 'Trampoline' };
const BKEY = { main: 0, main_v: 0, gar: 1, att: 2 };
function label(g, x, y, z, name, sub, info, cls = '') {
  if (cls) return null;   // building and "planned" tags: the shell's floor buttons do that job
  let en = SV2EN[name] || name;
  const b = BKEY[g.userData.key] ?? 3;
  if (b === 2 && en === 'Bedroom') en = HROOMS.some(r => r.b === 2 && r.name === 'Bedroom north') ? 'Bedroom south' : 'Bedroom north';
  const r = { g, x, z, b, name: en, area: sub ? String(sub).replace(/\\s*m²$/, '').replace(',', '.') : '' }; HROOMS.push(r); return r;
}
''' + mjs[j:]
mjs = rep(mjs, "labels.forEach(l => { if (l.cls === 'ghost') l.key = 'plan'; });\n", '')
mjs = mjs.replace("labels[labels.length - 1].key = 'nb';", '').replace("labels[labels.length - 1].key = 'site';", '').replace("labels[labels.length - 1].key = 'glass';", '')
# trees get their own group so the shell's "Trees" toggle can hide them
mjs = rep(mjs, 'jun.instanceColor.needsUpdate = true; yard.add(jun);', 'jun.instanceColor.needsUpdate = true; trees.add(jun);')
mjs = rep(mjs, 'crown.instanceColor.needsUpdate = true; yard.add(crown, trunk);', 'crown.instanceColor.needsUpdate = true; trees.add(crown, trunk);')
for k in ['plannedG', 'glassG', 'site', 'canopy', 'plotG', 'nbG', 'yard']:
    mjs = mjs.replace(f'const {k} = new THREE.Group(); scene.add({k});', f'const {k} = new THREE.Group(); world.add({k});')
# the shell has its own label(): the model's becomes mlabel()
mjs = re.sub(r'\blabel\(', 'mlabel(', mjs)
# the site gets two extra named places the model has no label for
glue = '''
// ---------- glue between the Gotland scene and the house-book shell ----------
const H = 2.8, D0 = Math.PI / 180, CUTY = 1.65;   // H is only a nominal storey; every building here is single-storey
const garden = site, street = new THREE.Group(), neighbours = nbG;
neighbours.visible = false;
HROOMS.push({ g: site, x: 17.5, z: -8.6, b: 3, name: 'Limestone patio', area: '52' }, { g: site, x: 5.8, z: 6.4, b: 3, name: 'Deck', area: '' }, { g: site, x: 8.5, z: -1.4, b: 3, name: 'Entrance', area: '' });
// the four "floors" of the shell are the buildings: main house, guest house & garage, attefallshus, the plot
const floors = [new THREE.Group(), new THREE.Group(), new THREE.Group(), new THREE.Group()];
floors.forEach(f => world.add(f));
floors[0].add(groups.main, groups.main_v); floors[1].add(groups.gar); floors[2].add(groups.att);
floors[3].add(site, canopy, yard, plotG);
const BASE = [.35, .05, .12, 0];
const frontDoor = null, garageDoor = null;
const shutterState = { open: 0, target: 0, t: 0 };
function placeShutters() { }
function updateFuture() { plannedG.visible = !!document.getElementById('t-future')?.checked; }
function relabel3D() { labels.forEach(l => { l.o.element.firstChild.textContent = t(l.name); }); }
let compassEl = null;
// bike-shed proposals (hidden groups from the model): Off · 1–5 under Display options; ?cykel=n opens one
function setBike(n) { BIKES.forEach((b, i) => b.v.visible = i + 1 === n); POOLS.clear('bike', n ? BIKES[n - 1].v.userData.clear : null); document.querySelectorAll('#bikerow button').forEach(b => b.setAttribute('aria-pressed', String(+b.dataset.n === n))); const c = document.getElementById('bike-cap'); if (c) c.textContent = n ? BIKES[n - 1].inf.title : ''; }
document.querySelectorAll('#bikerow button').forEach(b => b.onclick = () => setBike(+b.dataset.n));
{ const gb = document.getElementById('gar-btn'); if (gb) gb.onclick = () => { const o = gb.getAttribute('aria-pressed') !== 'true'; gb.setAttribute('aria-pressed', String(o)); gb.textContent = t(o ? 'Close' : 'Open'); setGarage(o); }; }
// pool / hot-tub proposals: Off · 1–3; ?pool=n opens one
function setPool(n) { POOLS.forEach((b, i) => b.v.visible = i + 1 === n); POOLS.clear('pool', n ? POOLS[n - 1].r : null); document.querySelectorAll('#poolrow button').forEach(b => b.setAttribute('aria-pressed', String(+b.dataset.n === n))); const c = document.getElementById('pool-cap'); if (c) c.textContent = n ? POOLS[n - 1].inf.title : ''; }
document.querySelectorAll('#poolrow button').forEach(b => b.onclick = () => setPool(+b.dataset.n));
{ const q = +new URLSearchParams(location.search).get('pool'); if (q) setPool(q); }
document.getElementById('t-glass')?.addEventListener('change', e => { glassG.visible = e.target.checked; glassG.userData.onToggle?.(e.target.checked); });
{ const sunEl = document.querySelector('.sun'), row = document.getElementById('bikerow'); if (sunEl && row) row.before(sunEl); }
{ const q = +new URLSearchParams(location.search).get('cykel'); if (q) setBike(q); }
'''
EXPORTS = 'groups, roofs, ceilings, HROOMS, plannedG, glassG, site, canopy, yard, plotG, nbG, furniture, BIKES, POOLS, setGarage'
scene_code = ('// ---------- the Gotland scene (from hulehallar-418d.html), in its own scope ----------\n'
  'const world = new THREE.Group(); scene.add(world);\nconst trees = new THREE.Group(); world.add(trees);\n'
  'const { ' + EXPORTS + ' } = (() => {\n' + mjs + '\nreturn { ' + EXPORTS + ' };\n})();\n' + glue)

# ---------------------------------------------------------------- shell: swap Joan Miró 87's scene for Gotland's
s = shell
i, j = between(s, '// ---------- textures ----------', '// ---------- room labels ----------')
s = s[:i] + scene_code + '\n' + s[j:]

# room labels: from the collected rooms, positioned in world space
i, j = between(s, '// ---------- room labels ----------', '// ---------- light & sun ----------')
s = s[:i] + '''// ---------- room labels ----------
const labels = [];
const ROOMS = [];
function label(floor, name, area, x, z, dy = 1.4) {
  const key = `${floor}:${name}`;
  const el = document.createElement('div'); el.className = 'lbl'; el.title = 'Open in the wiki';
  el.append(t(name)); if (area) { const s = document.createElement('span'); s.textContent = `${String(area).replace('.', LANG === 'en' ? '.' : ',')} m²`; el.append(s); }
  el.addEventListener('click', () => dispatchEvent(new CustomEvent('room-click', { detail: { key, name, floor } })));
  const o = new CSS2DObject(el); o.position.set(x, BASE[floor] + dy, z); o.visible = false;
  world.add(o); labels.push({ o, floor, key, name }); if (!ROOMS.some(r => r.key === key)) ROOMS.push({ key, name, floor, area });
}
world.updateMatrixWorld(true);
for (const r of HROOMS) { const p = r.g.localToWorld(new THREE.Vector3(r.x, 0, r.z)); label(r.b, r.name, r.area, p.x, p.z, r.b === 3 ? 1.6 : 1.1); }
{
  const el = document.createElement('div'); el.className = 'lbl compass'; el.textContent = 'N';
  el.title = 'North'; compassEl = el;
  const o = new CSS2DObject(el); o.position.set(12, .2, -36); scene.add(o);
}

''' + s[j:]

# sun: Gotland 57.3° N, 18.3° E; world +x is east, +z is south
s = rep(s, "Object.assign(sun.shadow.camera, { left: -18, right: 18, top: 18, bottom: -18, near: 1, far: 100 });",
        "sun.shadow.mapSize.set(4096, 4096); Object.assign(sun.shadow.camera, { left: -46, right: 46, top: 46, bottom: -46, near: 1, far: 220 });")
s = rep(s, "const center = new THREE.Vector3(3.2, 4, 9);", "const center = new THREE.Vector3(12, 0, -4);")
s = rep(s, "  // Palma 39.57°N. Avinguda de Joan Miró runs ~N–S: world +z (towards the garden) points to bearing 79°, world +x to 349°.", "  // Hamra 57.27°N, 18.3°E: world +x points east (90°), world +z south (180°).")
s = rep(s, "const noon = (m >= 3 && m <= 9) ? 13.82 : 12.82;", "const noon = (m >= 3 && m <= 9) ? 13.78 : 12.78;")
s = rep(s, "const Hh = (hr - noon) * 15 * D, lat = 39.57 * D;", "const Hh = (hr - noon) * 15 * D, lat = 57.27 * D;")
s = rep(s, "const dir = new THREE.Vector3(Math.cos((bearing - 349) * D) * Math.cos(e), Math.sin(e), Math.cos((bearing - 79) * D) * Math.cos(e));",
        "const dir = new THREE.Vector3(Math.cos((bearing - 90) * D) * Math.cos(e), Math.sin(e), Math.cos((bearing - 180) * D) * Math.cos(e));")
s = rep(s, "sun.position.copy(center).addScaledVector(dir, 50);", "sun.position.copy(center).addScaledVector(dir, 110);")

# views: one per building; nothing is hidden, the chosen building just loses its roof
i, j = between(s, '// ---------- views ----------', 'document.querySelectorAll(\'.floors button\').forEach(b => b.addEventListener(\'click\', () => applyView(b.dataset.view)));')
s = s[:i] + '''// ---------- views ----------
const views = {
  all: { pos: [34, 30, 46], tgt: [12, 0, -3] },
  0: { pos: [10.6, 19, 13], tgt: [10.6, 0, 2.4] },
  1: { pos: [5.0, 12, 1.5], tgt: [4.8, 0, -10.5] },
  2: { pos: [12.2, 11, -1], tgt: [21.5, 0, -7] },
  3: { pos: [12, 44, 30], tgt: [12, 0, -2] },
};
const ROOFKEY = { main: 0, main_v: 0, gar: 1, att: 2 };
let current = 'all';
const showLabels = document.getElementById('t-labels');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
let tween = null;
function applyView(v, animate = true) {
  current = v;
  if (walk) {
    document.querySelectorAll('.floors button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === v)));
    dispatchEvent(new CustomEvent('view-change', { detail: v }));
    walkStart(v === 'all' ? 0 : +v); return;
  }
  const lvl = v === 'all' ? -1 : +v;
  floors.forEach(f => f.visible = true);
  for (const [k, r] of Object.entries(roofs)) { const open = ROOFKEY[k] === lvl; r.visible = !open; if (ceilings[k]) ceilings[k].visible = !open; }
  canopy.visible = lvl !== 0;
  document.querySelectorAll('.floors button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === v)));
  labels.forEach(l => l.o.visible = showLabels.checked && v !== 'all' && l.floor === lvl);
  if (typeof updateFuture === 'function') updateFuture();
  dispatchEvent(new CustomEvent('view-change', { detail: v }));
  const { pos, tgt } = views[v];
  const to = { p: new THREE.Vector3(...pos), t: new THREE.Vector3(...tgt) };
  if (!animate || reduce) { camera.position.copy(to.p); controls.target.copy(to.t); return; }
  tween = { from: { p: camera.position.clone(), t: controls.target.clone() }, to, start: performance.now(), dur: 900 };
}
''' + s[j:]
s = rep(s, '''const CAMS = {
  street: () => ({ p: new THREE.Vector3(3.4, 6.5, -15), t: new THREE.Vector3(3.4, 4, 5) }),
  garden: () => ({ p: new THREE.Vector3(3.4, 9, 31), t: new THREE.Vector3(3.4, 3.5, 12) }),
  top: () => { const y = current === 'all' ? 3 * H : +current * H; return { p: new THREE.Vector3(3.45, y + 22, 9.7), t: new THREE.Vector3(3.4, y, 9.6) }; },
};''', '''const CAMS = {
  street: () => ({ p: new THREE.Vector3(9, 4.5, -32), t: new THREE.Vector3(10, 1, -6) }),
  garden: () => ({ p: new THREE.Vector3(9, 3, 24), t: new THREE.Vector3(10, 2, 2) }),
  top: () => { const t0 = new THREE.Vector3(...views[current].tgt); return { p: t0.clone().add(new THREE.Vector3(0, current === 'all' || current === '3' ? 70 : 26, .1)), t: t0 }; },
};''')
# thumbnails: every building stays visible; cut at the same height as the plan view
s = rep(s, "  floors.forEach((f, i) => f.visible = i <= lvl);\n  if (lvl < 3) { cutPlane.constant = lvl * H + 1.45; renderer.clippingPlanes = [cutPlane]; } else renderer.clippingPlanes = [];",
        "  floors.forEach(f => f.visible = true);\n  if (lvl < 3) { cutPlane.constant = CUTY; renderer.clippingPlanes = [cutPlane]; } else renderer.clippingPlanes = [];")
s = rep(s, '''    for (const lvl of [0, 1, 2, 3]) {
      const y = lvl * H, c = new THREE.Vector3(3.4, y, lvl === 0 ? 10 : 7.5);
      thumbs.floor[lvl] = snapView(lvl, new THREE.Vector3(-3.5, y + 13, c.z - 4), c);
    }''', '''    for (const lvl of [0, 1, 2, 3]) thumbs.floor[lvl] = snapView(lvl, new THREE.Vector3(...views[lvl].pos), new THREE.Vector3(...views[lvl].tgt));''')
s = rep(s, "const t0 = new THREE.Vector3(); l.o.getWorldPosition(t0); t0.y = l.floor * H + .4;", "const t0 = new THREE.Vector3(); l.o.getWorldPosition(t0); t0.y = BASE[l.floor] + .4;")
s = rep(s, "const t = new THREE.Vector3(); l.o.getWorldPosition(t); t.y = +current * H + .9; flyTo(t, 4.2, 4.2);", "const t = new THREE.Vector3(); l.o.getWorldPosition(t); t.y = BASE[+current] + .9; flyTo(t, +current === 3 ? 9 : 4.2, +current === 3 ? 7 : 4.2);")
s = rep(s, "  const on = document.getElementById('t-cut').checked && current !== 'all' && +current < 3;\n  if (on) { cutPlane.constant = +current * H + 1.45; renderer.clippingPlanes = [cutPlane]; } else renderer.clippingPlanes = [];",
        "  const on = document.getElementById('t-cut').checked && current !== 'all' && +current < 3;\n  if (on) { cutPlane.constant = CUTY; renderer.clippingPlanes = [cutPlane]; } else renderer.clippingPlanes = [];")
# walking: start points in world coordinates (the Gotland world is not mirrored)
s = rep(s, "const STARTS = { 0: [4.3, 1.0], 1: [3.6, 1.0], 2: [4.4, 3.0], 3: [3.4, 10.6] };   // model x, z per floor; you start looking towards the garden",
        "const STARTS = { 0: [13.3, 1.0, -Math.PI / 2], 1: [.4, -10.4, Math.PI / 2], 2: [21.4, -10.2, 0], 3: [16, -9.5, Math.PI] };   // world x, z and heading per building")
s = rep(s, "const toWorld = (x, z) => new THREE.Vector3(world.position.x + world.scale.x * x, 0, z);", "const toWorld = (x, z) => new THREE.Vector3(x, 0, z);")
s = rep(s, "  const [x, z] = STARTS[lvl], p = toWorld(x, z); p.y = lvl * H + EYE;\n  camera.position.copy(p); walk.yaw = 0; walk.pitch = -.05;",
        "  const [x, z, yaw] = STARTS[lvl], p = toWorld(x, z); p.y = BASE[lvl] + EYE;\n  camera.position.copy(p); walk.yaw = yaw; walk.pitch = -.05;")
s = rep(s, "    if (b.max.x - b.min.x < 30) walk.boxes.push({ b, o });",
        "    if (b.max.x - b.min.x < 30 && b.max.z - b.min.z < 30) walk.boxes.push({ b, o });")   # the plot's big ground planes never block
s = rep(s, "Object.assign(window, { camera, controls, applyView, world, THREE, walkState",
        "Object.assign(window, { camera, controls, applyView, world, THREE, labels, walkState")

# ---------------------------------------------------------------- shell: the house itself
s = rep(s, '<title>Townhouse El Terreno</title>', '<title>Hulehällar 418D</title>')
s = rep(s, "const HOME_ID = 'jm87';", "const HOME_ID = 'hamra';")   # the home switch marks Gotland as 'you are here'
s = rep(s, '<span class="addr">Joan Miró 87</span><small>Avinguda de Joan Miró 87 · El Terreno · Palma</small>',
        '<span class="addr">Hulehällar 418D</span><small>Hamra · Gotland</small>')
s = rep(s, '<div class="addrtag" aria-hidden="true"><b>Joan Miró 87</b><span>Avinguda de Joan Miró 87 · El Terreno · Palma</span></div>',
        '<div class="addrtag" aria-hidden="true"><b>Hulehällar 418D</b><span>Hamra · Gotland</span></div>')
i, j = between(s, '<div class="floors" data-stack role="group" aria-label="Choose floor">', '</div>')
s = s[:i] + '''<div class="floors" role="group" aria-label="Choose building">
    <button id="v-all" data-view="all" aria-pressed="true">Whole<small>plot</small></button>
    <button id="v-0" data-view="0" aria-pressed="false">Main house<small>122,5 m²</small></button>
    <button id="v-1" data-view="1" aria-pressed="false">Guest house<small>50 m²</small></button>
    <button id="v-2" data-view="2" aria-pressed="false">Attefall<small>30 m²</small></button>
    <button id="v-3" data-view="3" aria-pressed="false">The plot<small>2 600 m²</small></button>
  ''' + s[j:]
s = rep(s, '<button type="button" data-cam="street">Street</button>', '<button type="button" data-cam="street">From the drive</button>')
s = rep(s, '<button type="button" data-cam="garden">Garden</button>', '<button type="button" data-cam="garden">South side</button>')
s = rep(s, '<label><input type="checkbox" id="t-trees"> Street trees</label>', '<label><input type="checkbox" id="t-trees" checked> Trees</label>')
s = rep(s, '<label class="futuretoggle"><input type="checkbox" id="t-future"> Ideas</label>', '<label class="futuretoggle"><input type="checkbox" id="t-future"> Planned 2022</label>'
  '<label><input type="checkbox" id="t-glass"> Glass house as built</label>'
  '<div class="bikerow" id="bikerow"><span>Bike shed</span>' + ''.join(f'<button type="button" data-n="{n}" aria-pressed="{str(n == 0).lower()}">{"Off" if n == 0 else n}</button>' for n in range(10)) + '<small id="bike-cap"></small></div>'
  '<div class="bikerow" id="garrow"><span>Garage doors</span><button type="button" id="gar-btn" aria-pressed="false">Open</button></div>'
  '<div class="bikerow" id="poolrow"><span>Deck &amp; pool</span>' + ''.join(f'<button type="button" data-n="{n}" aria-pressed="{str(n == 0).lower()}">{"Off" if n == 0 else n}</button>' for n in range(6)) + '<small id="pool-cap"></small></div>')
s = rep(s, '</style>', '''.bikerow { flex-basis: 100%; display: flex; align-items: center; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.bikerow span { margin-right: 6px; }
.bikerow button { min-width: 30px; padding: 5px 8px; border: 1px solid var(--line, #d9d4cc); background: none; font: inherit; font-size: 12px; cursor: pointer; color: inherit; }
.bikerow button[aria-pressed="true"] { background: var(--ink, #3b3737); color: var(--paper, #efede9); border-color: var(--ink, #3b3737); }
.bikerow small { flex-basis: 100%; color: var(--muted, #8a837c); font-size: 12px; min-height: 1em; }
/* the sun lives inside Display options here (one model only – the standalone viewer's sun slider moved in) */
.toggles .sun { display: grid !important; position: static; transform: none; left: auto; bottom: auto; width: auto; flex-basis: 100%; margin-top: 6px; padding: 0; background: none; box-shadow: none; border: 0; backdrop-filter: none; grid-template-columns: auto 1fr auto; gap: 8px; align-items: center; }
.toggles .sun .sun-name { display: inline !important; }
.toggles .sun output { grid-column: 1 / -1; text-align: left !important; min-width: 0; }
</style>''', 1)
s = rep(s, "trees.visible = e.target.checked);", "trees.visible = e.target.checked);")
# not for sale: no buyer view, no viewing button, no shutters to close
s = rep(s, '</style>', '''.bookbtn, .bookbar, .vacbtn, [data-view-mode="buyer"], #t-plan, #t-laundry, .plannote { display: none !important; }
</style>''', 1)
s = rep(s, "if (v === 'guest' || v === 'buyer') viewMode = v;", "if (v === 'guest') viewMode = v;")
s = rep(s, "const startTab = () => 'model';", "const startTab = () => 'model';")
for a, b in [("'jm87-lang'", "'hh-lang'"), ("'jm87-view'", "'hh-view'")]:
    s = s.replace(a, b)
s = rep(s, "let LANG = 'en';", "let LANG = 'sv';")
s = rep(s, "if (LANGS.includes(n)) LANG = n; } } catch { }", "if (LANGS.includes(n)) LANG = n; } } catch { }")
s = rep(s, "const FLOOR_NAMES = ['Ground floor', 'First floor', 'Second floor', 'Roof'];", "const FLOOR_NAMES = ['Main house', 'Guest house & garage', 'Attefall house', 'The plot'];")
s = rep(s, "const ABOUT_CATS = ['Overview', 'Facades & exterior', 'Garden & pool', 'Materials & finishes', 'Dimensions & data'];",
        "const ABOUT_CATS = ['Overview', 'Facades & exterior', 'Garden & plot', 'Materials & finishes', 'Dimensions & data'];")
i, j = between(s, 'const PLANS = [', '];\n')
s = s[:i] + '''const PLANS = [
  { name: 'Main house', src: 'img/plan-huvudhus.jpg', note: 'Working drawing A2-2 (Jan Jansson ark., 2010): plan and sections. 21.18 × 5.38 m.' },
  { name: 'Guest house & garage', src: 'img/plan-garage.jpg', note: 'Drawing A3-1: guest cottage, workshop, storage and garage. 12.5 × 4.0 m.' },
  { name: 'Attefall house', src: 'img/plan-attefall.jpg', note: 'Building notice 2022 (Jörgen Åström ark.): two bedrooms and shower. 9.0 × 3.3 m.' },
  { name: 'The plot', src: 'img/plan-tomt.jpg', note: 'Site plan from the 2022 building notice.' },
''' + s[j:]
s = s.replace("t('Townhouse · El Terreno · Palma')", "t('Summer house · Hamra · Gotland')").replace("h('b', {}, 'Joan Miró 87')", "h('b', {}, 'Hulehällar 418D')").replace("h('h2', {}, 'Joan Miró 87')", "h('h2', {}, 'Hulehällar 418D')")
s = rep(s, "'You are the house book of Joan Miró 87, a townhouse in El Terreno, Palma de Mallorca. The person asking is '",
        "'You are the house book of Hulehällar 418D, a summer house in Hamra on southern Gotland, Sweden (main house, guest cottage with workshop and garage, and an attefall house). The person asking is '")
s = rep(s, "const AGENCY = { name: 'Your Agency',", "const AGENCY = { name: 'Westmans hus',")
s = rep(s, "const eur = n => Number(n).toLocaleString(LOC(), { style: 'currency', currency: 'EUR' });",
        "const eur = n => Number(n).toLocaleString(LOC(), { style: 'currency', currency: 'SEK', maximumFractionDigits: 0 });")
s = s.replace("label: 'Amount (€)'", "label: 'Amount (kr)'")

s = rep(s, "n.textContent = t('Pick a floor to jump to a room.');", "n.textContent = t('Pick a building to jump to a room.');")
# translations for the new interface words: "English": [sv, es, de]
extra = {
  'Main house': ['Huvudhuset', 'Casa principal', 'Haupthaus'], 'Guest house': ['Gäststugan', 'Casa de invitados', 'Gästehaus'],
  'Guest house & garage': ['Gäststuga och garage', 'Casa de invitados y garaje', 'Gästehaus und Garage'], 'Attefall': ['Attefall', 'Attefall', 'Attefall'],
  'Attefall house': ['Attefallshuset', 'Casa attefall', 'Attefallhaus'], 'The plot': ['Tomten', 'La parcela', 'Das Grundstück'], 'plot': ['tomten', 'parcela', 'Grundstück'],
  'Choose building': ['Välj byggnad', 'Elegir edificio', 'Gebäude wählen'], 'From the drive': ['Från uppfarten', 'Desde la entrada', 'Von der Einfahrt'],
  'South side': ['Södersidan', 'Lado sur', 'Südseite'], 'Trees': ['Träd', 'Árboles', 'Bäume'], 'Bike shed': ['Cykelförråd', 'Bicicletero', 'Fahrradschuppen'], 'Deck & pool': ['Trall & pool', 'Tarima y piscina', 'Deck & Pool'], 'Garage doors': ['Garageportar', 'Puertas del garaje', 'Garagentore'], 'Open': ['Öppna', 'Abrir', 'Öffnen'], 'Close': ['Stäng', 'Cerrar', 'Schließen'], 'Pool söder om huset': ['Pool söder om huset', 'Piscina al sur de la casa', 'Pool südlich vom Haus'], 'Bubbelpool vid däcket': ['Bubbelpool vid däcket', 'Jacuzzi junto a la terraza', 'Whirlpool am Deck'], 'Bubbelpool vid badtunnan': ['Bubbelpool vid badtunnan', 'Jacuzzi junto al barril', 'Whirlpool am Badezuber'], 'Glass house as built': ['Glashuset som det blir', 'La casa de cristal tal como será', 'Das Glashaus, wie es wird'], 'Off': ['Av', 'No', 'Aus'], 'Planned 2022': ['Planerat 2022', 'Previsto 2022', 'Geplant 2022'],
  'Summer house · Hamra · Gotland': ['Fritidshus · Hamra · Gotland', 'Casa de verano · Hamra · Gotland', 'Ferienhaus · Hamra · Gotland'],
  'Garden & plot': ['Gård och tomt', 'Jardín y parcela', 'Garten und Grundstück'],
  'Study / guest room': ['Arbets-/gästrum', 'Estudio / invitados', 'Arbeits-/Gästezimmer'], 'Storage': ['Förråd', 'Trastero', 'Abstellraum'],
  'Cloakroom': ['Kapprum', 'Guardarropa', 'Garderobe'], 'Laundry & plant room': ['Tvätt- och apparatrum', 'Lavadero y sala de máquinas', 'Wasch- und Technikraum'],
  'Passage': ['Passage', 'Pasillo', 'Flur'], 'Kitchen': ['Kök', 'Cocina', 'Küche'], 'Dining': ['Matplats', 'Comedor', 'Essplatz'], 'Living room': ['Vardagsrum', 'Salón', 'Wohnzimmer'],
  'Shower & WC': ['Dusch och wc', 'Ducha y WC', 'Dusche und WC'], 'Bedroom': ['Sovrum', 'Dormitorio', 'Schlafzimmer'], 'North bedroom': ['Sovrum norr', 'Dormitorio norte', 'Schlafzimmer Nord'], 'South bedroom': ['Sovrum söder', 'Dormitorio sur', 'Schlafzimmer Süd'], 'Hall & kitchenette': ['Hall & pentry', 'Recibidor y cocina office', 'Diele & Pantryküche'], 'Glazed veranda': ['Glasveranda', 'Veranda acristalada', 'Glasveranda'],
  'Guest cottage': ['Gäststuga', 'Casita de invitados', 'Gästehäuschen'], 'Workshop': ['Snickarbod', 'Taller', 'Werkstatt'], 'Storage & garage': ['Förråd och garage', 'Trastero y garaje', 'Lager und Garage'],
  'Bedroom north': ['Sovrum norr', 'Dormitorio norte', 'Schlafzimmer Nord'], 'Bedroom south': ['Sovrum söder', 'Dormitorio sur', 'Schlafzimmer Süd'],
  'Grill place': ['Grillplats', 'Barbacoa', 'Grillplatz'], 'Trampoline': ['Studsmatta', 'Cama elástica', 'Trampolin'], 'Limestone patio': ['Kalkstensplatta', 'Patio de piedra caliza', 'Kalksteinterrasse'],
  'Pick a building to jump to a room.': ['Välj en byggnad för att hoppa till ett rum.', 'Elige un edificio para ir a una estancia.', 'Wähle ein Gebäude, um zu einem Raum zu springen.'],
  'Deck': ['Trädäck', 'Terraza de madera', 'Holzdeck'], 'Entrance': ['Entré', 'Entrada', 'Eingang'],
}

# ---------------------------------------------------------------- UX layer (2026-10-18): fewer choices
# Nav: Hem · 3D · Bo här · Kontakt (+ Ägare for the owner). Rooms, How it works, Photos, Timeline and Documents
# are not tabs any more: rooms live in the 3D panel, how-to in "Bo här", the rest under "Ägare".
s = rep(s, '<button role="tab" data-tab="overview" aria-selected="true">Overview</button>', '<button role="tab" data-tab="overview" aria-selected="true">Home</button>')
s = rep(s, '>Home admin</button>', '>Owner</button>')
s = rep(s, '>3D &amp; plans</button>', '>3D</button>')
s = rep(s, "timelineTab.textContent = t('Timeline'); adminTab.textContent = t('Home admin');", "timelineTab.textContent = t('Timeline'); adminTab.textContent = t('Owner');")
s = rep(s, "guideTab.textContent = t(viewMode === 'buyer' ? 'Neighbourhood' : 'Guide');", "guideTab.textContent = t('Live here');")
# Gotland opens in the 3D model too (Gustav 24 Oct: 'utgå från 3D-modellen'); Home is one tab away
s = rep(s, "  const pages = { overview: pageOverview, rooms: pageRooms, how: pageHow, guide: pageGuide, timeline: pageTimeline, admin: pageAdmin, contacts: pageContacts, photos: pagePhotos, docs: pageDocs };",
        "  const pages = { overview: pageHome, rooms: pageRooms, how: pageStay, guide: pageStay, timeline: pageOwner, admin: pageOwner, contacts: pageContacts, photos: pageHome, docs: pageOwner };")
s = rep(s, '</style>', r"""
/* ---------- UX layer: fewer choices ---------- */
.tabs [data-tab="rooms"], .tabs [data-tab="how"], .tabs [data-tab="photos"], .tabs [data-tab="timeline"], .tabs [data-tab="docs"] { display: none !important; }
.navrow, .sun, .hint { display: none !important; }
.go3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 12px; }
.go3 button { all: unset; box-sizing: border-box; cursor: pointer; display: grid; gap: 6px; align-content: start; padding: 22px 22px 20px; border: 1px solid var(--line); background: var(--paper, #fff); min-height: 132px; transition: border-color .15s, transform .15s; }
.go3 button:hover { border-color: var(--ink); transform: translateY(-1px); }
.go3 button:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
.go3 b { font-size: 20px; font-weight: 400; }
.go3 span { font-size: 14px; color: var(--muted); line-height: 1.45; }
.go3 i { font-style: normal; font-size: 11px; letter-spacing: .2em; text-transform: uppercase; color: var(--ink); margin-top: auto; padding-top: 10px; }
.keyrow { display: flex; flex-wrap: wrap; gap: 8px 22px; font-size: 14px; }
.keyrow b { font-weight: 500; }
.stay { display: grid; gap: 34px; max-width: 760px; margin-inline: auto; width: 100%; }
.stay h3 { margin-bottom: 4px; }
.qa { border-top: 1px solid var(--line); }
.qa:last-child { border-bottom: 1px solid var(--line); }
.qa summary { list-style: none; cursor: pointer; display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: baseline; padding: 15px 2px; font-size: 17px; }
.qa summary::-webkit-details-marker { display: none; }
.qa summary::after { content: '+'; font-size: 20px; line-height: 1; color: var(--muted); }
.qa[open] summary::after { content: '–'; }
.qa summary small { display: block; font-size: 13.5px; color: var(--muted); margin-top: 3px; font-weight: 300; }
.qa .ans { padding: 0 2px 18px; display: grid; gap: 10px; font-size: 15px; line-height: 1.6; max-width: 64ch; }
.qa .ans p { margin: 0; white-space: pre-line; }
.qa .ans dl { display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; margin: 0; font-size: 14px; }
.qa .ans dt { color: var(--muted); }
.qa .ans dd { margin: 0; }
.ownerseg { display: inline-flex; border: 1px solid var(--line); margin: 0 auto; }
.ownerseg button { background: none; border: 0; padding: 9px 16px; font: inherit; font-size: 11px; letter-spacing: .16em; text-transform: uppercase; cursor: pointer; color: var(--muted); }
.ownerseg button[aria-pressed="true"] { background: var(--ink); color: var(--paper, #fff); }
</style>""", 1)
s = rep(s, "// ---------- timeline: building, machines, furniture, renovations, repairs, service ----------", r"""// ---------- UX layer: Home, Live here, Owner ----------
function pageHome() {
  const ov = byId('overview') || { body: '', images: [] };
  const intro = (ov.body || '').split('\n\n')[0];
  const keys = contactRows().filter(r => r.key);
  const up = ownerMode ? (privTables.upcoming || []).filter(r => !r.done).sort(byDate).slice(0, 4) : [];
  const card = (title, text, cta, fn) => h('button', { type: 'button', onclick: fn }, h('b', {}, t(title)), h('span', {}, t(text)), h('i', {}, t(cta) + ' →'));
  return h('div', { class: 'page' },
    h('div', { class: 'hero', style: 'cursor:pointer', onclick: () => showTab('model'), title: t('The house in 3D') }, h('img', { src: 'img/hero-3d.jpg', alt: t('The house in 3D') })),
    intro ? h('p', { class: 'lead', style: 'margin-inline:auto;text-align:center' }, intro) : null,
    h('div', { class: 'go3' },
      card('Live here', 'Rubbish, firewood, the grill, the bikes – everything for your stay.', 'Open the guide', () => showTab('guide')),
      card('The house in 3D', 'Walk around the plot, open the buildings and see every room.', 'Explore', () => showTab('model')),
      card('Who to call', keys.length ? keys.map(r => r.role).slice(0, 3).join(' · ') : 'Emergency numbers and tradespeople.', 'Contacts', () => showTab('contacts'))),
    keys.length ? h('section', { class: 'sec' }, h('h3', {}, t('Key numbers')), h('div', { class: 'keyrow' }, keys.map(r => h('span', {}, h('b', {}, t(r.role || '')), ' ', phoneEl(r.phone))))) : null,
    up.length ? h('section', { class: 'sec' }, h('div', { class: 'sechead' }, h('h3', {}, t('Coming up')), h('button', { class: 'wbtn small', type: 'button', onclick: () => showTab('admin') }, t('All tasks'))),
      h('ul', { class: 'uplist' }, up.map(r => h('li', { class: dueClass(r.date) }, h('time', {}, fmtDate(r.date)), h('span', {}, t(r.task || '')))))) : null);
}
// "Live here": every stay and how-to article in the order a visit happens, one line to scan, open for the detail
const STAY_GROUPS = [
  ['When you arrive', ['s-valkommen', 's-dorrar', 's-morklagg']],
  ['During your stay', ['s-sopor', 's-basvaror', 's-flugor', 's-tvatt', 's-vattning', 's-vinkyl', 's-leksaker', 'h-tv', 'h-disk']],
  ['Fire, grill and bikes', ['h-eldstad', 'h-ofyr', 'h-pizza', 'h-kolgrill', 'h-cyklar', 'h-ladcykel', 's-badkar']],
  ['Good to know', ['s-privat', 'h-bergvarme', 'h-vatten', 's-samf']],
];
function pageStay() {
  const all = articles().filter(e => e.cat === 'Your stay' || e.cat === 'How it works'), used = new Set();
  const qa = e => {
    used.add(e.id);
    const first = e.how?.use || (e.body || '').split('\n')[0];
    const more = e.how ? HOW.filter(([k]) => k !== 'use' && e.how[k]) : [];
    return h('details', { class: 'qa' }, h('summary', {}, h('span', {}, e.title, h('small', {}, first.length > 110 ? first.slice(0, 106).replace(/\s+\S*$/, '') + '…' : first))),
      h('div', { class: 'ans' }, e.how ? h('p', {}, e.how.use || '') : h('p', {}, e.body || ''),
        more.length ? h('dl', {}, more.map(([k, l]) => [h('dt', {}, t(l)), h('dd', {}, e.how[k])])) : null,
        e.images?.[0] ? h('img', { src: imgSrc(e.images[0]), alt: e.images[0].caption || '', style: 'max-width:100%;cursor:zoom-in', onclick: () => lightbox(e.images[0]) }) : null));
  };
  const groups = STAY_GROUPS.map(([g, ids]) => [g, ids.map(id => all.find(e => e.id === id)).filter(Boolean)]);
  const rest = all.filter(e => !STAY_GROUPS.some(([, ids]) => ids.includes(e.id)));
  if (rest.length) groups.push(['Good to know', rest]);
  return h('div', { class: 'page' }, h('h2', {}, t('Live here')), h('p', { class: 'lead' }, t('Everything for your stay, in the order you need it. Tap a line to open it.')),
    searchBox('psearch'),
    h('div', { class: 'stay' }, groups.filter(([, l]) => l.length).map(([g, l]) => h('section', {}, h('h3', { class: 'eyebrow' }, t(g)), l.map(qa)))));
}
// "Owner": tasks and money, documents and the timeline behind one switch (owner only)
let ownerPart = 'admin';
function pageOwner() {
  if (!ownerMode) return pageHome();
  const parts = [['admin', 'Tasks & costs'], ['docs', 'Documents'], ['timeline', 'Timeline']];
  const body = ownerPart === 'docs' ? pageDocs() : ownerPart === 'timeline' ? pageTimeline() : pageAdmin();
  return h('div', {}, h('div', { style: 'display:flex;justify-content:center;padding-top:26px' }, h('div', { class: 'ownerseg', role: 'group' }, parts.map(([k, n]) => h('button', { type: 'button', 'aria-pressed': String(ownerPart === k), onclick: () => { ownerPart = k; render(); } }, t(n))))), body);
}
// ---------- timeline: building, machines, furniture, renovations, repairs, service ----------""")
extra.update({
  'Home': ['Hem', 'Inicio', 'Start'], 'Owner': ['Ägare', 'Propietario', 'Eigentümer'], 'Live here': ['Bo här', 'Vivir aquí', 'Hier wohnen'],
  'Rubbish, firewood, the grill, the bikes – everything for your stay.': ['Sopor, ved, grillen, cyklarna – allt för vistelsen.', 'Basura, leña, la barbacoa, las bicis: todo para tu estancia.', 'Müll, Holz, Grill, Fahrräder – alles für den Aufenthalt.'],
  'Open the guide': ['Öppna guiden', 'Abrir la guía', 'Zum Leitfaden'], 'The house in 3D': ['Huset i 3D', 'La casa en 3D', 'Das Haus in 3D'],
  'Walk around the plot, open the buildings and see every room.': ['Gå runt på tomten, öppna husen och se varje rum.', 'Recorre la parcela, abre los edificios y ve cada estancia.', 'Über das Grundstück gehen, die Häuser öffnen, jeden Raum sehen.'],
  'Explore': ['Utforska', 'Explorar', 'Erkunden'], 'Who to call': ['Vem ringer man', 'A quién llamar', 'Wen anrufen'],
  'Emergency numbers and tradespeople.': ['Nödnummer och hantverkare.', 'Emergencias y profesionales.', 'Notrufnummern und Handwerker.'], 'Contacts': ['Kontakter', 'Contactos', 'Kontakte'],
  'When you arrive': ['När ni kommer', 'Al llegar', 'Bei der Ankunft'], 'During your stay': ['Under vistelsen', 'Durante la estancia', 'Während des Aufenthalts'],
  'Fire, grill and bikes': ['Eld, grill och cyklar', 'Fuego, barbacoa y bicis', 'Feuer, Grill und Fahrräder'], 'Good to know': ['Bra att veta', 'Bueno saber', 'Gut zu wissen'],
  'Everything for your stay, in the order you need it. Tap a line to open it.': ['Allt för vistelsen, i den ordning ni behöver det. Tryck på en rad för att öppna den.', 'Todo para tu estancia, en el orden en que lo necesitas. Toca una línea para abrirla.', 'Alles für den Aufenthalt, in der Reihenfolge, in der ihr es braucht. Tippt auf eine Zeile.'],
  'Tasks & costs': ['Att göra och kostnader', 'Tareas y costes', 'Aufgaben und Kosten'], 'Documents': ['Dokument', 'Documentos', 'Dokumente'], 'Timeline': ['Tidslinje', 'Cronología', 'Zeitleiste'],
})

s = rep(s, 'const I18N = {\n', 'const I18N = {\n' + ''.join(f'  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n' for k, v in extra.items()))

# ---------------------------------------------------------------- the snapshot: what signed-out visitors and guests see
snap = {'articles': content['articles'], 'contacts': [c for c in content['contacts'] if c.get('public')],
        'places': content.get('places', []),
        'timeline': [{'date': r['date'], 'approx': False, 'kind': 'Built', 'title': r['what'], 'note': '', 'who': '', 'public': True} for r in content['timeline']]}
i, j = between(s, '<script type="application/json" id="book-snapshot">', '</script>')
s = s[:i] + '<script type="application/json" id="book-snapshot">' + json.dumps(snap, ensure_ascii=False).replace('</', '<\\/') + s[j:]
