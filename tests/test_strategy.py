import copy
import unittest
from combat_rules import ACTIONS, unavailable
from server import GameServer


class StrategyTests(unittest.TestCase):
    def setUp(self):
        self.server = GameServer()
        self.addCleanup(self.server.sock.close)
        self.server._broadcast = lambda msg: None
        self.s = self.server.state
        self.s.phase = 'BATTLE'
        self.s.characters = dict(P1='Sasuke', P2='Zenitsu')

    def move(self, pid, action, **kwargs):
        self.server._process(dict(action=action, **kwargs), pid)

    def test_client_cannot_choose_damage(self):
        self.move('P1', 'ATTACK', dmg=99999)
        self.assertEqual(self.s.hp['P2'], 85)
        self.assertEqual(self.s.resources['P1']['chakra'], 40)

    def test_ultimate_requires_both_resources_and_charge(self):
        self.s.resources['P1']['chakra'] = 100
        before = copy.deepcopy(self.s.snapshot())
        self.move('P1', 'ULTIMATE')
        self.assertEqual(self.s.snapshot(), before)
        self.s.resources['P1']['charge'] = 3
        self.move('P1', 'ULTIMATE')
        self.assertEqual(self.s.hp['P2'], 50)
        self.assertEqual(self.s.resources['P1']['chakra'], 20)
        self.assertEqual(self.s.resources['P1']['charge'], 0)

    def test_guard_blocks_and_rewards_only_on_hit(self):
        self.move('P1', 'GUARD')
        self.move('P2', 'ATTACK')
        self.assertEqual(self.s.hp['P1'], 95)
        self.assertEqual(self.s.resources['P1']['chakra'], 45)
        before = copy.deepcopy(self.s.snapshot())
        self.move('P1', 'GUARD')
        self.assertEqual(self.s.snapshot(), before)
        self.move('P1', 'ATTACK')
        self.move('P2', 'ATTACK')
        self.assertEqual(self.s.hp['P1'], 80)

    def test_guard_expires_even_if_opponent_does_not_attack(self):
        self.move('P1', 'GUARD')
        self.move('P2', 'GUARD')
        self.move('P1', 'ATTACK')
        self.assertFalse(self.s.resources['P1']['guarding'])
        self.assertEqual(self.s.resources['P1']['chakra'], 40)

    def test_cooldown_counts_own_accepted_turns(self):
        self.move('P1', 'JUTSU')
        self.move('P2', 'ATTACK')
        self.s.resources['P1']['chakra'] = 100
        self.move('P1', 'JUTSU')
        self.assertEqual(self.s.turn, 'P1')
        self.move('P1', 'ATTACK')
        self.move('P2', 'ATTACK')
        self.assertFalse(unavailable(self.s.resources['P1'], 'JUTSU'))

    def test_failed_signs_charge_half_and_no_ultimate_progress(self):
        self.move('P1', 'JUTSU', success=False)
        self.assertEqual(self.s.hp['P2'], 100)
        self.assertEqual(self.s.resources['P1']['chakra'], 15)
        self.assertEqual(self.s.resources['P1']['charge'], 0)
        self.assertEqual(self.s.turn, 'P2')

    def test_chidori_pierces_guard(self):
        self.move('P1', 'GUARD')
        self.s.characters['P2'] = 'Sasuke'
        self.move('P2', 'JUTSU')
        self.assertEqual(self.s.hp['P1'], 82)

    def test_character_effects_and_counter_cap(self):
        self.s.characters = dict(P1='Itachi', P2='Tanjiro')
        self.move('P1', 'JUTSU')
        self.assertEqual(self.s.hp['P2'], 82)
        self.move('P2', 'JUTSU')
        self.assertTrue(self.s.last_action['reflected'])
        self.assertEqual(self.s.last_action['dmg'], 20)
        self.assertEqual(self.s.hp['P2'], 70)  # 82 - 20 counter + 8 sustain
        self.assertFalse(self.s.genjutsu_shield['P1'])

    def test_zenitsu_punishes_recover(self):
        self.s.hp['P1'] = 50
        self.move('P1', 'HEAL')
        self.move('P2', 'JUTSU')
        self.assertEqual(self.s.hp['P1'], 30)

    def test_reselect_cannot_reset_battle(self):
        self.move('P1', 'ATTACK')
        before = copy.deepcopy(self.s.snapshot())
        self.move('P2', 'SELECT_CHAR', character='Itachi')
        self.assertEqual(self.s.snapshot(), before)

    def test_reset_clears_resources_and_status(self):
        self.move('P1', 'GUARD')
        self.s.reset()
        self.assertEqual(self.s.resources['P1']['chakra'], 30)
        self.assertFalse(self.s.resources['P1']['guarding'])
        self.assertTrue(all(n == 0 for n in self.s.resources['P1']['cooldowns'].values()))
