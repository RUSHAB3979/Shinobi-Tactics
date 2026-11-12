import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import unittest
from pathlib import Path
import pygame
from animation import ClipLibrary, AnimationPlayer
from tools.audit_assets import natural_key

ROOT=Path(__file__).resolve().parents[1]


class AnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.display.set_mode((1,1))
        cls.library=ClipLibrary(ROOT)

    def test_numeric_order(self):
        self.assertEqual(sorted(["frame_100.png","frame_11.png","frame_99.png"],key=natural_key),
                         ["frame_11.png","frame_99.png","frame_100.png"])

    def test_attack_event_order_for_stalls_and_render_rates(self):
        for dt in (1/30,1/60,1/120,.5,2.0):
            actor=AnimationPlayer(self.library,"Sasuke")
            actor.play("attack")
            events=[]
            elapsed=0
            while elapsed<.9:
                actor.update(dt)
                events+=actor.drain_events()
                elapsed+=dt
            self.assertEqual(events,["release","impact"])
            self.assertEqual(actor.current_anim,"idle")

    def test_repeated_play_resets_event_identity(self):
        actor=AnimationPlayer(self.library,"Sasuke")
        for _ in range(2):
            actor.play("attack")
            actor.update(1)
            self.assertEqual(actor.drain_events(),["release","impact"])

    def test_mirror_match_players_are_independent(self):
        left=AnimationPlayer(self.library,"Sasuke")
        right=AnimationPlayer(self.library,"Sasuke")
        left.play("attack")
        left.update(.35)
        self.assertEqual(right.current_anim,"idle")
        self.assertEqual(right.frame_index,0)
        self.assertIs(left.library,right.library)

    def test_defeat_holds(self):
        actor=AnimationPlayer(self.library,"Sasuke")
        actor.play("down")
        actor.update(8)
        self.assertEqual(actor.current_anim,"down")
        self.assertTrue(actor.finished)

    def test_loop_wrapping_matches_short_update(self):
        long=AnimationPlayer(self.library,"Sasuke")
        short=AnimationPlayer(self.library,"Sasuke")
        duration=sum(f["duration"] for f in long.clip["frames"])
        long.update(duration*3+.4)
        short.update(.4)
        self.assertEqual(long.frame_index,short.frame_index)
        self.assertAlmostEqual(long.frame_timer,short.frame_timer)

    def test_fallback_is_explicit(self):
        actor=AnimationPlayer(self.library,"Sasuke")
        with self.assertLogs("animation",level="ERROR"):
            actor.play("missing")
        self.assertEqual(actor.current_anim,"idle")


if __name__=="__main__": unittest.main()
