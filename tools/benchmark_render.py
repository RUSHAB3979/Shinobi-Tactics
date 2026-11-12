"""Measure renderer cost without GIF/screenshot storage overhead (not vsync FPS)."""
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
from client import Game

start=time.perf_counter()
game=Game()
game.player_id="P1"
snapshot=dict(type="STATE",match_id="benchmark",phase="BATTLE",turn="P2",hp_p1=100,hp_p2=85,
              char_p1="Sasuke",char_p2="Sasuke",last_action=None)
game._handle_server_msg(snapshot)
startup=time.perf_counter()-start
frames=[]
for i in range(600):
    if i%60==0:
        snapshot["last_action"]=dict(id=i//60+1,action="ATTACK",by="P1",dmg=15)
        game._handle_server_msg(snapshot)
    start=time.perf_counter()
    game._scene_battle([],(-1,-1),1/60)
    frames.append((time.perf_counter()-start)*1000)
frames.sort()
report=dict(scope="One game, two independent Sasuke actors, 600 headless render/update frames; excludes compositor/vsync",
            startup_s=startup,frame_ms=dict(median=frames[300],p95=frames[570],p99=frames[594]),
            peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
out=ROOT/"work/benchmark"
out.mkdir(parents=True,exist_ok=True)
(out/"metrics.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report))
