#!/usr/bin/env python3
"""Fetch the public orbit catalogue (TLEs) and the SATCAT, for tools/build_orbits.py.

    python tools/fetch_catalog.py --tle-out /tmp/catalog.tle --satcat-out /tmp/satcat.csv

Tries Space-Track.org first (one authenticated bulk query for the whole catalogue —
far gentler on rate limits than CelesTrak's one-request-per-launch-year public endpoint),
using SPACETRACK_USER/SPACETRACK_PASS from the environment. Falls back to CelesTrak's
per-launch-year endpoint, stopping immediately on any non-200/404 response per their
usage policy, if Space-Track isn't configured or fails. Exits non-zero and writes
nothing usable if both fail, so the caller can leave yesterday's data in place
instead of overwriting it with an empty or partial catalogue.
"""
import argparse, csv, io, sys, time, urllib.error, urllib.parse, urllib.request, http.cookiejar, os

UA = "shared-sky-bot/1.0 (+https://github.com/nefinia/shared-sky)"
MIN_OBJECTS = 20000


def _count_tle_objects(text):
    return sum(1 for line in text.splitlines() if line.startswith('1 '))


def fetch_spacetrack(tle_out, satcat_out):
    user = os.environ.get('SPACETRACK_USER')
    pw = os.environ.get('SPACETRACK_PASS')
    if not user or not pw:
        print('space-track: no SPACETRACK_USER/SPACETRACK_PASS set, skipping', file=sys.stderr)
        return False
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [('User-Agent', UA)]
    try:
        login_data = urllib.parse.urlencode({'identity': user, 'password': pw}).encode()
        with opener.open('https://www.space-track.org/ajaxauth/login', login_data, timeout=60) as r:
            if r.status != 200:
                print(f'space-track login: HTTP {r.status}', file=sys.stderr); return False
            body = r.read().decode(errors='replace')
            if '"Login":"Failed"' in body or 'error' in body.lower()[:200]:
                print(f'space-track login rejected: {body[:200]}', file=sys.stderr); return False

        # One bulk query: every object with a recent element set that hasn't decayed.
        gp_url = ('https://www.space-track.org/basicspacedata/query/class/gp/'
                  'decay_date/null-val/epoch/%3Enow-30/orderby/norad_cat_id/format/3le')
        with opener.open(gp_url, timeout=180) as r:
            if r.status != 200:
                print(f'space-track gp query: HTTP {r.status}', file=sys.stderr); return False
            tle_data = r.read().decode(errors='replace')
        n = _count_tle_objects(tle_data)
        if n < MIN_OBJECTS:
            print(f'space-track gp query returned only {n} objects, treating as a failure', file=sys.stderr)
            return False

        satcat_url = 'https://www.space-track.org/basicspacedata/query/class/satcat/orderby/NORAD_CAT_ID/format/csv'
        with opener.open(satcat_url, timeout=180) as r:
            if r.status != 200:
                print(f'space-track satcat query: HTTP {r.status}', file=sys.stderr); return False
            satcat_raw = r.read().decode(errors='replace')
        rows = list(csv.DictReader(io.StringIO(satcat_raw)))
        if not rows:
            print('space-track satcat query returned no rows', file=sys.stderr); return False

        # Space-Track's SATCAT names columns COUNTRY / LAUNCH; CelesTrak's (which
        # tools/build_orbits.py was written against) uses OWNER / LAUNCH_DATE. Rename
        # so build_orbits.py reads either source without caring which one ran.
        with open(satcat_out, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=['NORAD_CAT_ID', 'OBJECT_TYPE', 'OWNER', 'LAUNCH_DATE'])
            w.writeheader()
            for row in rows:
                w.writerow({
                    'NORAD_CAT_ID': row.get('NORAD_CAT_ID', ''),
                    'OBJECT_TYPE': row.get('OBJECT_TYPE', ''),
                    'OWNER': row.get('COUNTRY', row.get('OWNER', '')),
                    'LAUNCH_DATE': row.get('LAUNCH', row.get('LAUNCH_DATE', '')),
                })
        with open(tle_out, 'w', encoding='utf-8') as f:
            f.write(tle_data)
        print(f'space-track: {n:,} objects')
        return True
    except Exception as e:
        print(f'space-track fetch failed: {e}', file=sys.stderr)
        return False
    finally:
        try:
            opener.open('https://www.space-track.org/ajaxauth/logout', timeout=30)
        except Exception:
            pass


def fetch_celestrak(tle_out, satcat_out):
    stopped_early = None
    open(tle_out, 'w').close()
    for y in range(1958, int(time.strftime('%Y')) + 1):
        url = f'https://celestrak.org/NORAD/elements/gp.php?INTDES={y}&FORMAT=tle'
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                code, body = r.status, r.read().decode(errors='replace')
        except urllib.error.HTTPError as e:
            code, body = e.code, ''
        except Exception as e:
            print(f'celestrak INTDES={y}: {e}', file=sys.stderr)
            stopped_early = f'{y} (error)'
            break
        if code == 200 and '\n1 ' in ('\n' + body):
            with open(tle_out, 'a') as out:
                out.write(body)
        elif code == 404:
            pass  # no objects catalogued for this launch year; not an error
        else:
            # CelesTrak's usage policy says stop immediately on any non-200/404 response
            # instead of hammering further — that's what got this blocked before.
            print(f'celestrak returned HTTP {code} for INTDES={y}; stopping, per celestrak.org/usage-policy.php', file=sys.stderr)
            stopped_early = f'{y} (HTTP {code})'
            break
        time.sleep(0.5)

    try:
        req = urllib.request.Request('https://celestrak.org/pub/satcat.csv', headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            open(satcat_out, 'wb').write(r.read())
    except Exception as e:
        print(f'celestrak satcat fetch failed: {e}', file=sys.stderr)
        return False

    n = _count_tle_objects(open(tle_out, encoding='replace').read())
    if stopped_early or n < MIN_OBJECTS:
        print(f'celestrak: only {n} objects' + (f', stopped at {stopped_early}' if stopped_early else ''), file=sys.stderr)
        return False
    print(f'celestrak: {n:,} objects')
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tle-out', required=True)
    ap.add_argument('--satcat-out', required=True)
    a = ap.parse_args()

    if fetch_spacetrack(a.tle_out, a.satcat_out):
        print('source: space-track')
        return 0
    print('space-track unavailable or failed; falling back to celestrak', file=sys.stderr)
    if fetch_celestrak(a.tle_out, a.satcat_out):
        print('source: celestrak')
        return 0
    print('::error::Could not refresh the orbit catalogue from either space-track or celestrak today.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
