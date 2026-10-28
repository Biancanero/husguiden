/* Husguiden runtime – gives a house book outside claude.ai the same window.claude it has inside claude.ai:
   claude.use('db')     documents and collections, live (server/server.py: /api/doc, /api/col, /api/watch)
   claude.use('user')   who is viewing: isOwner, canEdit, can, id, me, profiles
   claude.use('sample') "Ask the house" (only when the server has an Anthropic API key)
   Plus a small sign-in / sign-out link in the corner. Loaded before the book by a plain <script> tag. */
(() => {
  if (window.claude?.use && !window.claude.husguiden) return;          // inside claude.ai: the real runtime
  if (window.__husguiden) return; window.__husguiden = true;          // a family page writes its book in: load once
  const api = (p, o = {}) => fetch(p, { credentials: 'same-origin', ...o, headers: { 'content-type': 'application/json', ...(o.headers || {}) } })
    .then(async r => { const d = await r.json().catch(() => ({})); if (!r.ok) { const e = new Error(d.error || d.code || r.status); e.code = d.code || (r.status === 403 ? 'not_granted' : 'error'); throw e; } return d; });
  const session = api('/api/session').catch(() => null);   // null: no server (a file opened by itself) → the book shows its snapshot
  const rank = { visitor: 0, guest: 1, editor: 2, owner: 3 };

  // ---------- db ----------
  const freeze = o => (o && typeof o === 'object' && !Object.isFrozen(o) && (Object.values(o).forEach(freeze), Object.freeze(o)), o);
  const snapOf = docs => ({ docs: docs.map(d => ({ id: d.id, exists: true, data: () => freeze(structuredClone(d.data)) })), size: docs.length, empty: !docs.length });
  const newId = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  function docRef(path) {
    const q = '/api/doc?path=' + encodeURIComponent(path), id = path.split('/').pop();
    return {
      id, path,
      get: () => api(q).then(d => ({ id, exists: d.data != null, data: () => d.data })),
      set: data => api(q, { method: 'PUT', body: JSON.stringify(data) }),
      update: data => api(q, { method: 'PATCH', body: JSON.stringify(data) }),
      delete: () => api(q, { method: 'DELETE' }),
      onSnapshot(cb, err) {
        const parent = path.split('/').slice(0, -1).join('/');
        return colRef(parent).onSnapshot(s => { const d = s.docs.find(x => x.id === id); cb({ id, exists: !!d, data: () => d ? d.data() : undefined }); }, err);
      },
    };
  }
  function colRef(path) {
    return {
      path,
      doc: id => docRef(path + '/' + (id || newId())),
      get: () => api('/api/col?path=' + encodeURIComponent(path)).then(d => snapOf(d.docs)),
      onSnapshot(cb, err) {
        let es, closed = false, wait = 1000;
        const open = () => {
          if (closed) return;
          es = new EventSource('/api/watch?path=' + encodeURIComponent(path));
          es.onmessage = e => { wait = 1000; try { cb(snapOf(JSON.parse(e.data))); } catch (x) { console.error(x); } };
          es.onerror = () => { es.close(); if (closed) return; api('/api/col?path=' + encodeURIComponent(path)).then(() => setTimeout(open, wait = Math.min(wait * 2, 30000)), e => err?.(e)); };
        };
        open();
        return () => { closed = true; es?.close(); };
      },
      where() { return this; }, orderBy() { return this; }, limit() { return this; },
    };
  }
  const db = { doc: docRef, collection: colRef };

  // ---------- user ----------
  const user = s => ({
    isOwner: async () => s.role === 'owner',
    canEdit: async () => rank[s.role] >= 2,
    can: async n => n === 'data.write' ? rank[s.role] >= 1 : null,
    id: async () => s.id,
    me: async () => ({ id: s.id, name: s.name || '', guest: s.role === 'guest' }),
    profiles: async ids => Object.fromEntries((ids || []).map(i => [i, { id: i, name: i === s.id ? s.name : '' }])),
    search: async () => [],
  });

  // ---------- sample (Ask the house) ----------
  const sample = Object.assign(async (input, opts = {}) => {
    const messages = typeof input === 'string' ? [{ role: 'user', content: input }] : input;
    const d = await api('/api/sample', { method: 'POST', body: JSON.stringify({ messages }), signal: opts.signal });
    opts.onText?.({ text: d.text, delta: d.text });
    return { text: d.text, truncated: !!d.truncated };
  }, {
    json: async (input, opts) => { const r = await sample(input, opts); return JSON.parse(r.text.replace(/^```(json)?|```$/g, '')); },
    limits: async () => ({ images: false }),
  });

  window.claude = {
    husguiden: true,
    use: async name => {
      const s = await session;
      if (!s) return null;
      if (name === 'db') return db;
      if (name === 'user') return user(s);
      if (name === 'sample') return s.sample ? sample : null;
      return null;
    },
  };

  // ---------- sign in / out ----------
  session.then(s => {
    if (!s?.login) return;
    const put = () => {
      const b = document.createElement('button'); b.type = 'button'; b.id = 'hg-auth';
      b.textContent = s.role === 'visitor' ? 'Logga in' : 'Logga ut (' + ({ owner: 'ägare', editor: 'redaktör', guest: 'gäst' }[s.role] || s.role) + ')';
      b.setAttribute('style', 'position:fixed;left:10px;bottom:10px;z-index:400;font:12px/1 system-ui,sans-serif;letter-spacing:.04em;padding:7px 10px;border:1px solid rgba(59,55,55,.35);background:rgba(255,255,255,.85);color:#3b3737;cursor:pointer;backdrop-filter:blur(6px)');
      b.onclick = async () => {
        if (s.role !== 'visitor') { await api('/api/logout', { method: 'POST', body: '{}' }); return location.reload(); }
        const pw = prompt('Lösenord / Password'); if (!pw) return;
        try { await api('/api/login', { method: 'POST', body: JSON.stringify({ password: pw }) }); location.reload(); } catch { alert('Fel lösenord / Wrong password'); }
      };
      document.body.append(b);
    };
    document.body ? put() : addEventListener('DOMContentLoaded', put);
  });
})();
