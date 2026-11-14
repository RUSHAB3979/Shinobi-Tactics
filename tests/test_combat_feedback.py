import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
from client import Game
from combat_feedback import CombatFeedback


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.player_id = 'P1'
        self.state = dict(type='STATE', phase='BATTLE', match_id='feedback', turn='P1',
                          char_p1='Sasuke', char_p2='Itachi', hp_p1=100, hp_p2=100, last_action=None)
        self.game._handle_server_msg(self.state)

    def tearDown(self):
        pygame.quit()

    def act(self, action='ULTIMATE', damage=50, reflected=False):
        self.state['last_action'] = dict(id=1, by='P1', target='P2', action=action, dmg=damage, reflected=reflected)
        self.game._handle_server_msg(self.state)
        self.game._advance_presentation(.01)
        self.game._advance_presentation(self.game._presentation_timing('Sasuke', action.lower())['impact']-.01)

    def test_misses_and_heals_do_not_shake_or_destroy_ground(self):
        self.act(damage=0)
        self.assertEqual(self.game.feedback.impacts, [])
        self.game._handle_server_msg(dict(type='STATE', phase='SELECT'))
        self.state['last_action'] = None
        self.game._handle_server_msg(self.state)
        self.act('HEAL', 0)
        self.assertEqual(self.game.feedback.impacts, [])

    def test_reflected_ultimate_impacts_attacker_and_reverses_kick(self):
        self.act(reflected=True)
        impact = self.game.feedback.impacts[-1]
        self.assertEqual(impact.target, self.game._root('P1'))
        self.assertLess(self.game.feedback.camera()[0], 0)
        self.assertTrue(impact.illusion)

    def test_ultimate_has_stronger_hitstop_and_kick_than_basic(self):
        feedback = self.game.feedback
        feedback.hit('Sasuke', 'ATTACK', (195,414), (810,270))
        basic = abs(feedback.camera()[0])
        feedback.reset()
        feedback.hit('Sasuke', 'ULTIMATE', (195,414), (810,270))
        self.assertGreater(abs(feedback.camera()[0]), basic)
        self.assertGreater(feedback.hitstop('ULTIMATE'), feedback.hitstop('ATTACK'))

    def test_reduced_motion_disables_camera_and_knockback(self):
        self.act()
        feedback = self.game.feedback
        feedback.update(.1)
        self.assertEqual(feedback.camera(True), (0,0))
        self.assertEqual(feedback.displacement(self.game._root("P2"), True), (0,0))
        self.assertNotEqual(feedback.displacement(self.game._root("P2")), (0,0))

    def test_hud_is_pixel_identical_when_camera_moves(self):
        self.act()
        self.game._scene_battle([], (-1,-1), 0)
        before = self.game.screen.copy()
        with patch.object(self.game.feedback, 'camera', return_value=(-16,-10)):
            self.game._scene_battle([], (-1,-1), 0)
        for rect in [(0,530,1024,110), (650,35,328,42), (44,35,328,42)]:
            self.assertEqual(pygame.image.tobytes(before.subsurface(rect),'RGB'),
                             pygame.image.tobytes(self.game.screen.subsurface(rect),'RGB'))
        self.assertNotEqual(pygame.image.tobytes(before,'RGB'), pygame.image.tobytes(self.game.screen,'RGB'))

    def test_aftermath_bounded_expires_and_disconnect_clears_it(self):
        feedback = self.game.feedback
        for _ in range(20): feedback.hit('Tanjiro','ULTIMATE',(195,414),(810,270))
        self.assertEqual(len(feedback.impacts),6)
        feedback.update(3.3)
        self.assertEqual(feedback.impacts,[])
        self.act()
        self.game._handle_server_msg(dict(type='OPPONENT_DISCONNECTED'))
        self.assertEqual(feedback.impacts,[])

    def test_weight_audio_plays_on_contact_and_mute_stops_it(self):
        audio = self.game.audio
        audio.play('Sasuke', 'ULTIMATE', 'start')
        self.assertFalse(audio.channels['weight'].get_busy())
        audio.play('Sasuke', 'ULTIMATE', 'impact')
        self.assertTrue(audio.channels['weight'].get_busy())
        audio.update(.5,False)
        self.assertFalse(audio.channels['weight'].get_busy())

    def test_camera_aftermath_clock_is_independent_of_frame_size_and_hitstop(self):
        ages=[]
        for steps in ([2.4], [1/60]*144):
            self.game._handle_server_msg(dict(type='STATE', phase='SELECT'))
            self.state['last_action'] = None
            self.game._handle_server_msg(self.state)
            self.state['last_action'] = dict(id=1,by='P1',target='P2',action='ULTIMATE',dmg=50)
            self.game._handle_server_msg(self.state)
            for dt in steps: self.game._advance_presentation(dt)
            ages.append(self.game.feedback.impacts[-1].age)
        self.assertAlmostEqual(ages[0], ages[1])
        self.assertAlmostEqual(ages[0], .35)


if __name__ == '__main__': unittest.main()
