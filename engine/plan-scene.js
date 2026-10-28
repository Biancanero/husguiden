// ======================================================================
//  Husguiden – the generic 3D scene, built from a house's plan.json
//  (tools/plan_book.py wraps this file in a scope inside the house-book shell; PLAN, world and trees exist already)
//
//  Coordinates: metres, x = east, z = south, y = up. Origin = the point in house.json (lat/lng).
//  Every building is a rectangle 0..w (east) × 0..d (south) in its own frame, placed at (x, z), turned by rot degrees.
// ======================================================================
let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
function canvasTex(w, h, draw, rep) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  if (rep) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...rep); }
  return t;
}
const std = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: .9, ...o });
const wrapTex = t => (t.wrapS = t.wrapT = THREE.RepeatWrapping, t);
const seamTex = wrapTex(canvasTex(64, 64, (g, w, h) => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); g.fillStyle = '#c9cdd0'; g.fillRect(0, 0, 4, h); g.fillStyle = '#eef0f1'; g.fillRect(4, 0, 2, h); }));
const boardTex = wrapTex(canvasTex(64, 128, (g, w, h) => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 16) { g.fillStyle = 'rgba(0,0,0,.35)'; g.fillRect(0, y, w, 2); } }));
const vpanelTex = wrapTex(canvasTex(128, 64, (g, w, h) => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 32) { g.fillStyle = 'rgba(0,0,0,.22)'; g.fillRect(x, 0, 2, h); } }));
const tileRoofTex = wrapTex(canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#fff'; g.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 16) { g.fillStyle = 'rgba(0,0,0,.28)'; g.fillRect(0, y + 13, w, 3); for (let x = (y / 16 % 2) * 8; x < w; x += 16) { g.fillStyle = 'rgba(0,0,0,.12)'; g.fillRect(x, y, 2, 14); } } }));
const oakTex = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = '#c9ae86'; g.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 16) { let x = -rnd() * 120; while (x < w) { const L = 70 + rnd() * 110; g.fillStyle = `hsl(${32 + rnd() * 6},${30 + rnd() * 12}%,${62 + rnd() * 10}%)`; g.fillRect(x, y, L - 1, 15); x += L; } }
}, [1, 1]);
const tileTex = canvasTex(128, 128, (g, w, h) => { g.fillStyle = '#d9d6cf'; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(60,58,54,.35)'; g.lineWidth = 2; for (let i = 0; i <= w; i += 64) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, h); g.moveTo(0, i); g.lineTo(w, i); g.stroke(); } }, [1, 1]);
const gravelTex = canvasTex(256, 256, (g, w, h) => {
  g.fillStyle = '#cfc9bd'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 2600; i++) { const r = 1 + rnd() * 3.2; g.fillStyle = `hsl(${35 + rnd() * 20},${6 + rnd() * 8}%,${62 + rnd() * 30}%)`; g.beginPath(); g.ellipse(rnd() * w, rnd() * h, r, r * (.6 + rnd() * .4), rnd() * 3, 0, 7); g.fill(); }
}, [1, 1]);
const grassTex = canvasTex(512, 512, (g, w, h) => {
  g.fillStyle = '#8f9a6a'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 9000; i++) { const s = 1 + rnd() * 3; g.fillStyle = `hsl(${70 + rnd() * 30},${18 + rnd() * 20}%,${36 + rnd() * 22}%)`; g.fillRect(rnd() * w, rnd() * h, s, s); }
}, [30, 30]);

const C = PLAN.colors || {};
const M = {
  facade: std(C.facade || '#e4dfd5', { roughness: .95 }),
  boards: std(C.facade || '#8e3b2c', { map: boardTex, roughness: .95 }),
  inner: std(C.inner || '#efebe4', { roughness: .95 }),
  plinth: std('#bdb8ae'),
  frame: std(C.frames || '#f1efe9', { roughness: .55 }),
  door: std(C.door || '#3b3a38', { roughness: .6 }),
  glass: new THREE.MeshPhysicalMaterial({ color: '#cfe0e4', roughness: .05, metalness: .1, transparent: true, opacity: .26, depthWrite: false }),
  roofTile: std(C.roof || '#6e3b2f', { map: tileRoofTex, roughness: .85 }),
  roofMetal: std(C.roof || '#3d4042', { map: seamTex, metalness: .45, roughness: .45 }),
  roofFelt: std(C.roof || '#3a3a3a', { roughness: .95 }),
  roofEdge: std('#2f3133', { roughness: .7 }),
  slab: std('#d8d3ca', { roughness: .95 }),
  oak: std('#c9ae86', { map: oakTex, roughness: .7 }),
  tile: std('#ffffff', { map: tileTex, roughness: .5 }),
  concrete: std('#a9a59e', { roughness: .95 }),
  gravel: std('#d8d2c6', { map: gravelTex, roughness: 1 }),
  grass: std('#ffffff', { map: grassTex, roughness: 1 }),
  deck: std('#a39888', { map: boardTex, roughness: .95 }),
  water: new THREE.MeshPhysicalMaterial({ color: '#5fa9b8', roughness: .08, transmission: .3, transparent: true, opacity: .85 }),
  white: std('#f3f1ec', { roughness: .6 }), black: std('#2a2927', { roughness: .6 }),
  wood: std('#b8956a', { roughness: .7 }), sofa: std('#b9b8b4'), linen: std('#f1eee6'), steel: std('#9a9c9d', { metalness: .6, roughness: .35 }),
  nb: new THREE.MeshStandardMaterial({ color: '#efece6', transparent: true, opacity: .55, roughness: .9 }),
  ghost: new THREE.MeshStandardMaterial({ color: '#9fc3d6', transparent: true, opacity: .32, roughness: .4, depthWrite: false }),
  leaf: std('#5f7446', { roughness: .95 }), bark: std('#6b5847'),
};
const FLOORMAT = { oak: M.oak, wood: M.oak, parquet: M.oak, tile: M.tile, klinker: M.tile, stone: M.tile, concrete: M.concrete, betong: M.concrete };

const boxGeo = new THREE.BoxGeometry(1, 1, 1);
function box(g, x1, x2, y1, y2, z1, z2, mat, cast = true) {
  const m = new THREE.Mesh(boxGeo, mat);
  m.scale.set(Math.max(.002, Math.abs(x2 - x1)), Math.max(.002, Math.abs(y2 - y1)), Math.max(.002, Math.abs(z2 - z1)));
  m.position.set((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2);
  m.castShadow = cast && !mat.transparent; m.receiveShadow = true; g.add(m); return m;
}
// textured box: textures repeat per metre on the largest faces
function tbox(g, x1, x2, y1, y2, z1, z2, mat, per = [1, 1]) {
  const geo = new THREE.BoxGeometry(Math.abs(x2 - x1), Math.abs(y2 - y1), Math.abs(z2 - z1));
  const uv = geo.attributes.uv, pos = geo.attributes.position, nrm = geo.attributes.normal;
  for (let i = 0; i < uv.count; i++) {
    const nx = Math.abs(nrm.getX(i)), ny = Math.abs(nrm.getY(i)), px = pos.getX(i), py = pos.getY(i), pz = pos.getZ(i);
    if (ny > .5) uv.setXY(i, px / per[0], pz / per[1]); else if (nx > .5) uv.setXY(i, pz / per[0], py / per[1]); else uv.setXY(i, px / per[0], py / per[1]);
  }
  const m = new THREE.Mesh(geo, mat); m.position.set((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2);
  m.castShadow = !mat.transparent; m.receiveShadow = true; g.add(m); return m;
}
const cyl = (g, x, y, z, r, h, mat, seg = 20) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), mat); m.position.set(x, y + h / 2, z); m.castShadow = m.receiveShadow = true; g.add(m); return m; };
// a mesh from triangles given as [[x, y, z], …] (three points each)
function tris(g, list, mat) {
  const p = []; list.forEach(t => t.forEach(v => p.push(...v)));
  const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
  // planar UVs per metre, from the two largest axes of each face's normal
  geo.computeVertexNormals();
  const n = geo.attributes.normal, uv = [];
  for (let i = 0; i < p.length / 3; i++) {
    const ax = Math.abs(n.getX(i)), ay = Math.abs(n.getY(i)), az = Math.abs(n.getZ(i)), x = p[i * 3], y = p[i * 3 + 1], z = p[i * 3 + 2];
    uv.push(...(ay >= ax && ay >= az ? [x, z] : ax >= az ? [z, y + (ay > .2 ? z * ay : 0)] : [x, y + (ay > .2 ? x * ay : 0)]));
  }
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  const m = new THREE.Mesh(geo, mat); m.castShadow = m.receiveShadow = true; g.add(m); return m;
}
const quad = (a, b, c, d) => [[a, b, c], [a, c, d]];

// ---------- registries (the names the house-book shell expects) ----------
const groups = {}, cuttable = [], furniture = [], roofs = {}, ceilings = {}, HROOMS = [];
const F = m => (furniture.push(m), m);
const site = new THREE.Group(), yard = new THREE.Group(), plotG = new THREE.Group(), nbG = new THREE.Group(), canopy = new THREE.Group();
const plannedG = new THREE.Group(), glassG = new THREE.Group();
world.add(site, yard, plotG, nbG, canopy, plannedG, glassG);
plannedG.visible = false; glassG.visible = false;
const BIKES = [], POOLS = Object.assign([], { clear() { } });
function setGarage() { }

/* Walls with openings. axis 'x': the wall runs along x from a1 to a2 and is c1..c2 thick in z; axis 'z' the reverse.
   ops: { a, b, lo, hi, kind: 'win' | 'door' | 'open', slide } – an opening with lo 0 can be walked through. */
function wall(g, axis, a1, a2, c1, c2, h, ops, mats) {
  const [outMat, inMat] = Array.isArray(mats) ? mats : [mats, mats];
  const skins = outMat === inMat ? [[c1, c2, outMat]] : [[c1, (c1 + c2) / 2, outMat], [(c1 + c2) / 2, c2, inMat]];
  const B = (p1, p2, y1, y2) => { if (p2 - p1 < .005 || y2 - y1 < .005) return; for (const [d1, d2, mat] of skins) cuttable.push({ m: axis === 'x' ? tbox(g, p1, p2, y1, y2, d1, d2, mat) : tbox(g, d1, d2, y1, y2, p1, p2, mat), y1, y2 }); };
  const cm = (c1 + c2) / 2;
  const G = (p1, p2, y1, y2, mat, t = .025, off = 0) => axis === 'x' ? box(g, p1, p2, y1, y2, cm + off - t, cm + off + t, mat, mat !== M.glass) : box(g, cm + off - t, cm + off + t, y1, y2, p1, p2, mat, mat !== M.glass);
  const list = [...ops].filter(o => o.b > o.a).sort((p, q) => p.a - q.a); let at = a1;
  for (const o of list) {
    if (o.a > at) B(at, o.a, 0, h);
    if (o.lo > 0) B(o.a, o.b, 0, o.lo);
    if (o.hi < h) B(o.a, o.b, o.hi, h);
    const f = .06, kind = o.kind || (o.lo > 0 ? 'win' : 'door');
    if (kind !== 'open') {
      G(o.a, o.a + f, o.lo, o.hi, M.frame, .05); G(o.b - f, o.b, o.lo, o.hi, M.frame, .05); G(o.a, o.b, o.hi - f, o.hi, M.frame, .05);
      if (o.lo > 0) G(o.a, o.b, o.lo, o.lo + f, M.frame, .05);
      if (kind === 'door' && !o.glass && !o.slide) { const leaf = G(o.a + f, o.b - f, o.lo, o.hi - f, o.outer ? M.door : M.white, .022); leaf.userData.pass = true; }
      else {
        G(o.a, o.b, o.lo, o.hi, M.glass, .012).userData.pass = kind === 'door';
        if (o.b - o.a > 1.3 && kind === 'win') { const mid = (o.a + o.b) / 2; G(mid - .03, mid + .03, o.lo, o.hi, M.frame, .04); }
      }
      if (kind === 'win') {   // a window sill outside
        const s = .14; axis === 'x' ? box(g, o.a - .03, o.b + .03, o.lo - .04, o.lo, c1 - s * (o.side < 0 ? 1 : 0), c2 + s * (o.side > 0 ? 1 : 0), M.frame) : box(g, c1 - s * (o.side < 0 ? 1 : 0), c2 + s * (o.side > 0 ? 1 : 0), o.lo - .04, o.lo, o.a - .03, o.b + .03, M.frame);
      }
    }
    at = Math.max(at, o.b);
  }
  if (at < a2) B(at, a2, 0, h);
}
const fmtA = n => (Math.round(n * 10) / 10).toString();

// ---------- furniture from the room's name (sv / en / es / de) ----------
const KIND = [
  ['bed', /sov|bed|dorm|schlaf|master|gäst ?rum|guest ?room/i], ['bath', /bad|bath|dusch|shower|wc|toa|aseo|baño/i],
  ['kitchen', /kök|kitchen|cocina|küche|pentry/i], ['living', /vardag|living|salón|salon|wohn|allrum|family|tv/i],
  ['dining', /mat|dining|comedor|ess/i], ['laundry', /tvätt|laundry|lavad|wasch/i], ['study', /kontor|arbets|study|office|estudio|büro/i],
];
const kindOf = (name, k) => k || (KIND.find(([, re]) => re.test(name)) || [''])[0];
function furnish(g, kind, x1, x2, z1, z2) {
  const w = x2 - x1, d = z2 - z1, cx = (x1 + x2) / 2, cz = (z1 + z2) / 2, along = w >= d;
  if (kind === 'bed' && w > 2 && d > 2) {
    const bw = Math.min(1.6, (along ? d : w) - .8) > 1.2 ? 1.6 : .9;
    // head against the wall furthest north (or west), centred
    if (along) { F(box(g, x1 + .05, x1 + 2.05, 0, .45, cz - bw / 2, cz + bw / 2, M.linen)); F(box(g, x1 + .05, x1 + .12, 0, 1.0, cz - bw / 2 - .05, cz + bw / 2 + .05, M.wood)); }
    else { F(box(g, cx - bw / 2, cx + bw / 2, 0, .45, z1 + .05, z1 + 2.05, M.linen)); F(box(g, cx - bw / 2 - .05, cx + bw / 2 + .05, 0, 1.0, z1 + .05, z1 + .12, M.wood)); }
  } else if (kind === 'living' && w > 2.6 && d > 2.6) {
    if (along) { F(box(g, cx - 1.1, cx + 1.1, 0, .42, z2 - 1.0, z2 - .1, M.sofa)); F(box(g, cx - 1.1, cx + 1.1, .42, .8, z2 - .3, z2 - .1, M.sofa)); F(box(g, cx - .55, cx + .55, 0, .4, z2 - 1.9, z2 - 1.3, M.wood)); }
    else { F(box(g, x2 - 1.0, x2 - .1, 0, .42, cz - 1.1, cz + 1.1, M.sofa)); F(box(g, x2 - .3, x2 - .1, .42, .8, cz - 1.1, cz + 1.1, M.sofa)); F(box(g, x2 - 1.9, x2 - 1.3, 0, .4, cz - .55, cz + .55, M.wood)); }
  } else if (kind === 'kitchen' && w > 1.8 && d > 1.6) {
    // counter along the north (or west) wall with a worktop, wall cabinets above
    if (along) { box(g, x1 + .02, x2 - .02, 0, .86, z1 + .02, z1 + .62, M.white); box(g, x1 + .02, x2 - .02, .86, .9, z1, z1 + .64, M.black); box(g, x1 + .02, x2 - .02, 1.5, 2.2, z1 + .02, z1 + .37, M.white); }
    else { box(g, x1 + .02, x1 + .62, 0, .86, z1 + .02, z2 - .02, M.white); box(g, x1, x1 + .64, .86, .9, z1 + .02, z2 - .02, M.black); box(g, x1 + .02, x1 + .37, 1.5, 2.2, z1 + .02, z2 - .02, M.white); }
    if (w > 3 && d > 3) dining(g, cx, cz + (along ? .5 : 0), along);
  } else if (kind === 'dining' && w > 2.2 && d > 2.2) dining(g, cx, cz, along);
  else if (kind === 'bath' && w > 1 && d > 1) {
    F(box(g, x1 + .1, x1 + .5, 0, .42, z1 + .1, z1 + .65, M.white));                          // wc
    F(box(g, x2 - .55, x2 - .05, .78, .86, z1 + .1, z1 + .55, M.white));                       // basin
    if (w * d > 4) box(g, x2 - .95, x2 - .05, 0, .04, z2 - .95, z2 - .05, M.tile);            // shower tray
  } else if (kind === 'laundry' && w > 1.2) { F(box(g, x1 + .05, x1 + .65, 0, .85, z1 + .05, z1 + .65, M.white)); F(box(g, x1 + .7, x1 + 1.3, 0, .85, z1 + .05, z1 + .65, M.white)); }
  else if (kind === 'study' && w > 1.8) { F(box(g, x1 + .1, x1 + 1.5, .72, .76, z1 + .1, z1 + .8, M.wood)); F(box(g, x1 + .5, x1 + 1.0, 0, .48, z1 + .9, z1 + 1.4, M.black)); }
}
function dining(g, cx, cz, along) {
  const [hw, hd] = along ? [.9, .45] : [.45, .9];
  F(box(g, cx - hw, cx + hw, .72, .76, cz - hd, cz + hd, M.wood));
  for (const [sx, sz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) F(box(g, cx + sx * hw * .5 - .03, cx + sx * hw * .5 + .03, 0, .72, cz + sz * hd * .5 - .03, cz + sz * hd * .5 + .03, M.wood));
  const chairs = along ? [[-.5, -hd - .3], [.5, -hd - .3], [-.5, hd + .3], [.5, hd + .3]] : [[-hw - .3, -.5], [-hw - .3, .5], [hw + .3, -.5], [hw + .3, .5]];
  for (const [dx, dz] of chairs) F(box(g, cx + dx - .22, cx + dx + .22, 0, .46, cz + dz - .22, cz + dz + .22, M.wood));
}

// ---------- roofs ----------
const ROOFMAT = { tile: () => M.roofTile, tegel: () => M.roofTile, metal: () => M.roofMetal, plåt: () => M.roofMetal, felt: () => M.roofFelt, papp: () => M.roofFelt };
function roof(g, b, y0) {
  const R = b.roof || { type: 'flat' }, w = b.w, d = b.d, o = R.overhang ?? (R.type === 'flat' ? 0 : .4), t = .18;
  const mat = (ROOFMAT[R.material] || ROOFMAT[R.type === 'flat' ? 'felt' : 'tile'])();
  const rg = new THREE.Group(); g.add(rg); roofs[b.id] = rg;
  const tan = Math.tan((R.pitch ?? (R.type === 'mono' ? 8 : 27)) * Math.PI / 180);
  if (R.type === 'flat') {
    box(rg, 0, w, y0, y0 + .25, 0, d, M.slab); const p = R.parapet ?? .5, s = .2;
    if (p > 0) { box(rg, 0, w, y0, y0 + .25 + p, 0, s, M.facade); box(rg, 0, w, y0, y0 + .25 + p, d - s, d, M.facade); box(rg, 0, s, y0, y0 + .25 + p, 0, d, M.facade); box(rg, w - s, w, y0, y0 + .25 + p, 0, d, M.facade); }
    return y0 + .25 + p;
  }
  // in the roof's own frame the ridge runs along u (length L) and the slopes fall towards v = 0 and v = S
  const alongX = (R.ridge || (w >= d ? 'x' : 'z')) === 'x', L = alongX ? w : d, S = alongX ? d : w;
  const P = (u, y, v) => alongX ? [u, y, v] : [v, y, u];
  const u1 = -o, u2 = L + o, v1 = -o, v2 = S + o, yE = y0 - o * tan;
  const fill = [], ends = [];
  if (R.type === 'mono') {   // one slope, high at v = 0 (R.high: 'n' | 's' | 'e' | 'w' turns it)
    const flip = R.high === 's' || R.high === 'e', hY = y0 + S * tan;
    const yv = v => flip ? y0 + v * tan : hY - v * tan;
    fill.push(...quad(P(u1, yv(v1), v1), P(u2, yv(v1), v1), P(u2, yv(v2), v2), P(u1, yv(v2), v2)));
    // gable triangles + the high wall strip on the walls
    for (const u of [0, L]) ends.push(...quad(P(u, y0, 0), P(u, y0, S), P(u, yv(S), S), P(u, yv(0), 0)));
    ends.push(...quad(P(0, y0, flip ? S : 0), P(L, y0, flip ? S : 0), P(L, hY, flip ? S : 0), P(0, hY, flip ? S : 0)));
  } else {
    const yR = y0 + S / 2 * tan, hip = R.type === 'hip' ? Math.min(S / 2, L / 2) : 0;
    const r1 = hip, r2 = L - hip;   // ridge ends
    fill.push(...quad(P(u1 + (hip ? -0 : 0), yE, v1), P(u2, yE, v1), P(r2 + (hip ? 0 : o), yR, S / 2), P(r1 - (hip ? 0 : o), yR, S / 2)));
    fill.push(...quad(P(u2, yE, v2), P(u1, yE, v2), P(r1 - (hip ? 0 : o), yR, S / 2), P(r2 + (hip ? 0 : o), yR, S / 2)));
    if (hip) { fill.push([P(u1, yE, v2), P(u1, yE, v1), P(r1, yR, S / 2)], [P(u2, yE, v1), P(u2, yE, v2), P(r2, yR, S / 2)]); }
    else for (const u of [0, L]) ends.push([P(u, y0, 0), P(u, y0, S), P(u, yR, S / 2)]);
  }
  const m = tris(rg, fill, mat); m.material.side = THREE.DoubleSide;
  if (ends.length) { const e = tris(rg, ends, M.facade); e.material = M.facade.clone(); e.material.side = THREE.DoubleSide; }
  return y0 + S / 2 * tan;
}

// ---------- buildings ----------
const PSL = PLAN.slots;
// which of the shell's buttons a building's storey belongs to: its own 'building' button, else the 'storey' button of that level
const slotOf = (bid, k) => { let i = PSL.findIndex(p => p.type === 'building' && p.building === bid); if (i >= 0) return i; i = PSL.findIndex((p, n) => (p.type || 'storey') === 'storey' && (p.level ?? n) === k); return i >= 0 ? i : 0; };
const STOREYS = {};          // 'buildingId:level' → its group
const BASEY = {};            // level → floor height above the ground
for (const b of PLAN.buildings) {
  const g = new THREE.Group(); g.position.set(b.x || 0, 0, b.z || 0); g.rotation.y = -(b.rot || 0) * Math.PI / 180; g.userData.key = b.id; world.add(g); groups[b.id] = g;
  const T = b.wall ?? .3, plinth = b.floor ?? .15, sts = b.storeys || [];
  const outer = b.cladding === 'boards' ? M.boards : M.facade;
  let y = plinth;
  box(g, -.05, b.w + .05, 0, plinth, -.05, b.d + .05, M.plinth);
  sts.forEach((st, k) => {
    const H = st.height ?? PLAN.storey_height ?? 2.7, sg = new THREE.Group(); sg.position.y = y; sg.userData.key = b.id; g.add(sg); STOREYS[b.id + ':' + k] = sg;
    if (BASEY[k] === undefined) BASEY[k] = y;
    tbox(sg, 0, b.w, -.2, 0, 0, b.d, M.slab);   // the floor slab
    // rooms: floor, label, furniture
    for (const r of st.rooms || []) {
      const fm = FLOORMAT[r.floor] || (kindOf(r.name, r.kind) === 'bath' || kindOf(r.name, r.kind) === 'laundry' ? M.tile : M.oak);
      const f = tbox(sg, r.x1, r.x2, -.01, .012, r.z1, r.z2, fm, fm === M.oak ? [2.5, 2.5] : [1, 1]); f.castShadow = false; f.userData.pass = true;
      HROOMS.push({ g: sg, x: r.lx ?? (r.x1 + r.x2) / 2, z: r.lz ?? (r.z1 + r.z2) / 2, b: slotOf(b.id, k), name: r.name, area: r.area ?? fmtA((r.x2 - r.x1) * (r.z2 - r.z1)) });
      if (r.furnish !== false) furnish(sg, kindOf(r.name, r.kind), r.x1, r.x2, r.z1, r.z2);
    }
    // outer walls with their openings; a = distance from the west end (N/S sides) or the north end (E/W sides)
    const ops = side => (st.openings || []).filter(o => o.side === side).map(o => ({ a: o.a, b: o.a + o.w, lo: o.sill ?? (o.kind === 'door' ? 0 : .9), hi: (o.sill ?? (o.kind === 'door' ? 0 : .9)) + (o.h ?? (o.kind === 'door' ? 2.1 : 1.3)), kind: o.kind, slide: o.slide, glass: o.glass, outer: true, side: side === 'N' || side === 'W' ? -1 : 1 }));
    wall(sg, 'x', 0, b.w, 0, T, H, ops('N'), [outer, M.inner]);
    wall(sg, 'x', 0, b.w, b.d - T, b.d, H, ops('S'), [M.inner, outer]);
    wall(sg, 'z', T, b.d - T, 0, T, H, ops('W'), [outer, M.inner]);
    wall(sg, 'z', T, b.d - T, b.w - T, b.w, H, ops('E'), [M.inner, outer]);
    // inner walls: { x1, z1, x2, z2 } (one of the two pairs equal), doors: [{ a, w }] measured from the start point
    for (const iw of st.walls || []) {
      const ax = Math.abs(iw.z2 - iw.z1) < Math.abs(iw.x2 - iw.x1) ? 'x' : 'z', t = (iw.t ?? .1) / 2;
      const [a1, a2] = ax === 'x' ? [Math.min(iw.x1, iw.x2), Math.max(iw.x1, iw.x2)] : [Math.min(iw.z1, iw.z2), Math.max(iw.z1, iw.z2)], c = ax === 'x' ? iw.z1 : iw.x1;
      wall(sg, ax, a1, a2, c - t, c + t, H, (iw.doors || []).map(o => ({ a: a1 + o.a, b: a1 + o.a + (o.w ?? .9), lo: 0, hi: o.h ?? 2.1, kind: o.open ? 'open' : 'door' })), M.inner);
    }
    // stairs: { x1, x2, z1, z2, dir: 'n' | 's' | 'e' | 'w' } – steps rising towards dir, pass-through for walking
    for (const s of st.stairs || []) {
      const n = Math.max(8, Math.round(H / .18)), up = s.dir || 'n';
      for (let i = 0; i < n; i++) {
        const f0 = i / n, f1 = (i + 1) / n, hy = (i + 1) * H / n;
        const [xa, xb, za, zb] = up === 'n' ? [s.x1, s.x2, s.z2 - (s.z2 - s.z1) * f1, s.z2 - (s.z2 - s.z1) * f0] : up === 's' ? [s.x1, s.x2, s.z1 + (s.z2 - s.z1) * f0, s.z1 + (s.z2 - s.z1) * f1]
          : up === 'e' ? [s.x1 + (s.x2 - s.x1) * f0, s.x1 + (s.x2 - s.x1) * f1, s.z1, s.z2] : [s.x2 - (s.x2 - s.x1) * f1, s.x2 - (s.x2 - s.x1) * f0, s.z1, s.z2];
        box(sg, xa, xb, hy - .05, hy, za, zb, M.oak).userData.pass = true;
      }
    }
    y += H + .2;
  });
  if (!sts.length) y += 2.5;
  roof(g, b, y - .2);
  // a porch or terrace in front of a door: { side, a, w, depth, kind: 'deck' | 'stone' }
  for (const p of b.terraces || []) {
    const m = p.kind === 'stone' ? M.concrete : M.deck, D = p.depth ?? 2.5, h = Math.max(.05, plinth - .02);
    if (p.side === 'S') box(g, p.a, p.a + p.w, 0, h, b.d, b.d + D, m); else if (p.side === 'N') box(g, p.a, p.a + p.w, 0, h, -D, 0, m);
    else if (p.side === 'E') box(g, b.w, b.w + D, 0, h, p.a, p.a + p.w, m); else box(g, -D, 0, 0, h, p.a, p.a + p.w, m);
  }
}

// ---------- the ground, the plot, neighbours, trees, pools ----------
{
  const gr = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), M.grass); gr.rotation.x = -Math.PI / 2; gr.position.y = -.02; gr.receiveShadow = true; site.add(gr);
  const G = PLAN.ground;
  if (G?.image) {   // the aerial photo, centred on the origin, `size` metres across (north up)
    const tex = new THREE.TextureLoader().load(G.image); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
    const ph = new THREE.Mesh(new THREE.PlaneGeometry(G.size, G.size), new THREE.MeshStandardMaterial({ map: tex, roughness: 1 }));
    ph.rotation.x = -Math.PI / 2; ph.position.set(G.cx || 0, -.01, G.cz || 0); ph.receiveShadow = true; site.add(ph);
  }
  const poly = PLAN.plot?.polygon;
  if (poly?.length > 2) {
    const pts = [...poly, poly[0]].map(([x, z]) => new THREE.Vector3(x, .03, z));
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: '#c0392b' })); plotG.add(line);
    for (let i = 0; i < poly.length; i++) {   // low marker posts at the corners
      const [x, z] = poly[i]; const m = cyl(plotG, x, 0, z, .04, .5, M.white, 8); m.userData.pass = true;
    }
    if (!G?.image) {   // without a photo: the plot itself as lawn with a gravel drive edge
      const sh = new THREE.Shape(poly.map(([x, z]) => new THREE.Vector2(x, -z)));
      const m = new THREE.Mesh(new THREE.ShapeGeometry(sh), M.grass); m.rotation.x = -Math.PI / 2; m.position.y = -.005; m.receiveShadow = true; site.add(m);
    }
  }
  for (const nb of PLAN.neighbours || []) {   // { polygon: [[x, z], …], h }
    const sh = new THREE.Shape(nb.polygon.map(([x, z]) => new THREE.Vector2(x, -z)));
    const geo = new THREE.ExtrudeGeometry(sh, { depth: nb.h || 6, bevelEnabled: false }); geo.rotateX(-Math.PI / 2);
    const m = new THREE.Mesh(geo, M.nb); m.castShadow = true; nbG.add(m);
  }
  for (const p of PLAN.pools || []) {
    const D = p.depth ?? 1.4; box(site, p.x1 - .3, p.x2 + .3, -.02, .04, p.z1 - .3, p.z2 + .3, M.concrete);
    box(site, p.x1, p.x2, -D, -.08, p.z1, p.z2, M.water, false).userData.pass = true;
  }
  for (const s of PLAN.surfaces || []) {   // { kind: 'gravel' | 'stone' | 'deck', polygon }
    const sh = new THREE.Shape(s.polygon.map(([x, z]) => new THREE.Vector2(x, -z)));
    const m = new THREE.Mesh(new THREE.ShapeGeometry(sh), s.kind === 'deck' ? M.deck : s.kind === 'stone' ? M.concrete : M.gravel);
    m.rotation.x = -Math.PI / 2; m.position.y = .01; m.receiveShadow = true; m.material.map?.repeat?.set(1, 1); site.add(m);
  }
  const TR = PLAN.trees || [];   // [x, z, crown radius, height]
  if (TR.length) {
    const crown = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1, 1), M.leaf, TR.length), trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(.12, .16, 1, 7), M.bark, TR.length);
    const o = new THREE.Object3D();
    TR.forEach(([x, z, r = 2, h = 6], i) => {
      o.position.set(x, h / 2 * .55, z); o.scale.set(1, h * .55, 1); o.rotation.set(0, 0, 0); o.updateMatrix(); trunk.setMatrixAt(i, o.matrix);
      o.position.set(x, h - r * .8, z); o.scale.set(r, r * .9, r); o.rotation.y = rnd() * 3; o.updateMatrix(); crown.setMatrixAt(i, o.matrix);
    });
    crown.castShadow = trunk.castShadow = true; trees.add(crown, trunk);
  }
}
