"""Build data/earth.json: shaded-relief land (world + detailed crops around the featured places), borders, cities, peaks.
All sources are Natural Earth (public domain), fetched from its GitHub mirrors.

    pip install numpy pillow
    python tools/build_earth.py
"""
import base64, io, json, pathlib, urllib.request
import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
VEC = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/'
RAS = 'https://raw.githubusercontent.com/nvkelso/natural-earth-raster/master/'
HR = RAS + '10m_rasters/HYP_HR_SR_OB_DR/HYP_HR_SR_OB_DR.tif'   # 21600 x 10800, uncompressed, one row per strip
W, ROW, OFF, HALF = 21600, 21600*3, 22026, 5.0
PLACES = {'sydney': (-33.8688, 151.2093), 'tyrrell': (-35.33, 142.80), 'atacama': (-22.9087, -68.1997), 'temuco': (-38.7359, -72.5904),
          'pine': (43.0255, -102.5563), 'navajo': (35.6806, -109.0526), 'tecpan': (14.7667, -90.9944), 'macas': (-2.3087, -78.1114),
          'maralal': (1.0968, 36.6981), 'oukaimeden': (31.2064, -7.8664), 'auckland': (-36.8485, 174.7633), 'tama': (35.6369, 139.4468),
          'paris': (48.8566, 2.3522)}

def get(url, rng=None):
    req = urllib.request.Request(url, headers={'Range': f'bytes={rng[0]}-{rng[1]}'} if rng else {})
    with urllib.request.urlopen(req, timeout=600) as r: return r.read()

def crop(lat, lon):
    r0, r1 = int((90 - (lat + HALF))*60), int((90 - (lat - HALF))*60)
    rows = np.frombuffer(get(HR, (OFF + r0*ROW, OFF + r1*ROW - 1)), np.uint8).reshape(r1 - r0, W, 3)
    hw = HALF/np.cos(np.radians(lat)); c0, c1 = int((lon - hw + 180)*60), int((lon + hw + 180)*60)
    buf = io.BytesIO(); Image.fromarray(rows[:, np.arange(c0, c1) % W, :]).save(buf, 'JPEG', quality=82)
    return {'b': [90 - r0/60, 90 - r1/60, c0/60 - 180, c1/60 - 180], 'img': base64.b64encode(buf.getvalue()).decode()}

def main():
    local = {k: crop(*v) for k, v in PLACES.items()}
    Image.MAX_IMAGE_PIXELS = None
    g = Image.open(io.BytesIO(get(RAS + '50m_rasters/HYP_50M_SR_W/HYP_50M_SR_W.tif'))).convert('RGB').resize((2400, 1200), Image.LANCZOS)
    buf = io.BytesIO(); g.save(buf, 'JPEG', quality=80)
    places = [[f['properties'][k] for k in ('name', 'latitude', 'longitude', 'scalerank', 'adm0name', 'pop_max')]
              for f in json.loads(get(VEC + 'ne_10m_populated_places_simple.geojson'))['features']]
    places = [[p[0], round(p[1], 3), round(p[2], 3), p[3], p[4] or '', p[5] or 0] for p in places]
    peaks = [[f['properties']['name'], round(f['properties']['lat_y'], 2), round(f['properties']['long_x'], 2), f['properties']['elevation'], f['properties']['scalerank']]
             for f in json.loads(get(VEC + 'ne_10m_geography_regions_elevation_points.geojson'))['features'] if f['properties']['name']]
    borders = []
    for f in json.loads(get(VEC + 'ne_50m_admin_0_boundary_lines_land.geojson'))['features']:
        gm = f['geometry']; lines = gm['coordinates'] if gm['type'] == 'MultiLineString' else [gm['coordinates']]
        for l in lines: borders.append([v for p in l for v in (round(p[0], 2), round(p[1], 2))])
    out = {'local': local, 'global': base64.b64encode(buf.getvalue()).decode(), 'places': places, 'peaks': peaks, 'borders': borders}
    (ROOT / 'data/earth.json').write_text(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
    print(f'{len(local)} local relief crops, {len(places)} places, {len(peaks)} peaks')

if __name__ == '__main__':
    main()
