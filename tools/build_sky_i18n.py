"""Add Spanish and French text to data/sky.json.gz from Stellarium's own translations.

Each sky culture in stellarium-skycultures ships po/<lang>.po files with translated culture names,
introductions, author notes, constellation names and the description sections that hold the stories.
This script matches them to the English text already in data/sky.json.gz and stores them next to it:

    culture['tr'][lang] = {'title', 'intro', 'authors'}
    figure['t'][lang]   = {'e': name, 's': story}

Missing translations are simply left out, and the page falls back to English. Hand-written additions
(for strings Stellarium has not translated yet) live in tools/sky_i18n_extra.json and win over the po files.

    git clone --depth 1 https://github.com/Stellarium/stellarium-skycultures.git /tmp/sc
    python tools/build_sky_i18n.py --skycultures /tmp/sc
"""
import argparse, ast, gzip, json, pathlib, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_sky import section, clean, stories  # same parsing as the English build

ROOT = pathlib.Path(__file__).resolve().parent.parent
LANGS = ['es', 'fr']
norm = lambda s: re.sub(r'\s+', ' ', s or '').strip()

def read_po(path):
    """msgid -> msgstr (normalised whitespace keys), skipping fuzzy and empty entries."""
    out = {}
    if not path.exists(): return out
    entries = path.read_text(encoding='utf-8').split('\n\n')
    for e in entries:
        if '#, fuzzy' in e: continue
        mid, mstr, cur = [], [], None
        for line in e.splitlines():
            if line.startswith('msgctxt'): cur = None; continue
            if line.startswith('msgid '): cur = mid; line = line[6:]
            elif line.startswith('msgstr '): cur = mstr; line = line[7:]
            elif not line.startswith('"'): cur = None if line.startswith('#') else cur; continue
            if cur is not None and line.startswith('"'): cur.append(ast.literal_eval(line))
        i, s = ''.join(mid), ''.join(mstr)
        if i and s: out[norm(i)] = s
    return out

def ordered_stories(md):
    return [(m.group(1).strip().lower(), clean(m.group(2))) for m in re.finditer(r'^#####\s*(.+?)\s*\n(.*?)(?=^#{2,5}\s|\Z)', md, re.S | re.M)]

def translate_md(md, po):
    """Replace every translated paragraph block / section of the markdown with its translation."""
    out = md
    # whole sections first (Stellarium translates each ## section as one string)
    for m in re.finditer(r'^(##+[^\n]*\n)(.*?)(?=^##\s|\Z)', md, re.S | re.M):
        body = m.group(2).strip()
        t = po.get(norm(body))
        if t: out = out.replace(body, t)
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--skycultures', required=True); a = ap.parse_args()
    sc = pathlib.Path(a.skycultures)
    data = json.loads(gzip.decompress((ROOT / 'data/sky.json.gz').read_bytes()))
    extra_p = ROOT / 'tools/sky_i18n_extra.json'
    extra = json.loads(extra_p.read_text()) if extra_p.exists() else {}
    stats = {l: [0, 0, 0, 0] for l in LANGS}  # names, names total, stories, stories total
    for c in data['cultures']:
        cid = c['id']; md = (sc / cid / 'description.md').read_text()
        c['tr'] = {}
        for k in c['cons']: k.pop('t', None)
        for lang in LANGS:
            po = read_po(sc / cid / 'po' / f'{lang}.po')
            ex = extra.get(lang, {}).get(cid, {})
            tr = {}
            t = ex.get('title') or po.get(norm(c['title'])) or po.get(norm(md.splitlines()[0].lstrip('# ')))
            if t: tr['title'] = t
            raw_intro = section(md, 'Introduction')
            ti = po.get(norm(raw_intro))
            if ti:
                ti = clean(ti)
                if len(ti) > 420: ti = ti[:420].rsplit('. ', 1)[0] + '.'
                tr['intro'] = ti
            if ex.get('intro'): tr['intro'] = ex['intro']
            ta = po.get(norm(section(md, 'Authors')))
            if ta and cid != 'kamilaroi':
                ta = re.sub(r'\S+@\S+', '', clean(ta))
                if len(ta) > 300: ta = ta[:300].rsplit(' ', 1)[0] + '…'
                tr['authors'] = ta
            if ex.get('authors'): tr['authors'] = ex['authors']
            if tr: c['tr'][lang] = tr
            md_tr = translate_md(md, po)
            st_tr = stories(md_tr) if md_tr != md else {}
            os_en, os_tr = ordered_stories(md), ordered_stories(md_tr)
            by_pos = {en: tr_ for (en, _), (_, tr_) in zip(os_en, os_tr)} if len(os_en) == len(os_tr) and md_tr != md else {}
            exf = ex.get('figures', {})
            for k in c['cons']:
                e, n = k['e'], k.get('n', '')
                name = exf.get(e, {}).get('e') or po.get(norm(e))
                if cid == 'kamilaroi' and n == 'Emu in the Sky':
                    pass  # the Emu's native name sits in e; its English gloss is n
                rec = {}
                if name and name != e: rec['e'] = name
                if n == 'Emu in the Sky':
                    gl = exf.get(e, {}).get('n') or po.get(norm(n))
                    if gl: rec['n'] = gl
                stats[lang][1] += 1; stats[lang][0] += bool(name)
                if k.get('s'):
                    stats[lang][3] += 1
                    s = exf.get(e, {}).get('s')
                    if not s and md_tr != md:
                        s = (st_tr.get((name or '').lower()) or st_tr.get(e.lower()) or st_tr.get(n.lower())
                             or by_pos.get(e.lower()) or by_pos.get(n.lower()))
                        if s and norm(s[:700]) == norm(k['s']): s = None  # untranslated
                    if s: rec['s'] = s[:700]; stats[lang][2] += 1
                if rec: k.setdefault('t', {})[lang] = rec
    (ROOT / 'data/sky.json.gz').write_bytes(gzip.compress(json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode(), 9, mtime=0))
    for l, (a1, b1, a2, b2) in stats.items(): print(f'{l}: names {a1}/{b1}, stories {a2}/{b2}')
    for c in data['cultures']:
        print(c['id'], {l: sorted(v) for l, v in c['tr'].items()},
              {l: (sum('e' in k.get('t', {}).get(l, {}) for k in c['cons']), sum('s' in k.get('t', {}).get(l, {}) for k in c['cons']), sum(bool(k.get('s')) for k in c['cons'])) for l in LANGS})

if __name__ == '__main__':
    main()
