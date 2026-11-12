"""Render all 32 character/action/side combinations from authoritative fixtures."""
import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
import json
import resource
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image
from client import Game,CHARACTERS

output=ROOT/"work/matrix"
output.mkdir(parents=True,exist_ok=True)
game=Game()
game.player_id="P1"
sheet=Image.new("RGB",(4*512,4*320))
times=[]
cases=[]
for ci,char in enumerate(CHARACTERS):
    for ai,action in enumerate(("ATTACK","JUTSU","ULTIMATE","HEAL")):
        for by in ("P1","P2"):
            game._handle_server_msg(dict(type="STATE",phase="SELECT"))
            other="P2" if by=="P1" else "P1"
            hp={"P1":60 if action=="HEAL" and by=="P1" else 100,
                "P2":60 if action=="HEAL" and by=="P2" else 100}
            state=dict(type="STATE",match_id=f"{char}-{action}-{by}",phase="BATTLE",turn=by,
                       char_p1=char if by=="P1" else "Sasuke",char_p2=char if by=="P2" else "Sasuke",
                       hp_p1=hp["P1"],hp_p2=hp["P2"],last_action=None)
            game._handle_server_msg(state)
            hp[by if action=="HEAL" else other]=80 if action=="HEAL" else 75
            state.update(hp_p1=hp["P1"],hp_p2=hp["P2"],turn=other,
                         last_action=dict(id=1,action=action,by=by,target=other,dmg=25))
            game._handle_server_msg(state)
            timing=game._timing(char,action.lower())
            capture_tick=round((timing["impact"]+.03)*60)
            frames=[]
            for tick in range(round((timing["duration"]+.35)*60)):
                before=time.perf_counter()
                game._scene_battle([],(-1,-1),1/60)
                times.append((time.perf_counter()-before)*1000)
                if tick%3==0 and by=="P1":
                    frames.append(Image.frombytes("RGB",game.screen.get_size(),pygame.image.tobytes(game.screen,"RGB")).resize((512,320)))
                if tick==capture_tick:
                    image=Image.frombytes("RGB",game.screen.get_size(),pygame.image.tobytes(game.screen,"RGB"))
                    image.save(output/f"{char.lower()}-{action.lower()}-{by}.png")
                    if by=="P1":sheet.paste(image.resize((512,320)),(ci*512,ai*320))
            assert game.presentation.visible_hp==hp
            assert not game.presentation.busy
            if frames:
                frames[0].save(output/f"{char.lower()}-{action.lower()}.gif",save_all=True,
                               append_images=frames[1:],duration=50,loop=0)
            cases.append(dict(character=char,action=action,side=by,passed=True))
sheet.save(output/"all-moves.png")
ordered=sorted(times)
report=dict(cases=cases,rendered_frames=len(times),frame_ms=dict(median=ordered[len(ordered)//2],
            p95=ordered[int(len(ordered)*.95)],p99=ordered[int(len(ordered)*.99)]),
            peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            scope="Headless rendering on target laptop; no compositor/vsync, live sound or webcam")
(output/"results.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="cases"}))
pygame.quit()
