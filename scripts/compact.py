#!/usr/bin/env python3
"""Two cropped maps per portrait A4; source scale is preserved."""
import argparse,copy,json,shutil
from pathlib import Path
from build import preamble,map_content,tex,compile_tex,KIT

def panel(d,name,mode,b,top):
 unit=1000/d['map']['scale'];w=(b[2]-b[0])*unit;h=(b[3]-b[1])*unit
 assert 0<w<=194 and 0<h<=119,'Crop too large for a half sheet at this scale'
 source=d['map']['bounds']
 assert source[0]<=b[0]<b[2]<=source[2] and source[1]<=b[1]<b[3]<=source[3],'Crop outside source map'
 left=(210-w)/2;bottom=top-12-h
 # Translate the original full map, then clip it: no rescaling or stretching.
 local=copy.deepcopy(d);orig=d['map']['bounds'];local['map']['x_mm']=left+(orig[0]-b[0])*unit;local['map']['y_mm']=bottom+(orig[1]-b[1])*unit
 c=d['courses'].get(name,{});seq=c.get('controls',[])
 used=list(d['points']) if mode=='all' else ['S','J']+seq
 for k in used:
  x,y=d['points'][k]['xy'];assert b[0]+8<=x<=b[2]-8 and b[1]+8<=y<=b[3]-8,f'{name}: {k} too close to crop'
 out=[rf'\begin{{scope}}\clip ({left},{bottom}) rectangle ++({w},{h});',map_content(local,mode,seq),r'\end{scope}']
 title=name if name else 'All controls';length=f" · {c['distance_m']} m" if c.get('distance_m') else ''
 out += [rf'\Put{{{left}}}{{{top}}}{{90}}{{12}}{{\bfseries\color{{ESOCGreen}}{tex(title)}}}',rf'\Put{{{left+25}}}{{{top-1}}}{{80}}{{8}}{{1:{d["map"]["scale"]:,}{tex(length)}}}',rf'\node[anchor=north east,inner sep=0pt] at ({left+w},{top+1}) {{\includegraphics[height=8mm]{{assets/esoc-logo.png}}}};']
 bar=50*unit;bx=left+w-43;by=top-4
 out +=[rf'\draw[line width=.25mm] ({bx},{by})--++({bar},0);',rf'\Put{{{bx}}}{{{by-2}}}{{35}}{{6}}{{50 m}}']
 for x in [bx,bx+bar]:out.append(rf'\draw[line width=.25mm] ({x},{by-1})--++(0,2);')
 credits=d.get('copyright',[])
 for i,line in enumerate(credits):out.append(rf'\Put{{{left}}}{{{bottom-1-i*3}}}{{{w}}}{{5.5}}{{{tex(line)}}}')
 return '\n'.join(out)

def build(d,names,mode,path,engine):
 out=[preamble(d['title'],d.get('author',''),'portrait')]
 for i in range(0,len(names),2):
  pair=names[i:i+2]
  if len(pair)==1:pair*=2 # useful spare on the otherwise unused half
  out += [r'\SheetStart',r'\draw[ESOCRule,dashed,line width=.15mm] (8,148.5)--(202,148.5);']
  for name,top in zip(pair,[287,144]):
   bounds=d['print_layout']['all_bounds'] if mode=='all' else d['courses'][name]['crop_bounds']
   out.append(panel(d,name,mode,bounds,top))
  out.append(r'\SheetEnd')
 out.append(r'\end{document}');path.write_text('\n'.join(out));compile_tex(path,engine)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('session',type=Path);ap.add_argument('--outdir',type=Path,required=True);ap.add_argument('--engine',default='tectonic');a=ap.parse_args();d=json.loads(a.session.read_text());o=a.outdir;o.mkdir(parents=True,exist_ok=True)
 shutil.copytree(KIT/'assets',o/'assets',dirs_exist_ok=True);shutil.copy2(a.session.parent/d['map']['file'],o/'map.png')
 all_names=[]
 for p in d['packs']:
  mode=p.get('mode','normal');names=p['courses'] or [''];build(d,names,mode,o/(p['file']+'.tex'),a.engine)
  if mode=='normal':all_names+=names
 build(d,all_names,'normal',o/'00-all-course-maps.tex',a.engine)
 for f in a.session.parent.glob('*.tex'):
  shutil.copy2(f,o/f.name);compile_tex(o/f.name,a.engine)
if __name__=='__main__':main()
