"""Technique timeline regression checks replacing the rejected portrait pre-roll."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import unittest
import pygame
from client import Game

class TechniqueTimelineTests(unittest.TestCase):
    def setUp(self):
        self.game=Game();self.game.player_id="P1"
        self.state=dict(type="STATE",phase="BATTLE",match_id="technique",turn="P2",
                        char_p1="Sasuke",char_p2="Itachi",hp_p1=100,hp_p2=100,last_action=None)
        self.game._handle_server_msg(self.state)
    def tearDown(self):pygame.quit()
    def enqueue(self):
        self.game._handle_server_msg({**self.state,"hp_p2":50,
            "last_action":dict(id=1,by="P1",target="P2",action="ULTIMATE",dmg=50)})
    def test_body_and_effect_start_immediately_hp_waits_for_contact(self):
        self.enqueue();self.game._advance_presentation(.7)
        self.assertIsNotNone(self.game.effect)
        self.assertAlmostEqual(self.game.effect.age,.7)
        self.assertAlmostEqual(self.game.player_anim.elapsed,.7)
        self.assertEqual(self.game.presentation.visible_hp["P2"],100)
        timing=self.game._timing("Sasuke","ultimate")
        self.game._advance_presentation(timing["impact"]-.7-.01)
        self.assertEqual(self.game.presentation.visible_hp["P2"],100)
        self.game._advance_presentation(.02)
        self.assertEqual(self.game.presentation.visible_hp["P2"],50)
        self.assertEqual(len(self.game.feedback.impacts),1)
    def test_long_frame_and_small_steps_agree(self):
        samples=[]
        for steps in ([2.4],[.01]*240):
            self.game._handle_server_msg(dict(type="STATE",phase="SELECT"))
            self.game._handle_server_msg(self.state);self.enqueue()
            for dt in steps:self.game._advance_presentation(dt)
            samples.append((self.game.effect.age,self.game.player_anim.elapsed,self.game.feedback.impacts[-1].age))
        for a,b in zip(*samples):self.assertAlmostEqual(a,b)
    def test_disconnect_clears_pending_technique(self):
        self.enqueue();self.game._advance_presentation(.4)
        self.game._handle_server_msg(dict(type="OPPONENT_DISCONNECTED"))
        self.assertFalse(self.game.presentation.busy)
        self.assertIsNone(self.game.effect)
    def test_charge_and_release_markers_do_not_apply_damage(self):
        for name in self.game.clip_library.data["characters"]:
            for action in ("jutsu","ultimate"):
                timing=self.game._presentation_timing(name,action)
                original=self.game._timing(name,action)
                self.assertNotIn("intro",timing)
                self.assertEqual(timing["impact"],original["impact"])
                self.assertLess(timing["release"],timing["impact"])

    def test_background_and_front_effects_bind_same_current_hand(self):
        from unittest.mock import patch
        self.state.update(char_p1="Tanjiro")
        self.game._handle_server_msg(dict(type="STATE",phase="SELECT"))
        self.game._handle_server_msg(self.state)
        self.game._handle_server_msg({**self.state,"hp_p2":75,
            "last_action":dict(id=1,by="P1",target="P2",action="JUTSU",dmg=25)})
        self.game._advance_presentation(0)
        observed=[]
        original=self.game.effect.draw_background
        def check(surface,intensity):
            root=self.game.effect.movement()
            observed.append((self.game.effect.hand,self.game.player_anim.socket("hand",root,"right")))
            original(surface,intensity)
        with patch.object(self.game.effect,"draw_background",side_effect=check):
            self.game._scene_battle([],(-1,-1),1.0)
        self.assertEqual(observed[0][0],observed[0][1])
        self.assertGreater(observed[0][0][0],500)

    def test_sixfold_moves_through_six_endpoints_godspeed_does_not_zigzag(self):
        from power_visuals import CombatEffect
        effects=[]
        for action in ("JUTSU","ULTIMATE"):
            effect=CombatEffect("Zenitsu",action,(195,450),(810,420),self.game._timing("Zenitsu",action.lower()))
            r,i=effect.timing["release"],effect.timing["impact"]
            positions=[effect.movement(age=r+(i-r)*k/6) for k in range(7)]
            effects.append(positions)
        self.assertEqual(len(set(effects[0])),7)
        self.assertTrue(any(b[0]<a[0] for a,b in zip(effects[0],effects[0][1:])))
        self.assertTrue(all(b[0]>=a[0] for a,b in zip(effects[1],effects[1][1:])))

    def test_kirin_forms_before_release_then_descends_to_contact(self):
        from power_visuals import CombatEffect
        effect=CombatEffect("Sasuke","ULTIMATE",(195,450),(810,420),self.game._timing("Sasuke","ultimate"))
        layer=pygame.Surface((1024,530),pygame.SRCALPHA)
        effect.update(effect.timing["form"]+.4);effect._kirin(layer)
        self.assertGreater(layer.get_bounding_rect().width,100)
        held=effect.kirin_jaw
        effect.age=effect.timing["impact"]
        self.assertGreater(effect.kirin_jaw[1],held[1])
        self.assertAlmostEqual(effect.kirin_jaw[0],810)
        self.assertAlmostEqual(effect.kirin_jaw[1],340)
