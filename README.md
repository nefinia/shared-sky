# Shared Sky

**The sky above any place and moment, laid one-to-one onto the Earth.** Indigenous and Western constellations, and every publicly tracked object in orbit passing through them.

Made for [YOHAKU 余白](https://www.space4innovation.com/yohaku), the Space4Innovation hackathon on space debris, AI and Indigenous knowledge (25–27 September 2026). Submitted to Challenge 1, *Caring for Sky Country*, and Challenge 2, *Seven Generations in Orbit*: how can we decide which pieces of space debris humanity should take responsibility for first?

## The idea

A star at zenith distance *z* and azimuth *A* is directly overhead at the point on Earth *z* × 111.2 km away on bearing *A*. That point is its *geographic position*, the same fact celestial navigators use. So one globe can hold both the land and the sky, drawn as the real Earth seen from space (orthographic projection):

- **1° of sky = 111.2 km of ground**, at every zoom.
- Your zenith sits on your spot, and your horizon is a great circle 10,008 km out: exactly half of the Earth. Centre the globe on yourself and the horizon is its edge.
- A constellation lies over the part of the Earth where it is overhead. Tonight the Kamilaroi **Emu in the Sky** stretches from the Southern Ocean to Indonesia, seen from Sydney.
- Satellites and debris can be drawn two ways: **as seen in your sky** (lined up with the stars) or **physically overhead** (the ground they are flying above).

## What you can do

- **Sky on the land:** the one-to-one map over real shaded-relief terrain. Pan, zoom, save as PNG, and switch every layer on or off (land, night light, places, stars, Milky Way, figures, names, Western lines, objects, paths, rings).
- **Standing there (3D):** the same sky above an illustrative landscape, from the ground.
- **One figure:** a long-exposure view of every object crossing one constellation.
- **Whole sky:** the classic all-sky dome.
- **Choose any place and moment:** city search (7,342 cities), coordinates, map links, tap the map, or *Use my location* when the page is hosted on its own site. Date and time go from 1900 to 2100.
- **"Does it pass over…?"** finds when a figure is at your zenith in a dark sky, lists the cities it passes over, and jumps there with *Take me there*.
- **Paths ahead:** where each object crossing the figure is now, and where it goes over the next 10–60 minutes, with who launched it and when.
- **Seven generations in orbit:** how long each object will stay up, how many will still be there in seven generations (about 175 years), who they are registered to, and a ranked list of which pieces to take responsibility for first. Four sliders (future generations, crowding, size, shared skies) set how much each value counts, so the ranking is a conversation rather than a verdict. The seven-generations view dims what will come down on its own and marks the first 20 in line on the sky. Tap any object to see its orbit, how long it will stay, how much of the Earth it passes over and its place in line.

**Live:** [sofiagallego.com/shared-sky](https://sofiagallego.com/shared-sky/) · by [Sofia Gallego](https://sofiagallego.com)

**What comes next** (skies uploaded and controlled by the communities who hold them, listening to the sky, and more) is in [FUTURE.md](FUTURE.md).

## Run it

`index.html` is a single self-contained file. Open it in a browser, or publish the repository with GitHub Pages.
Because this repository lives under the same GitHub account as [sofiagallego.com](https://sofiagallego.com) (`nefinia.github.io`), GitHub Pages serves it automatically at **https://sofiagallego.com/shared-sky/**.

### Publish with GitHub Pages (daily orbit refresh)

1. Push this repository to GitHub.
2. In **Settings → Pages**, set **Source** to **GitHub Actions**.
3. The workflow in `.github/workflows/update.yml` runs on every push and once a day. It downloads the public orbit catalogue from CelesTrak, rebuilds `index.html`, commits it and publishes the site. You can also run it by hand from the **Actions** tab.

## Build it yourself

```bash
pip install -r tools/requirements.txt

# orbits (daily): three-line TLE catalogue + CelesTrak SATCAT
python tools/build_orbits.py --tle catalog.tle --satcat satcat.csv

# sky (rarely): stars, Milky Way, sky cultures
git clone --depth 1 https://github.com/Stellarium/stellarium-skycultures.git /tmp/sc
npm pack d3-celestial@0.7.35 && mkdir -p /tmp/d3c && tar xzf d3-celestial-0.7.35.tgz -C /tmp/d3c
python tools/build_sky.py --skycultures /tmp/sc --d3celestial /tmp/d3c/package/data

# land (rarely): Natural Earth relief, borders, cities, peaks
python tools/build_earth.py

# assemble index.html
python tools/build.py
```

| Path | What it is |
|---|---|
| `src/template.html` | The app: layout, styles and all code |
| `data/orbits.json.gz` | Orbital elements for ~31,000 objects, with type, owner and launch year |
| `data/sky.json.gz` | Stars, Milky Way, 15 sky cultures (lines, artwork, stories) |
| `data/earth.json` | World and local shaded relief, borders, cities, peaks |
| `vendor/` | three.js and satellite.js (MIT) |
| `tools/` | Scripts that rebuild the data and the page |

## Limits, stated plainly

- **Debris positions** come from one snapshot of the public catalogue and are reliable only within about ±7 days of it. Outside that window the page shows stars and figures only. With the daily workflow, "today" is always covered.
- **Lifetimes and the ranking are rough.** Decay times come from a rule of thumb by height and vary several-fold with solar activity and each object's shape and mass. Masses are typical values for each kind of object (named for the heaviest rocket-stage families). The ranking is for thinking together, not an official risk rating.
- **Only objects larger than about 10 cm are tracked.** Millions of smaller fragments are not in any public catalogue.
- **Sky cultures:** the open datasets hold 15 sky cultures. **Mapuche, Lakota, Maya Kaqchikel, Shuar, Gadigal and Samburu skies are not here.** They should be added only if those communities choose to share them, on their terms.
- **The 3D landscape is illustrative.** The one-to-one map uses real relief from Natural Earth, at about 2 km per pixel near the featured places and coarser elsewhere.

## Indigenous knowledge

The Kamilaroi/Euahlayi, Boorong and other Indigenous sky cultures here come from openly licensed Stellarium contributions, each credited in the app and in [CREDITS.md](CREDITS.md). This project follows the [CARE Principles for Indigenous Data Governance](https://www.gida-global.org/care): Collective benefit, Authority to control, Responsibility, Ethics. If you are a knowledge holder and want a figure corrected, described differently or removed, please open an issue. That request comes before anything else.

## Credits and licences

Code: MIT, © 2026 Sofia Gallego ([LICENSE](LICENSE)). Data and libraries keep their own licences, listed in [CREDITS.md](CREDITS.md). Some are ShareAlike or non-commercial, so the built `index.html` carries those terms too.
