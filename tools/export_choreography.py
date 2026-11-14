"""Reproduce registered technique poses from reviewed, transparent source atlases.

Run after export_powers.py. Cell scale stays constant per atlas; only root and
attachment registration vary. Never resize each pose to its own bounding box.
"""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

SPECS={
 "Sasuke/jutsu":dict(source="sasuke-chidori",grid=[4,3],
  hands=[(.58,.42),(.36,.61),(.22,.66),(.13,.58),(.17,.52),(.18,.58),(.19,.57),(.86,.42),(.90,.36),(.90,.40),(.43,.70),(.55,.65)],
  durations=[.10,.17,.24,.24,.09,.11,.10,.15,.12,.16,.28,.34],
  events={"charge":.25,"release":.75,"impact":1.20,"recover":1.60}),
 "Sasuke/ultimate":dict(source="sasuke-kirin",grid=[4,3],
  hands=[(.56,.39),(.74,.56),(.74,.29),(.77,.18),(.69,.07),(.73,.07),(.71,.08),(.75,.22),(.76,.57),(.80,.56),(.65,.63),(.62,.63)],
  durations=[.15,.20,.20,.20,.22,.22,.18,.18,.15,.30,.40,.40],
  events={"charge":.35,"form":.55,"release":1.55,"impact":2.05,"recover":2.35}),
}

def export():
 manifest=json.loads((ROOT/"assets/animations.json").read_text())
 spec_path=ROOT/"assets/sources/choreography/registration.json"
 specs=json.loads(spec_path.read_text()) if spec_path.exists() else SPECS
 for key,spec in specs.items():
  name,action=key.split("/");sheet=Image.open(ROOT/"assets/sources/choreography"/(spec["source"]+".png")).convert("RGBA")
  cols,rows=spec["grid"];cw,ch=sheet.width/cols,sheet.height/rows
  first=sheet.crop((0,0,round(cw),round(ch)))
  bounds=first.getchannel("A").point(lambda a:255 if a>=128 else 0).getbbox()
  scale=158/(bounds[3]-bounds[1])
  output=ROOT/f"assets/curated/{name.lower()}/techniques/{action}";output.mkdir(parents=True,exist_ok=True)
  frames=[]
  for idx,(hand,dt) in enumerate(zip(spec["hands"],spec["durations"])):
   x,y=idx%cols,idx//cols;box=(round(x*cw),round(y*ch),round((x+1)*cw),round((y+1)*ch))
   image=sheet.crop(box);image.putalpha(image.getchannel("A").point(lambda a:0 if a<16 else a))
   bounds=image.getchannel("A").point(lambda a:255 if a>=128 else 0).getbbox()
   if not bounds:raise ValueError(f"empty {key}/{idx}")
   anchor=[round((cw*.5)*scale),round((bounds[3]-1)*scale)]
   image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.NEAREST)
   path=output/f"{idx:02d}.png";image.save(path)
   sockets={"hand":[round(hand[0]*cw*scale),round(hand[1]*ch*scale)]}
   if spec.get("tips"):
    tip=spec["tips"][idx];sockets["weapon"]=[round(tip[0]*cw*scale),round(tip[1]*ch*scale)]
   frames.append(dict(path=str(path.relative_to(ROOT)),anchor=anchor,sockets=sockets,duration=dt))
  manifest["characters"][name]["clips"][action]=dict(source_facing="right",loop=False,hold=False,finish="idle",frames=frames,
   events=[dict(name=n,time=t) for n,t in spec["events"].items()])
 retimed=ROOT/"assets/sources/choreography/retimed-clips.json"
 if retimed.exists():
  for key,clip in json.loads(retimed.read_text()).items():
   name,action=key.split("/");manifest["characters"][name]["clips"][action]=clip
 (ROOT/"assets/animations.json").write_text(json.dumps(manifest,indent=2)+"\n")
 spec_path.write_text(json.dumps(specs,indent=2)+"\n")
 print("Exported",sum(len(s["hands"]) for s in specs.values()),"technique keys")
if __name__=="__main__":export()
