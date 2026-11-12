"""Capture the original renderer against the available sparse source subset."""
import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
import importlib.util
import json
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
original=subprocess.check_output(["git","show","HEAD:client.py"],cwd=ROOT,text=True)
module=type(sys)("baseline_client")
module.__file__=str(ROOT/"client.py")
exec(compile(original,str(ROOT/"client.py"),"exec"),module.__dict__)
start=time.perf_counter()
game=module.Game()
game.player_id="P1"
game.my_char=game.opp_char="Sasuke"
game.player_anim=game._get_anim_sprite("Sasuke")
game.enemy_anim=game._get_anim_sprite("Sasuke")
game.game_state=dict(hp_p1=100,hp_p2=85,turn="P2",phase="BATTLE")
startup=time.perf_counter()-start
game.scene="BATTLE"
output=ROOT/"work/baseline"
output.mkdir(parents=True,exist_ok=True)
game._process_action(dict(action="ATTACK",by="P1",attacker_char="Sasuke",dmg=15))
times=[]
for i in range(90):
    start=time.perf_counter()
    game._scene_battle([],(-1,-1),1/60)
    times.append((time.perf_counter()-start)*1000)
    if i in (0,10,25,45): module.pygame.image.save(game.screen,str(output/f"attack-{i:02d}.png"))
ordered=sorted(times)
report=dict(scope="Sparse original asset subset only; not a full checkout baseline",startup_s=startup,
            frame_ms=dict(median=ordered[len(ordered)//2],p95=ordered[int(len(ordered)*.95)],p99=ordered[-1]),
            peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
            mirror_players_shared=game.player_anim is game.enemy_anim)
(output/"metrics.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report))
module.pygame.quit()
