import array
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import wave

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
from client import Game
from combat_audio import CombatAudio

ROOT = Path(__file__).resolve().parents[1]


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.game = Game()
        self.game.player_id = 'P1'
        self.game._handle_server_msg(dict(type='STATE', match_id='audio', phase='BATTLE',
            turn='P1', char_p1='Tanjiro', char_p2='Sasuke', hp_p1=100, hp_p2=100,
            last_action=None))

    def tearDown(self):
        pygame.quit()

    def state(self, damage=25, reflected=False):
        return dict(type='STATE', match_id='audio', phase='BATTLE', turn='P2',
            char_p1='Tanjiro', char_p2='Sasuke', hp_p1=100, hp_p2=100-damage,
            last_action=dict(id=1, by='P1', target='P2', action='JUTSU', dmg=damage,
                             reflected=reflected))

    def test_contact_release_and_voice_are_once_per_action(self):
        with patch.object(self.game.audio, 'play') as play:
            state = self.state()
            self.game._handle_server_msg(state)
            self.game._handle_server_msg(state)
            self.game._advance_presentation(.01)
            self.assertEqual([c.args[2] for c in play.call_args_list], ['start'])
            self.game._advance_presentation(3)
            self.assertEqual([c.args[2] for c in play.call_args_list], ['start', 'release', 'impact'])

    def test_miss_has_release_but_no_contact(self):
        with patch.object(self.game.audio, 'play') as play:
            self.game._handle_server_msg(self.state(damage=0))
            self.game._advance_presentation(3)
            self.assertEqual([c.args[2] for c in play.call_args_list], ['start', 'release'])

    def test_reflection_plays_block_instead_of_damage_sound(self):
        with patch.object(self.game.audio, 'play') as play:
            self.game._handle_server_msg(self.state(reflected=True))
            self.game._advance_presentation(3)
            self.assertEqual([c.args[2] for c in play.call_args_list], ['start', 'release', 'block'])

    def test_voice_holds_recovery_without_moving_contact(self):
        for character in ('Tanjiro', 'Sasuke'):
            with self.subTest(character=character):
                self.game.sfx_enabled = True
                original = self.game._timing(character, 'jutsu')
                presentation = self.game._presentation_timing(character, 'jutsu')
                voice = self.game.audio.voice_duration(character, 'jutsu')
                self.assertGreater(voice, .1)
                self.assertGreaterEqual(presentation['duration'], voice)
                self.assertAlmostEqual(presentation['impact'], original['impact'])
                self.game.audio.play(character, 'jutsu', 'start')
                self.assertTrue(self.game.audio.channels['voice'].get_busy())
                self.game.sfx_enabled = False
                muted = self.game._presentation_timing(character, 'jutsu')
                self.assertEqual(muted['impact'], presentation['impact'])
                self.assertEqual(muted['duration'], original['duration'])

    def test_voice_ducking_and_master_mute(self):
        audio = self.game.audio
        audio.update(.8, True)
        audio.play('Tanjiro', 'jutsu', 'start')
        audio.play('Tanjiro', 'jutsu', 'release')
        self.assertTrue(audio.channels['voice'].get_busy())
        self.assertLess(audio.channels['release'].get_volume(), audio.channels['voice'].get_volume())
        audio.update(.2, True)
        self.assertLessEqual(audio.channels['voice'].get_volume(), .2)
        audio.update(.2, False)
        self.assertFalse(any(c.get_busy() for c in audio.channels.values()))

    def test_no_device_and_missing_samples_are_nonfatal(self):
        audio = self.game.audio
        audio.moves['Sasuke']['jutsu']['release'] = 'missing.wav'
        audio.play('Sasuke', 'jutsu', 'release')
        self.assertTrue(audio.channels['release'].get_busy())  # Generated fallback.
        pygame.mixer.quit()
        audio.update(.5, True)
        audio.play('Tanjiro', 'jutsu', 'start')
        self.assertEqual(audio.voice_duration('Tanjiro', 'jutsu'), 0)

    def test_new_turn_and_disconnect_clear_previous_voice(self):
        audio = self.game.audio
        audio.play('Tanjiro', 'jutsu', 'start')
        audio.play('Sasuke', 'attack', 'start')
        self.assertFalse(audio.channels['voice'].get_busy())
        audio.play('Tanjiro', 'jutsu', 'start')
        self.game._handle_server_msg(dict(type='OPPONENT_DISCONNECTED'))
        self.assertFalse(any(c.get_busy() for c in audio.channels.values()))

    def test_all_sampled_cues_decode_and_have_headroom(self):
        manifest = json.loads((ROOT/'assets/audio/combat.json').read_text())
        referenced = set()
        for moves in manifest['characters'].values():
            for action, move in moves.items():
                self.assertIn('impact', move)
                if action != 'heal':
                    self.assertIn('release', move)
                for stage in ('voice', 'start', 'release', 'impact', 'block'):
                    if stage in move:
                        referenced.add(move[stage])
        self.assertEqual(len(referenced), 64)
        for path in referenced:
            with self.subTest(path=path), wave.open(str(ROOT/path)) as stream:
                self.assertEqual((stream.getnchannels(), stream.getsampwidth(), stream.getframerate()), (1, 2, 44100))
                values = array.array('h', stream.readframes(stream.getnframes()))
                self.assertGreater(max(abs(v) for v in values), 1000)
                self.assertLess(max(abs(v) for v in values), 30000)
                self.assertEqual((values[0], values[-1]), (0, 0))
            self.assertGreater(pygame.mixer.Sound(str(ROOT/path)).get_length(), .05)


if __name__ == '__main__':
    unittest.main()
