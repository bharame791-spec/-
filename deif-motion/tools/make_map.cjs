// Builds assets/map.json: outline of historic Palestine + Gaza Strip as SVG paths
const path=require('path');
const NM=process.argv[2]; // node_modules dir
const w=require(path.join(NM,'world-atlas/countries-50m.json'));
const t=require(path.join(NM,'topojson-client'));
const d3=require(path.join(NM,'d3-geo'));
const geoms=w.objects.countries.geometries;
const isr=geoms.find(g=>g.id==='376'), pal=geoms.find(g=>g.id==='275');
const outline=t.merge(w,[isr,pal]);
const palF=t.feature(w,pal);
const gaza={type:'Feature',geometry:{type:'Polygon',coordinates:palF.geometry.coordinates.find(p=>p[0][0][0]<34.6)}};
const W=700,H=1200;
const proj=d3.geoMercator().fitExtent([[40,40],[W-40,H-40]],{type:'Feature',geometry:outline});
const gp=d3.geoPath(proj);
const ky=proj([34.30,31.345]), gc=proj([34.39,31.42]);
require('fs').writeFileSync(process.argv[3],JSON.stringify({W,H,outline:gp(outline),gaza:gp(gaza),khanYunis:ky,gazaCenter:gc}));
console.log('map ok',ky,gc);
