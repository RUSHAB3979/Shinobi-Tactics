"""Short, deterministic character cut-ins before the attack animation begins.

Portrait keyframes are cached; eye aperture, iris and elemental motion are live.
No network state, damage or audio is owned by this renderer.
"""
import math
from pathlib import Path
import pygame

ROOT = Path(__file__).resolve().parent / "assets/cinematics"
COLORS = {"Sasuke": (91, 185, 255), "Itachi": (239, 65, 98),
          "Tanjiro": (70, 220, 210), "Zenitsu": (255, 208, 89)}


def smooth(q):
    q = max(0., min(1., q))
    return q*q*(3-2*q)


def intro_duration(action):
    return {"jutsu": 1.05, "ultimate": 1.45}.get(action.lower(), 0.)


class SpecialCinematic:
    def __init__(self):
        self.portraits = {}
        self.eye_details = {}
        self.panel = pygame.Surface((1024, 420)).convert()
        self.fx = pygame.Surface((1024, 420), pygame.SRCALPHA)
        font = Path(__file__).resolve().parent / "assets/fonts/SpaceGrotesk-Bold.otf"
        self.font = pygame.font.Font(str(font), 30)
        self.small = pygame.font.Font(str(font), 13)
        self.reset()

    def reset(self):
        self.age = self.duration = 0.
        self.character = None

    def start(self, character, action, label, direction):
        self.character, self.action = character, action
        self.duration = intro_duration(action)
        self.age = 0.
        self.direction = direction
        color = COLORS[character]
        self.title = self.font.render(label.upper(), True, (248, 243, 230))
        self.subtitle = self.small.render(character.upper()+"  /  "+("SECRET TECHNIQUE" if action == "ULTIMATE" else "SPECIAL TECHNIQUE"), True, color)
        if self.duration and character not in self.portraits:
            image = pygame.image.load(str(ROOT / (character.lower()+".png"))).convert()
            # Fixed-size cache; cropping at draw time gives a camera push without
            # allocating or rescaling a full image on every frame.
            self.portraits[character] = pygame.transform.smoothscale(image, (1152, 768))
            if character in ("Sasuke", "Itachi"):
                center = (1036, 451) if character == "Sasuke" else (973, 416)
                crop = pygame.Rect(center[0]-200, center[1]-80, 400,160)
                self.eye_details[character] = pygame.transform.smoothscale(image.subsurface(crop),(900,360))

    @property
    def active(self):
        return self.character is not None and self.age < self.duration

    def consume(self, dt):
        """Advance intro only, returning time available to the battle actors."""
        used = min(dt, max(0., self.duration-self.age))
        self.age += used
        return dt-used

    def draw_eye(self, progress, reduced):
        # Use the painted eye itself, magnified as a second camera shot. A
        # shutter reveal avoids a low-detail geometric eye over detailed art.
        detail = self.eye_details[self.character]
        opened = 1. if reduced else smooth(progress/.4)
        half = max(1, round(156*opened))
        area = pygame.Rect(0,180-half,900,half*2)
        # A full matte makes this a clean shot change rather than a floating eye.
        self.panel.fill((7,5,14))
        self.panel.blit(detail,(62,12+area.y),area)
        if opened > .85:
            self.fx.fill((0,0,0,0))
            angle = 0 if reduced else progress*2
            alpha = round(130*smooth((opened-.85)/.15))
            pygame.draw.arc(self.fx,(255,62,78,alpha),(414,94,196,196),angle,angle+2.2,2)
            pygame.draw.arc(self.fx,(255,132,140,alpha),(407,87,210,210),angle+3,angle+4.7,1)
            self.panel.blit(self.fx,(0,0));self.fx.fill((0,0,0,0))

    def draw(self, surface, reduced=False):
        if not self.active:return
        q = self.age/self.duration
        color = COLORS[self.character]
        if self.character == "Tanjiro" and self.action == "ULTIMATE":color=(255,151,61)
        panel = self.panel
        panel.fill((5,9,19))
        portrait = self.portraits[self.character]
        # Calm portrait in accessibility mode, directional camera drift otherwise.
        drift = 0 if reduced else round(28*smooth(q)*self.direction)
        panel.blit(portrait,(-64+drift,-150+(0 if reduced else round(12*smooth(q)))))
        self.fx.fill((0,0,0,0))
        # A dark lower matte keeps long move names readable over detailed art.
        for y in range(290,420):
            pygame.draw.line(self.fx,(3,7,15,round(230*(y-290)/129)),(0,y),(1024,y))
        if self.character in ("Sasuke","Itachi") and .29 < q < .79:
            self.fx.fill((8,3,15,195))
            panel.blit(self.fx,(0,0));self.fx.fill((0,0,0,0))
            self.draw_eye((q-.29)/.5,reduced)
        if not reduced:
            for k in range(16):
                x = (k*79+q*320*self.direction)%1100-40
                y = 30+(k*43)%260
                if 180 < x < 844:continue
                if self.character == "Itachi":
                    pygame.draw.polygon(self.fx,(*color,100),[(x,y),(x-20,y-8),(x-6,y+4),(x-28,y+11)])
                elif self.character == "Tanjiro":
                    pygame.draw.arc(self.fx,(*color,140),(x-60,y,120,32),.1,2.8,2)
                else:
                    pygame.draw.lines(self.fx,(*color,150),False,[(x,y),(x+26,y-8),(x+16,y+7),(x+52,y-1)],2)
        panel.blit(self.fx,(0,0))
        panel.blit(self.subtitle,(38,338))
        panel.blit(self.title,(38,360))
        pygame.draw.line(panel,color,(28,326),(230,326),3)
        pygame.draw.line(panel,color,(0,0),(1024,0),2)
        pygame.draw.line(panel,color,(0,419),(1024,419),2)
        if reduced:
            panel.set_alpha(round(255*min(smooth(q/.12),smooth((1-q)/.15))))
            surface.blit(panel,(0,104));panel.set_alpha(None)
        else:
            # Opening shutter and final directional wipe; HUD stays outside.
            reveal = min(smooth(q/.12),smooth((1-q)/.15))
            h=max(1,round(420*reveal))
            crop=pygame.Rect(0,(420-h)//2,1024,h)
            x=round(self.direction*1024*smooth((q-.85)/.15))
            surface.blit(panel,(x,104+crop.y),crop)
