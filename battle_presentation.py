"""Deterministic presentation queue. Authoritative state is never recalculated here."""
from collections import deque
from copy import deepcopy
import math


class PresentationQueue:
    def __init__(self, timings):
        self.timings = timings
        self.reset()

    def reset(self):
        self.pending = deque()
        self.seen = set()
        self.active = None
        self.elapsed = 0.0
        self.markers = []
        self.visible_hp = {"P1": 100, "P2": 100}
        self.visible_shields = {"P1": False, "P2": False}
        self.pause_remaining = 0.0

    @property
    def busy(self):
        return self.active is not None or bool(self.pending)

    def enqueue(self, snapshot):
        action = snapshot.get("last_action")
        if not action:
            if not self.busy:
                self.visible_hp = {"P1": snapshot["hp_p1"], "P2": snapshot["hp_p2"]}
            return False
        # IDs are emitted by the matching server version; never dedup by move name.
        identity = (snapshot["match_id"], action["id"])
        if identity in self.seen:
            return False
        self.seen.add(identity)
        self.pending.append(deepcopy(snapshot))
        return True

    def update(self, dt, on_event=None, on_advance=None, on_clock=None):
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt must be finite and nonnegative")
        events = []
        def emit(name, state):
            events.append((name,state))
            if on_event is not None:
                on_event(name,state)
        while self.busy:
            if self.pause_remaining > 0:
                pause = min(dt,self.pause_remaining)
                if on_clock is not None: on_clock(pause)
                self.pause_remaining -= pause
                dt -= pause
                if dt < 1e-9:
                    break
            if self.active is None:
                self.active = self.pending.popleft()
                action = self.active["last_action"]
                char = self.active["char_p1" if action["by"] == "P1" else "char_p2"]
                timing = self.timings(char, action["action"].lower())
                self.markers = deque(sorted([(timing["release"],"release"),
                                             (timing["impact"],"impact"),
                                             (timing["duration"],"finish")]))
                self.elapsed = 0.0
                emit("start",self.active)
            marker, name = self.markers[0]
            step = min(dt, max(0.0, marker-self.elapsed))
            if on_clock is not None: on_clock(step)
            if on_advance is not None:
                on_advance(step)
            self.elapsed += step
            dt -= step
            if self.elapsed + 1e-9 >= marker:
                self.markers.popleft()
                if name == "impact":
                    self.visible_hp = {"P1": self.active["hp_p1"], "P2": self.active["hp_p2"]}
                    self.visible_shields = {pid:self.active.get(f"genjutsu_shield_{pid.lower()}",False)
                                            for pid in ("P1","P2")}
                emit(name,self.active)
                if name == "finish":
                    self.active = None
            else:
                break
            if dt < 1e-9:
                break
        if dt > 1e-9 and not self.busy:
            if on_clock is not None: on_clock(dt)
            if on_advance is not None: on_advance(dt)
        return events

    @property
    def progress(self):
        return self.elapsed
