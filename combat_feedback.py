"""Bounded, deterministic camera impulses and elemental impact aftermath.

All coordinates are world coordinates. The client composites this world once,
then draws its HUD in screen space. No gameplay state is changed here.
"""
import math
from dataclasses import dataclass

import pygame


@dataclass
class Impact:
    character: str
    action: str
    target: tuple
    direction: int
    reflected: bool = False
    age: float = 0.

    @property
    def strength(self):
        return {'ATTACK': .35, 'JUTSU': .7, 'ULTIMATE': 1.}[self.action]

    @property
    def illusion(self):
        return self.reflected or (self.character == 'Itachi' and self.action != 'ATTACK')

    @property
    def color(self):
        if self.illusion: return (235, 65, 120)
        if self.character == 'Tanjiro':
            return (255, 150, 48) if self.action == 'ULTIMATE' else (85, 220, 245)
        return (130, 205, 255) if self.character == 'Sasuke' else (255, 222, 95)


class CombatFeedback:
    def __init__(self):
        self.impacts = []
        self.layer = pygame.Surface((1024, 530), pygame.SRCALPHA)

    def reset(self):
        self.impacts.clear()

    def hit(self, character, action, source, target, reflected=False):
        if action == 'HEAL': return
        self.impacts.append(Impact(character, action, target,
                                   1 if target[0] > source[0] else -1, reflected))
        self.impacts = self.impacts[-6:]

    def update(self, dt):
        for impact in self.impacts: impact.age += dt
        self.impacts = [hit for hit in self.impacts if hit.age < 3.2]

    @staticmethod
    def hitstop(action, reduced=False):
        return .025 if reduced else {'ATTACK': .045, 'JUTSU': .065, 'ULTIMATE': .095}[action]

    def camera(self, reduced=False):
        if reduced: return (0, 0)
        x = y = 0.
        for hit in self.impacts:
            duration = .18 + hit.strength * .32
            if hit.age >= duration: continue
            q = hit.age / duration
            amplitude = (3 + 10 * hit.strength) * (1-q)**2
            # A decisive directional kick followed by a damped recoil.
            x += hit.direction * amplitude * math.cos(q*27)
            y += amplitude * .6 * math.sin(q*34 + .8)
        return (round(max(-16, min(16, x))), round(max(-10, min(10, y))))

    def displacement(self, root, reduced=False):
        if reduced: return (0, 0)
        x = y = 0.
        for hit in self.impacts:
            if hit.target != root or hit.age > .48: continue
            q = hit.age / .48
            kick = math.sin(math.pi*q) * (1-q)
            x += hit.direction * kick * (12 if hit.illusion else 40) * hit.strength
            y -= kick * (3 if hit.illusion else 16) * hit.strength
        return (x, y)

    def draw_ground(self, surface, reduced=False):
        layer = self.layer
        layer.fill((0, 0, 0, 0))
        for hit in self.impacts:
            if hit.action == 'ATTACK': continue
            x, y = hit.target
            fade = min(1, (3.2-hit.age)/1.1)
            s = hit.strength
            radius = (52 + 35*s)
            if hit.illusion:
                pygame.draw.ellipse(layer, (*hit.color, round(95*fade)),
                    (x-radius, y-13, radius*2, 26), 2)
                continue
            water = hit.character == 'Tanjiro' and hit.action == 'JUTSU'
            pygame.draw.ellipse(layer, (45, 85, 100, round(75*fade)) if water else (18, 20, 28, round(135*fade)),
                                (x-radius, y-15, radius*2, 30))
            for j in range(9):
                a = j*math.tau/9
                points = [(x, y), (x+math.cos(a)*radius*.45, y+math.sin(a)*9),
                          (x+math.cos(a+.13)*radius, y+math.sin(a+.13)*21)]
                if water:
                    pygame.draw.ellipse(layer, (*hit.color, round(65*fade)),
                        (x-radius+j*3, y-13+j, radius*2-j*6, max(2,26-j*2)), 1)
                else:
                    pygame.draw.lines(layer, (12, 16, 23, round(220*fade)), False, points, 3)
                    pygame.draw.lines(layer, (*hit.color, round(110*fade)), False, points, 1)
        surface.blit(layer, (0, 0))

    def draw_front(self, surface, reduced=False):
        layer = self.layer
        layer.fill((0, 0, 0, 0))
        for hit in self.impacts:
            t, s = hit.age, hit.strength
            x, ground = hit.target
            y = ground-75
            color = hit.color
            if t < .48:
                fade = (1-t/.48)**1.5
                r = 26 + (20 if reduced else 230)*t*s
                pygame.draw.ellipse(layer, (*color, round(180*fade)),
                    (x-r, y-r*.65, r*2, r*1.3), max(1, round(6*fade)))
                if not reduced and not hit.illusion:
                    # A flattened ground shockwave, distinct from the contact ring.
                    r = 25 + 330*t*s
                    pygame.draw.ellipse(layer, (*color, round(130*fade)),
                        (x-r, ground-r*.22, r*2, r*.44), max(1, round(5*fade)))
            if reduced: continue
            if hit.illusion:
                if t > .8: continue
                # Inward shards: an implosion, rather than physical rubble.
                for j in range(18):
                    a = j*2.399
                    r = (1-t/.8)*(65+30*(j%3))
                    px, py = x+math.cos(a)*r, y+math.sin(a)*r
                    pygame.draw.polygon(layer, (*color, round(160*(1-t/.8))),
                        [(px,py-9),(px+3,py),(px,py+9),(px-3,py)])
                continue
            if t > 1.15: continue
            fade = (1-t/1.15)**.8
            water = hit.character == 'Tanjiro' and hit.action == 'JUTSU'
            fire = hit.character == 'Tanjiro' and hit.action == 'ULTIMATE'
            for j in range(28 if hit.action == 'ULTIMATE' else 16):
                a = j*2.399
                velocity = 65 + (j*43 % 180)*s
                px = x+math.cos(a)*velocity*t
                py = ground-8-(80+(j*29 % 145))*t+170*t*t
                if py > ground+16: continue
                radius = 2+(j%4)
                if water or fire:
                    pygame.draw.line(layer, (*color, round(200*fade)), (px,py),
                        (px-math.cos(a)*7, py+9 if water else py+5), 2 if water else 3)
                else:
                    pygame.draw.polygon(layer, (84+j%3*19, 88+j%3*16, 98+j%3*14, round(240*fade)),
                        [(px-radius,py),(px,py-radius),(px+radius,py+1),(px+1,py+radius)])
                    if j%3 == 0:
                        pygame.draw.line(layer, (*color, round(210*fade)), (px,py-3),(px+4,py-7),2)
            # Slow dust settles after the fast shards. Water uses a blue mist.
            if hit.action != 'ATTACK':
                for j in range(7):
                    px = x + (j-3)*(11+t*34)*s
                    py = ground-4-t*17+math.sin(j*3)*5
                    r = 10+t*19
                    dust = (90,160,180) if water else (111,100,87)
                    pygame.draw.ellipse(layer, (*dust, round(44*fade)), (px-r,py-r*.5,r*2,r))
        surface.blit(layer, (0, 0))
