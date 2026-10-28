#!/usr/bin/env python3
"""Builds the house guides.

  python3 tools/build.py                    every house in houses/ + the family page  → dist/
  python3 tools/build.py villa              one house only
  python3 tools/build.py --target claude    pages for claude.ai artifacts (no runtime, three.js from the CDN)
  python3 tools/build.py --no-family        skip the family page

The example family portal (portal/) goes to dist/index.html when every house is built.
Each house becomes dist/<slug>/ – a complete, independent house guide (page, images, trip, runtime, vendored three.js).
dist/family/ holds every house listed in family.json in ONE page, with the globe trip between them.
Needs only Python 3.9+ (standard library)."""
import argparse, glob, importlib.util, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from lib.common import put_snapshot, put_homes, standalone, vendored, check_content, RUNTIME_TAG   # noqa: E402
from lib import plan_book                                                     # noqa: E402
import plan_svg                                                               # noqa: E402

read = lambda *p: open(os.path.join(ROOT, *p), encoding='utf-8').read()
load = lambda *p: json.load(open(os.path.join(ROOT, *p), encoding='utf-8'))


def houses():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'houses', '*', 'house.json'))):
        d = os.path.dirname(f)
        if os.path.basename(d).startswith('_'):
            continue   # _mall: the template for new houses
        h = json.load(open(f, encoding='utf-8'))
        h['_dir'] = d
        out[h['id']] = h
    return out


def home_entry(h):
    """One home for the trip menu (shell's HOMES)."""
    return {k: h.get(k) for k in ('id', 'name', 'place', 'town', 'url', 'sat', 'c', 'north')} | {'ll': [h['lng'], h['lat']]}


def book(h, shell):
    """The finished house book for one house (before HOMES / runtime)."""
    content = check_content(json.load(open(os.path.join(h['_dir'], 'content.json'), encoding='utf-8')))
    kind = h.get('kind', 'plan')
    if kind == 'shell':          # the shell's own model (Joan Miró 87)
        return put_snapshot(shell, content)
    if kind == 'scene':          # a hand-written scene with its own build step (Hulehällar 418D)
        spec = importlib.util.spec_from_file_location('build_book_' + h['id'], os.path.join(h['_dir'], 'build_book.py'))
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod.build(shell, h['_dir'])
    plan = json.load(open(os.path.join(h['_dir'], 'plan.json'), encoding='utf-8'))   # a new house from data
    # floor-plan drawings made from plan.json; they are the guide's plans until scans are listed in house.json 'plans'
    h['_gen'] = plan_svg.drawings(plan, 'plan-auto-' + h['id'])
    if not h.get('plans'):
        def slot_name(bid, k):
            own = [x for x in plan['slots'] if x.get('type') == 'building' and x.get('building') == bid]
            lv = [x for n, x in enumerate(plan['slots']) if x.get('type', 'storey') == 'storey' and x.get('level', n) == k]
            return (own or lv or [{'name': f'{bid} {k}'}])[0]['name'] + (f' · {k}' if own and k else '')
        h = {**h, 'plans': [{'name': slot_name(f.rsplit('-', 2)[-2], int(f.rsplit('-', 1)[-1][:-4])), 'src': 'img/' + f,
                             'note': 'Drawn from plan.json – add a scan of the real drawing in house.json "plans".'} for f in h['_gen']]}
    return put_snapshot(plan_book.build(shell, h, plan, content, read('engine', 'plan-scene.js')), content)


def copy_tree(src, dst, seen=None):
    if not os.path.isdir(src):
        return
    for f in sorted(os.listdir(src)):
        if f.startswith('.') or f.lower() == 'readme.md':
            continue
        s = os.path.join(src, f)
        if os.path.isdir(s):
            copy_tree(s, os.path.join(dst, f), seen); continue
        if seen is not None:
            if f in seen and seen[f] != s:
                sys.exit(f'build: two houses have an image called {f!r} ({seen[f]} and {s}) – rename one, they share img/ in the family page')
            seen[f] = s
        os.makedirs(dst, exist_ok=True)
        shutil.copy2(s, os.path.join(dst, f))


def assets(out, hs, target, shared_img=False):
    seen = {} if shared_img else None
    for h in hs:
        copy_tree(os.path.join(h['_dir'], 'img'), os.path.join(out, 'img'), seen)
        for f, svg in (h.get('_gen') or {}).items():
            os.makedirs(os.path.join(out, 'img'), exist_ok=True)
            open(os.path.join(out, 'img', f), 'w', encoding='utf-8').write(svg)
        sd = os.path.join(h['_dir'], 'sat')
        if os.path.isdir(sd):
            os.makedirs(os.path.join(out, 'trip', 'sat'), exist_ok=True)
            for f in os.listdir(sd):
                if f.endswith('.jpg'):
                    shutil.copy2(os.path.join(sd, f), os.path.join(out, 'trip', 'sat', f"{h['id']}-{f}"))
    copy_tree(os.path.join(ROOT, 'engine', 'trip'), os.path.join(out, 'trip'))
    if target == 'standalone':
        copy_tree(os.path.join(ROOT, 'runtime'), os.path.join(out, 'runtime'))
        copy_tree(os.path.join(ROOT, 'engine', 'vendor'), os.path.join(out, 'vendor'))


def family_page(fam, hs, books):
    """One page holding several finished books as JSON strings; it writes the chosen one into itself while loading.
    Switching home plays the trip, stores the choice (#home=… + localStorage) and reloads the same page."""
    emb = lambda s: json.dumps(s, ensure_ascii=False).replace('</', '<\\/')
    meta = {h['id']: {'prefix': '' if h['id'] == fam['first'] else h['id'] + '-', 'town': h['town'], 'name': h['name'], 'last': len(h.get('sat') or [])} for h in hs}
    page = f'<title>{fam.get("title", "Our homes")}</title>\n'
    page += ''.join(f'<script type="application/json" id="book-{h["id"]}">{emb(books[h["id"]])}</script>\n' for h in hs)
    page += '''<script>
(() => {
  // which home: #home=… (set by the trip), else the last one visited, else the first
  const HOMES = ''' + json.dumps(meta, ensure_ascii=False) + ''', FIRST = ''' + json.dumps(fam['first']) + ''';
  const store = (k, v) => { try { v === undefined ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (e) { } };
  const load = k => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const hash = (location.hash.match(/home=([\\w-]+)/) || [])[1];
  const id = HOMES[hash] ? hash : HOMES[load('family-home')] ? load('family-home') : FIRST;
  const from = (location.hash.match(/from=([\\w-]+)/) || [])[1];
  store('family-home', id);
  // just arrived from another home: the last satellite photo of the dive covers the page until the model takes over
  const arrived = HOMES[from] && from !== id;
  window.WESTMAN = { home: id, first: FIRST, prefix: HOMES[id].prefix, from: arrived ? from : null,
    go(to, was) { store('family-home', to); location.hash = 'home=' + to + '&from=' + (was || id); location.reload(); },
    reveal() { const v = document.getElementById('westman-arrive'); if (!v || v.dataset.out) return; v.dataset.out = 1; v.style.opacity = 0; setTimeout(() => v.remove(), 1600); } };
  document.write(JSON.parse(document.getElementById('book-' + id).textContent));
  if (arrived && HOMES[id].last) {
    const v = document.createElement('div'); v.id = 'westman-arrive';
    v.setAttribute('style', 'position:fixed;inset:0;z-index:300;background:#e7ebe9 url(trip/sat/' + id + '-' + HOMES[id].last + '.jpg) center/cover no-repeat;transition:opacity .9s ease;pointer-events:none');
    document.body.append(v); history.replaceState(null, '', '#home=' + id);
    addEventListener('load', () => setTimeout(() => WESTMAN.reveal(), 9000));
  }
})();
</script>
'''
    return page


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ids', nargs='*', help='house ids (default: all)')
    ap.add_argument('--target', choices=['standalone', 'claude'], default='standalone')
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist'))
    ap.add_argument('--no-family', action='store_true')
    a = ap.parse_args()
    shell = read('engine', 'shell.html')
    H = houses()
    ids = a.ids or list(H)
    for i in ids:
        if i not in H:
            sys.exit(f'build: no house {i!r} (have: {", ".join(H)})')
    fam = load('family.json') if os.path.exists(os.path.join(ROOT, 'family.json')) else None
    hub = (fam or {}).get('hub')
    books = {}
    for i in ids:
        h = H[i]
        books[i] = book(h, shell)
        # an independent guide lists only itself, plus homes that have their own address (url) to travel to
        others = [home_entry(H[k]) for k in H if k != i and H[k].get('url')]
        s = put_homes(books[i], [home_entry(h)] + others, hub)
        if a.target == 'standalone':
            s = standalone(s)
        out = os.path.join(a.out, h.get('slug', i))
        shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
        open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(s)
        assets(out, [h], a.target)
        print(f'  {i:10} → {os.path.relpath(out, ROOT)}/index.html  {len(s.encode()) // 1024} KB')
    if fam and not a.no_family and all(k in books for k in fam['homes']):
        hs = [H[k] for k in fam['homes']]
        homes = [home_entry(h) for h in hs]
        fb = {k: put_homes(books[k], homes, hub) for k in fam['homes']}
        if a.target == 'standalone':
            fb = {k: vendored(v) for k, v in fb.items()}
        page = family_page(fam, hs, fb)
        if a.target == 'standalone':
            page = RUNTIME_TAG + page
        out = os.path.join(a.out, fam.get('slug', 'family'))
        shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
        open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(page)
        assets(out, hs, a.target, shared_img=True)
        print(f'  family     → {os.path.relpath(out, ROOT)}/index.html  {len(page.encode()) // 1024} KB  ({" + ".join(fam["homes"])})')

    # the family portal demo (portal/, invented figures) at the top of dist/, its 'Open the house book' links point to the slugs
    if not a.ids and os.path.isdir(os.path.join(ROOT, 'portal')):
        copy_tree(os.path.join(ROOT, 'portal'), a.out)
        copy_tree(os.path.join(ROOT, 'engine', 'vendor'), os.path.join(a.out, 'vendor'))
        print(f'  portal     → {os.path.relpath(a.out, ROOT)}/index.html  (example family portal, invented figures)')


if __name__ == '__main__':
    main()
