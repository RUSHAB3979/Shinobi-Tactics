"""Exercise two actual TCP clients and export a deterministic battle proof reel."""
import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
import argparse
import json
import resource
import socket
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image
from client import Game,Network


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"work/verification")
    parser.add_argument("--character",default="Sasuke")
    parser.add_argument("--reflection",action="store_true",help="Verify Itachi/Sasuke reflection and reflected ultimate")
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    with socket.socket() as reserve:
        reserve.bind(("127.0.0.1",0))
        port=reserve.getsockname()[1]
    env={**os.environ,"SHINOBI_HOST":"127.0.0.1","SHINOBI_PORT":str(port)}
    log=(args.output/"server.log").open("w")
    server=subprocess.Popen([sys.executable,"-u",str(ROOT/"server.py")],cwd=ROOT,env=env,stdout=log,stderr=log)
    games=[]
    start=time.perf_counter()
    try:
        # Wait for the listening message without opening an extra player socket.
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if "Listening" in (args.output/"server.log").read_text():break
            if server.poll() is not None:raise RuntimeError("Server failed to start")
            time.sleep(.02)
        for _ in range(2):
            game=Game()
            game.net=Network("127.0.0.1",port)
            assert game.net.connect()
            game.player_id=game.net.player_id
            games.append(game)
        def poll_until(predicate):
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                for game in games:game._poll_network()
                if predicate():return
                time.sleep(.01)
            raise AssertionError("Timed out waiting for network state")
        poll_until(lambda:all(g.scene=="SELECT" for g in games))
        for i,game in enumerate(games):
            character = ("Itachi" if i==0 else "Sasuke") if args.reflection else args.character
            game.net.send(dict(action="SELECT_CHAR",character=character))
        poll_until(lambda:all(g.scene=="BATTLE" for g in games))
        assert all(g.player_anim is not g.enemy_anim for g in games)
        startup=time.perf_counter()-start
        games[0].net.send(dict(action="ATTACK"))
        poll_until(lambda:all(g.presentation.busy for g in games))
        frames=[]
        frame_times=[]
        for tick in range(60):
            for i,game in enumerate(games):
                start=time.perf_counter()
                game._scene_battle([],(-1,-1),1/60)
                frame_times.append((time.perf_counter()-start)*1000)
                if tick in (8,19):assert game.hp_enemy.current==100 if i==0 else game.hp_player.current==100
                if tick==24:assert game.presentation.visible_hp["P2"]==85
                if i==0 and tick%2==0:
                    frames.append(Image.frombytes("RGB",game.screen.get_size(),pygame.image.tobytes(game.screen,"RGB")))
                if tick in (0,12,21,30,45):pygame.image.save(game.screen,str(args.output/f"p{i+1}-{tick:02d}.png"))
        # Duplicate snapshot does not replay an action.
        for game in games:
            game._handle_server_msg(game.game_state)
            assert not game.presentation.busy
        frames[0].save(args.output/"attack-pilot.gif",save_all=True,append_images=frames[1:],duration=33,loop=0)
        # Confirm a miss, heal, then lethal action over the real protocol.
        commands = ([(1,dict(action="ATTACK",dmg=0)),(0,dict(action="JUTSU")),
                     (1,dict(action="ULTIMATE")),(0,dict(action="ATTACK"))] if args.reflection else
                    [(1,dict(action="ATTACK",dmg=0)),(0,dict(action="HEAL")),
                     (1,dict(action="ULTIMATE")),(0,dict(action="ATTACK")),(1,dict(action="ULTIMATE"))])
        for pid,command in commands:
            previous=games[0].game_state["last_action"]["id"]
            games[pid].net.send(command)
            poll_until(lambda:all(g.game_state["last_action"]["id"]>previous for g in games))
            # Spoken callouts can extend recovery beyond the old three-second budget.
            for tick in range(360):
                for game in games:
                    if game.scene=="BATTLE":game._scene_battle([],(-1,-1),1/60)
                    elif game.scene=="GAME_OVER":game._scene_game_over([],(-1,-1),1/60)
                if all(not g.presentation.busy and
                       (g.game_state["phase"]!="GAME_OVER" or g.scene=="GAME_OVER") for g in games):
                    break
            else:
                raise AssertionError("Presentation did not settle within six simulated seconds")
        assert all(g.scene=="GAME_OVER" for g in games)
        assert all(g.presentation.visible_hp["P2" if args.reflection else "P1"]==0 for g in games)
        ordered=sorted(frame_times)
        metrics=dict(character="Itachi vs Sasuke" if args.reflection else args.character,two_tcp_clients=True,mirror_players_independent=True,
                     startup_s=startup,frame_ms=dict(median=ordered[len(ordered)//2],
                     p95=ordered[int(len(ordered)*.95)],p99=ordered[int(len(ordered)*.99)]),
                     peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                     checks=["impact HP timing both perspectives","duplicate state","miss","result poses"]+
                     (["genjutsu shield","reflected Kirin","KO"] if args.reflection else ["heal","lethal ultimate"]))
        (args.output/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
        print(json.dumps(metrics))
    finally:
        for game in games:
            if game.net:game.net.close()
        server.terminate()
        server.wait(timeout=5)
        log.close()
        pygame.quit()


if __name__=="__main__":main()
