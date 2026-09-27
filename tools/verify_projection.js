// Check: a star drawn at (zenith distance, azimuth) from the observer must land exactly on its geographic position
// (latitude = declination, longitude = RA − Greenwich sidereal time), for any observer.
const sat = require('satellite.js');
const D2R = Math.PI/180, R2D = 180/Math.PI;
function altaz(ra, dec, lst, phi){ const H = lst - ra, sd = Math.sin(dec), cd = Math.cos(dec), sp = Math.sin(phi), cp = Math.cos(phi), cH = Math.cos(H);
  return [Math.asin(sp*sd + cp*cd*cH), Math.atan2(-cd*Math.sin(H), sd*cp - cd*cH*sp)]; }
function dest(lat, lon, bearing, dist){ // great-circle destination
  const p1 = lat*D2R, l1 = lon*D2R; const p2 = Math.asin(Math.sin(p1)*Math.cos(dist) + Math.cos(p1)*Math.sin(dist)*Math.cos(bearing));
  const l2 = l1 + Math.atan2(Math.sin(bearing)*Math.sin(dist)*Math.cos(p1), Math.cos(dist) - Math.sin(p1)*Math.sin(p2)); return [p2*R2D, ((l2*R2D+540)%360)-180]; }
const stars = [['Sirius',101.287,-16.716],['Antares',247.352,-26.432],['Acrux',186.650,-63.099],['Altair',297.696,8.868],['Vega',279.234,38.784]];
const obs = [['Sydney',-33.8688,151.2093],['Paris',48.8566,2.3522],['Atacama',-22.9087,-68.1997]];
const t = new Date(Date.UTC(2026,8,26,10,30)); const g = sat.gstime(t); let worst = 0;
for (const [on,la,lo] of obs) for (const [sn,ra,dec] of stars){
  const [al,az] = altaz(ra*D2R, dec*D2R, g + lo*D2R, la*D2R);
  const [plat, plon] = dest(la, lo, az, Math.PI/2 - al);
  const gpLat = dec, gpLon = ((ra - g*R2D + 540)%360) - 180;
  const err = Math.acos(Math.min(1, Math.sin(plat*D2R)*Math.sin(gpLat*D2R) + Math.cos(plat*D2R)*Math.cos(gpLat*D2R)*Math.cos((plon-gpLon)*D2R)))*6371;
  worst = Math.max(worst, err);
  if (on === 'Sydney') console.log(`${sn.padEnd(8)} from ${on}: alt ${(al*R2D).toFixed(1)}°, placed at ${plat.toFixed(3)}, ${plon.toFixed(3)} · geographic position ${gpLat.toFixed(3)}, ${gpLon.toFixed(3)}`);
}
console.log('largest difference over 15 star/observer pairs:', worst.toExponential(2), 'km');
