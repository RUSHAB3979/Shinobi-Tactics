"""Review regressions: pose/contact semantics, socket transforms and distinct VFX."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from pathlib import Path
import pygame
from animation import AnimationPlayer,ClipLibrary
from power_visuals import CombatEffect

ROOT=Path(__file__).resolve().parents[1]


class PowerTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init();pygame.display.set_mode((1024,640))
        self.library=ClipLibrary(ROOT)

    def effect(self,name='Sasuke',action='JUTSU',**kwargs):
        clip=self.library.data['characters'][name]['clips'][action.lower()]
        timing={e['name']:e['time'] for e in clip['events']}
        timing['duration']=sum(f['duration'] for f in clip['frames'])
        return CombatEffect(name,action,(195,414),(810,270),timing,**kwargs)

    def test_chidori_bare_hand_pose_and_attached_charge_at_contact(self):
        actor=AnimationPlayer(self.library,'Sasuke');actor.play('jutsu')
        effect=self.effect();actor.update(effect.timing['impact'])
        frame=actor.clip['frames'][actor.frame_index]
        self.assertEqual(Path(frame['path']).parts[-3:],('techniques','jutsu','08.png'))
        self.assertNotIn('weapon',frame['sockets'])
        effect.update(effect.timing['impact']);position=effect.movement()
        effect.bind(actor,position,'right')
        self.assertEqual(effect.hand,actor.socket('hand',position,'right'))
        # Contact hand reaches the opponent's silhouette, not the original root.
        self.assertLess(abs(effect.hand[0]-effect.target[0]),45)
        self.assertGreater(effect.hand[0],700)

    def test_sockets_mirror_about_anchor_and_move_with_actor(self):
        actor=AnimationPlayer(self.library,'Sasuke');actor.play('jutsu');actor.update(.65)
        a=actor.socket('hand',(500,300),'right');b=actor.socket('hand',(500,300),'left')
        self.assertAlmostEqual(a[0]+b[0],1000);self.assertEqual(a[1],b[1])
        moved=actor.socket('hand',(530,310),'right')
        self.assertEqual(moved,(a[0]+30,a[1]+10))

    def test_reduced_motion_melee_still_reaches_contact_both_sides(self):
        for name in ('Sasuke','Tanjiro','Zenitsu'):
            for source,target in [((195,414),(810,270)),((810,270),(195,414))]:
                effect=self.effect(name,'ATTACK');effect.source=source;effect.target=target
                effect.contact_target=target;effect.direction=1 if target[0]>source[0] else -1
                effect.update(effect.timing['impact'])
                pos=effect.movement(reduced=True)
                self.assertLessEqual(abs(pos[0]-target[0]),82)
                self.assertEqual(pos[1],target[1])
                effect.reduced=True;self.assertEqual(effect.trail_positions(),[])

    def test_itachi_techniques_distinct_in_normal_and_reduced_modes(self):
        for reduced in (False,True):
            renders=[]
            for action in ('JUTSU','ULTIMATE'):
                effect=self.effect('Itachi',action);effect.reduced=reduced;effect.update(.58)
                surface=pygame.Surface((1024,640));surface.fill((30,40,50))
                effect.draw_background(surface);effect.draw(surface)
                renders.append(pygame.image.tobytes(surface,'RGB'))
            self.assertNotEqual(*renders)

    def test_power_art_has_eight_unique_poses_per_move(self):
        for name in self.library.data['characters']:
            for action in ('jutsu','ultimate'):
                frames=self.library.data['characters'][name]['clips'][action]['frames']
                self.assertGreaterEqual(len({f['path'] for f in frames}),8)
                self.assertTrue(all('hand' in f['sockets'] for f in frames))

    def test_kirin_reflection_and_miss_keep_actual_target(self):
        effect=self.effect(action='ULTIMATE',reflected=True,contact_target=(810,270))
        effect.target=effect.source;effect.update(effect.timing['impact']);effect.impact()
        surface=pygame.Surface((1024,640));surface.fill((0,0,0))
        effect.draw(surface)
        self.assertNotEqual(surface.get_at((195,334))[:3],(0,0,0))
        self.assertEqual(effect.target,(195,414))
        effect=self.effect(action='ULTIMATE',miss=True)
        effect.update(effect.timing['impact']);effect.impact()
        layer=pygame.Surface((1024,530),pygame.SRCALPHA);effect._impact(layer,1)
        self.assertEqual(layer.get_bounding_rect().width,0)

    def test_sixfold_has_six_distinct_ordered_accents_single_damage_event(self):
        effect=self.effect('Zenitsu')
        self.assertEqual(len(set(effect.accent_times)),6)
        self.assertEqual(effect.accent_times,sorted(effect.accent_times))
        clip=self.library.data['characters']['Zenitsu']['clips']['jutsu']
        self.assertEqual(sum(e['name']=='impact' for e in clip['events']),1)

    def test_effect_layers_cannot_obscure_command_panel(self):
        for name in self.library.data['characters']:
            for action in ('JUTSU','ULTIMATE'):
                effect=self.effect(name,action);effect.update(effect.timing['impact']);effect.impact()
                surface=pygame.Surface((1024,640));surface.fill((37,49,61))
                effect.draw_background(surface);effect.draw(surface)
                self.assertEqual(surface.get_at((512,575))[:3],(37,49,61))


if __name__=='__main__':unittest.main()
