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
    _sky_dragons=None
    def __init__(self,character,action,source,target,timing,*,miss=False,reflected=False,contact_target=None):
        self.character,self.action=character,action;self.source,self.target=source,target
        self.contact_target=contact_target or target;self.timing=timing
        self.miss,self.reflected=miss,reflected;self.age=0.;self.impact_age=None
        self.layer=pygame.Surface((1024,530),pygame.SRCALPHA)
        self.back_layer=pygame.Surface((1024,530),pygame.SRCALPHA)
        self.direction=1 if self.contact_target[0]>source[0] else -1
        self.reduced=False;self.hand=(source[0],source[1]-80);self.weapon=self.hand;self.head=(source[0],source[1]-135);self.body=source
        self.accent_times=[]
        if character=='Zenitsu' and action=='JUTSU':
            r,i=timing['release'],timing['impact'];self.accent_times=[r+(i-r)*(k+1)/6 for k in range(6)]
        if character=='Sasuke' and action=='ULTIMATE' and CombatEffect._dragons is None:
            root=Path(__file__).resolve().parent/'assets/vfx/kirin'
            images=[pygame.image.load(str(root/f'{i:02d}.png')).convert_alpha() for i in range(8)]
            CombatEffect._dragons=images+[pygame.transform.flip(image,True,False) for image in images]
            # Precompute the downward-facing sky dragon and its transformed jaw.
            CombatEffect._sky_dragons=[]
            for facing in (1,-1):
                for image in images:
                    oriented=pygame.transform.flip(image,True,False) if facing<0 else image
                    angle=-32*facing;size=1.05
                    art=pygame.transform.rotozoom(oriented,angle,size)
                    jaw=pygame.Vector2((180 if facing>0 else 44)-112,143-112).rotate(-angle)*size
                    anchor=(art.get_width()/2+jaw.x,art.get_height()/2+jaw.y)
                    CombatEffect._sky_dragons.append((art,anchor))

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
        if t>=d:return self.source
        if self.character=='Sasuke' and self.action=='JUTSU':
            contact=(self.contact_target[0]-self.direction*64,self.contact_target[1]-(60 if self.miss else 0))
            if t<r:return self.source
            if reduced:return self.source if self.reflected or t>=1.60 else contact
            if t<i:
                q=ease((t-r)/(i-r))
                if self.reflected:q=ease((t-r)/(i-r)/.65) if q<.65 else 1-ease((q-.65)/.35)
                return lerp(self.source,contact,q)
            if self.reflected or t>=1.60:return self.source
            return contact
        if t<r:
            if reduced or self.action == "ATTACK":return self.source
            # Weight shifts backward before the drive; sockets follow the body.
            coil=math.sin(math.pi*clamp(t/r))
            return (self.source[0]-self.direction*14*coil,self.source[1]+5*coil)
        contact=(self.contact_target[0]-self.direction*64,self.contact_target[1]-(60 if self.miss else 0))
        if self.character=='Zenitsu' and self.action in ('JUTSU','ULTIMATE'):
            if t<r:return self.source
            if t>=i:
                if self.reflected or t>=d-.20:return self.source
                return contact
            if reduced:return self.source
            q=clamp((t-r)/(i-r))
            if self.action=='ULTIMATE':
                # A single fast iaido burst, distinct from Sixfold direction changes.
                return lerp(self.source,contact,1-(1-q)**4)
            nodes=self.dash_nodes
            segment=min(5,int(q*6));local=q*6-segment
            return lerp(nodes[segment],nodes[segment+1],ease(local))
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
        position = lerp(self.source,contact,amount)
        if self.character == "Tanjiro" and r<t<i and not self.reflected:
            # Sword technique follows an airborne arc and lands at contact.
            lift=(22 if self.action == "JUTSU" else 38)*math.sin(math.pi*clamp((t-r)/(i-r)))
            return (position[0],position[1]-lift)
        return position

    def bind(self,actor,root,facing,reduced=False):
        self.body=root;self.reduced=reduced
        self.hand=actor.socket('hand',root,facing);self.weapon=actor.socket('weapon',root,facing)
        self.head=actor.socket('head',root,facing)
    @property
    def dash_nodes(self):
        end=(self.contact_target[0]-self.direction*64,self.contact_target[1]-(60 if self.miss else 0))
        nodes=[self.source]
        for q,lift in ((.24,-34),(.41,12),(.65,-42),(.54,17),(.84,-26),(1,0)):
            x,y=lerp(self.source,end,q);nodes.append((x,y+lift))
        return nodes

    @property
    def caster_opacity(self):
        if self.character=='Itachi' and self.action=='JUTSU' and self.timing['release']<self.age<self.timing['impact']:
            return round(255*(1-.78*math.sin(math.pi*self.travel)))
        return 255

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
            sky=ease(t/.65)*(1-ease((t-i-.10)/.65))
            layer.fill((5,12,35,round(135*sky)))
            for k in range(11):
                drift=0 if self.reduced else math.sin(t*.8+k)*12
                x=50+k*94+drift
                pygame.draw.ellipse(layer,(12,25,52,round(230*sky)),(x-80,90+(k%3)*20,205,100))
                pygame.draw.arc(layer,(77,107,151,round(150*sky)),(x-65,115+(k%3)*17,165,58),.1,3.0,2)
            if .35<t<r:
                for k in range(3 if self.reduced else 6):
                    start=(self.contact_target[0]-self.direction*70+(k-2)*38,140)
                    bolt(layer,start,(self.contact_target[0]-self.direction*60,205),t,(80,153,240),1,k)
        elif self.character=='Itachi' and self.action=='JUTSU':
            pygame.draw.ellipse(layer,(135,35,90,round(80*fade)),(tx-78,ty-85,156,190),3)
        if self.character=='Tanjiro' and self.action=='JUTSU':self._water(layer,back=True)
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
        r,i=self.timing['release'],self.timing['impact']
        if self.age<.18 or self.age>i+.20:return
        charge=ease((self.age-.18)/(r-.18));x,y=self.hand
        fade=1-ease((self.age-i)/.2)
        # Irregular fingertip discharge around a compact white palm core.
        for k in range(5 if self.reduced else 9):
            a=k*2.399+(0 if self.reduced else int(self.age*18)*.31)
            reach=(15+charge*23)*(1+(k%3)*.17)
            end=(x+math.cos(a)*reach,y+math.sin(a)*reach)
            elbow=lerp((x,y),end,.58)
            bolt(surface,(x,y),end,self.age,(77,174,255),2,k)
            branch=(end[0]+math.sin(a)*12,end[1]-math.cos(a)*12)
            bolt(surface,elbow,branch,self.age,(117,210,255),1,k+13)
        core=[(x+math.cos(k*math.tau/9)*(7+charge*5)*(1 if k%2 else .68),
               y+math.sin(k*math.tau/9)*(7+charge*5)) for k in range(9)]
        pygame.draw.polygon(surface,(225,249,255,round(255*fade)),core)
        if r<self.age<i and not self.reduced:
            # Only a short attached wake; this technique is not a ranged beam.
            for k in range(3):
                end=(x-self.direction*(18+k*11),y+10+k*6)
                bolt(surface,(x,y),end,self.age,(65,147,245),1,k)
            pygame.draw.line(surface,(128,198,242,110),(self.body[0]-self.direction*38,self.body[1]-6),
                             (self.body[0]-self.direction*80,self.body[1]-3),2)

    @property
    def kirin_jaw(self):
        q=self.travel
        sky=(self.contact_target[0]-self.direction*70,240)
        destination=(self.contact_target[0],self.contact_target[1]-80-(75 if self.miss else 0))
        return lerp(sky,destination,q*q)

    def _kirin(self,surface):
        t=self.age;r,i=self.timing['release'],self.timing['impact']
        form=self.timing.get('form',.55)
        if t<form or t>i+.38:return
        jaw=self.kirin_jaw
        if t<r:
            forming=ease((t-form)/.52)
            frame=min(3,int(forming*3.9))
            # Fully formed readable hold before the downward command.
            alpha=round(255*forming)
        elif t<i:
            frame=4;alpha=255
        else:
            frame=min(7,5+int((t-i)*9));alpha=round(255*(1-ease((t-i)/.38)))
        if t<r:
            image=self._dragons[frame+(8 if self.direction<0 else 0)]
            anchor=(180 if self.direction>0 else 44,143)
        else:
            image,anchor=self._sky_dragons[frame+(8 if self.direction<0 else 0)]
        image.set_alpha(alpha)
        surface.blit(image,(round(jaw[0]-anchor[0]),round(jaw[1]-anchor[1])))
        image.set_alpha(None)
        if r<t<i:
            bolt(surface,(jaw[0]-self.direction*35,145),jaw,t,(100,190,255),3)
        if self.impact_age is not None and not self.miss and not self.reflected and self.impact_age<.32:
            for k in range(5):
                bolt(surface,jaw,(self.target[0]+(k-2)*49,self.target[1]+3),t,(139,212,255),2,k)
        if self.reflected and self.travel>.70:
            a=(self.contact_target[0],self.contact_target[1]-85)
            b=(self.target[0],self.target[1]-85)
            self._eye(surface,a,30)
            bolt(surface,a,lerp(a,b,ease((self.travel-.70)/.30)),t,(216,83,143),2)

    def _illusion(self,surface):
        r,i=self.timing['release'],self.timing['impact'];tx,ty=self.target[0],self.target[1]-100-(60 if self.miss else 0)
        if self.age<r:
            self._eye(surface,self.head,4+ease(self.age/r)*4);return
        if self.action=='JUTSU':
            for k in range(8 if not self.reduced else 4):
                q=clamp(self.travel*1.4-k*.055);p=lerp((self.source[0],self.source[1]-110),(tx,ty),ease(q))
                self._crow(surface,p[0]+math.sin(k*2.3+self.age*4)*40*q,p[1]+math.cos(k*1.7+self.age*4)*42,self.age*18+k,.6+k*.07)
            if self.age<i+.22:
                pygame.draw.ellipse(surface,(160,49,120,160),(tx-38,ty-52,76,105),2)
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

    def _water(self,surface,back=False):
        if self.age<self.timing['release'] or (self.impact_age is not None and self.impact_age>.32):return
        tx,ty=self.hand
        angle=math.atan2(self.weapon[1]-ty,self.weapon[0]-tx)
        if not back:crescent(surface,(tx,ty),max(35,math.dist(self.hand,self.weapon)),angle,(69,190,224,190),11,2.4)
        for turn in ((0,1) if back else (2,)):
            points=[]
            for k in range(48):
                a=k/47*math.tau*1.3+self.age*(3 if self.reduced else 9)+turn*2.1;radius=32+k*.95+turn*7
                points.append((tx+math.cos(a)*radius,ty+math.sin(a)*radius*.50-k*.35))
            ribbon(surface,points,(24,105+turn*30,178+turn*22,200),8-turn)
            pygame.draw.lines(surface,(175,245,255,230),False,points[-30:],2)
        for k in range(0 if back else 14):
            a=k*2.4+self.age*2;x=self.weapon[0]+math.cos(a)*(10+k*2);y=self.weapon[1]+math.sin(a)*(10+k*2)+k*1.1
            pygame.draw.ellipse(surface,(165,240,255,200),(x,y,3,6))

    def _flame(self,surface):
        if self.age<self.timing['release']:
            for k in range(6):
                q=(self.age*1.3+k/6)%1;x=self.hand[0]+math.sin(k*3)*22;y=self.hand[1]-q*45
                pygame.draw.circle(surface,(250,125,37,150),point((x,y)),2)
            return
        if self.impact_age is not None and self.impact_age>.35:return
        center=self.hand;angle=math.atan2(self.weapon[1]-self.hand[1],self.weapon[0]-self.hand[0])
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
                if not 0<=self.age-when<.115:continue
                node=self.dash_nodes[k+1]
                center=(node[0],node[1]-75)
                # Each arc coincides with a real dash endpoint.
                crescent(surface,center,38,-1.1 if k%2 else .9,yellow,5 if self.reduced else 9,2.7)
                if not self.reduced:
                    prev=self.dash_nodes[k]
                    bolt(surface,(prev[0],prev[1]-75),center,self.age,yellow,2,k)
        else:
            head=(self.body[0]+self.direction*35,self.body[1]-85)
            if not self.reduced:
                ribbon(surface,[lerp(start,head,k/20) for k in range(21)],(255,175,35,90),18)
                bolt(surface,start,head,self.age,yellow,3)
            if self.travel>.65:crescent(surface,head,65,-.8,(255,225,100),10,2.5)
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
        if self.character=='Itachi':
            fade=1-self.impact_age/.30
            self._eye(surface,(self.target[0],self.target[1]-125),15+20*self.impact_age,round(180*fade))
            return
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
