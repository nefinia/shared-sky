"""Turn a TLE catalogue and CelesTrak's SATCAT into data/orbits.json.gz.

    python tools/build_orbits.py --tle catalog.tle --satcat satcat.csv [--updated 2026-09-25T13:53:29Z]

The TLE file is the three-line format (name, line 1, line 2). The GitHub workflow in
.github/workflows/update.yml fetches both files from CelesTrak once a day.
"""
import argparse, csv, datetime, gzip, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TYPES = ['PAY', 'R/B', 'DEB', 'UNK']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tle', required=True)
    ap.add_argument('--satcat', required=True)
    ap.add_argument('--updated', default=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    a = ap.parse_args()
    lines = pathlib.Path(a.tle).read_text(errors='replace').splitlines()
    sats = {}
    i = 0
    while i < len(lines) - 2:
        if lines[i+1].startswith('1 ') and lines[i+2].startswith('2 '):
            sats[int(lines[i+1][2:7])] = (lines[i].strip(), lines[i+1].rstrip(), lines[i+2].rstrip()); i += 3
        else:
            i += 1
    cat = {int(r['NORAD_CAT_ID']): r for r in csv.DictReader(open(a.satcat, newline='', encoding='utf-8', errors='replace'))}
    owners, idx, out = [], {}, []
    for nid, (name, l1, l2) in sats.items():
        r = cat.get(nid, {})
        t = r.get('OBJECT_TYPE') or ('DEB' if ' DEB' in name else 'R/B' if 'R/B' in name else 'UNK')
        o = r.get('OWNER') or '?'
        if o not in idx: idx[o] = len(owners); owners.append(o)
        year = (r.get('LAUNCH_DATE') or '')[:4]
        out.append([name, l1, l2, TYPES.index(t) if t in TYPES else 3, idx[o], int(year) if year.isdigit() else 0])
    data = {'sats': out, 'types': TYPES, 'owners': owners, 'epoch': a.updated}
    (ROOT / 'data/orbits.json.gz').write_bytes(gzip.compress(json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode(), 9))
    print(f'{len(out):,} objects, updated {a.updated}')

if __name__ == '__main__':
    main()
