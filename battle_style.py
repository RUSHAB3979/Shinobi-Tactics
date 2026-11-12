"""Shared painted-arena lighting and readable fighting-game interface.

Small cached light textures keep the software renderer practical on integrated
graphics. Decorative effects never encode unavailable gameplay resources.
"""
import math
from pathlib import Path
import pygame

INK=(10,17,28)
GOLD=(223,185,115)
WHITE=(239,239,228)
MUTED=(144,161,176)
COLORS={'Sasuke':(100,179,255),'Itachi':(240,91,114),
        'Tanjiro':(75,219,201),'Zenitsu':(255,207,89)}


class BattleStyle:
    def __init__(self):
        self.time=0.
        font=Path(__file__).resolve().parent/'assets/fonts/SpaceGrotesk-Bold.otf'
        self.fonts={size:pygame.font.Font(str(font),size) for size in (10,12,14,18,24,32,48)}
        self.text_cache={}
        self.lights={}
        self.overlay=pygame.Surface((1024,530),pygame.SRCALPHA)
        self.vignette=pygame.Surface((1024,530),pygame.SRCALPHA)
        for i in range(48):
            alpha=round(50*(1-i/48)**2)
            pygame.draw.rect(self.vignette,(2,8,18,alpha),(i*2,i,1024-i*4,530-i*2),2)
        for color in list(COLORS.values())+[(255,155,60),(150,200,220)]:
            glow=pygame.Surface((192,192)).convert()
            glow.fill((0,0,0))
            for radius in range(95,0,-1):
                strength=(1-radius/96)**2*.65
                pygame.draw.circle(glow,tuple(round(c*strength) for c in color),(96,96),radius)
            self.lights[color]=(glow,pygame.transform.smoothscale(glow,(240,72)))

    def text(self,surface,value,xy,size=12,color=WHITE,center=False):
        key=(value,size,color)
        if key not in self.text_cache:
            if len(self.text_cache)>512:self.text_cache.clear()
            self.text_cache[key]=self.fonts[size].render(value,True,color)
        img=self.text_cache[key]
        surface.blit(img,img.get_rect(center=xy) if center else xy)

    @staticmethod
    def color(effect):
        if effect.character=='Tanjiro' and effect.action=='ULTIMATE':return (255,155,60)
        return COLORS[effect.character]

    def atmosphere(self,surface,dt,reduced=False):
        self.time+=dt
        surface.blit(self.vignette,(0,0))
        if reduced:return
        layer=self.overlay;layer.fill((0,0,0,0))
        # Slow, sparse foreground ash; the fighting corridor stays readable.
        for j in range(24):
            x=(j*173+self.time*(9+j%4*3))%1080-28
            y=125+(j*67-self.time*(5+j%3))%380
            a=round(45+35*(.5+.5*math.sin(self.time+j)))
            color=(235,181,103,a) if j%3==0 else (164,201,218,a)
            pygame.draw.circle(layer,color,(round(x),round(y)),1 if j%4 else 2)
        surface.blit(layer,(0,0))

    def lighting(self,surface,effect,reduced=False):
        if not effect or effect.action not in ('JUTSU','ULTIMATE'):return
        if effect.age>effect.timing['impact']+.45:return
        color=self.color(effect)
        glow,ground=self.lights[color]
        # Illumination is attached to the same socket as the attack effect.
        contact=effect.impact_age is not None
        x,y=(effect.target[0],effect.target[1]-75) if contact else effect.hand
        strength=max(0,1-effect.impact_age/.45) if contact else min(1,effect.age/effect.timing['release'])*.55
        if reduced:strength*=.55
        glow.set_alpha(round(255*strength));ground.set_alpha(round(200*strength))
        # BLEND_RGB_ADD ignores per-surface alpha, so use cached quantized light levels.
        key=(color,round(strength*8))
        if key not in self.lights:
            factor=key[1]/8
            a=glow.copy();b=ground.copy()
            a.fill((round(255*factor),)*3,special_flags=pygame.BLEND_RGB_MULT)
            b.fill((round(210*factor),)*3,special_flags=pygame.BLEND_RGB_MULT)
            self.lights[key]=(a,b)
        a,b=self.lights[key]
        surface.blit(a,(round(x)-96,round(y)-96),special_flags=pygame.BLEND_RGB_ADD)
        floor=effect.target if contact else effect.body
        surface.blit(b,(round(floor[0])-120,round(floor[1])-32),special_flags=pygame.BLEND_RGB_ADD)

    def health(self,surface,name,portrait,bar,x,side,active=False,shield=False):
        color=COLORS[name]
        width=370
        polygon=[(x,18),(x+width-16,18),(x+width,34),(x+width,89),(x+16,89),(x,73)]
        pygame.draw.polygon(surface,INK,polygon)
        pygame.draw.lines(surface,color,False,[(x+2,35),(x+2,20),(x+width-18,20)],2)
        pygame.draw.polygon(surface,(29,42,57),[(x+11,29),(x+63,29),(x+63,78),(x+11,78)])
        surface.blit(portrait,(x+17,32))
        self.text(surface,name.upper(),(x+77,27),18)
        self.text(surface,side,(x+width-77,31),10,color)
        bx,by,bw=x+77,58,272
        bar.rect=pygame.Rect(bx,by,bw,12)
        pygame.draw.rect(surface,(35,44,56),bar.rect)
        ghost=round(bw*max(0,min(100,bar.display))/100)
        current=round(bw*max(0,min(100,bar.current))/100)
        pygame.draw.rect(surface,(226,170,112),(bx,by,ghost,12))
        pygame.draw.rect(surface,color if bar.current>25 else (244,78,88),(bx,by,current,12))
        pygame.draw.line(surface,WHITE,(bx,by),(bx+max(0,current-1),by),1)
        for j in range(1,10):pygame.draw.line(surface,INK,(bx+j*bw/10,by),(bx+j*bw/10,by+11),1)
        self.text(surface,f'{bar.current:03d} / 100',(bx,74),10,MUTED)
        if shield:self.text(surface,'REFLECT READY',(x+239,74),10,(240,115,155))
        elif active:self.text(surface,'ACTING',(x+300,74),10,color)

    def commands(self,surface,buttons,enabled,mouse,dt):
        pygame.draw.rect(surface,(8,14,24),(0,530,1024,110))
        pygame.draw.line(surface,(92,78,58),(24,530),(1000,530))
        descriptions=('DIRECT STRIKE','HAND SIGN TECHNIQUE','ULTIMATE TECHNIQUE','RESTORE HEALTH')
        colors=((113,177,226),(151,139,244),(244,177,88),(103,207,165))
        for i,button in enumerate(buttons):
            button.enabled=enabled;button.update(mouse,dt)
            x,y,w,h=button.rect
            color=colors[i]
            base=(30,42,57) if button.hovered else (16,26,40)
            pygame.draw.polygon(surface,base,[(x,y),(x+w-12,y),(x+w,y+12),(x+w,y+h),(x,y+h)])
            pygame.draw.line(surface,color if enabled else (69,82,96),(x,y),(x+w-14,y),2)
            pygame.draw.line(surface,color if enabled else (69,82,96),(x,y),(x,y+h),2)
            self.text(surface,f'0{i+1}',(x+12,y+12),12,color if enabled else MUTED)
            self.text(surface,button.text.strip(),(x+42,y+8),18,WHITE if enabled else (170,184,197))
            self.text(surface,descriptions[i],(x+42,y+36),10,MUTED)
        self.text(surface,'SHINOBI / TACTICS',(24,616),10,GOLD)

    def technique(self,surface,effect,label,reduced=False):
        if not effect or effect.action not in ('JUTSU','ULTIMATE'):return
        color=self.color(effect)
        if effect.age<effect.timing['release'] and effect.action=='ULTIMATE':
            # Brief ink cut-in below the HUD, stationary in reduced motion.
            q=min(1,effect.age/.13)
            x=30 if reduced else round(-440+470*q)
            pygame.draw.polygon(surface,INK,[(x,113),(x+425,113),(x+395,192),(x,192)])
            pygame.draw.line(surface,color,(x,113),(x+425,113),3)
            self.text(surface,'ULTIMATE  /  '+effect.character.upper(),(x+18,122),10,color)
            self.text(surface,label,(x+18,142),24)
        else:
            box=pygame.Rect(362,100,300,34)
            pygame.draw.polygon(surface,INK,[(box.left,box.top),(box.right,box.top),(box.right-12,box.bottom),(box.left+12,box.bottom)])
            self.text(surface,label,box.center,14,color,True)
