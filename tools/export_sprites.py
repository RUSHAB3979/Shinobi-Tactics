"""Extract approved 4x4 pose sheets. Preserve alpha and one scale across all poses.

This is deterministic atlas extraction, not artwork generation. Source cells and
semantic foot anchors are recorded explicitly; originals are never overwritten.
"""
import argparse
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FRAMES = {
    "idle": ([0,1,0,7], [.32,.26,.32,.26]),
    "attack": ([0,2,4,5,6,7], [.10,.14,.08,.10,.14,.16]),
    "jutsu": ([0,8,9,9,4,6,7], [.12,.20,.18,.12,.12,.16,.18]),
    "ultimate": ([0,8,10,10,9,6,7], [.15,.25,.30,.35,.30,.25,.25]),
    "heal": ([0,8,11,11,8,0], [.10,.16,.22,.22,.16,.18]),
    "hit": ([12,12,6,0], [.09,.12,.12,.12]),
    "guard": ([13,13,13,0], [.12,.22,.18,.12]),
    "down": ([12,12,14], [.12,.18,.65]),
    "victory": ([7,15,15], [.15,.30,.60]),
}
MARKERS = {"attack":(.18,.34), "jutsu":(.32,.64),
           "ultimate":(.55,1.15), "heal":(.20,.56)}


def export(character):
    name = character.lower()
    src_path = ROOT / f"assets/sources/{name}-poses.png"
    sheet = Image.open(src_path).convert("RGBA")
    w,h = sheet.size
    output = ROOT / f"assets/curated/{name}"
    output.mkdir(parents=True, exist_ok=True)
    # A 176px square canvas at a fixed scale per sheet. No per-pose height fit.
    scale = 176/(w/4)
    anchors = []
    for index in range(16):
        col,row = index%4,index//4
        box = (round(col*w/4),round(row*h/4),round((col+1)*w/4),round((row+1)*h/4))
        if index == 14 and character == "Sasuke":
            # Reviewed prone pose extends 3px into the left gutter. Preserve it.
            box = (box[0]-4,box[1],box[2],box[3])
        if character == "Tanjiro" and row == 1:
            # Reviewed sword tips cross the nominal grid gutters. Use the actual
            # transparent separators rather than cutting weapons at cell edges.
            separators = [0,348,668,951,w]
            box = (separators[col],box[1],separators[col+1],box[3])
        if character == "Tanjiro" and index == 10:
            box = (box[0],box[1]-8,box[2],box[3])
        if character == "Sasuke" and index == 15:
            box = (box[0]+20,box[1],box[2],box[3])
        image = sheet.crop(box)
        # Source PNGs carry nearly transparent RGB noise (alpha 1–2). This is
        # export quantization: it must not influence semantic foot anchors.
        alpha = image.getchannel("A")
        image.putalpha(alpha.point(lambda value: 0 if value < 8 else value))
        bounds = alpha.point(lambda value: 255 if value >= 128 else 0).getbbox()
        if not bounds:
            raise ValueError(f"Empty source pose {character}/{index}")
        anchor = [(col+.5)*w/4-box[0], bounds[3]-1]
        size = tuple(max(1,round(v*scale)) for v in image.size)
        image.resize(size, Image.Resampling.NEAREST).save(output/f"pose_{index:02d}.png")
        anchors.append([round(v*scale) for v in anchor])
    clips = {}
    for action,(indices,durations) in FRAMES.items():
        if action == "ultimate" and character in ("Tanjiro","Zenitsu"):
            indices = [0,8,10 if character == "Tanjiro" else 9,2,4,5,6,7]
            durations = [.15,.25,.30,.25,.20,.20,.20,.25]
        # The overhead windup in source cell 3 touches the upper sheet edge;
        # it is intentionally not included in any runtime clip.
        clips[action] = dict(source_facing="right",loop=action=="idle",
                             hold=action in ("down","victory"),finish="idle",
                             frames=[dict(path=f"assets/curated/{name}/pose_{i:02d}.png",
                                          duration=dt,anchor=anchors[i]) for i,dt in zip(indices,durations)])
        if action in MARKERS:
            release,impact = MARKERS[action]
            if action == "ultimate" and character in ("Tanjiro","Zenitsu"):
                impact = 1.05
            clips[action]["events"] = [dict(name="release",time=release),dict(name="impact",time=impact)]
    manifest_path = ROOT/"assets/animations.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else dict(version=1,characters={})
    manifest["characters"][character] = dict(clips=clips,source=f"assets/sources/{name}-poses.png",
                                              scale=scale)
    manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
    print(f"Exported {character}: 16 poses, {len(clips)} clips")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character",choices=["Sasuke","Tanjiro","Itachi","Zenitsu"])
    export(parser.parse_args().character)
