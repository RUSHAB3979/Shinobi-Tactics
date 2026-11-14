"""Export phase-labelled real-renderer boards and body-only pose strips."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from PIL import Image, ImageDraw
from client import Game
from animation import AnimationPlayer


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    game=Game();game.player_id='P1'
    for name in ('Sasuke','Itachi','Tanjiro','Zenitsu'):
        for action in ('JUTSU','ULTIMATE'):
            timing=game._timing(name,action.lower())
            r,i,d=timing['release'],timing['impact'],timing['duration']
            stages=[('Prepare',.08),('Form',r*.55),('Hold',r-.02),('Release',r+.02),
                    ('Travel',r+(i-r)*.65),('Contact',i+.02),('Follow through',i+.25),('Recover',d-.10)]
            board=Image.new('RGB',(2048,700),(8,15,25));ink=ImageDraw.Draw(board)
            for j,(label,t) in enumerate(stages):
                game._handle_server_msg(dict(type='STATE',phase='SELECT'))
                state=dict(type='STATE',phase='BATTLE',match_id='board',turn='P1',char_p1=name,
                           char_p2='Itachi' if name!='Itachi' else 'Sasuke',hp_p1=100,hp_p2=100,last_action=None)
                game._handle_server_msg(state)
                state['hp_p2']=50;state['last_action']=dict(id=1,by='P1',target='P2',action=action,dmg=50)
                game._handle_server_msg(state)
                # Short steps include hitstop and follow the runtime clock.
                for _ in range(int(t*60)):game._scene_battle([],(-1,-1),1/60)
                game._scene_battle([],(-1,-1),t-int(t*60)/60)
                shot=Image.frombytes('RGB',(1024,640),pygame.image.tobytes(game.screen,'RGB')).resize((512,320))
                x,y=j%4*512,j//4*350;board.paste(shot,(x,y))
                ink.text((x+10,y+326),f'{label} / {t:.2f}s',fill=(220,235,248))
            key=name.lower()+'-'+action.lower();board.save(args.output/(key+'-storyboard.png'))
            clip=game.clip_library.data['characters'][name]['clips'][action.lower()]
            strip=pygame.Surface((200*len(clip['frames']),220));strip.fill((16,28,42))
            actor=AnimationPlayer(game.clip_library,name);actor.play(action.lower())
            for idx,frame in enumerate(clip['frames']):
                actor.frame_index=idx;actor.draw(strip,(idx*200+100,205))
            pygame.image.save(strip,str(args.output/(key+'-body-keys.png')))
    pygame.quit()


if __name__=='__main__':main()
