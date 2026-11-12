"""Validate every runtime reference, PNG decode, pivot, event, and generated cue."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import sys
import json
import wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from animation import ClipLibrary,REQUIRED


def main():
    pygame.display.init()
    pygame.display.set_mode((1,1))
    library=ClipLibrary(ROOT)
    assert set(library.data["characters"])=={"Sasuke","Tanjiro","Itachi","Zenitsu"}
    paths=set()
    clips=0
    for name,char in library.data["characters"].items():
        for action,clip in char["clips"].items():
            clips+=1
            for frame in clip["frames"]:
                assert frame["path"].startswith(f"assets/curated/{name.lower()}/"),frame["path"]
                surface=library.image(frame["path"])
                assert surface.get_bounding_rect(min_alpha=128).width>0
                ax,ay=frame["anchor"]
                assert 0<=ax<=surface.get_width() and 0<=ay<=surface.get_height(),frame
                for sx,sy in frame.get('sockets',{}).values():
                    assert 0<=sx<=surface.get_width() and 0<=sy<=surface.get_height(),frame
                paths.add(frame["path"])
            if action in ("attack","jutsu","ultimate","heal"):
                markers={event["name"]:event["time"] for event in clip["events"]}
                assert 0<markers["release"]<markers["impact"]<sum(f["duration"] for f in clip["frames"])
        for cue in ("attack","jutsu","ultimate","heal","hit","block"):
            with wave.open(str(ROOT/f"assets/audio/generated/{name.lower()}-{cue}.wav")) as audio:
                assert audio.getnchannels()==1 and audio.getnframes()>0
                assert audio.getsampwidth()==2
    arena=pygame.image.load(str(ROOT/"assets/arena.png"))
    assert arena.get_width()>0
    arena=pygame.image.load(str(ROOT/'assets/arena-glowup.png'))
    assert arena.get_width()>=1024 and arena.get_height()>=640
    pygame.font.init()
    assert pygame.font.Font(str(ROOT/'assets/fonts/SpaceGrotesk-Bold.otf'),18).size('SHINOBI')[0]>0
    assert (ROOT/'assets/fonts/OFL-SpaceGrotesk.txt').is_file()
    for i in range(8):
        dragon=pygame.image.load(str(ROOT/f'assets/vfx/kirin/{i:02d}.png'))
        assert dragon.get_size()==(224,224) and dragon.get_bounding_rect(min_alpha=128).width>0
    audio_manifest=json.loads((ROOT/'assets/audio/combat.json').read_text())
    sampled=set()
    for moves in audio_manifest['characters'].values():
        for action,move in moves.items():
            assert 'impact' in move
            if action!='heal':assert 'release' in move
            for stage in ('voice','start','release','impact','block'):
                if stage in move:sampled.add(move[stage])
    for path in sampled:
        with wave.open(str(ROOT/path)) as audio:
            assert (audio.getnchannels(),audio.getsampwidth(),audio.getframerate())==(1,2,44100)
            assert audio.getnframes()>0
    for name in ('slash','electric','thunder','water','fire','illusion','counter'):
        with wave.open(str(ROOT/f'assets/audio/impact/{name}.wav')) as audio:
            assert (audio.getnchannels(),audio.getsampwidth(),audio.getframerate())==(1,2,44100)
            assert audio.getnframes()>0
    print(f"PASS: {clips} clips, {len(paths)} body poses, 8 Kirin VFX frames, 24 fallback + {len(sampled)} sampled + 7 impact WAV cues, arena; no legacy body frames")
    pygame.quit()


if __name__=="__main__":main()
