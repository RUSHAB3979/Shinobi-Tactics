"""Render every power outcome/side/motion combination and export playable evidence.

Offline authoritative fixtures: this validates presentation, not webcam recognition.
Use verify_battle.py as well for real TCP/server integration.
"""
import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import json
import sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pygame
from client import Game


def main():
    output=ROOT/'work/powers';output.mkdir(parents=True,exist_ok=True)
    game=Game();game.player_id='P1';cases=[];reel=[]
    for name in ('Sasuke','Itachi','Tanjiro','Zenitsu'):
        for action in ('JUTSU','ULTIMATE'):
            for by in ('P1','P2'):
                for reduced in (False,True):
                    for outcome in ('hit','miss','reflected'):
                        other='P2' if by=='P1' else 'P1'
                        game._handle_server_msg(dict(type='STATE',phase='SELECT'))
                        state=dict(type='STATE',phase='BATTLE',match_id='powers',turn=by,
                            char_p1=name if by=='P1' else 'Itachi',char_p2=name if by=='P2' else 'Itachi',
                            hp_p1=100,hp_p2=100,last_action=None)
                        game._handle_server_msg(state);game.reduced_motion=reduced
                        recipient=by if outcome=='reflected' else other
                        if outcome!='miss':state['hp_'+recipient.lower()]=75
                        state.update(turn=other,last_action=dict(id=1,by=by,target=other,action=action,
                            dmg=0 if outcome=='miss' else 25,reflected=outcome=='reflected'))
                        game._handle_server_msg(state)
                        timing=game._timing(name,action.lower())
                        export=by=='P1' and not reduced and outcome=='hit'
                        export_reduced=by=='P1' and reduced and outcome=='hit'
                        frames=[];samples=[]
                        sample_ticks={round(t*60) for t in (.1,timing['release']+.04,
                            (timing['release']+timing['impact'])/2,timing['impact']-.02,
                            timing['impact']+.08,timing['duration']-.05)}
                        for tick in range(round((timing['duration']+.45)*60)):
                            game._scene_battle([],(-1,-1),1/60)
                            if tick==1 and outcome=='reflected':
                                assert game.effect.target==game._root(by)
                            if (export or export_reduced) and tick%3==0:
                                frame=Image.frombytes('RGB',game.screen.get_size(),pygame.image.tobytes(game.screen,'RGB')).resize((768,480))
                                frames.append(frame)
                            if export and tick in sample_ticks:
                                frame=Image.frombytes('RGB',game.screen.get_size(),pygame.image.tobytes(game.screen,'RGB')).resize((512,320))
                                ImageDraw.Draw(frame).text((10,12),f'{name} {action} / {tick/60:.2f}s',fill=(255,220,140))
                                samples.append(frame)
                            if export_reduced and tick==round((timing['impact']+.04)*60):
                                pygame.image.save(game.screen,str(output/f'{name.lower()}-{action.lower()}-reduced-impact.png'))
                        assert not game.presentation.busy
                        assert game.presentation.visible_hp=={p:state['hp_'+p.lower()] for p in ('P1','P2')}
                        if frames:
                            suffix='-reduced' if reduced else ''
                            frames[0].save(output/f'{name.lower()}-{action.lower()}{suffix}.gif',save_all=True,
                                append_images=frames[1:],duration=50,loop=0)
                        if samples:
                            sheet=Image.new('RGB',(512*len(samples),320))
                            for k,frame in enumerate(samples):sheet.paste(frame,(k*512,0))
                            sheet.save(output/f'{name.lower()}-{action.lower()}-sequence.png')
                        if export:
                            title=Image.new('RGB',(768,480),(12,18,31))
                            ImageDraw.Draw(title).text((250,220),f'{name.upper()} / {action}',fill=(235,195,120))
                            reel.extend([title]*10);reel.extend(frames);reel.extend([frames[-1]]*5)
                        cases.append(dict(character=name,action=action,side=by,reduced_motion=reduced,outcome=outcome,passed=True))
    reel[0].save(output/'power-reel.gif',save_all=True,append_images=reel[1:],duration=50,loop=0)
    (output/'results.json').write_text(json.dumps(dict(cases=cases,total=len(cases),passed=True),indent=2)+'\n')
    print(f'PASS: {len(cases)} power presentation cases; 16 normal/reduced GIFs, 8 phase sheets, reel')
    pygame.quit()


if __name__=='__main__':main()
