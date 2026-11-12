"""Offline sprite inspector: no server, camera, audio, or video decoder required."""
import argparse
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export",type=Path,help="Export contact sheets and animation GIFs headlessly")
    args=parser.parse_args()
    if args.export:
        os.environ["SDL_VIDEODRIVER"]="dummy"
        os.environ["SDL_AUDIODRIVER"]="dummy"
    import pygame
    from PIL import Image
    from animation import ClipLibrary,AnimationPlayer
    pygame.display.init()
    pygame.font.init()
    screen=pygame.display.set_mode((800,600))
    font=pygame.font.Font(None,24)
    library=ClipLibrary(ROOT)
    names=list(library.data["characters"])
    actions=list(library.data["characters"][names[0]]["clips"])
    if args.export:
        args.export.mkdir(parents=True,exist_ok=True)
        for name in names:
            contact=Image.new("RGB",(256*3,240*3),(24,32,46))
            for a,action in enumerate(actions):
                actor=AnimationPlayer(library,name)
                actor.play(action)
                duration=sum(f["duration"] for f in actor.clip["frames"])
                frames=[]
                for tick in range(round(duration*25)):
                    tile=pygame.Surface((256,240))
                    tile.fill((24,32,46))
                    pygame.draw.line(tile,(70,95,110),(10,210),(246,210))
                    actor.draw(tile,(128,210))
                    tile.blit(font.render(f"{name} / {action}",True,(220,230,245)),(10,8))
                    frame=Image.frombytes("RGB",tile.get_size(),pygame.image.tobytes(tile,"RGB"))
                    frames.append(frame)
                    if tick==round(duration*25)//2:
                        contact.paste(frame,((a%3)*256,(a//3)*240))
                    actor.update(1/25)
                frames[0].save(args.export/f"{name.lower()}-{action}.gif",save_all=True,
                               append_images=frames[1:],duration=40,loop=0)
            contact.save(args.export/f"{name.lower()}-comparison.png")
        pygame.quit()
        print(f"Exported {len(names)*len(actions)} clips to {args.export}")
        return
    ni=ai=0
    actor=AnimationPlayer(library,names[ni])
    paused=False
    facing="right"
    speed=1.0
    bounds=True
    clock=pygame.time.Clock()
    running=True
    while running:
        dt=clock.tick(60)/1000
        for event in pygame.event.get():
            if event.type==pygame.QUIT: running=False
            if event.type!=pygame.KEYDOWN: continue
            key=event.key
            if key==pygame.K_ESCAPE: running=False
            elif key==pygame.K_SPACE: paused=not paused
            elif key==pygame.K_TAB:
                ni=(ni+1)%len(names)
                actor=AnimationPlayer(library,names[ni])
                actor.play(actions[ai])
            elif key in (pygame.K_UP,pygame.K_DOWN):
                ai=(ai+(1 if key==pygame.K_DOWN else -1))%len(actions)
                actor.play(actions[ai])
            elif key==pygame.K_f: facing="left" if facing=="right" else "right"
            elif key==pygame.K_b: bounds=not bounds
            elif key==pygame.K_r: actor.play(actions[ai])
            elif key==pygame.K_EQUALS: speed=min(4,speed+.25)
            elif key==pygame.K_MINUS: speed=max(.25,speed-.25)
            elif key in (pygame.K_LEFT,pygame.K_RIGHT):
                paused=True
                actor.frame_index=(actor.frame_index+(1 if key==pygame.K_RIGHT else -1))%len(actor.clip["frames"])
                actor.frame_timer=0
        if not paused: actor.update(dt*speed)
        for y in range(0,600,24):
            for x in range(0,800,24):
                pygame.draw.rect(screen,((28,34,45) if (x//24+y//24)%2 else (35,42,54)),(x,y,24,24))
        rect=actor.draw(screen,(400,450),facing=facing,scale=2)
        if bounds:
            pygame.draw.rect(screen,(85,155,185),rect,1)
            pygame.draw.line(screen,(255,200,70),(390,450),(410,450),2)
            pygame.draw.line(screen,(255,200,70),(400,440),(400,460),2)
            for socket in actor.clip['frames'][actor.frame_index].get('sockets',{}):
                x,y=actor.socket(socket,(400,450),facing,scale=2)
                color=(100,220,255) if socket=='hand' else (255,160,80)
                pygame.draw.circle(screen,color,(round(x),round(y)),5,2)
                screen.blit(font.render(socket,True,color),(x+8,y-10))
        text=[f"{names[ni]} / {actions[ai]} | frame {actor.frame_index} | {speed:g}x",
              "Tab character | Up/Down clip | Space pause | Left/Right step",
              "F flip | B bounds/root | R restart | +/- speed | Esc quit",
              "Markers: "+str(actor.clip.get("events",[]))]
        for i,line in enumerate(text): screen.blit(font.render(line,True,(235,240,250)),(16,14+26*i))
        pygame.display.flip()
    pygame.quit()


if __name__=="__main__": main()
