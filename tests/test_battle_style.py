import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
import pygame
from client import Game,CHARACTERS
from power_visuals import CombatEffect


class BattleStyleTests(unittest.TestCase):
    def setUp(self):self.game=Game()
    def tearDown(self):pygame.quit()

    def test_all_move_titles_fit_command_cards(self):
        for character in CHARACTERS.values():
            for title in character['move_names']:
                self.assertLessEqual(self.game.style.fonts[18].size(title)[0],184)
        for button in self.game.battle_buttons:
            self.assertGreaterEqual(button.rect.left,0)
            self.assertLessEqual(button.rect.right,1024)
            self.assertGreaterEqual(button.rect.top,530)

    def test_lighting_cache_is_bounded_and_healing_has_no_attack_light(self):
        style=self.game.style
        surface=pygame.Surface((1024,530));surface.fill((10,10,10))
        effect=CombatEffect('Sasuke','HEAL',(195,450),(810,420),dict(release=.2,impact=.5,duration=1))
        before=pygame.image.tobytes(surface,'RGB')
        style.lighting(surface,effect)
        self.assertEqual(before,pygame.image.tobytes(surface,'RGB'))
        effect.action='ULTIMATE'
        for i in range(200):
            effect.age=i/400
            style.lighting(surface,effect)
        self.assertLessEqual(len(style.lights),15)  # Six colors plus nine quantized levels.

    def test_reduced_motion_removes_ambient_particles(self):
        style=self.game.style
        a=pygame.Surface((1024,530));a.fill((10,10,10))
        b=a.copy()
        style.atmosphere(a,0,True)
        style.atmosphere(b,1,True)
        self.assertEqual(pygame.image.tobytes(a,'RGB'),pygame.image.tobytes(b,'RGB'))


if __name__=='__main__':unittest.main()
