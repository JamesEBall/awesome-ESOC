#!/usr/bin/env python3
"""Render map sheets as LaTeX; compile using Tectonic or XeLaTeX."""
from pathlib import Path
import argparse,json,math,subprocess,shutil,sys,re
KIT=Path(__file__).resolve().parents[1]

def tex(s):
 return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in str(s))
def coord(p):return f'({p[0]:.3f},{p[1]:.3f})'
def validate(d):
 b=d['map']['bounds'];scale=d['map']['scale']
 assert d['map'].get('orientation','landscape') in ['landscape','portrait'],'Invalid orientation'
 assert len(b)==4 and b[0]<b[2] and b[1]<b[3] and scale>0,'Invalid map extent/scale'
 land=d['map'].get('orientation','landscape')=='landscape'
 assert (b[2]-b[0])*1000/scale<=(281.01 if land else 194.01) and (b[3]-b[1])*1000/scale<=(194.01 if land else 281.01),'Map exceeds A4 content area'
 for k,p in d['points'].items():
  x,y=p['xy'];assert b[0]<=x<=b[2] and b[1]<=y<=b[3],f'{k} outside map'
 for name,c in d['courses'].items():
  assert d.get('allow_two_controls',False) or len(c['controls'])!=2,f'{name}: use one control or at least three'
  if c.get('distance_m') is not None:
   assert 0<c['distance_m']<=d.get('max_total_m',float('inf')),f'{name}: invalid distance or exceeds cap'
  assert c['controls'] and all(str(x) in d['points'] for x in c['controls']),f'{name}: missing control'
 for p in d['packs']:
  assert re.fullmatch(r'[A-Za-z0-9_-]+',p['file']),'Pack filename must be a simple basename'
  assert p.get('mode','normal') in ['normal','score','all','blank'],'Unknown map mode'
  assert all(n in d['courses'] for n in p['courses']),'Unknown course in pack'
  if p.get('mode','normal')=='normal':
   assert all(d['courses'][n].get('distance_m') for n in p['courses']),'Normal courses need a measured distance'


def preamble(title,author="",orientation="landscape"):return r'''\documentclass[10pt,a4paper]{article}
\usepackage{assets/esoc}
\hypersetup{pdfauthor={'''+tex(author)+r'''},pdftitle={'''+tex(title)+r'''}}
\geometry{a4paper,'''+orientation+r''',margin=8mm}
\begin{document}
'''

def map_content(d,mode,seq):
 m=d['map'];b=m['bounds'];unit=1000/m['scale'];x0=m.get('x_mm',15);y0=m.get('y_mm',92)
 width=(b[2]-b[0])*unit;height=(b[3]-b[1])*unit
 def pos(pt):return (x0+(pt[0]-b[0])*unit,y0+(pt[1]-b[1])*unit)
 def point(k):return pos(d['points'][k]['xy'])
 out=[rf'\node[anchor=south west,inner sep=0pt] at ({x0},{y0}) {{\includegraphics[width={width:.4f}mm,height={height:.4f}mm]{{map.png}}}};',rf'\draw[ESOCRule,line width=.15mm] ({x0},{y0}) rectangle ++({width:.4f},{height:.4f});']
 if mode!='blank':
  # Aim the triangle along the marked access, or towards the first control.
  sx,sy=point('S')
  towards=next((pos(p) for p in d.get('access',[]) if math.dist(pos(p),(sx,sy))>.1),None)
  if towards is None:towards=point(seq[0]) if mode=='normal' and seq else (sx,sy+1)
  angle=math.atan2(towards[1]-sy,towards[0]-sx)
  vertices=[(sx+3.2*math.cos(angle+i*2*math.pi/3),sy+3.2*math.sin(angle+i*2*math.pi/3)) for i in range(3)]
  out+=[rf'\draw[CoursePurple,line width=.35mm] ({sx},{sy}) circle[radius=3.8mm];',rf'\draw[CoursePurple,line width=.35mm] ({sx},{sy}) circle[radius=3mm];',r'\draw[CoursePurple,line width=.35mm] '+'--'.join(map(coord,vertices))+'--cycle;']
  path=[pos(p) for p in d.get('access',[])];start=path[0] if path else (sx,sy)
  # Stop the marked path at the outside of the combined symbol.
  for i,p in enumerate(path[1:],1):
   if math.dist(start,p)>4:
    prev=path[i-1];a=math.dist(start,prev);z=math.dist(prev,p);t=max(0,min(1,(4-a)/z))
    path=[(prev[0]+t*(p[0]-prev[0]),prev[1]+t*(p[1]-prev[1]))]+path[i:];break
  if path:out.append(r'\draw[CoursePurple,line width=.35mm,dash pattern=on 1.2mm off .8mm] '+'--'.join(map(coord,path))+';')
 if mode=='normal':
  route=['J']+seq+['J']
  for a,bk in zip(route,route[1:]):
   base_gap=4.2 if math.dist(point('J'),point('S'))<.01 else 0
   p=point(a);q=point(bk);dist=math.dist(p,q);ra=base_gap if a=='J' else 3.4;rb=base_gap if bk=='J' else 3.4
   if dist<=ra+rb:continue
   v=((q[0]-p[0])/dist,(q[1]-p[1])/dist)
   p=(p[0]+v[0]*ra,p[1]+v[1]*ra);q=(q[0]-v[0]*rb,q[1]-v[1]*rb)
   out.append(r'\draw[CoursePurple,line width=.35mm] '+coord(p)+'--'+coord(q)+';')
 if mode=='all':seq=[k for k in d['points'] if k not in ['S','J','F']]
 if mode!='blank':
  for i,k in enumerate(seq):
   x,y=point(k);dx,dy=d['points'][k].get('label_offset_mm',[4,4]);label=k if mode in ['all','score'] else str(i+1)
   out +=[rf'\draw[CoursePurple,line width=.35mm] ({x},{y}) circle[radius=3mm];',rf'\Label{{{x+dx}}}{{{y+dy}}}{{{tex(label)}}}']
 # Source north lines are retained. Course sheets carry no prose labels.
 return '\n'.join(out)

def page(d,pack,name,page_number):
 mode=pack.get('mode','normal');c=d['courses'].get(name,{})
 seq=c.get('controls',[]);code=name if name else pack['title'];land=d['map'].get('orientation','landscape')=='landscape';pw,ph=(297,210) if land else (210,297);top=ph-10
 out=[r'\SheetStart',map_content(d,mode,seq)]
 # A small corner key sits clear of every planned leg and control.
 out +=[rf'\fill[white,rounded corners=1.2mm] (10,{top-20}) rectangle (57,{top});',rf'\node[anchor=north east,inner sep=0pt] at (54,{top-2}) {{\includegraphics[height=11mm]{{assets/esoc-logo.png}}}};',rf'\Put{{13}}{{{top-2}}}{{34}}{{15}}{{\bfseries\color{{ESOCGreen}}{tex(code)}}}']
 if c.get('distance_m') is not None:out.append(rf'\Put{{13}}{{{top-9}}}{{27}}{{8}}{{{c["distance_m"]} m}}')
 out.append(rf'\Put{{13}}{{{top-15}}}{{40}}{{7}}{{1:{d["map"]["scale"]:,}}}')
 bx,by=65,top-13;bar=50*1000/d['map']['scale']
 out.append(rf'\fill[white] ({bx-2},{by-6}) rectangle ({bx+bar+8},{by+3});')
 out.append(rf'\draw[line width=.25mm] ({bx},{by})--++({bar},0);')
 for v in [0,bar/2,bar]:out.append(rf'\draw[line width=.25mm] ({bx+v},{by-1})--++(0,2);')
 out.append(rf'\Put{{{bx+bar-3}}}{{{by-2}}}{{12}}{{7}}{{50 m}}')
 out.append(rf'\fill[white] (8,8) rectangle ({pw-8},13);')
 credits=' · '.join(d.get('copyright',[]))
 out.append(rf'\Put{{10}}{{12}}{{{pw-20}}}{{6.5}}{{{tex(credits)}}}')
 out.append(r'\SheetEnd')
 return '\n'.join(out)

def compile_tex(path,engine):
 if engine=='tectonic':cmd=['tectonic','--keep-logs',path.name]
 else:cmd=['xelatex','-interaction=nonstopmode','-halt-on-error',path.name]
 result=subprocess.run(cmd,cwd=path.parent,capture_output=True,text=True)
 if result.returncode:
  print(result.stdout+result.stderr,file=sys.stderr);raise RuntimeError(f'LaTeX failed: {path.name}')
 print(path.with_suffix('.pdf').name)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('session',type=Path);ap.add_argument('--outdir',type=Path,required=True);ap.add_argument('--engine',choices=['tectonic','xelatex'],default='tectonic');ap.add_argument('--no-compile',action='store_true');args=ap.parse_args()
 src=args.session.resolve();d=json.loads(src.read_text());validate(d);out=args.outdir.resolve();out.mkdir(parents=True,exist_ok=True)
 shutil.copytree(KIT/'assets',out/'assets',dirs_exist_ok=True);shutil.copy2(src.parent/d['map']['file'],out/'map.png')
 for pack in d['packs']:
  names=pack['courses'] or [''];body=preamble(d['title']+' - '+pack['title'],d.get('author',''),d['map'].get('orientation','landscape'))+'\n'.join(page(d,pack,n,i+1) for i,n in enumerate(names))+r'\end{document}'
  path=out/(pack['file']+'.tex');path.write_text(body)
  if not args.no_compile:compile_tex(path,args.engine)
 for extra in src.parent.glob('*.tex'):
  target=out/extra.name;shutil.copy2(extra,target)
  if not args.no_compile:compile_tex(target,args.engine)
if __name__=='__main__':main()
