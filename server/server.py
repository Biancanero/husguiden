#!/usr/bin/env python3
"""Husguiden server – one independent house guide (or one family page) with its own database.

Serves a built guide (dist/<slug>/) and the small API that runtime/husguiden-runtime.js uses in place of
claude.ai's runtime: documents and collections (SQLite), live updates (server-sent events), sign-in by role,
and optionally "Ask the house" through the Anthropic API. Python 3.9+ standard library only.

  python3 server/server.py --site dist/husbok-palma --db data/palma.sqlite --seed houses/joanmiro87

Environment (all optional except OWNER_PASSWORD for editing):
  OWNER_PASSWORD      sign in as owner (sees private, edits everything)
  EDITOR_PASSWORD     sign in as editor (edits the public house book)
  GUEST_PASSWORD      sign in as guest (may send a viewing request)
  PUBLIC=1            signed-out visitors may open the guide (0 = everything behind sign-in)
  SECRET              signs the session cookie (default: generated once and kept next to the database)
  ANTHROPIC_API_KEY   turns on "Ask the house";  HUSGUIDEN_MODEL (default claude-sonnet-5-5)
  HOST / PORT         default 0.0.0.0:8080
"""
import argparse, base64, hashlib, hmac, json, mimetypes, os, re, secrets, sqlite3, sys, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVEL = {'view': 0, 'interact': 1, 'admin': 2, 'owner': 3}
ROLE_LEVEL = {'visitor': 0, 'guest': 1, 'editor': 2, 'owner': 3}


# ---------------------------------------------------------------- storage
class Store:
    def __init__(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.path, self.local = path, threading.local()   # one SQLite connection per thread: sharing one across threads can crash
        self.db.execute('pragma journal_mode=wal')
        self.db.execute('create table if not exists docs (col text not null, id text not null, data text not null, updated real not null, primary key (col, id))')
        self.db.commit()
        self.lock = threading.Lock()
        self.cv = threading.Condition()
        self.ver = 0

    @property
    def db(self):
        c = getattr(self.local, 'c', None)
        if c is None:
            c = self.local.c = sqlite3.connect(self.path, timeout=30)
            c.execute('pragma busy_timeout=30000')
        return c

    def split(self, path):
        seg = [s for s in path.strip('/').split('/') if s]
        if len(seg) < 2 or len(seg) % 2:
            raise ValueError('a document path has an even number of segments: ' + path)
        return '/'.join(seg[:-1]), seg[-1]

    def get(self, path):
        col, i = self.split(path)
        r = self.db.execute('select data from docs where col = ? and id = ?', (col, i)).fetchone()
        return json.loads(r[0]) if r else None

    def list(self, col):
        return [{'id': i, 'data': json.loads(d)} for i, d in self.db.execute('select id, data from docs where col = ? order by id', (col.strip('/'),))]

    def put(self, path, data, merge=False):
        col, i = self.split(path)
        with self.lock:
            if merge:
                old = self.get(path) or {}
                old.update(data); data = old
            self.db.execute('insert or replace into docs values (?, ?, ?, ?)', (col, i, json.dumps(data, ensure_ascii=False), time.time()))
            self.db.commit()
        self.bump()

    def delete(self, path):
        col, i = self.split(path)
        with self.lock:
            self.db.execute('delete from docs where col = ? and id = ?', (col, i)); self.db.commit()
        self.bump()

    def empty(self):
        return self.db.execute('select count(*) from docs').fetchone()[0] == 0

    def bump(self):
        with self.cv:
            self.ver += 1; self.cv.notify_all()


def seed(store, house_dir, prefix='', private_example=None):
    """Fills an empty database from a house's content.json (public articles, contacts, places, timeline)."""
    c = json.load(open(os.path.join(house_dir, 'content.json'), encoding='utf-8'))
    w = prefix + 'wiki'
    for a in c.get('articles', []):
        store.put(f'{w}/{a["id"]}', {k: v for k, v in a.items() if k != 'id'})
    store.put(f'{w}/contacts', {'rows': [x for x in c.get('contacts', []) if x.get('public', True)]})
    store.put(f'{w}/places', {'rows': c.get('places', [])})
    tl = c.get('timeline', [])
    if tl and 'what' in tl[0]:
        tl = [{'date': r['date'], 'approx': False, 'kind': r.get('kind', 'Built'), 'title': r['what'], 'note': '', 'who': '', 'public': True} for r in tl]
    store.put(f'{w}/timeline', {'rows': tl})
    if private_example:
        for k, v in json.load(open(private_example, encoding='utf-8')).items():
            if not k.startswith('_'):
                store.put(f'{prefix}private/{k}', v)
    print(f'seeded {w} from {house_dir}' + (f' + example private data' if private_example else ''))


# ---------------------------------------------------------------- rules
class Rules:
    def __init__(self, path):
        self.rules = json.load(open(path, encoding='utf-8'))['rules']

    def level(self, path, op, uid):
        seg = [s for s in path.strip('/').split('/') if s]
        if seg:
            seg[0] = re.sub(r'^[a-z0-9]+-(?=[a-z])', '', seg[0])   # a family page's '<home>-' prefix
        best, n = None, -1
        for r in self.rules:
            rs = [s for s in r['path'].split('/') if s]
            if len(rs) > len(seg) or len(rs) <= n:
                continue
            if all(a == b or (a == '{self}' and b == uid) for a, b in zip(rs, seg)) and op in r:
                best, n = r, len(rs)
        return LEVEL[(best or {}).get(op, 'view' if op == 'read' else 'admin')]


# ---------------------------------------------------------------- sessions
class Sessions:
    def __init__(self, secret):
        self.key = secret.encode()

    def make(self, role, uid):
        body = base64.urlsafe_b64encode(json.dumps({'r': role, 'u': uid, 't': int(time.time())}).encode()).decode()
        return body + '.' + hmac.new(self.key, body.encode(), hashlib.sha256).hexdigest()

    def read(self, cookie):
        try:
            body, sig = cookie.split('.')
            if not hmac.compare_digest(sig, hmac.new(self.key, body.encode(), hashlib.sha256).hexdigest()):
                return None
            d = json.loads(base64.urlsafe_b64decode(body))
            return d if time.time() - d['t'] < 60 * 86400 else None
        except Exception:
            return None


def password_role(pw):
    for role, env in (('owner', 'OWNER_PASSWORD'), ('editor', 'EDITOR_PASSWORD'), ('guest', 'GUEST_PASSWORD')):
        v = os.environ.get(env)
        if v and hmac.compare_digest(pw.encode(), v.encode()):
            return role
    return None


# ---------------------------------------------------------------- Ask the house
def ask_claude(messages, system=None, max_tokens=1500):
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key:
        raise PermissionError('no ANTHROPIC_API_KEY')
    body = {'model': os.environ.get('HUSGUIDEN_MODEL', 'claude-sonnet-5-5'), 'max_tokens': max_tokens, 'messages': messages}
    if system:
        body['system'] = system
    req = urllib.request.Request('https://api.anthropic.com/v1/messages', json.dumps(body).encode(),
                                 {'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return ''.join(b.get('text', '') for b in d.get('content', []) if b.get('type') == 'text'), d.get('stop_reason') == 'max_tokens'


LOGIN_PAGE = '''<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Logga in</title>
<style>body{font:16px/1.5 system-ui,sans-serif;background:#efede9;color:#3b3737;display:grid;place-items:center;min-height:100vh;margin:0}
form{display:grid;gap:12px;width:min(320px,90vw)}input,button{font:inherit;padding:12px;border:1px solid #3b3737;background:#fff}button{background:#3b3737;color:#fff;cursor:pointer}
p{margin:0;font-size:14px;color:#8a837c}</style>
<form onsubmit="event.preventDefault();fetch('/api/login',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({password:pw.value})}).then(r=>r.ok?location.reload():(m.textContent='Fel lösenord / Wrong password'))">
<b>Husguiden</b><input id=pw type=password autocomplete=current-password placeholder="Lösenord / Password" autofocus><button>Logga in</button><p id=m></p></form>'''


# ---------------------------------------------------------------- HTTP
def make_handler(cfg):
    store, rules, sess, site = cfg['store'], cfg['rules'], cfg['sessions'], cfg['site']

    class H(BaseHTTPRequestHandler):
        server_version = 'husguiden'

        def log_message(self, fmt, *a):
            if os.environ.get('QUIET') != '1':
                sys.stderr.write('%s %s\n' % (self.address_string(), fmt % a))

        # who is asking
        def who(self):
            c = self.headers.get('Cookie', '')
            m = re.search(r'(?:^|;\s*)hg=([^;]+)', c)
            s = sess.read(m.group(1)) if m else None
            vid = re.search(r'(?:^|;\s*)hgv=([A-Za-z0-9_-]+)', c)
            if s:
                return s['r'], s['u']
            return 'visitor', vid.group(1) if vid else None

        def send(self, code, body=b'', ctype='application/json', headers=()):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False).encode()
            elif isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            for k, v in headers:
                self.send_header(k, v)
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)

        def body(self):
            n = int(self.headers.get('Content-Length') or 0)
            if n > 5_000_000:
                raise ValueError('too large')
            return json.loads(self.rfile.read(n) or b'{}')

        def allowed(self, path, op):
            role, uid = self.who()
            if not cfg['public'] and role == 'visitor':
                return False
            return ROLE_LEVEL[role] >= rules.level(path, op, uid or '')

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            u = urlparse(self.path); q = parse_qs(u.query); p = u.path
            if p == '/api/session':
                role, uid = self.who()
                hdr = []
                if not uid:
                    uid = 'v' + secrets.token_urlsafe(9)
                    hdr = [('Set-Cookie', f'hgv={uid}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax')]
                return self.send(200, {'role': role, 'id': uid, 'name': {'owner': 'Owner', 'editor': 'Editor', 'guest': 'Guest'}.get(role, ''),
                                       'login': bool(os.environ.get('OWNER_PASSWORD') or os.environ.get('EDITOR_PASSWORD') or os.environ.get('GUEST_PASSWORD')),
                                       'sample': bool(os.environ.get('ANTHROPIC_API_KEY')) and role != 'visitor' or bool(os.environ.get('ANTHROPIC_API_KEY')) and cfg['ask_public']}, headers=hdr)
            if p == '/api/col':
                path = q.get('path', [''])[0]
                if not self.allowed(path + '/x', 'read'):
                    return self.send(403, {'error': 'not_granted'})
                return self.send(200, {'docs': store.list(path), 'v': store.ver})
            if p == '/api/doc':
                path = q.get('path', [''])[0]
                if not self.allowed(path, 'read'):
                    return self.send(403, {'error': 'not_granted'})
                try:
                    return self.send(200, {'data': store.get(path)})
                except ValueError as e:
                    return self.send(400, {'error': str(e)})
            if p == '/api/watch':   # server-sent events: a fresh snapshot of the collection whenever anything changes
                path = q.get('path', [''])[0]
                if not self.allowed(path + '/x', 'read'):
                    return self.send(403, {'error': 'not_granted'})
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream'); self.send_header('Cache-Control', 'no-cache'); self.end_headers()
                last, sent = -1, None
                try:
                    while True:
                        with store.cv:
                            if store.ver == last:
                                store.cv.wait(25)
                        last = store.ver
                        docs = json.dumps(store.list(path), ensure_ascii=False)
                        if docs != sent:
                            self.wfile.write(f'data: {docs}\n\n'.encode()); sent = docs
                        else:
                            self.wfile.write(b': ping\n\n')
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    return
            if p == '/health':
                return self.send(200, {'ok': True})
            return self.static(p)

        def static(self, p):
            role, _ = self.who()
            if not cfg['public'] and role == 'visitor' and not p.startswith('/runtime/'):
                return self.send(200, LOGIN_PAGE, 'text/html; charset=utf-8')
            rel = unquote(p).lstrip('/') or 'index.html'
            if rel.endswith('/'):
                rel += 'index.html'
            full = os.path.realpath(os.path.join(site, rel))
            if not full.startswith(os.path.realpath(site) + os.sep) or any(s.startswith('.') for s in rel.split('/')):
                return self.send(404, 'not found', 'text/plain')
            if os.path.isdir(full):
                full = os.path.join(full, 'index.html')
            if not os.path.isfile(full):
                return self.send(404, 'not found', 'text/plain')
            ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
            if ctype.startswith('text/') or ctype in ('application/javascript', 'application/json'):
                ctype += '; charset=utf-8'
            data = open(full, 'rb').read()
            if full.endswith('.html'):   # html is small and changes with every build; images can be cached
                return self.send(200, data, ctype, [('Cache-Control', 'no-cache')])
            return self.send(200, data, ctype, [('Cache-Control', 'public, max-age=86400')])

        def do_POST(self):
            u = urlparse(self.path); p = u.path
            try:
                b = self.body()
            except Exception:
                return self.send(400, {'error': 'bad json'})
            if p == '/api/login':
                role = password_role(str(b.get('password', '')))
                if not role:
                    time.sleep(1)
                    return self.send(401, {'error': 'wrong password'})
                uid = role + '-' + hashlib.sha256((role + cfg['secret']).encode()).hexdigest()[:10]
                return self.send(200, {'role': role}, headers=[('Set-Cookie', f'hg={sess.make(role, uid)}; Path=/; Max-Age=5184000; HttpOnly; SameSite=Lax')])
            if p == '/api/logout':
                return self.send(200, {'ok': True}, headers=[('Set-Cookie', 'hg=; Path=/; Max-Age=0')])
            if p == '/api/sample':
                role, _ = self.who()
                if role == 'visitor' and not cfg['ask_public']:
                    return self.send(403, {'code': 'not_granted'})
                try:
                    text, trunc = ask_claude(b.get('messages') or [], b.get('system'), int(b.get('max_tokens') or 1500))
                    return self.send(200, {'text': text, 'truncated': trunc})
                except PermissionError:
                    return self.send(403, {'code': 'not_granted'})
                except Exception as e:
                    return self.send(502, {'code': 'upstream', 'message': str(e)[:200]})
            return self.send(404, {'error': 'no such endpoint'})

        def do_PUT(self):
            return self.write(False)

        def do_PATCH(self):
            return self.write(True)

        def do_DELETE(self):
            path = parse_qs(urlparse(self.path).query).get('path', [''])[0]
            if not self.allowed(path, 'write'):
                return self.send(403, {'error': 'not_granted'})
            store.delete(path)
            return self.send(200, {'ok': True})

        def write(self, merge):
            u = urlparse(self.path)
            if u.path != '/api/doc':
                return self.send(404, {'error': 'no such endpoint'})
            path = parse_qs(u.query).get('path', [''])[0]
            if not self.allowed(path, 'write'):
                return self.send(403, {'error': 'not_granted'})
            try:
                store.put(path, self.body(), merge)
            except ValueError as e:
                return self.send(400, {'error': str(e)})
            return self.send(200, {'ok': True})

    return H


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--site', required=True, help='a built guide, e.g. dist/husbok-palma')
    ap.add_argument('--db', required=True, help='SQLite file (created if missing)')
    ap.add_argument('--seed', action='append', default=[], help="houses/<dir>[:prefix] – fills an EMPTY database from content.json (repeat for a family page)")
    ap.add_argument('--example-private', help='also load invented private rows (db/examples/private.example.json) – for demos only')
    ap.add_argument('--host', default=os.environ.get('HOST', '0.0.0.0'))
    ap.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8080')))
    a = ap.parse_args()
    store = Store(a.db)
    if store.empty():
        for s in a.seed:
            d, _, pre = s.partition(':')
            seed(store, d if os.path.isabs(d) else os.path.join(os.getcwd(), d), pre, a.example_private)
    secret = os.environ.get('SECRET')
    if not secret:
        kp = os.path.abspath(a.db) + '.secret'
        if not os.path.exists(kp):
            open(kp, 'w').write(secrets.token_hex(32)); os.chmod(kp, 0o600)
        secret = open(kp).read().strip()
    cfg = {'store': store, 'rules': Rules(os.path.join(ROOT, 'db', 'schema.json')), 'sessions': Sessions(secret), 'secret': secret,
           'site': os.path.abspath(a.site), 'public': os.environ.get('PUBLIC', '1') == '1', 'ask_public': os.environ.get('ASK_PUBLIC') == '1'}
    srv = ThreadingHTTPServer((a.host, a.port), make_handler(cfg))
    srv.daemon_threads = True
    print(f'husguiden: {a.site} on http://{a.host}:{a.port}  (public={cfg["public"]}, ask={"on" if os.environ.get("ANTHROPIC_API_KEY") else "off"})')
    srv.serve_forever()


if __name__ == '__main__':
    main()
