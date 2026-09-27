"""Assemble index.html: the page template + vendored libraries + data, all inlined into one self-contained file.

    python tools/build.py            # writes index.html at the repository root
"""
import base64, gzip, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def main():
    sky = json.loads(gzip.decompress((ROOT / 'data/sky.json.gz').read_bytes()))
    orbits = json.loads(gzip.decompress((ROOT / 'data/orbits.json.gz').read_bytes()))
    sky.update(orbits)  # sats, types, owners, epoch
    blob = base64.b64encode(gzip.compress(json.dumps(sky, separators=(',', ':'), ensure_ascii=False).encode(), 9)).decode()
    page = (ROOT / 'src/template.html').read_text()
    page = (page.replace('__EARTH__', (ROOT / 'data/earth.json').read_text())
                .replace('__THREE__', (ROOT / 'vendor/three.min.js').read_text())
                .replace('__SATLIB__', (ROOT / 'vendor/satellite.min.js').read_text())
                .replace('__DATA__', blob))
    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="description" content="The sky above any place and moment mapped one-to-one onto the Earth, with Indigenous and Western constellations and every tracked object in orbit.">\n'
            '<style>html{color-scheme:dark}[hidden]{display:none!important}body{margin:0}</style>\n')
    # the template starts with <title> and <style>; they belong in <head>, the rest in <body>
    split = page.index('<div class="app"')
    out = head + page[:split] + '</head>\n<body>\n' + page[split:] + '\n</body>\n</html>\n'
    (ROOT / 'index.html').write_text(out)
    print(f'index.html: {len(out)/1e6:.2f} MB, orbits measured up to {orbits["epoch"]}, {len(orbits["sats"]):,} objects')

if __name__ == '__main__':
    main()
