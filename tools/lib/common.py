"""Small helpers shared by the build steps. Every patch asserts its anchor, so a changed shell fails loudly instead of quietly."""
import json, re, sys


def rep(s, a, b, n=1):
    c = s.count(a)
    if c != n:
        sys.exit(f'build: expected {n}× but found {c}×: {a[:90]!r}')
    return s.replace(a, b)


def between(s, start, end):
    i = s.index(start); j = s.index(end, i)
    return i, j


def emb(s):
    """A string that is safe inside <script type="application/json">."""
    return json.dumps(s, ensure_ascii=False).replace('</', '<\\/')


def i18n_block(s, extra):
    """Adds interface translations, "English": [sv, es, de], at the top of the shell's I18N dictionary."""
    if not extra:
        return s
    for k, v in extra.items():
        assert isinstance(v, list) and len(v) == 3, f'i18n {k!r}: give [sv, es, de]'
    return rep(s, 'const I18N = {\n', 'const I18N = {\n' + ''.join(f'  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n' for k, v in extra.items()))


def check_content(c):
    """content.json: the snapshot signed-out visitors see. Translations of facts/captions must line up with the English."""
    for a in c.get('articles', []):
        for L, tr in (a.get('i18n') or {}).items():
            for key, en in (('facts', a.get('facts') or []), ('captions', a.get('images') or [])):
                if isinstance(tr.get(key), list) and len(tr[key]) != len(en):
                    sys.exit(f"content: article {a['id']!r} i18n.{L}.{key} has {len(tr[key])} rows, English has {len(en)}")
    return c


def put_snapshot(s, content):
    snap = {'articles': content.get('articles', []), 'contacts': [c for c in content.get('contacts', []) if c.get('public', True)],
            'places': content.get('places', []), 'timeline': content.get('timeline', [])}
    if snap['timeline'] and 'what' in snap['timeline'][0]:   # short form {date, what}
        snap['timeline'] = [{'date': r['date'], 'approx': False, 'kind': r.get('kind', 'Built'), 'title': r['what'], 'note': r.get('note', ''), 'who': '', 'public': True} for r in snap['timeline']]
    i, j = between(s, '<script type="application/json" id="book-snapshot">', '</script>')
    return s[:i] + '<script type="application/json" id="book-snapshot">' + json.dumps(snap, ensure_ascii=False).replace('</', '<\\/') + s[j:]


def put_homes(s, homes, hub=None):
    """The homes the trip can fly between, and the optional family hub link."""
    js = 'const HOMES = [\n' + ''.join('  ' + json.dumps(h, ensure_ascii=False) + ',\n' for h in homes) + '];'
    s = re.sub(r'const HOMES = \[[^\n]*?\];[^\n]*', lambda m: js, s, count=1)
    s = re.sub(r'const HUB = null;[^\n]*', lambda m: 'const HUB = ' + (json.dumps(hub, ensure_ascii=False) if hub else 'null') + ';', s, count=1)
    return s


RUNTIME_TAG = '<script src="runtime/husguiden-runtime.js"></script>\n'


def vendored(s):
    """three.js from the vendored copy (engine/vendor) instead of the CDN – the guide then runs without internet."""
    return (s.replace('"three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"', '"three": "./vendor/three/build/three.module.js"')
             .replace('"three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"', '"three/addons/": "./vendor/three/addons/"'))


def standalone(s):
    """Outside claude.ai: a small runtime provides window.claude (db, user, sample) against server/server.py."""
    return RUNTIME_TAG + vendored(s)
