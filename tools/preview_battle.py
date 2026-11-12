"""Interactive offline art review. Fixtures never connect to the game server."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from client import Game,CHARACTERS


def main():
    game=Game()
    game.player_id="P1"
    names=list(CHARACTERS)
    ni=0
    by="P1"
    identity=0
    paused=False
    def reset():
        game._handle_server_msg(dict(type="STATE",phase="SELECT"))
        game._handle_server_msg(dict(type="STATE",match_id="offline",phase="BATTLE",turn="P1",
            char_p1=names[ni],char_p2=names[ni],hp_p1=100,hp_p2=100,last_action=None))
    reset()
    running=True
    while running:
        dt=game.clock.tick(60)/1000
        for event in pygame.event.get():
            if event.type==pygame.QUIT:running=False
            if event.type!=pygame.KEYDOWN:continue
            if event.key==pygame.K_ESCAPE:running=False
            elif event.key==pygame.K_n:
                ni=(ni+1)%len(names)
                reset()
            elif event.key==pygame.K_TAB:by="P2" if by=="P1" else "P1"
            elif event.key==pygame.K_SPACE:paused=not paused
            elif event.key==pygame.K_m:game.sfx_enabled=not game.sfx_enabled
            elif event.key==pygame.K_r:game.reduced_motion=not game.reduced_motion
            elif event.key in (pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4) and not game.presentation.busy:
                action=("ATTACK","JUTSU","ULTIMATE","HEAL")[event.key-pygame.K_1]
                identity+=1
                other="P2" if by=="P1" else "P1"
                state=dict(game.game_state)
                state["last_action"]=None
                state["hp_p1"]=state["hp_p2"]=100
                if action=="HEAL":state["hp_"+by.lower()]=60
                game.presentation.enqueue(state)
                state["hp_"+(by if action=="HEAL" else other).lower()]=80 if action=="HEAL" else 100-{"ATTACK":15,"JUTSU":25,"ULTIMATE":50}[action]
                state["last_action"]=dict(id=identity,action=action,by=by,target=other,dmg={"ATTACK":15,"JUTSU":25,"ULTIMATE":50}.get(action,0))
                game._handle_server_msg(state)
        game.anim_time+=dt
        if game.status_timer>0:game.status_timer-=dt
        game.audio.update(game.volume, game.sfx_enabled)
        game._scene_battle([],(-1,-1),0 if paused else dt)
        label=f"OFFLINE ART PREVIEW / {names[ni]} / {by}   |   1-4 move  N character  Tab side  Space pause  M mute  R motion"
        bg=pygame.Rect(0,0,1024,22)
        pygame.draw.rect(game.screen,(10,15,25),bg)
        game.screen.blit(game.font_sm.render(label,True,(210,225,240)),(10,2))
        pygame.display.flip()
    pygame.quit()


if __name__=="__main__":main()
