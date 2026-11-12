"""Inventory original art without importing the game or modifying source assets."""
import argparse
import ast
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def natural_key(value):
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", str(value))]


def inventory(output):
    output.mkdir(parents=True, exist_ok=True)
    groups = defaultdict(list)
    hashes = defaultdict(list)
    errors = []
    review_path = ROOT / "docs/legacy-review.json"
    reviews = json.loads(review_path.read_text()) if review_path.exists() else {}
    for path in sorted((ROOT / "assets").rglob("*.png"), key=natural_key):
        if "curated" in path.parts or "sources" in path.parts or path.name == "arena.png":
            continue
        rel = path.relative_to(ROOT).as_posix()
        try:
            with Image.open(path) as src:
                image = src.convert("RGBA")
                bounds = image.getbbox()
                digest = hashlib.sha256(image.tobytes()).hexdigest()
                entry = dict(path=rel, size=list(image.size), bounds=bounds,
                             bytes=path.stat().st_size, sha256=digest,
                             classification=reviews.get(str(path.parent.relative_to(ROOT)), {}).get("classification", "unreviewed; quarantined"))
                groups[str(path.parent.relative_to(ROOT))].append(entry)
                hashes[digest].append(rel)
        except Exception as exc:
            errors.append(dict(path=rel, error=str(exc)))
    sheets = output / "contact-sheets"
    sheets.mkdir(exist_ok=True)
    for folder, entries in groups.items():
        # Preserve aspect ratio; labels always identify the exact source frame.
        for page in range(0, len(entries), 64):
            part = entries[page:page+64]
            sheet = Image.new("RGB", (1280, ((len(part)+7)//8)*156), (34, 38, 48))
            draw = ImageDraw.Draw(sheet)
            for index, item in enumerate(part):
                image = Image.open(ROOT/item["path"]).convert("RGBA")
                image.thumbnail((150, 126), Image.Resampling.NEAREST)
                x, y = (index % 8)*160, (index//8)*156
                sheet.paste(image, (x+(160-image.width)//2, y), image)
                draw.text((x+3, y+128), Path(item["path"]).stem, fill="white")
                draw.text((x+3, y+141), str(item["size"]), fill=(170,190,210))
            sheet.save(sheets/(folder.replace("/", "_")+f"_{page//64:02}.jpg"))
    source = ast.parse((ROOT/"client.py").read_text(encoding="utf-8-sig"))
    chars = next(ast.literal_eval(n.value) for n in source.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "CHARACTERS" for t in n.targets))
    mappings = []
    for name, data in chars.items():
        for action, folder in data.get("anim_map", {}).items():
            key = f"assets/{data['sprite_folder']}/{folder}"
            mappings.append(dict(character=name, action=action, folder=key,
                                 local_frames=len(groups.get(key, []))))
    try:
        tracked = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "HEAD"],
                                          cwd=ROOT, text=True, stderr=subprocess.DEVNULL).splitlines()
        commit = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    except subprocess.CalledProcessError:
        upstream = json.loads((ROOT/"docs/upstream-assets.json").read_text())
        tracked = [item["path"] for item in upstream["files"]]
        commit = upstream["commit"]+" (snapshot metadata; no Git checkout)"
    missing = [p for p in tracked if p.endswith(".png") and not (ROOT/p).exists()]
    sequences = {}
    for folder, entries in groups.items():
        numbers = [int(re.search(r"frame_(\d+)", e["path"])[1]) for e in entries
                   if re.search(r"frame_(\d+)", e["path"])]
        sequences[folder] = dict(count=len(entries),
                                gaps=[i for i in range(min(numbers),max(numbers)+1) if i not in numbers] if numbers else [],
                                numeric_order=[e["path"] for e in entries],
                                review=reviews.get(folder,dict(status="unreviewed; quarantined")))
    for mapping in mappings:
        prefix=mapping["folder"]+"/"
        mapping["tracked_frames"] = sum(p.startswith(prefix) and p.endswith(".png") for p in tracked)
        mapping["missing_mapping"] = mapping["tracked_frames"] == 0
    report = dict(commit=commit,
                  groups=groups, mappings=mappings, unmaterialized=missing,
                  sequences=sequences,
                  legacy_audio_references={name:data.get("sfx",{}) for name,data in chars.items()},
                  media_files=[p.relative_to(ROOT).as_posix() for p in (ROOT/"assets").rglob("*")
                               if p.suffix.lower() in (".mp3",".mp4",".wav")],
                  duplicates=[v for v in hashes.values() if len(v)>1], errors=errors)
    (output/"inventory.json").write_text(json.dumps(report, indent=2)+"\n")
    print(f"Inventoried {sum(map(len,groups.values()))} PNGs; {len(missing)} unmaterialized; "
          f"{len(errors)} decode errors. Sheets: {sheets}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT/"work"/"audit")
    inventory(parser.parse_args().output)
