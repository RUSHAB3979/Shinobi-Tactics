"""Layered, actor-anchored battle effects; no blocking loops or random targets."""
import math
from pathlib import Path
import pygame

PALETTES={"Sasuke":(120,190,255),"Tanjiro":(70,215,215),
          "Itachi":(238,75,98),"Zenitsu":(255,215,95)}
ACTOR_ROOTS={"left":(195,450),"right":(810,420)}


def lerp(a,b,t):
    return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)


def ease(t):
    t=max(0,min(1,t))
    return t*t*(3-2*t)


from power_visuals import CombatEffect


def create_arena(root, size):
    path=Path(root)/"assets/arena-glowup.png"
    if not path.exists():path=Path(root)/"assets/arena.png"
    if path.exists():
        return pygame.transform.smoothscale(pygame.image.load(str(path)).convert(),size)
    surface=pygame.Surface(size)
    w,h=size
    for y in range(h):
        t=y/h
        pygame.draw.line(surface,(int(15+13*t),int(24+17*t),int(39+18*t)),(0,y),(w,y))
    pygame.draw.circle(surface,(80,100,130),(590,145),58)
    for i in range(12):
        x=i*95
        pygame.draw.polygon(surface,(20,35,48),[(x,300),(x+60,155),(x+125,300)])
    pygame.draw.polygon(surface,(33,48,62),[(0,375),(w,220),(w,h),(0,h)])
    for i in range(9):
        y=270+i*38
        pygame.draw.line(surface,(43,59,72),(0,y+110),(w,y-35),1)
    return surface
