"""Extract reviewed power atlases at a fixed sheet scale and author attachment points.

Run after export_sprites.py to reproduce the complete library. No original atlas is
modified. Low-alpha RGB quantization noise is discarded, as in the base exporter.
"""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
# Normalized positions in each source cell, inspected on the source atlases.
HANDS = {
    'Sasuke': [(.56,.40),(.31,.53),(.25,.54),(.28,.54),(.27,.55),(.84,.49),(.87,.43),(.39,.67),
               (.56,.41),(.56,.48),(.69,.34),(.80,.13),(.58,.11),(.61,.65),(.75,.66),(.57,.65)],
    'Itachi': [(.55,.53),(.56,.36),(.59,.40),(.84,.30),(.87,.28),(.87,.28),(.58,.61),(.57,.58),
               (.63,.24),(.66,.21),(.72,.22),(.60,.30),(.75,.35),(.76,.23),(.56,.59),(.56,.59)],
    'Tanjiro': [(.53,.44),(.57,.62),(.56,.65),(.62,.31),(.73,.51),(.59,.56),(.57,.63),(.39,.62),
                (.53,.46),(.56,.40),(.53,.21),(.56,.23),(.62,.62),(.57,.69),(.58,.59),(.36,.63)],
    'Zenitsu': [(.59,.52),(.60,.57),(.55,.63),(.53,.60),(.38,.61),(.66,.48),(.68,.62),(.57,.59),
                (.57,.54),(.55,.66),(.42,.64),(.45,.64),(.69,.59),(.58,.64),(.57,.62),(.57,.53)]}
TIPS = {
    'Tanjiro': [(.53,.07),(.09,.89),(.08,.59),(.14,.31),(.98,.44),(.94,.72),(.85,.84),(.18,.90),
                (.53,.08),(.24,.19),(.17,.05),(.12,.11),(.94,.91),(.93,.83),(.82,.46),(.20,.90)],
    'Zenitsu': [(.57,.70),(.63,.73),(.51,.72),(.78,.67),(.05,.72),(.94,.16),(.98,.69),(.63,.73),
                (.62,.72),(.55,.76),(.68,.72),(.75,.75),(.98,.45),(.89,.88),(.65,.72),(.65,.73)]}


def cleaned(image):
    image = image.convert('RGBA')
    image.putalpha(image.getchannel('A').point(lambda a: 0 if a < 8 else a))
    return image


def export():
    manifest_path = ROOT/'assets/animations.json'
    manifest = json.loads(manifest_path.read_text())
    for name in HANDS:
        sheet = Image.open(ROOT/f'assets/sources/powers/{name.lower()}.png')
        w,h = sheet.size
        scale = 176/(w/4)
        output = ROOT/f'assets/curated/{name.lower()}/powers'
        output.mkdir(parents=True,exist_ok=True)
        frames=[]
        for i in range(16):
            x,y=i%4,i//4
            box=(round(x*w/4),round(y*h/4),round((x+1)*w/4),round((y+1)*h/4))
            # Reviewed sword tips cross a nominal cell edge. Split in the real
            # transparent gutter so neither a blade nor a neighbor is clipped.
            if name=='Tanjiro' and y==1:
                cuts=[0,346,627,940,w]
                box=(cuts[x],box[1],cuts[x+1],box[3])
            if name=='Zenitsu' and y==3:
                cuts=[0,330,627,940,w]
                box=(cuts[x],box[1],cuts[x+1],box[3])
            image=cleaned(sheet.crop(box))
            bounds=image.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
            if not bounds: raise ValueError(f'Empty {name}/{i}')
            anchor=[round(((x+.5)*w/4-box[0])*scale),round((bounds[3]-1)*scale)]
            image=image.resize(tuple(round(v*scale) for v in image.size),Image.Resampling.NEAREST)
            path=f'assets/curated/{name.lower()}/powers/{i:02d}.png'
            image.save(ROOT/path)
            hand=HANDS[name][i]
            sockets={'hand':[round(((x+hand[0])*w/4-box[0])*scale),round(hand[1]*h/4*scale)]}
            if name in TIPS:
                tip=TIPS[name][i]
                sockets['weapon']=[round(((x+tip[0])*w/4-box[0])*scale),round(tip[1]*h/4*scale)]
            frames.append(dict(path=path,anchor=anchor,sockets=sockets))
        for action,start in [('jutsu',0),('ultimate',8)]:
            if action=='jutsu':
                indices=list(range(8))
                durations=[.08,.10,.14,.08,.10,.12,.16,.30]
                # Contact is the forward draw-cut, not a sprint pose.
                if name in ('Tanjiro','Zenitsu','Itachi'):
                    durations=[.08,.10,.14,.18,.12,.16,.14,.16]
                release,impact=.32,.64
            else:
                indices=list(range(8,16))
                durations=[.15,.20,.20,.25,.30,.20,.25,.30]
                release,impact=.55,1.15
                if name in ('Tanjiro','Zenitsu'):
                    durations=[.15,.20,.20,.30,.32,.20,.23,.25]
                    impact=1.05
            manifest['characters'][name]['clips'][action]=dict(
                source_facing='right',loop=False,hold=False,finish='idle',
                frames=[dict(**frames[i],duration=dt) for i,dt in zip(indices,durations)],
                events=[dict(name='release',time=release),dict(name='impact',time=impact)])
        manifest['characters'][name]['power_source']=f'assets/sources/powers/{name.lower()}.png'
    sheet=Image.open(ROOT/'assets/sources/powers/kirin.png')
    w,h=sheet.size
    output=ROOT/'assets/vfx/kirin';output.mkdir(parents=True,exist_ok=True)
    for i in range(8):
        image=cleaned(sheet.crop((round(i%4*w/4),round(i//4*h/2),round((i%4+1)*w/4),round((i//4+1)*h/2))))
        image.resize((224,224),Image.Resampling.NEAREST).save(output/f'{i:02d}.png')
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('Exported 64 unique power poses with hand/weapon sockets and 8 Kirin VFX frames')


if __name__=='__main__':export()
