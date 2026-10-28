#!/usr/bin/env python3
"""Draws a floor plan per storey from a house's plan.json → houses/<dir>/img/plan-auto-<building>-<level>.svg.
(tools/build.py does the same by itself for every plan house: the drawings go into the built guide as plan-auto-<house>-…)

  python3 tools/plan_svg.py houses/villa

Useful to check your measurements against the real drawings side by side, and as the guide's plan images until
scans of the real drawings are added (house.json "plans")."""
import json, os, sys
from xml.sax.saxutils import escape

PX = 40   # pixels per metre


def draw(b, st, title):
    W, D = b['w'], b['d']
    pad = 1.2
    w, h = (W + 2 * pad) * PX, (D + 2 * pad) * PX + 40
    X = lambda x: (x + pad) * PX
    Z = lambda z: (z + pad) * PX + 30
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" font-family="Helvetica, Arial, sans-serif">',
         f'<rect width="100%" height="100%" fill="#fbfaf7"/>',
         f'<text x="{X(0):.0f}" y="22" font-size="15" fill="#3b3737">{escape(title)}</text>']
    for r in st.get('rooms', []):
        o.append(f'<rect x="{X(r["x1"]):.1f}" y="{Z(r["z1"]):.1f}" width="{(r["x2"] - r["x1"]) * PX:.1f}" height="{(r["z2"] - r["z1"]) * PX:.1f}" fill="#efe9de"/>')
        a = r.get('area') or round((r['x2'] - r['x1']) * (r['z2'] - r['z1']), 1)
        cx, cz = X((r['x1'] + r['x2']) / 2), Z((r['z1'] + r['z2']) / 2)
        o.append(f'<text x="{cx:.0f}" y="{cz:.0f}" font-size="12" text-anchor="middle" fill="#3b3737">{escape(r["name"])}</text>')
        o.append(f'<text x="{cx:.0f}" y="{cz + 15:.0f}" font-size="11" text-anchor="middle" fill="#8a837c">{a} m²</text>')
    T = b.get('wall', .3)
    o.append(f'<path d="M{X(0)},{Z(0)}h{W * PX}v{D * PX}h{-W * PX}z M{X(T)},{Z(T)}v{(D - 2 * T) * PX}h{(W - 2 * T) * PX}v{-(D - 2 * T) * PX}z" fill="#3b3737" fill-rule="evenodd"/>')
    for wl in st.get('walls', []):
        t = wl.get('t', .1)
        if abs(wl['z2'] - wl['z1']) < abs(wl['x2'] - wl['x1']):
            o.append(f'<rect x="{X(min(wl["x1"], wl["x2"])):.1f}" y="{Z(wl["z1"] - t / 2):.1f}" width="{abs(wl["x2"] - wl["x1"]) * PX:.1f}" height="{t * PX:.1f}" fill="#3b3737"/>')
            for d in wl.get('doors', []):
                o.append(f'<rect x="{X(min(wl["x1"], wl["x2"]) + d["a"]):.1f}" y="{Z(wl["z1"] - t / 2) - 1:.1f}" width="{d.get("w", .9) * PX:.1f}" height="{t * PX + 2:.1f}" fill="#efe9de"/>')
        else:
            o.append(f'<rect x="{X(wl["x1"] - t / 2):.1f}" y="{Z(min(wl["z1"], wl["z2"])):.1f}" width="{t * PX:.1f}" height="{abs(wl["z2"] - wl["z1"]) * PX:.1f}" fill="#3b3737"/>')
            for d in wl.get('doors', []):
                o.append(f'<rect x="{X(wl["x1"] - t / 2) - 1:.1f}" y="{Z(min(wl["z1"], wl["z2"]) + d["a"]):.1f}" width="{t * PX + 2:.1f}" height="{d.get("w", .9) * PX:.1f}" fill="#efe9de"/>')
    for op in st.get('openings', []):
        door = op.get('kind') == 'door'
        col = '#c0392b' if door else '#7fa7c9'
        a, ow = op['a'], op['w']
        if op['side'] in 'NS':
            z = 0 if op['side'] == 'N' else D - T
            o.append(f'<rect x="{X(a):.1f}" y="{Z(z):.1f}" width="{ow * PX:.1f}" height="{T * PX:.1f}" fill="{col}"/>')
        else:
            x = 0 if op['side'] == 'W' else W - T
            o.append(f'<rect x="{X(x):.1f}" y="{Z(T + a - T):.1f}" width="{T * PX:.1f}" height="{ow * PX:.1f}" fill="{col}"/>')
    # scale bar and north
    o.append(f'<path d="M{X(0)},{h - 14}h{PX * 2}" stroke="#3b3737" stroke-width="2"/><text x="{X(0) + PX * 2 + 6}" y="{h - 10}" font-size="11" fill="#3b3737">2 m</text>')
    o.append(f'<text x="{w - 26}" y="22" font-size="13" fill="#3b3737">N ↑</text></svg>')
    return '\n'.join(o)


def drawings(plan, prefix='plan-auto'):
    """{file name: svg} – one drawing per storey of every building."""
    out = {}
    for b in plan['buildings']:
        for k, st in enumerate(b.get('storeys', [])):
            out[f'{prefix}-{b["id"]}-{k}.svg'] = draw(b, st, f'{b["id"]} · level {k}' + (' (drawn unrotated)' if b.get('rot') else ''))
    return out


def main(hdir):
    plan = json.load(open(os.path.join(hdir, 'plan.json'), encoding='utf-8'))
    os.makedirs(os.path.join(hdir, 'img'), exist_ok=True)
    d = drawings(plan)
    for f, svg in d.items():
        open(os.path.join(hdir, 'img', f), 'w', encoding='utf-8').write(svg)
    print('wrote', ', '.join(d))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__))
