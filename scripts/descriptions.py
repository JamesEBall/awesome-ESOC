#!/usr/bin/env python3
"""Make separate IOF-style control-description strips in LaTeX.

The small vector symbol set below follows IOF Control Descriptions 2024.
It is deliberately explicit: unsupported symbols fail instead of becoming text
or an approximate icon. Extend it only after checking the IOF specification.
"""
import argparse
import json
import math
import shutil
from pathlib import Path
from build import KIT, compile_tex, preamble, tex

# Independent TikZ drawings in millimetres, centred in a 7 mm square.
SYMBOLS = {
    'start': r'\draw (-1.8,-2.1)--(1.85,0)--(-1.8,2.1)--cycle;',
    '1.9': r'\draw (0,0) ellipse[x radius=2.25mm,y radius=1.45mm];',
    '1.10': r'\fill (0,0) circle[radius=.95mm];',
    '2.4': r'\fill (-1.8,-1.55)--(1.8,-1.55)--(0,1.6)--cycle;',
    '4.5': r'''\begin{scope}\clip (0,2.55)--(2.55,0)--(0,-2.55)--(-2.55,0)--cycle;
        \foreach \q in {-2,0,2} {\draw (-3,\q-3)--(3,\q+3);\draw (-3,\q+3)--(3,\q-3);}\end{scope}''',
    '4.7': r'\foreach \x/\y in {-1.5/1.8,-.75/1.35,0/.9,.75/.45,1.5/0,.75/-.45,0/-.9,-.75/-1.35,-1.5/-1.8} {\fill (\x,\y) circle[radius=.23mm];}',
    '4.9': r'\draw (-1.15,-1.05)--(0,2.15)--(1.15,-1.05)--cycle;\draw (0,-1.15)--(0,-2.2);',
    '5.2': r'\draw (-2.3,-2.3)--(-1.2,-1.2);\draw (-.55,-.55)--(.55,.55);\draw (1.2,1.2)--(2.3,2.3);',
    '10.1': r'\draw (-2.1,-2.1)--(2.1,2.1);\draw (-2.1,2.1)--(2.1,-2.1);',
    '10.2': r'\draw (-1.7,-2.15)--(1.7,2.15);\draw (-1.7,2.15)--(0,0);',
    '12.1N': r'\draw (0,-.35) circle[radius=1.6mm];\fill (0,2.15) circle[radius=.32mm];',
    '12.1E': r'\draw (-.35,0) circle[radius=1.6mm];\fill (2.15,0) circle[radius=.32mm];',
    '12.1W': r'\draw (.35,0) circle[radius=1.6mm];\fill (-2.15,0) circle[radius=.32mm];',
}


def symbol(name, x, y):
    if name not in SYMBOLS:
        raise ValueError(f'Unsupported IOF symbol: {name}; implement and check it first')
    return rf'\begin{{scope}}[shift={{({x},{y})}},draw=black,fill=black,line width=.36mm,line cap=round,line join=round]'+SYMBOLS[name]+r'\end{scope}'


def label(x, y, value, bold=False):
    weight = r'\bfseries' if bold else ''
    return rf'\node[inner sep=0pt,text=black,font=\fontsize{{11}}{{12}}\selectfont{weight}] at ({x},{y}) {{{tex(value)}}};'


def rule(y, width=.16):
    return rf'\draw[black,line width={width}mm] (0,{y})--(56,{y});'


def row(y, number, code, point):
    fields = point.get('iof')
    if not fields or 'D' not in fields:
        raise ValueError(f'{code}: missing reviewed IOF feature')
    if set(fields)-set('CDEFGH'):
        raise ValueError(f'{code}: invalid description column')
    if fields.get('F') in ['10.1','10.2'] or fields.get('G') == '12.14':
        assert fields.get('D') and fields.get('E'), 'Combination requires two features'
    out = [rule(y), rule(y-7)]
    for n in range(9):
        out.append(rf'\draw[black,line width=.16mm] ({n*7},{y})--++(0,-7);')
    out.append(symbol('start',3.5,y-3.5) if number=='start' else label(3.5,y-3.5,number))
    if code:
        out.append(label(10.5,y-3.5,code))
    for col, value in fields.items():
        out.append(symbol(value,('ABCDEFGH'.index(col)+.5)*7,y-3.5))
    return out


def instruction(y, distance, kind):
    assert distance>0
    out=[rule(y,.35),rule(y-7,.35),rf'\draw[black,line width=.35mm] (0,{y})--++(0,-7);\draw[black,line width=.35mm] (56,{y})--++(0,-7);']
    cy=y-3.5
    out += [rf'\draw[black,line width=.3mm] (3.5,{cy}) circle[radius=2.2mm];',label(28,cy,f'{distance} m')]
    if kind=='15.1':
        out.append(rf'\draw[black,line width=.3mm,dash pattern=on 3mm off 1mm] (5.7,{cy})--(19,{cy});')
        out.append(rf'\draw[black,line width=.3mm,dash pattern=on 3mm off 1mm] (37,{cy})--(53,{cy});\draw[black,line width=.3mm] (50.8,{cy+2.2})--(53,{cy})--(50.8,{cy-2.2});')
    elif kind in ['16.1','16.2','16.3']:
        if kind!='16.3':
            a=11 if kind=='16.2' else 5.7
            out.append(rf'\draw[black,line width=.3mm,dash pattern=on 3mm off 1mm] ({a},{cy})--(19,{cy});\draw[black,line width=.3mm,dash pattern=on 3mm off 1mm] (37,{cy})--(50.3,{cy});')
        if kind=='16.2':
            out.append(rf'\draw[black,line width=.3mm] (8.8,{cy+2.2})--(11,{cy})--(8.8,{cy-2.2});')
        if kind=='16.3':
            out.append(rf'\draw[black,line width=.3mm] (8,{cy+2.2})--(5.8,{cy})--(8,{cy-2.2});')
        out.append(rf'\draw[black,line width=.3mm] (48.1,{cy+2.2})--(50.3,{cy})--(48.1,{cy-2.2});\draw[black,line width=.3mm] (52.5,{cy}) circle[radius=2.2mm];\draw[black,line width=.3mm] (52.5,{cy}) circle[radius=1.65mm];')
    else:
        raise ValueError(f'Unsupported route instruction {kind}')
    return out


def strip(d, name, x, y, master=False):
    settings=d['descriptions'];out=[rf'\begin{{scope}}[shift={{({x},{y})}},draw=black,text=black]']
    out += [rule(0,.35),rule(-7,.35),label(28,-3.5,d['title'])]
    top=-7
    if not master:
        c=d['courses'][name]
        km=math.floor(c['distance_m']/100+.5)/10
        out += [label(10.5,top-3.5,name,True),label(31.5,top-3.5,f'{km:.1f} km'),rule(top-7,.35)]
        for xx in [21,42]:out.append(rf'\draw[black,line width=.25mm] ({xx},{top})--++(0,-7);')
        if c.get('climb_m') is not None:out.append(label(49,top-3.5,f'{round(c["climb_m"]/5)*5} m'))
        top-=7
    else:
        out += [label(28,top-3.5,'All controls',True),rule(top-7,.35)];top-=7
    out += row(top,'start','',d['points']['S']);top-=7
    if not master and settings.get('start_taped_m'):
        out += instruction(top,settings['start_taped_m'],'15.1');top-=7
    codes=sorted({k for c in d['courses'].values() for k in c['controls']},key=int) if master else c['controls']
    for n,k in enumerate(codes,1):
        out += row(top,'' if master else n,k,d['points'][k]);top-=7
        if n%3==0:out.append(rule(top,.35))
    if not master:
        out += instruction(top,c['finish_distance_m'],settings['finish_symbol']);top-=7
    out += [rf'\draw[black,line width=.35mm] (0,0) rectangle (56,{top});',r'\end{scope}']
    return '\n'.join(out)


def write_descriptions(d, path):
    names=list(d['courses'])+[None]
    out=[preamble(d['title']+' - control descriptions',d.get('author',''),'portrait')]
    def height(name):
        if name is None:
            return 21+7*len({k for c in d['courses'].values() for k in c['controls']})
        return 28+7*len(d['courses'][name]['controls'])+(7 if d['descriptions'].get('start_taped_m') else 0)
    top=0
    for i in range(0,len(names),2):
        pair=names[i:i+2];h=max(map(height,pair))
        if h>220:raise ValueError('Description strip too tall for A4; split the course at a suitable map exchange')
        if top-h<24:
            if top:out.append(r'\SheetEnd')
            out += [r'\SheetStart',rf'\Head{{{tex(d["title"])}}}{{Control descriptions}}{{Cut out · Print at 100\% · 7 mm boxes}}']
            top=244
        for name,x in zip(pair,[30,124]):out.append(strip(d,name,x,top,master=name is None))
        top-=h+22
    out += [r'\SheetEnd']
    out.append(r'\end{document}')
    path.write_text('\n'.join(out))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('session',type=Path)
    ap.add_argument('--outdir',required=True,type=Path)
    ap.add_argument('--engine',default='tectonic')
    a=ap.parse_args();d=json.loads(a.session.read_text());a.outdir.mkdir(parents=True,exist_ok=True)
    shutil.copytree(KIT/'assets',a.outdir/'assets',dirs_exist_ok=True)
    p=a.outdir/'07-control-descriptions.tex';write_descriptions(d,p);compile_tex(p,a.engine)


if __name__=='__main__':main()
