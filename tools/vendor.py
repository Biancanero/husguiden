#!/usr/bin/env python3
"""Fetches three.js 0.160.0 and the addons the house book imports (plus everything they import) into engine/vendor/,
so a built guide runs without any CDN. Already done in the repo; run again only to change the three.js version."""
import os, re, sys, urllib.request

VER = '0.160.0'
CDN = f'https://cdn.jsdelivr.net/npm/three@{VER}/'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'engine', 'vendor', 'three')
START = ['controls/OrbitControls.js', 'environments/RoomEnvironment.js', 'loaders/GLTFLoader.js', 'postprocessing/EffectComposer.js',
         'postprocessing/GTAOPass.js', 'postprocessing/OutputPass.js', 'postprocessing/RenderPass.js', 'renderers/CSS2DRenderer.js']


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'husguiden-vendor'}), timeout=60) as r:
        return r.read().decode('utf-8')


def main():
    os.makedirs(os.path.join(OUT, 'build'), exist_ok=True)
    open(os.path.join(OUT, 'build', 'three.module.js'), 'w', encoding='utf-8').write(get(CDN + 'build/three.module.js'))
    todo, done = list(START), set()
    while todo:
        rel = os.path.normpath(todo.pop()).replace(os.sep, '/')
        if rel in done:
            continue
        done.add(rel)
        src = get(CDN + 'examples/jsm/' + rel)
        dst = os.path.join(OUT, 'addons', rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'w', encoding='utf-8').write(src)
        for m in re.finditer(r"""(?:from|import)\s*['"](\.{1,2}/[^'"]+)['"]""", src):
            todo.append(os.path.join(os.path.dirname(rel), m.group(1)))
    print(f'three {VER}: build + {len(done)} addon files → {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    sys.exit(main())
