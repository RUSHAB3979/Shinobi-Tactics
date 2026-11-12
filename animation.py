"""Manifest-driven, per-actor animation with shared immutable image caches."""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import pygame

LOG = logging.getLogger(__name__)
REQUIRED = {"idle", "attack", "jutsu", "ultimate", "heal", "hit", "guard", "down", "victory"}


class ClipLibrary:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.data = json.loads((self.root / "assets/animations.json").read_text())
        self.images = {}
        self.transforms = {}
        self.validate()

    def validate(self):
        if self.data.get("version") != 1:
            raise ValueError("Unsupported animation manifest version")
        for name, char in self.data["characters"].items():
            clips = char["clips"]
            missing = REQUIRED - clips.keys()
            if missing:
                raise ValueError(f"{name}: missing clips {sorted(missing)}")
            for action, clip in clips.items():
                frames = clip["frames"]
                if not frames:
                    raise ValueError(f"{name}/{action}: no frames")
                duration = 0.0
                for frame in frames:
                    path = (self.root / frame["path"]).resolve()
                    if not path.is_relative_to(self.root.resolve()) or not path.is_file():
                        raise ValueError(f"{name}/{action}: missing/invalid image {frame['path']}")
                    dt = frame["duration"]
                    if not isinstance(dt, (int,float)) or not math.isfinite(dt) or dt <= 0:
                        raise ValueError(f"{name}/{action}: invalid duration {dt}")
                    if len(frame["anchor"]) != 2 or not all(math.isfinite(x) for x in frame["anchor"]):
                        raise ValueError(f"{name}/{action}: invalid anchor")
                    for socket in frame.get("sockets", {}).values():
                        if len(socket) != 2 or not all(math.isfinite(x) for x in socket):
                            raise ValueError(f"{name}/{action}: invalid attachment point")
                    duration += dt
                if clip.get("finish", "idle") not in clips:
                    raise ValueError(f"{name}/{action}: invalid completion target")
                if clip.get("source_facing") not in ("left", "right"):
                    raise ValueError(f"{name}/{action}: invalid source facing")
                for event in clip.get("events", []):
                    if not 0 < event["time"] <= duration:
                        raise ValueError(f"{name}/{action}: event outside clip: {event}")

    def image(self, path):
        if path not in self.images:
            image = pygame.image.load(str(self.root / path))
            self.images[path] = image.convert_alpha() if pygame.display.get_surface() else image
        return self.images[path]

    def transformed(self, path, scale, flip):
        key = (path, scale, flip)
        if key not in self.transforms:
            image = self.image(path)
            if scale != 1:
                image = pygame.transform.scale(image, (max(1,round(image.get_width()*scale)),
                                                       max(1,round(image.get_height()*scale))))
            if flip:
                image = pygame.transform.flip(image, True, False)
            self.transforms[key] = image
        return self.transforms[key]


class AnimationPlayer:
    def __init__(self, library: ClipLibrary, character: str):
        self.library = library
        self.char_name = character
        self.clips = library.data["characters"][character]["clips"]
        self.events = []
        self.play("idle", loop=True)

    def play(self, action_name, loop=None, on_finish=None):
        if action_name not in self.clips:
            LOG.error("%s has no '%s' clip; showing idle fallback", self.char_name, action_name)
            action_name = "idle"
        if getattr(self, "current_anim", None) == action_name and loop is True:
            return
        self.current_anim = action_name
        self.clip = self.clips[action_name]
        self.looping = self.clip.get("loop", False) if loop is None else loop
        self.on_finish = on_finish or self.clip.get("finish", "idle")
        self.frame_index = 0
        self.frame_timer = 0.0
        self.elapsed = 0.0
        self.finished = False
        self.events = []
        self._fired = set()

    def update(self, dt):
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt must be finite and nonnegative")
        while dt > 1e-10 and not self.finished:
            frame = self.clip["frames"][self.frame_index]
            step = min(dt, frame["duration"] - self.frame_timer)
            previous = self.elapsed
            self.elapsed += step
            self.frame_timer += step
            dt -= step
            for event in self.clip.get("events", []):
                if previous < event["time"] <= self.elapsed + 1e-10:
                    # The epsilon may reach a marker slightly early at a boundary;
                    # a playback-local set prevents it firing again next update.
                    token = (event["name"], event["time"])
                    if token not in getattr(self, "_fired", set()):
                        self._fired = getattr(self, "_fired", set()) | {token}
                        self.events.append(event["name"])
            if self.frame_timer + 1e-10 >= frame["duration"]:
                self.frame_timer = 0.0
                self.frame_index += 1
                if self.frame_index == len(self.clip["frames"]):
                    if self.looping:
                        self.frame_index = 0
                        self.elapsed = 0.0
                        self._fired = set()
                    elif self.clip.get("hold", False):
                        self.frame_index -= 1
                        self.finished = True
                    else:
                        events = self.events
                        self.play(self.on_finish)
                        self.events = events

    def drain_events(self):
        events, self.events = self.events, []
        return events

    def get_frame(self):
        return self.library.image(self.clip["frames"][self.frame_index]["path"])

    def socket(self, name, anchor, facing="right", scale=1.0):
        """Use the exact same pivot/offset/mirroring as draw, including playback poses."""
        frame = self.clip["frames"][self.frame_index]
        ax,ay = frame["anchor"]
        x,y = frame.get("sockets", {}).get(name, (ax,ay-80))
        ox,oy = frame.get("offset", (0,0))
        sign = 1 if self.clip["source_facing"] == facing else -1
        return (anchor[0]+sign*(x-ax+ox)*scale, anchor[1]+(y-ay+oy)*scale)

    def draw(self, surface, anchor, facing="right", scale=1.0, opacity=255):
        frame = self.clip["frames"][self.frame_index]
        flip = self.clip["source_facing"] != facing
        image = self.library.transformed(frame["path"], scale, flip)
        ax, ay = frame["anchor"]
        ox, oy = frame.get("offset", (0,0))
        if flip:
            ax = self.library.image(frame["path"]).get_width() - ax
            ox = -ox
        position = (round(anchor[0]+(ox-ax)*scale), round(anchor[1]+(oy-ay)*scale))
        if opacity != 255:
            image = image.copy()
            image.set_alpha(opacity)
        surface.blit(image, position)
        return pygame.Rect(position, image.get_size())

    @property
    def has_anims(self):
        return bool(self.clips)
