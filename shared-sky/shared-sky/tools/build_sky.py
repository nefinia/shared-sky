"""Build data/sky.json.gz: bright stars, Milky Way outline, and the sky cultures (lines, artwork, stories).

    git clone --depth 1 https://github.com/Stellarium/stellarium-skycultures.git /tmp/sc
    npm pack d3-celestial@0.7.35 && mkdir -p /tmp/d3c && tar xzf d3-celestial-0.7.35.tgz -C /tmp/d3c
    python tools/build_sky.py --skycultures /tmp/sc --d3celestial /tmp/d3c/package/data
"""
import argparse, base64, gzip, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CULTURES = ['western', 'maori', 'navajo', 'northern_andes', 'boorong', 'tupi', 'inuit', 'aztec', 'hawaiian_starlines',
            'blackfoot', 'tukano', 'lokono', 'tongan', 'anutan']

def section(md, name):
    m = re.search(r'^##+\s*' + name + r'\s*\n(.*?)(?=^##\s|\Z)', md, re.S | re.M)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else ''

def clean(s):
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
    return re.sub(r'\s+', ' ', re.sub(r'[_*]', '', s)).strip()

def stories(md):
    out = {}
    for m in re.finditer(r'^#####\s*(.+?)\s*\n(.*?)(?=^#{2,5}\s|\Z)', md, re.S | re.M):
        out[m.group(1).strip().lower()] = clean(m.group(2))
    for m in re.finditer(r'^\|([^|\n]+)\|([^|\n]+)\|([^|\n]*)\|\s*$', md, re.M):
        a, b, c = [x.strip() for x in m.groups()]
        if a and not set(a) <= set('-') and a.lower() != 'name':
            out.setdefault(a.lower(), b + (' · ' + c if c else ''))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skycultures', required=True)
    ap.add_argument('--d3celestial', required=True, help='the data/ folder of the d3-celestial npm package')
    a = ap.parse_args()
    sc, d3 = pathlib.Path(a.skycultures), pathlib.Path(a.d3celestial)
    s6 = json.loads((d3 / 'stars.6.json').read_text())['features']
    s8 = {f['id']: f for f in json.loads((d3 / 'stars.8.json').read_text())['features']}
    names = json.loads((d3 / 'starnames.json').read_text())
    need, cultures = set(), []
    for c in CULTURES:
        d = json.loads((sc / c / 'index.json').read_text()); md = (sc / c / 'description.md').read_text()
        intro = clean(section(md, 'Introduction'))
        if len(intro) > 420: intro = intro[:420].rsplit('. ', 1)[0] + '.'
        auth = re.sub(r'\S+@\S+', '', clean(section(md, 'Authors')))
        if len(auth) > 300: auth = auth[:300].rsplit(' ', 1)[0] + '…'
        st, cons = stories(md), []
        for k in d['constellations']:
            L = [[x for x in l if isinstance(x, int)] for l in k.get('lines', [])]
            L = [l for l in L if len(l) > 1]
            if not L: continue
            for l in L: need.update(l)
            cn = k['common_name']; e = cn.get('english', ''); n = cn.get('native') or cn.get('pronounce') or ''
            item = {'e': e, 'n': n, 'l': L}
            s = st.get(e.lower()) or st.get(n.lower())
            if s: item['s'] = s[:700]
            cons.append(item)
        cultures.append({'id': c, 'title': md.splitlines()[0].lstrip('# ').strip(), 'region': d.get('region', ''), 'intro': intro,
                         'authors': auth, 'license': section(md, 'License')[:120], 'cons': cons})
    # Kamilaroi/Euahlayi: figures drawn as artwork anchored to three stars each
    k = json.loads((sc / 'kamilaroi/index.json').read_text()); md = (sc / 'kamilaroi/description.md').read_text(); st = stories(md)
    kcons, kimg, emu, anchors_needed = [], {}, None, set()
    for c in k['constellations']:
        im = c['image']; fn = im['file'].split('/')[-1]
        kimg[fn] = base64.b64encode((sc / 'kamilaroi/illustrations' / fn).read_bytes()).decode()
        anchors = [[p['pos'][0], p['pos'][1], p['hip']] for p in im['anchors']]; anchors_needed.update(p[2] for p in anchors)
        if c['id'].endswith('Emu2'): emu['img2'] = {'f': fn, 'size': im['size'], 'a': anchors}; continue
        name = c['common_name']['english']
        e = {'e': name, 'n': '', 'l': [], 'img': {'f': fn, 'size': im['size'], 'a': anchors}, 's': (st.get(name.lower()) or '')[:700]}
        if c['id'].endswith('Emu1'): e['n'] = 'Emu in the Sky'; emu = e
        kcons.append(e)
    cultures.append({'id': 'kamilaroi', 'title': 'Kamilaroi/Euahlayi', 'region': 'Oceania', 'intro': clean(section(md, 'Introduction'))[:420],
                     'authors': 'Robert Fuller (Macquarie University), with Kamilaroi and Euahlayi knowledge holders; artwork from the Stellarium sky culture.',
                     'license': 'CC BY-SA', 'cons': kcons})
    stars = {f['id']: f for f in s6 if f['properties']['mag'] <= 5.8}
    for h in need | anchors_needed:
        if h not in stars and h in s8: stars[h] = s8[h]
    out = []
    for h, f in stars.items():
        ra, dec = f['geometry']['coordinates']
        try: bv = float(f['properties'].get('bv') or 0.6)
        except ValueError: bv = 0.6
        out.append([h, round(ra % 360, 4), round(dec, 4), round(f['properties']['mag'], 2), round(bv, 2)])
    out.sort(key=lambda s: s[3])
    sn = {h: v['name'] for h, v in ((int(h), v) for h, v in names.items()) if h in stars and stars[h]['properties']['mag'] < 2.6 and v.get('name')}
    mw = []
    for f in json.loads((d3 / 'mw.json').read_text())['features']:
        rings = [[[round(p[0] % 360, 1), round(p[1], 1)] for p in ring[::2]] for poly in f['geometry']['coordinates'] for ring in poly]
        mw.append({'id': f['id'], 'p': [r for r in rings if len(r) > 3]})
    data = {'stars': out, 'names': sn, 'mw': mw, 'cultures': cultures, 'kimg': kimg}
    (ROOT / 'data/sky.json.gz').write_bytes(gzip.compress(json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode(), 9))
    print(f'{len(out)} stars, {len(cultures)} sky cultures')

if __name__ == '__main__':
    main()
