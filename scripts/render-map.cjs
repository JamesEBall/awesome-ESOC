#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const {readOcad} = require('ocad2geojson');
const OcadTiler = require('ocad-tiler');
const {render} = require('ocad2tiles');
async function main(){
 const [input,sessionFile,output] = process.argv.slice(2);
 if(!input||!sessionFile||!output) throw new Error('Usage: node scripts/render-map.cjs input.ocd session.json output.png');
 const session=JSON.parse(fs.readFileSync(sessionFile,'utf8'));
 const m=session.map, bounds=m.bounds;
 if(!Array.isArray(bounds)||bounds.length!==4||!bounds.every(Number.isFinite)||bounds[0]>=bounds[2]||bounds[1]>=bounds[3]) throw new Error('Invalid projected bounds');
 if(!Number.isFinite(m.scale)||m.scale<=0) throw new Error('Invalid print scale');
 const file=await readOcad(input), crs=file.getCrs();
 // Exclude only individually verified layout objects from this in-memory copy.
 const excluded=new Set(m.exclude_objects||[]);
 if(excluded.size) file.objects=file.objects.filter(o=>!excluded.has(o.objIndex._index));
 const dpi=m.dpi||400, resolution=m.scale/1000*25.4/dpi;
 fs.mkdirSync(path.dirname(output),{recursive:true});
 await render(new OcadTiler(file),bounds,resolution,{outputPath:output,fill:'white'});
 fs.writeFileSync(output+'.info.json',JSON.stringify({source:path.basename(input),sourceScale:crs.scale,printScale:m.scale,crs:crs.code||crs.gridId||crs.epsg||null,bounds,excludedObjects:[...excluded],resolutionMetresPerPixel:resolution,warnings:file.warnings||[]},null,2)+'\n');
 console.log(output);
}
main().catch(e=>{console.error(e.message);process.exit(1)});
