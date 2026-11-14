"""Verify 96 power outcomes; export 16 renderer videos with event-aligned sound.

Requires FFmpeg for review video export, not for running the game.
Audio is an offline reconstruction from actual emitted presentation events.
"""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import argparse
import array
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from client import Game
from combat_audio import CombatAudio


def soundtrack(game, events, duration, path):
    rate = 44100
    mix = [[0.,0.] for _ in range(round(duration*rate))]
    move = game.audio.moves[game.effect.character][game.effect.action.lower()]
    def read(entry):
        with wave.open(str(ROOT/entry)) as stream:
            assert stream.getframerate() == rate
            pcm = array.array('h',stream.readframes(stream.getnframes()))
        if sys.byteorder != 'little': pcm.byteswap()
        return pcm
    voice_end = len(read(move['voice']))/rate if 'voice' in move else 0
    for at, stage in events:
        layers = [(move.get(stage), .45, stage == 'impact')]
        if stage == 'start': layers.append((move.get('voice'), .72, False))
        if stage == 'impact':
            layer = CombatAudio.impact_layer(game.effect.character,game.effect.action)
            layers.append((f'assets/audio/impact/{layer}.wav',.22,True))
        for entry, gain, pan in layers:
            if not entry: continue
            start = round(at*rate)
            for i, value in enumerate(read(entry)):
                index = start+i
                if index >= len(mix): break
                duck = .48 if gain != .72 and index/rate < voice_end else 1.
                level = value/32768*gain*duck
                x = game.effect.target[0]/1024
                mix[index][0] += level*(1-.4*x if pan else 1)
                mix[index][1] += level*(.6+.4*x if pan else 1)
    peak = max(abs(v) for pair in mix for v in pair)
    gain = min(1,.94/max(.001,peak))
    pcm = array.array('h',(round(v*gain*32767) for pair in mix for v in pair))
    if sys.byteorder != 'little': pcm.byteswap()
    with wave.open(str(path),'wb') as stream:
        stream.setparams((2,2,rate,0,'NONE','not compressed'))
        stream.writeframes(pcm.tobytes())
    return {'peak':peak*gain, 'limiter_gain':gain, 'events':events}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'work/feedback')
    parser.add_argument('--character',choices=('Sasuke','Itachi','Tanjiro','Zenitsu'))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True,exist_ok=True)
    (output/'clips').mkdir(exist_ok=True)
    scratch = ROOT/'work/feedback-video'
    scratch.mkdir(parents=True,exist_ok=True)
    game = Game(); game.player_id = 'P1'
    cases=[]; clips=[]; costs=[]
    duration=5.2
    for name in ((args.character,) if args.character else ('Sasuke','Itachi','Tanjiro','Zenitsu')):
        for action in ('JUTSU','ULTIMATE'):
            for by in ('P1','P2'):
                for reduced in (False,True):
                    for outcome in ('hit','miss','reflected'):
                        game._handle_server_msg(dict(type='STATE',phase='SELECT'))
                        other = 'P2' if by == 'P1' else 'P1'
                        state = dict(type='STATE',phase='BATTLE',match_id='feedback',turn=by,
                            char_p1=name if by=='P1' else 'Itachi',char_p2=name if by=='P2' else 'Itachi',
                            hp_p1=100,hp_p2=100,last_action=None)
                        game._handle_server_msg(state)
                        game.reduced_motion=reduced
                        recipient=by if outcome=='reflected' else other
                        damage=0 if outcome=='miss' else (50 if action=='ULTIMATE' else 25)
                        state['hp_'+recipient.lower()]-=damage
                        state['last_action']=dict(id=1,by=by,target=other,action=action,dmg=damage,reflected=outcome=='reflected')
                        game._handle_server_msg(state)
                        export = by=='P1' and outcome=='hit'
                        key=name.lower()+'-'+action.lower()+('-reduced' if reduced else '')
                        events=[]; now=0.; hit_seen=False; shot=False
                        original=game.audio.play
                        def record(character, move, stage):
                            events.append((now,stage)); original(character,move,stage)
                        game.audio.play=record
                        if export:
                            encoder=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24',
                                '-s','1024x640','-r','30','-i','-','-an','-c:v','libx264','-threads','2',
                                '-preset','fast','-crf','21','-pix_fmt','yuv420p',str(scratch/'silent.mp4')],stdin=subprocess.PIPE)
                        for tick in range(round(duration*60)):
                            now=tick/60
                            start=time.perf_counter()
                            game._scene_battle([],(-1,-1),1/60)
                            costs.append((time.perf_counter()-start)*1000)
                            if game.feedback.impacts:
                                hit_seen=True
                                assert outcome!='miss'
                                assert game.feedback.impacts[-1].target==game._root(recipient)
                                if export and not reduced and not shot and game.feedback.impacts[-1].age>=.12:
                                    pygame.image.save(game.screen,str(output/(key+'.png')))
                                    shot=True
                            if reduced: assert game.feedback.camera(True)==(0,0)
                            if export and tick%2==0:
                                encoder.stdin.write(pygame.image.tobytes(game.screen,'RGB'))
                        game.audio.play=original
                        assert hit_seen == (outcome!='miss')
                        assert not game.presentation.busy
                        assert game.presentation.visible_hp=={p:state['hp_'+p.lower()] for p in ('P1','P2')}
                        if export:
                            encoder.stdin.close()
                            assert encoder.wait(timeout=30)==0
                            audio=soundtrack(game,events,duration,scratch/'mix.wav')
                            dest=output/'clips'/f'{key}.mp4'
                            subprocess.run(['ffmpeg','-y','-v','error','-i',str(scratch/'silent.mp4'),'-i',str(scratch/'mix.wav'),
                                '-c:v','copy','-c:a','aac','-b:a','160k','-threads','2','-movflags','+faststart','-shortest',str(dest)],check=True,timeout=30)
                            clips.append(dict(character=name,action=action,reduced=reduced,file='clips/'+dest.name,**audio))
                        cases.append(dict(character=name,action=action,side=by,reduced=reduced,outcome=outcome,passed=True))
            print(f'PASS {name} {action}',flush=True)
    costs.sort()
    report=dict(passed=True,cases=cases,total=len(cases),clips=clips,
        scope='Headless Pygame rendering; video encoding excluded from frame timings; audio reconstructed from emitted events; physical speakers/vsync not verified.',
        frame_ms=dict(median=costs[len(costs)//2],p95=costs[int(len(costs)*.95)],p99=costs[int(len(costs)*.99)]),
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    # Same codec and dimensions: concatenate the eight full-motion power clips.
    (scratch/'reel.txt').write_text(''.join("file '"+str(output/c['file'])+"'\n" for c in clips if not c['reduced']))
    subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(scratch/'reel.txt'),
                    '-c','copy','-movflags','+faststart',str(output/'battle-reel.mp4')],check=True,timeout=30)
    print(json.dumps({k:report[k] for k in ('total','frame_ms','peak_rss_mib')}))
    pygame.quit()


if __name__=='__main__': main()
