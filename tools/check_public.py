#!/usr/bin/env python3
"""Stops private data before it reaches git. Run before every commit/push (the repo may be public):

  python3 tools/check_public.py            # every file git would commit
  python3 tools/check_public.py path …     # just these

Looks for bank accounts (IBAN), Spanish NIE/DNI, Swedish personnummer, API keys, door/alarm/wifi codes written out,
the database's private tables, and every word listed in .private-words (one per line, never committed – put your own
account numbers, contract numbers, names of private contacts there). Exit code 1 = something to remove."""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = ('engine/vendor/', 'engine/trip/', '.git/')
TEXT = ('.html', '.js', '.json', '.py', '.md', '.txt', '.yaml', '.yml', '.sh', '.env', '.example', '.svg', '.css', '')
PATTERNS = [
    ('IBAN', r'\b[A-Z]{2}\d{2}(?: ?[0-9A-Z]{4}){3,7}\b'),
    ('NIE', r'\b[XYZ]-?\d{7}-?[A-Z]\b'),
    ('DNI', r'\b\d{8}-?[A-HJ-NP-TV-Z]\b'),
    ('personnummer', r'\b(?:19|20)?\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])[-+]\d{4}\b'),
    ('API key', r'sk-ant-[A-Za-z0-9_-]{12,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}'),
    ('a code written out', r'(?i)(?:wifi|wi-fi)[- ]?(?:lösenord(?:et)?|password|clave|contraseña)\s*(?:är|is|es|:)\s*\S{4,}|(?:larmkod|alarm code|código de alarma|portkod|door code|nyckelkod|key code|pin)\s*(?:är|is|es|:)?\s*\d{3,}'),
    ('private table', r'"(?:payments|costs|rental)"\s*:\s*\{\s*"rows"\s*:\s*\[\s*\{[^\]]*?"(?:amount|gross)"\s*:\s*\d'),
    ('meter / supply number', r'\bES\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?[A-Z]{2}\b|\bCUPS\s*[A-Z]{2}\d'),
]
ALLOW = [r'\(example\)', r'ES00 0000', r'EXEMPEL', r'EX-0000', r'\b0000\b']


def files(args):
    if args:
        return args
    out = subprocess.run(['git', 'ls-files', '-co', '--exclude-standard'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
    return [f for f in out if f and not f.startswith(SKIP_DIRS) and os.path.splitext(f)[1].lower() in TEXT]


def main(args):
    words = []
    pw = os.path.join(ROOT, '.private-words')
    if os.path.exists(pw):
        words = [w.strip() for w in open(pw, encoding='utf-8') if w.strip() and not w.startswith('#')]
    bad = 0
    for f in files(args):
        p = os.path.join(ROOT, f)
        if not os.path.isfile(p) or os.path.getsize(p) > 20_000_000:
            continue
        s = open(p, encoding='utf-8', errors='ignore').read()
        hits = [(n, m.group(0)) for n, rx in PATTERNS for m in re.finditer(rx, s)]
        hits += [('.private-words', w) for w in words if w.lower() in s.lower()]
        hits = [(n, h) for n, h in hits if not any(re.search(a, h) for a in ALLOW)]
        for n, h in hits[:8]:
            print(f'{f}: {n}: {h[:80]!r}')
        bad += len(hits)
    print('check_public:', 'OK – nothing private found' if not bad else f'{bad} finding(s) – remove them before committing')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
