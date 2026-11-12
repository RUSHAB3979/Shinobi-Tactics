"""Deterministic move choreography with body, socket, environment and impact tracks."""
import math
from pathlib import Path
import pygame

PALETTES={'Sasuke':(110,190,255),'Tanjiro':(65,210,230),'Itachi':(235,65,100),'Zenitsu':(255,210,70)}
ACTOR_ROOTS={'left':(195,450),'right':(810,420)}
WHITE=(240,250,255)
def lerp(a,b,t):return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
def clamp(t):return max(0,min(1,t))
def ease(t):
    t=clamp(t)
    return t*t*(3-2*t)
def point(p):return (round(p[0]),round(p[1]))


def ribbon(surface,points,color,width):
    left=[];right=[]
    for i,p in enumerate(points):
        a,b=points[max(0,i-1)],points[min(len(points)-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1];length=max(1,math.hypot(dx,dy))
        w=width*math.sin(math.pi*(i+.5)/len(points))**.6
        left.append((p[0]-dy/length*w,p[1]+dx/length*w))
        right.append((p[0]+dy/length*w,p[1]-dx/length*w))
    if len(points)>1:pygame.draw.polygon(surface,color,left+right[::-1])


def bolt(surface,a,b,age,color,width=2,seed=0):
    pts=[];dx,dy=b[0]-a[0],b[1]-a[1];length=max(1,math.hypot(dx,dy))
    for i in range(13):
        q=i/12
        n=math.sin(i*13.37+seed*8+int(age*24)*2.7)*min(19,length*.08)*math.sin(q*math.pi)
        x,y=lerp(a,b,q);pts.append((x-dy/length*n,y+dx/length*n))
    pygame.draw.lines(surface,(*color,65),False,pts,width+7)
    pygame.draw.lines(surface,color,False,pts,width)
    pygame.draw.lines(surface,WHITE,False,pts,1)


def crescent(surface,center,radius,angle,color,width=13,span=2.4):
    points=[(center[0]+math.cos(angle-span/2+i*span/35)*radius,
             center[1]+math.sin(angle-span/2+i*span/35)*radius*.8) for i in range(36)]
    ribbon(surface,points,color,width)
    pygame.draw.lines(surface,WHITE,False,points,2)


class CombatEffect:
    _dragons=None
    def __init__(self,character,action,source,target,timing,*,miss=False,reflected=False,contact_target=None):
        self.character,self.action=character,action;self.source,self.target=source,target
        self.contact_target=contact_target or target;self.timing=timing
        self.miss,self.reflected=miss,reflected;self.age=0.;self.impact_age=None
        self.layer=pygame.Surface((1024,530),pygame.SRCALPHA)
        self.back_layer=pygame.Surface((1024,530),pygame.SRCALPHA)
        self.direction=1 if self.contact_target[0]>source[0] else -1
        self.reduced=False;self.hand=(source[0],source[1]-80);self.weapon=self.hand;self.body=source
        self.accent_times=[]
        if character=='Zenitsu' and action=='JUTSU':
            r,i=timing['release'],timing['impact'];self.accent_times=[r+(i-r)*k/6 for k in range(6)]
        if character=='Sasuke' and action=='ULTIMATE' and CombatEffect._dragons is None:
            root=Path(__file__).resolve().parent/'assets/vfx/kirin'
            images=[pygame.image.load(str(root/f'{i:02d}.png')).convert_alpha() for i in range(8)]
            CombatEffect._dragons=images+[pygame.transform.flip(image,True,False) for image in images]

    def update(self,dt):
        self.age+=dt
        if self.impact_age is not None:self.impact_age+=dt
    def impact(self):self.impact_age=0.
    @property
    def travel(self):return clamp((self.age-self.timing['release'])/(self.timing['impact']-self.timing['release']))
    @property
    def melee(self):
        return (self.action=='ATTACK' and self.character!='Itachi') or (
            self.action in ('JUTSU','ULTIMATE') and self.character in ('Tanjiro','Zenitsu')) or (
            self.character=='Sasuke' and self.action=='JUTSU')

    def movement(self,reduced=False,age=None):
        t=self.age if age is None else age
        if not self.melee:return self.source
        r,i,d=self.timing['release'],self.timing['impact'],self.timing['duration']
        if t<r or t>=d:return self.source
        contact=(self.contact_target[0]-self.direction*82,self.contact_target[1]-(60 if self.miss else 0))
        # Intentional contact-position cut at reduced motion, with no traversal.
        if reduced:
            if self.reflected and t>=i:return self.source
            return contact if t<d-.15 else self.source
        if t<i:
            q=clamp((t-r)/(i-r))
            if self.reflected:amount=ease(q/.58) if q<.58 else 1-ease((q-.58)/.42)
            elif self.character=='Zenitsu':amount=1-(1-q)**3
            else:amount=ease(q)
        else:
            if self.reflected:return self.source
            amount=1-ease((t-i-.09)/(d-i-.09))
        return lerp(self.source,contact,amount)

    def bind(self,actor,root,facing,reduced=False):
        self.body=root;self.reduced=reduced
        self.hand=actor.socket('hand',root,facing);self.weapon=actor.socket('weapon',root,facing)
    def trail_positions(self):
        if self.reduced or not self.melee or not self.timing['release']<self.age<self.timing['impact']:return []
        return [(self.movement(age=max(self.timing['release'],self.age-lag)),alpha)
                for lag,alpha in ((.11,30),(.075,50),(.035,80))]

    def draw_background(self,surface,intensity=1.):
        if self.age>self.timing['duration']+.3:return
        layer=self.back_layer;layer.fill((0,0,0,0));t=self.age;r=self.timing['release'];i=self.timing['impact']
        fade=ease(t/max(.1,r))*(1-ease((t-i-.18)/.45));tx,ty=self.target[0],self.target[1]-85
        if self.character=='Itachi' and self.action=='ULTIMATE':
            # Slow fade. No alternating flash; the HUD is drawn after this layer.
            layer.fill((34,2,15,round(145*fade*(.65 if self.reduced else 1))))
            moon=(512,132)
            pygame.draw.circle(layer,(100,16,36,round(225*fade)),moon,88)
            pygame.draw.circle(layer,(220,72,87,round(230*fade)),moon,79,2)
            for k in range(7):
                x=310+k*67
                pygame.draw.line(layer,(13,5,14,round(220*fade)),(x,245),(x,490),7)
                pygame.draw.line(layer,(13,5,14,round(220*fade)),(x-22,288),(x+22,288),5)
            for k in range(3):
                a=k*math.tau/3+.4;p=(moon[0]+math.cos(a)*42,moon[1]+math.sin(a)*42)
                pygame.draw.circle(layer,(22,4,15,round(255*fade)),point(p),13)
                pygame.draw.arc(layer,(22,4,15,round(255*fade)),(p[0]-22,p[1]-19,38,38),a,a+2.3,7)
            pygame.draw.circle(layer,(20,3,12,round(240*fade)),moon,20)
        elif self.character=='Sasuke' and self.action=='ULTIMATE':
            layer.fill((8,19,55,round(80*fade)))
            for k in range(9):
                x=tx-230+k*55
                pygame.draw.ellipse(layer,(22,36,76,round(180*fade)),(x,35+math.sin(k)*12,145,65))
                pygame.draw.arc(layer,(80,133,209,round(170*fade)),(x+10,45,110,44),.2,2.7,2)
            if r<t<i:
                for k in range(4):
                    a=(tx-150+k*92,68);bolt(layer,a,(a[0]+38,120),t,(90,170,255),1,k)
        elif self.character=='Itachi' and self.action=='JUTSU':
            pygame.draw.ellipse(layer,(135,35,90,round(80*fade)),(tx-78,ty-85,156,190),3)
        if self.action in ('JUTSU','ULTIMATE') and self.age < self.timing['impact']:
            charge = ease(self.age / self.timing['release'])
            col = PALETTES[self.character]
            if self.character == 'Tanjiro' and self.action == 'ULTIMATE': col = (255,155,55)
            # Energy gathers around the caster before the release. No full-screen flashes.
            sx, sy = self.source[0], self.source[1]-70
            if not self.reduced:
                for j in range(12):
                    a = j*2.399
                    q = (self.age*.85+j/12)%1
                    r = 25+(1-q)*85
                    p = (sx+math.cos(a)*r,sy+math.sin(a)*r*.7)
                    end = (sx+math.cos(a)*(r+12),sy+math.sin(a)*(r+12)*.7)
                    pygame.draw.line(layer,(*col,round(130*charge*q)),p,end,2)
            pygame.draw.ellipse(layer,(*col,round(100*charge)),
                (self.source[0]-48,self.source[1]-9,96,18),2)
        surface.blit(layer,(0,0))

    def _crow(self,surface,x,y,phase,scale=1):
        wing=math.sin(phase*(.35 if self.reduced else 1))*13
        pts=[(-3,0),(-23,-9-wing),(-17,5),(-6,5),(0,10),(7,4),(18,4),(25,-8-wing),(3,-2)]
        pygame.draw.polygon(surface,(15,12,29),[(x+a*scale,y+b*scale) for a,b in pts])
        pygame.draw.polygon(surface,(97,60,100),[(x-21*scale,y+(-8-wing)*scale),(x-4*scale,y),(x-15*scale,y+2*scale)])
        pygame.draw.circle(surface,(235,68,91),point((x+3*scale,y-scale)),max(1,round(scale)))
    def _eye(self,surface,center,radius,alpha=255):
        x,y=center
        pygame.draw.ellipse(surface,(130,20,49,alpha),(x-radius,y-radius*.43,radius*2,radius*.86))
        pygame.draw.ellipse(surface,(247,132,155,alpha),(x-radius,y-radius*.43,radius*2,radius*.86),2)
        pygame.draw.circle(surface,(24,5,16,alpha),point(center),round(radius*.31))
        for k in range(3):
            a=k*math.tau/3+self.age*.7
            pygame.draw.circle(surface,(24,5,16,alpha),point((x+math.cos(a)*radius*.54,y+math.sin(a)*radius*.26)),max(2,round(radius*.1)))

    def _chidori(self,surface):
        if self.age>self.timing['impact']+.18:return
        charge=ease(self.age/self.timing['release']);x,y=self.hand;radius=7+charge*9
        pygame.draw.circle(surface,(35,115,245,70),point((x,y)),round(radius+14))
        pygame.draw.circle(surface,(82,184,255),point((x,y)),round(radius))
        pygame.draw.circle(surface,WHITE,point((x,y)),round(radius*.55))
        for k in range(7 if not self.reduced else 4):
            a=k*math.tau/7+self.age*2;end=(x+math.cos(a)*(radius+22),y+math.sin(a)*(radius+22))
            bolt(surface,(x,y),end,self.age,(110,205,255),1,k)
        if self.age>self.timing['release'] and not self.reduced:
            for k in range(3):bolt(surface,(self.source[0],self.source[1]-35),(x-k*13*self.direction,y+k*9),self.age,(64,145,255),2,k)

    def _kirin(self,surface):
        r,i=self.timing['release'],self.timing['impact']
        if self.age<r:return
        tx,ty=self.target[0],self.target[1]-80-(75 if self.miss else 0)
        # Jaw, rather than image center, is the contact anchor.
        jaw=lerp((tx-self.direction*135,18),(tx,ty),ease(self.travel))
        if self.age<=i:frame=min(4,int(self.travel*5))
        elif self.impact_age is not None and self.impact_age<.30:frame=min(7,5+int(self.impact_age*10))
        else:return
        image=self._dragons[frame+(8 if self.direction<0 else 0)]
        anchor=(180 if self.direction>0 else 44,143)
        surface.blit(image,(round(jaw[0]-anchor[0]),round(jaw[1]-anchor[1])))
        bolt(surface,(tx-self.direction*110,80),jaw,self.age,(85,170,255),4)
        if self.impact_age is not None and not self.miss and self.impact_age<.28:
            for k in range(5):bolt(surface,(tx,ty),(tx+(k-2)*47,self.target[1]+4-abs(k-2)*10),self.age,(130,210,255),2,k)

    def _illusion(self,surface):
        r,i=self.timing['release'],self.timing['impact'];tx,ty=self.target[0],self.target[1]-100-(60 if self.miss else 0)
        if self.age<r:
            self._eye(surface,(self.hand[0],self.hand[1]-10),11+ease(self.age/r)*8);return
        if self.action=='JUTSU':
            for k in range(8 if not self.reduced else 4):
                q=clamp(self.travel*1.4-k*.055);p=lerp((self.source[0],self.source[1]-110),(tx,ty),ease(q))
                self._crow(surface,p[0]+math.sin(k*2.3+self.age*4)*40*q,p[1]+math.cos(k*1.7+self.age*4)*42,self.age*18+k,.6+k*.07)
            if self.age<i+.22:
                self._eye(surface,(tx,ty),24+20*self.travel)
                for k in range(3):
                    radius=60+k*10
                    pygame.draw.arc(surface,(160,49,120,130),(tx-radius,ty-radius,radius*2,radius*2),self.age+k,self.age+k+2,2)
        elif self.age<i+.32:
            self._eye(surface,(tx,ty),38+20*self.travel)
            for k in range(4):
                x=tx+(k-1.5)*30;pygame.draw.line(surface,(202,54,83,110),(x,ty-60),(x,ty+75),2)
            if not self.reduced:
                for k in range(12):
                    a=k*2.4;x=tx+math.cos(a)*100;y=ty+math.sin(a)*90
                    pygame.draw.polygon(surface,(150,38,73,160),[(x,y),(x+6,y-13),(x+13,y-16),(x+6,y+4)])

    def _water(self,surface):
        if self.age<self.timing['release'] or (self.impact_age is not None and self.impact_age>.32):return
        tx,ty=self.body[0]+self.direction*30,self.body[1]-65
        for turn in range(3):
            points=[]
            for k in range(48):
                a=k/47*math.tau*1.3+self.age*(3 if self.reduced else 9)+turn*2.1;radius=32+k*.95+turn*7
                points.append((tx+math.cos(a)*radius,ty+math.sin(a)*radius*.50-k*.35))
            ribbon(surface,points,(24,105+turn*30,178+turn*22,200),8-turn)
            pygame.draw.lines(surface,(175,245,255,230),False,points[-30:],2)
        for k in range(14):
            a=k*2.4+self.age*2;x=self.weapon[0]+math.cos(a)*(10+k*2);y=self.weapon[1]+math.sin(a)*(10+k*2)+k*1.1
            pygame.draw.ellipse(surface,(165,240,255,200),(x,y,3,6))

    def _flame(self,surface):
        if self.age<self.timing['release']:
            for k in range(6):
                q=(self.age*1.3+k/6)%1;x=self.hand[0]+math.sin(k*3)*22;y=self.hand[1]-q*45
                pygame.draw.circle(surface,(250,125,37,150),point((x,y)),2)
            return
        if self.impact_age is not None and self.impact_age>.35:return
        center=(self.body[0]+self.direction*35,self.body[1]-78);angle=-1.5+self.travel*3.4
        for j in range(3):
            points=[]
            for k in range(42):
                a=angle-self.direction*(k/41*3.5+j*.17);radius=70+j*9+math.sin(k*.8+self.age*18)*4
                points.append((center[0]+math.cos(a)*radius*self.direction,center[1]+math.sin(a)*radius*.85))
            ribbon(surface,points,((225,55,27),(255,137,37),(255,225,122))[j],13-j*3)
        crescent(surface,center,82,angle,(255,236,166),3,2.6)
        for k in range(18 if not self.reduced else 6):
            q=(self.age*1.5+k*.071)%1;x=self.weapon[0]-self.direction*q*85+math.sin(k*8)*20;y=self.weapon[1]-q*65+math.cos(k*4)*28
            pygame.draw.polygon(surface,(255,145+int(q*70),66,round((1-q)*230)),[(x,y),(x-3,y+8),(x+4,y+5)])

    def _thunder(self,surface):
        r,i=self.timing['release'],self.timing['impact'];yellow=(255,210,66)
        if self.age<r:
            q=ease(self.age/r)
            pygame.draw.ellipse(surface,(240,180,50,150),(self.source[0]-35-q*15,self.source[1]-6,70+q*30,12),2)
            for k in range(4):bolt(surface,self.hand,(self.hand[0]+math.sin(k*3)*30*q,self.hand[1]-20*q),self.age,yellow,1,k)
            return
        if self.age>i+.26:return
        start=(self.source[0],self.source[1]-60);end=(self.contact_target[0],self.contact_target[1]-75-(70 if self.miss else 0))
        if self.action=='JUTSU':
            for k,when in enumerate(self.accent_times):
                if not 0<=self.age-when<.12:continue
                center=lerp(start,end,(k+1)/6);center=(center[0],center[1]+(22 if k%2 else -22))
                crescent(surface,center,50,-1.1 if k%2 else .9,yellow,10,2.7)
                bolt(surface,lerp(start,end,k/6),center,self.age,yellow,2,k)
        else:
            head=lerp(start,end,min(1,self.travel*1.65))
            ribbon(surface,[lerp(start,head,k/20) for k in range(21)],(255,175,35,90),22)
            bolt(surface,start,head,self.age,yellow,4)
            if self.travel>.6:crescent(surface,end,90,-.8,(255,225,100),17,3.5)
            if not self.reduced:
                for k in range(7):pygame.draw.line(surface,(250,220,120,110),(start[0],start[1]+(k-3)*18),(head[0]-self.direction*25,head[1]+(k-3)*10),1)
        if self.reflected:
            bounce=(self.contact_target[0],self.contact_target[1]-75);dest=(self.target[0],self.target[1]-75)
            bolt(surface,bounce,lerp(bounce,dest,ease((self.travel-.58)/.42)),self.age,(225,115,185),2)

    def _basic(self,surface):
        r,i=self.timing['release'],self.timing['impact']
        if not r<=self.age<i+.17:return
        dest=(self.target[0],self.target[1]-75-(65 if self.miss else 0))
        if self.character=='Itachi':
            if self.age>i:return
            start=(self.source[0],self.source[1]-90);pos=lerp(start,dest,self.travel)
            if self.reflected:
                bounce=(self.contact_target[0],self.contact_target[1]-75)
                pos=lerp(start,bounce,self.travel/.58) if self.travel<.58 else lerp(bounce,dest,(self.travel-.58)/.42)
            d=self.direction
            pygame.draw.polygon(surface,(220,230,245),[(pos[0]+d*19,pos[1]),(pos[0]-d*8,pos[1]-6),(pos[0]-d*8,pos[1]+6)])
            pygame.draw.line(surface,(95,115,155),start,pos,2)
        else:crescent(surface,(self.body[0]+self.direction*40,self.body[1]-75-(55 if self.miss else 0)),63,-1.4+self.travel*2.5,PALETTES[self.character],8,2)

    def _impact(self,surface,intensity):
        if self.impact_age is None or self.miss or self.impact_age>.30:return
        k=self.impact_age;tx,ty=self.target[0],self.target[1]-75;col=PALETTES[self.character];fade=1-k/.30;radius=12+k*180
        if self.character=='Tanjiro' and self.action=='ULTIMATE':col=(255,160,55)
        pygame.draw.ellipse(surface,(*col,round(180*fade)),(tx-radius,ty-radius*.65,radius*2,radius*1.3),max(1,round(4*fade)))
        for j in range(12 if intensity>.5 else 6):
            a=j*2.4;reach=radius*(.9+(j%3)*.3);p=(tx+math.cos(a)*reach,ty+math.sin(a)*reach*.8)
            pygame.draw.line(surface,(*col,round(255*fade)),(tx+math.cos(a)*radius*.3,ty+math.sin(a)*radius*.3),p,2)
        if self.reflected:pygame.draw.circle(surface,(235,80,155),point((tx,ty)),round(radius),2)
        if k<.12:crescent(surface,(tx,ty),30+k*210,-.8,WHITE,8*fade,1.9)

    def draw(self,surface,intensity=1.):
        if self.age>self.timing['duration']+.3:return
        layer=self.layer;layer.fill((0,0,0,0))
        if self.action=='HEAL':
            if self.age<self.timing['release']:return
            for k in range(12):
                q=(self.age*.9+k/12)%1;x=self.source[0]+math.sin(k*2.4)*36;y=self.source[1]-q*130;color=(110,240,170,round((1-q)*230))
                pygame.draw.line(layer,color,(x-3,y),(x+3,y),2);pygame.draw.line(layer,color,(x,y-3),(x,y+3),2)
            pygame.draw.ellipse(layer,(90,225,170,190),(self.source[0]-42,self.source[1]-5,84,13),2)
        elif self.action=='ATTACK':self._basic(layer)
        elif self.character=='Sasuke':(self._chidori if self.action=='JUTSU' else self._kirin)(layer)
        elif self.character=='Itachi':self._illusion(layer)
        elif self.character=='Tanjiro':(self._water if self.action=='JUTSU' else self._flame)(layer)
        elif self.character=='Zenitsu':self._thunder(layer)
        if self.action!='HEAL':self._impact(layer,intensity)
        end=self.timing['duration'] if self.action=='HEAL' else self.timing['impact']+.27
        opacity=(1-ease((self.age-end)/.3))*(.65+.35*intensity)
        layer.set_alpha(round(255*opacity))
        surface.blit(layer,(0,0))
