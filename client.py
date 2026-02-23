"""
client.py  –  Shinobi Tactics Game Client
Pokemon-style battle UI with video cutscenes.
Run:  python client.py
"""

import os
import sys
import math
import time
import socket
import struct
import pickle
import threading
import random

import pygame

# ── Optional video deps (degrade gracefully) ──────────────────────
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from ffpyplayer.player import MediaPlayer
    HAS_FFPY = True
except ImportError:
    HAS_FFPY = False

# ── Hand-sign jutsu modules ────────────────────────────────────────
try:
    from hand_sign_config import HAND_SIGN_SEQUENCES, TIME_PER_SIGN
    from hand_sign_ui import run_hand_sign_challenge
    HAS_HAND_SIGNS = True
except ImportError:
    HAS_HAND_SIGNS = False

# ── Paths ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS   = os.path.join(BASE_DIR, "assets")
VIDEOS   = os.path.join(ASSETS, "videos")
AUDIO    = os.path.join(ASSETS, "audio")

# ── Constants ──────────────────────────────────────────────────────
WIDTH, HEIGHT = 1024, 640
FPS = 60

# Colours
C_BG          = (15, 15, 25)
C_PANEL       = (25, 25, 40)
C_PANEL_EDGE  = (60, 60, 90)
C_WHITE       = (240, 240, 240)
C_GREY        = (120, 120, 140)
C_DARK        = (30, 30, 45)
C_RED         = (220, 50, 50)
C_GREEN       = (50, 200, 80)
C_YELLOW      = (230, 200, 50)
C_CYAN        = (0, 220, 240)

# Character data
# anim_map maps game actions → sprite folder names
CHARACTERS = {
    "Sasuke": {
        "color": (130, 80, 200), "accent": (180, 120, 255),
        "sprite_folder": "sasuke", "ultimate_video": "chidori.mp4",
        "anim_map": {
            "idle": "idle", "attack": "attack_1", "jutsu": "chidori_new",
            "ultimate": "kirin", "hit": "hit", "down": "down",
            "guard": "guard", "heal": "healing", "run": "run",
            "walk": "walk", "victory": "victory",
        },
        "move_names": ["KATANA", "CHIDORI", "KIRIN", "RECOVER"],
        "sfx": {
            "JUTSU":    "sasuke/chidori-1.mp3",
            "ULTIMATE": "sasuke/kirin.mp3",
        },
    },
    "Tanjiro": {
        "color": (30, 160, 100), "accent": (50, 220, 140),
        "sprite_folder": "tanjiro", "ultimate_video": "sun_breathing.mp4",
        "anim_map": {
            "idle": "idle", "attack": "attack_1", "jutsu": "special_1",
            "ultimate": "ultimate", "hit": "hit", "down": "down",
            "guard": "guard", "heal": "idle", "run": "run",
            "victory": "victory",
        },
        "move_names": ["SLASH", "WHIRLPOOL", "SUN BREATH", "RECOVER"],
    },
    "Itachi": {
        "color": (180, 40, 40), "accent": (240, 80, 80),
        "sprite_folder": "itachi", "ultimate_video": "tsukuyomi.mp4",
        "anim_map": {
            "idle": "idle", "attack": "kunai", "jutsu": "genjutsu",
            "ultimate": "tsukuyomi", "hit": "hit", "down": "down",
            "guard": "guard", "heal": "idle", "run": "run",
            "walk": "walk", "victory": "victory",
        },
        "move_names": ["KUNAI", "GENJUTSU", "TSUKUYOMI", "RECOVER"],
        "sfx": {
            "JUTSU":    "itachi/itachi-mangekyou-sharingan-sound-effect.mp3",
            "ULTIMATE": "itachi/itachi_tsukuyomi.mp3",
        },
    },
    "Zenitsu": {
        "color": (200, 180, 30), "accent": (255, 230, 60),
        "sprite_folder": "zenitsu", "ultimate_video": "thunderclap.mp4",
        "anim_map": {
            "idle": "idle_new", "attack": "attack_1", "jutsu": "sixfold",
            "ultimate": "godspeed", "hit": "hit", "down": "down",
            "guard": "guard", "heal": "healing", "run": "run",
            "dash": "dash", "victory": "victory",
        },
        "move_names": ["SLASH", "SIXFOLD", "GODSPEED", "RECOVER"],
    },
}

DAMAGE = {"ATTACK": 15, "JUTSU": 25, "ULTIMATE": 50}
HEAL_AMOUNT = 20
ANIM_FPS = 8       # Frames per second for sprite animation
ATTACK_ANIM_FPS = 20  # Faster FPS for attack/jutsu/ultimate (many frames)
MAX_IDLE_FRAMES = 12  # Cap idle animation to first N frames
MAX_ATTACK_FRAMES = 30  # Cap attack/jutsu/ultimate to first N frames
MAX_HEAL_FRAMES = 20   # Cap healing animation frames



class Network:
    def __init__(self, server_ip: str, port: int = 5555):
        self.server_ip = server_ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.player_id = None
        self._recv_buffer = b""

    def connect(self) -> bool:
        try:
            self.sock.settimeout(5)
            self.sock.connect((self.server_ip, self.port))
            self.sock.settimeout(None)
            self.sock.setblocking(False)
            self.connected = True

            # First message is our player assignment (blocking read)
            self.sock.setblocking(True)
            self.sock.settimeout(5)
            assign = self._recv_blocking()
            self.sock.setblocking(False)
            if assign and assign.get("type") == "ASSIGN":
                self.player_id = assign["player_id"]
            return True
        except Exception as e:
            print(f"[NET] Connect failed: {e}")
            return False

    def send(self, obj):
        if not self.connected:
            return
        data = pickle.dumps(obj)
        length = struct.pack("!I", len(data))
        try:
            self.sock.sendall(length + data)
        except Exception:
            self.connected = False

    def poll(self) -> list:
        """Non-blocking poll for messages. Returns list of dicts."""
        msgs = []
        if not self.connected:
            return msgs
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    self.connected = False
                    return msgs
                self._recv_buffer += chunk
        except BlockingIOError:
            pass
        except Exception:
            self.connected = False
            return msgs

        # Parse all complete messages out of the buffer
        while len(self._recv_buffer) >= 4:
            msg_len = struct.unpack("!I", self._recv_buffer[:4])[0]
            if len(self._recv_buffer) < 4 + msg_len:
                break
            raw = self._recv_buffer[4:4 + msg_len]
            self._recv_buffer = self._recv_buffer[4 + msg_len:]
            try:
                msgs.append(pickle.loads(raw))
            except Exception:
                pass
        return msgs

    def _recv_blocking(self):
        raw_len = self._recv_n(4)
        if raw_len is None:
            return None
        msg_len = struct.unpack("!I", raw_len)[0]
        raw = self._recv_n(msg_len)
        if raw is None:
            return None
        return pickle.loads(raw)

    def _recv_n(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                return None
            buf += chunk
        return buf

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass
        self.connected = False



class Button:
    def __init__(self, x, y, w, h, text, color, text_color=C_WHITE, font_size=22):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.base_color = color
        self.hover_color = tuple(min(255, c + 40) for c in color)
        self.text_color = text_color
        self.font = pygame.font.SysFont("Segoe UI", font_size, bold=True)
        self.hovered = False
        self.enabled = True
        self._anim_t = 0

    def update(self, mouse_pos, dt):
        self.hovered = self.rect.collidepoint(mouse_pos) and self.enabled
        self._anim_t += dt

    def draw(self, surf):
        col = self.hover_color if self.hovered else self.base_color
        if not self.enabled:
            col = C_GREY

        # Shadow
        shadow = self.rect.inflate(0, 0).move(3, 3)
        pygame.draw.rect(surf, (0, 0, 0, 80), shadow, border_radius=10)

        # Main button
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        # Border glow on hover
        if self.hovered:
            pygame.draw.rect(surf, (255, 255, 255, 60), self.rect, width=2, border_radius=10)

        # Text
        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surf.blit(txt_surf, txt_rect)

    def clicked(self, event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


class HPBar:
    def __init__(self, x, y, w, h, max_hp=100):
        self.rect = pygame.Rect(x, y, w, h)
        self.max_hp = max_hp
        self.current = max_hp
        self.display = float(max_hp)

    def update(self, real_hp, dt):
        self.current = real_hp
        # Smooth lerp
        speed = 120 * dt
        if self.display > self.current:
            self.display = max(self.current, self.display - speed)
        elif self.display < self.current:
            self.display = min(self.current, self.display + speed)

    def draw(self, surf):
        # Background
        pygame.draw.rect(surf, C_DARK, self.rect, border_radius=6)

        ratio = max(0, self.display / self.max_hp)
        fill_w = int(self.rect.w * ratio)
        if fill_w > 0:
            # Color gradient: green → yellow → red
            if ratio > 0.5:
                t = (ratio - 0.5) * 2
                col = (int(230 * (1 - t) + 50 * t), int(200 * (1 - t) + 200 * t), 50)
            else:
                t = ratio * 2
                col = (220, int(50 + 150 * t), 50)

            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.h)
            pygame.draw.rect(surf, col, fill_rect, border_radius=6)

        # Border
        pygame.draw.rect(surf, C_PANEL_EDGE, self.rect, width=2, border_radius=6)

        # HP text
        font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        txt = font.render(f"{self.current}/{self.max_hp}", True, C_WHITE)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.vx = random.uniform(-120, 120)
        self.vy = random.uniform(-180, -40)
        self.life = random.uniform(0.3, 0.8)
        self.age = 0.0
        self.color = color
        self.size = random.randint(3, 7)

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt  # gravity

    def draw(self, surf):
        alpha = max(0, 1 - self.age / self.life)
        r = max(1, int(self.size * alpha))
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)

    @property
    def alive(self):
        return self.age < self.life


class AnimatedSprite:
    """Manages multi-frame sprite animations for a character."""

    def __init__(self, char_name, char_data):
        self.char_name = char_name
        self.animations = {}     # {anim_name: [Surface, ...]}
        self.anim_map = char_data.get("anim_map", {})
        self.current_anim = "idle"
        self.frame_index = 0
        self.frame_timer = 0.0
        self.looping = True
        self.on_finish_anim = "idle"  # What to return to after one-shot
        self._load_all(char_data.get("sprite_folder", char_name.lower()))

    def _load_all(self, folder):
        """Load all animation frames from assets/<folder>/<anim>/"""
        base = os.path.join(ASSETS, folder)
        if not os.path.isdir(base):
            return
        for anim_dir in os.listdir(base):
            anim_path = os.path.join(base, anim_dir)
            if not os.path.isdir(anim_path):
                continue
            frames = []
            for fname in sorted(os.listdir(anim_path)):
                if fname.endswith(".png"):
                    img = pygame.image.load(os.path.join(anim_path, fname)).convert_alpha()
                    frames.append(img)
            if frames:
                # Cap frame counts to prevent absurdly long animations
                if "idle" in anim_dir:
                    frames = frames[:MAX_IDLE_FRAMES]
                elif "healing" in anim_dir or "heal" in anim_dir:
                    frames = frames[:MAX_HEAL_FRAMES]
                elif anim_dir in ("hit", "down", "guard", "run", "walk",
                                  "jump", "crouch", "dash", "fall", "dodge"):
                    pass  # Keep original count for basic anims
                else:
                    # Attack/jutsu/special/ultimate - cap to keep snappy
                    frames = frames[:MAX_ATTACK_FRAMES]
                self.animations[anim_dir] = frames

    def play(self, action_name, loop=False, on_finish="idle"):
        """Switch to an animation. Maps game action → sprite folder name."""
        anim_folder = self.anim_map.get(action_name, action_name)
        if anim_folder not in self.animations:
            # Try direct name
            if action_name in self.animations:
                anim_folder = action_name
            else:
                return  # Animation not found, keep current
        if self.current_anim == anim_folder and loop:
            return  # Already playing
        self.current_anim = anim_folder
        self.frame_index = 0
        self.frame_timer = 0.0
        self.looping = loop
        self.on_finish_anim = self.anim_map.get(on_finish, on_finish)

    def _get_anim_fps(self):
        """Return appropriate FPS for the current animation type."""
        a = self.current_anim
        if "idle" in a or a in ("walk", "run", "guard", "crouch"):
            return ANIM_FPS  # Normal speed for looping anims
        elif a in ("hit", "down", "fall"):
            return ANIM_FPS  # Normal speed for reaction anims
        elif "healing" in a or "heal" in a:
            return ANIM_FPS + 4  # Slightly faster
        else:
            # Attack / jutsu / ultimate / specials → play faster
            return ATTACK_ANIM_FPS

    def update(self, dt):
        """Advance animation frame."""
        self.frame_timer += dt
        current_fps = self._get_anim_fps()
        spf = 1.0 / current_fps
        if self.frame_timer >= spf:
            self.frame_timer -= spf
            frames = self.animations.get(self.current_anim, [])
            if not frames:
                return
            self.frame_index += 1
            if self.frame_index >= len(frames):
                if self.looping:
                    self.frame_index = 0
                else:
                    # One-shot finished → return to idle
                    self.frame_index = 0
                    self.current_anim = self.on_finish_anim
                    self.looping = True

    def get_frame(self) -> pygame.Surface:
        """Get the current animation frame surface."""
        frames = self.animations.get(self.current_anim, [])
        if not frames:
            # Fallback: try idle
            frames = self.animations.get(self.anim_map.get("idle", "idle"), [])
        if not frames:
            # Last resort: colored rect
            s = pygame.Surface((120, 160), pygame.SRCALPHA)
            pygame.draw.rect(s, C_GREY, (0, 0, 120, 160), border_radius=12)
            return s
        idx = min(self.frame_index, len(frames) - 1)
        return frames[idx]

    @property
    def has_anims(self):
        return len(self.animations) > 0


class TextInput:
    """Minimal text input box."""
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.font = pygame.font.SysFont("Segoe UI", 22)
        self.cursor_blink = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return "SUBMIT"
            elif event.unicode.isprintable() and len(self.text) < 40:
                self.text += event.unicode
        return None

    def draw(self, surf, dt):
        self.cursor_blink += dt
        col = C_CYAN if self.active else C_PANEL_EDGE
        pygame.draw.rect(surf, C_DARK, self.rect, border_radius=8)
        pygame.draw.rect(surf, col, self.rect, width=2, border_radius=8)

        display_text = self.text if self.text else self.placeholder
        color = C_WHITE if self.text else C_GREY
        txt = self.font.render(display_text, True, color)
        surf.blit(txt, (self.rect.x + 12, self.rect.y + (self.rect.h - txt.get_height()) // 2))

        if self.active and int(self.cursor_blink * 2) % 2 == 0:
            cx = self.rect.x + 14 + self.font.size(self.text)[0]
            pygame.draw.line(surf, C_WHITE, (cx, self.rect.y + 8), (cx, self.rect.y + self.rect.h - 8), 2)



def play_cutscene(screen: pygame.Surface, video_filename: str):
    """
    Play an .mp4 cutscene full-screen, then return.
    Falls back to a cinematic flash if dependencies / file missing.
    Press ESC to skip.
    """
    video_path = os.path.join(VIDEOS, video_filename)

    if not os.path.isfile(video_path) or not HAS_CV2:
        _play_flash_effect(screen)
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        _play_flash_effect(screen)
        return

    fps_vid = cap.get(cv2.CAP_PROP_FPS) or 30
    scr_w, scr_h = screen.get_size()
    clock = pygame.time.Clock()

    # Audio via ffpyplayer
    player = None
    if HAS_FFPY:
        try:
            player = MediaPlayer(video_path)
        except Exception:
            player = None

    running = True
    while running:
        ret, frame = cap.read()
        if not ret:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                if player:
                    player.close_player()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break

        if not running:
            break

        # ── Render the frame to the Pygame screen ─────────────────
        # Convert BGR → RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Scale to fill the screen (maintain aspect ratio, letterbox)
        fh, fw = frame_rgb.shape[:2]
        scale = min(scr_w / fw, scr_h / fh)
        new_w, new_h = int(fw * scale), int(fh * scale)
        frame_resized = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Create Pygame surface and blit centered
        surf = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
        screen.fill((0, 0, 0))
        x_off = (scr_w - new_w) // 2
        y_off = (scr_h - new_h) // 2
        screen.blit(surf, (x_off, y_off))

        pygame.display.flip()

        # Drain audio frames to keep audio in sync
        if player:
            player.get_frame()

        clock.tick(fps_vid)

    cap.release()
    if player:
        player.close_player()


def _play_flash_effect(screen: pygame.Surface):
    """No-op — flash removed so sprite animations stay visible."""
    pass


# ═══════════════════════════════════════════════════════════════════
#  KIRIN LIGHTNING DRAGON EFFECT
# ═══════════════════════════════════════════════════════════════════

class KirinBolt:
    """Single lightning bolt segment for the Kirin dragon."""
    def __init__(self, x, y_start, y_end):
        self.x = x
        self.y_start = y_start
        self.y_end = y_end
        self.segments = []  # list of (x, y) points
        self._generate()
        self.life = random.uniform(0.08, 0.18)
        self.age = 0.0
        self.color = random.choice([
            (100, 180, 255), (150, 200, 255), (200, 230, 255),
            (80, 140, 255), (255, 255, 255),
        ])
        self.width = random.randint(1, 3)

    def _generate(self):
        """Generate jagged lightning path."""
        self.segments = [(self.x, self.y_start)]
        y = self.y_start
        step = 12
        while y < self.y_end:
            y += step
            x_offset = random.randint(-25, 25)
            self.segments.append((self.x + x_offset, min(y, self.y_end)))

    def update(self, dt):
        self.age += dt

    def draw(self, surf):
        if len(self.segments) < 2:
            return
        alpha = max(0.0, 1.0 - self.age / self.life)
        col = tuple(int(c * alpha) for c in self.color)
        for i in range(len(self.segments) - 1):
            pygame.draw.line(surf, col, self.segments[i], self.segments[i + 1], self.width)
        # Glow at the tip
        tip = self.segments[-1]
        glow_r = int(8 * alpha)
        if glow_r > 0:
            glow_surf = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*col, int(80 * alpha)),
                               (glow_r * 2, glow_r * 2), glow_r * 2)
            surf.blit(glow_surf, (tip[0] - glow_r * 2, tip[1] - glow_r * 2))

    @property
    def alive(self):
        return self.age < self.life


class KirinDragonEffect:
    """
    Animated Kirin lightning dragon that strikes down onto a target.
    Draws a dragon silhouette made of lightning descending from the sky.
    """
    def __init__(self, target_x, target_y, duration=2.0):
        self.target_x = target_x
        self.target_y = target_y
        self.duration = duration
        self.age = 0.0
        self.bolts = []
        self.bolt_timer = 0.0
        self.phase = "charge"  # charge → strike → impact → fade
        self.strike_y = -100   # dragon head Y position (descends)
        self.impact_particles = []
        self.flash_alpha = 0

    def update(self, dt):
        self.age += dt
        self.bolt_timer += dt

        # Phase transitions
        if self.age < 0.4:
            self.phase = "charge"
        elif self.age < 1.0:
            self.phase = "strike"
        elif self.age < 1.6:
            self.phase = "impact"
        else:
            self.phase = "fade"

        # ── Charge: lightning gathers at top ──
        if self.phase == "charge":
            if self.bolt_timer > 0.03:
                self.bolt_timer = 0.0
                bx = self.target_x + random.randint(-120, 120)
                self.bolts.append(KirinBolt(bx, -20, random.randint(30, 100)))
            self.flash_alpha = int(60 * abs(math.sin(self.age * 15)))

        # ── Strike: dragon descends ──
        elif self.phase == "strike":
            progress = (self.age - 0.4) / 0.6
            self.strike_y = -100 + (self.target_y + 100) * min(progress, 1.0)

            # Main dragon lightning bolts
            if self.bolt_timer > 0.02:
                self.bolt_timer = 0.0
                # Central thick bolt
                bx = self.target_x + random.randint(-15, 15)
                self.bolts.append(KirinBolt(bx, -30, int(self.strike_y)))
                # Side bolts for dragon "wings"
                for offset in [-60, -40, 40, 60]:
                    if random.random() > 0.5:
                        wing_x = self.target_x + offset + random.randint(-10, 10)
                        y_top = max(-20, self.strike_y - random.randint(80, 160))
                        self.bolts.append(KirinBolt(wing_x, y_top, int(self.strike_y)))

            self.flash_alpha = int(100 * abs(math.sin(self.age * 20)))

        # ── Impact: explosion at target ──
        elif self.phase == "impact":
            if self.bolt_timer > 0.02:
                self.bolt_timer = 0.0
                # Bolts radiating from impact point
                for _ in range(3):
                    bx = self.target_x + random.randint(-50, 50)
                    by_end = self.target_y + random.randint(-60, 80)
                    self.bolts.append(KirinBolt(bx, self.target_y - 20, by_end))
                # Impact particles
                for _ in range(2):
                    self.impact_particles.append({
                        "x": float(self.target_x + random.randint(-30, 30)),
                        "y": float(self.target_y + random.randint(-20, 20)),
                        "vx": random.uniform(-200, 200),
                        "vy": random.uniform(-300, -50),
                        "life": random.uniform(0.3, 0.7),
                        "age": 0.0,
                        "size": random.randint(3, 8),
                        "color": random.choice([
                            (100, 180, 255), (200, 230, 255), (255, 255, 200),
                        ]),
                    })

            impact_progress = (self.age - 1.0) / 0.6
            self.flash_alpha = int(150 * max(0, 1 - impact_progress))

        # ── Fade ──
        else:
            self.flash_alpha = int(30 * max(0, 1 - (self.age - 1.6) / 0.4))

        # Update bolts
        alive_bolts = []
        for b in self.bolts:
            b.update(dt)
            if b.alive:
                alive_bolts.append(b)
        self.bolts = alive_bolts

        # Update impact particles
        alive_parts = []
        for p in self.impact_particles:
            p["age"] += dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 400 * dt
            if p["age"] < p["life"]:
                alive_parts.append(p)
        self.impact_particles = alive_parts

    def draw(self, surf):
        # Flash overlay (blue-white)
        if self.flash_alpha > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((100, 150, 255, min(self.flash_alpha, 200)))
            surf.blit(overlay, (0, 0))

        # Draw dragon head during strike (simple beast shape via circles + lines)
        if self.phase == "strike" and self.strike_y > 0:
            # Dragon head glow
            head_y = int(self.strike_y)
            glow_size = 40
            glow = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (80, 160, 255, 120), (glow_size, glow_size), glow_size)
            surf.blit(glow, (self.target_x - glow_size, head_y - glow_size))

            # Eyes (red dots)
            for ex in [-8, 8]:
                pygame.draw.circle(surf, (255, 50, 50),
                                   (self.target_x + ex, head_y - 5), 3)

            # Mouth / jaw lines
            pygame.draw.line(surf, (150, 200, 255),
                             (self.target_x - 20, head_y + 5),
                             (self.target_x, head_y + 15), 2)
            pygame.draw.line(surf, (150, 200, 255),
                             (self.target_x + 20, head_y + 5),
                             (self.target_x, head_y + 15), 2)

        # Impact ring
        if self.phase == "impact":
            impact_progress = (self.age - 1.0) / 0.6
            ring_r = int(20 + 80 * impact_progress)
            ring_alpha = int(200 * max(0, 1 - impact_progress))
            ring_surf = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (100, 180, 255, ring_alpha),
                               (ring_r + 2, ring_r + 2), ring_r, 3)
            surf.blit(ring_surf,
                      (self.target_x - ring_r - 2, self.target_y - ring_r - 2))

        # Lightning bolts
        for b in self.bolts:
            b.draw(surf)

        # Impact particles
        for p in self.impact_particles:
            alpha = max(0.0, 1.0 - p["age"] / p["life"])
            r = max(1, int(p["size"] * alpha))
            col = tuple(int(c * alpha) for c in p["color"])
            pygame.draw.circle(surf, col, (int(p["x"]), int(p["y"])), r)

        # "KIRIN" text during strike/impact
        if self.phase in ("strike", "impact"):
            font = pygame.font.SysFont("Segoe UI", 42, bold=True)
            text_alpha = 255 if self.phase == "strike" else int(255 * max(0, 1 - (self.age - 1.0) / 0.6))
            txt = font.render("⚡ K I R I N ⚡", True, (100, 200, 255))
            txt.set_alpha(text_alpha)
            surf.blit(txt, txt.get_rect(center=(WIDTH // 2, 40)))

    @property
    def alive(self):
        return self.age < self.duration



def play_genjutsu_anim(screen: pygame.Surface, is_vs_sasuke: bool):
    """
    Itachi's Genjutsu JUTSU animation.
    1) Dodge sidestep  2) Red genjutsu overlay
    If vs Sasuke, plays tsukuyomi.mp4 video afterwards.
    """
    clock = pygame.time.Clock()
    bg_snapshot = screen.copy()
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Phase 1: red flash + sharingan eye effect
    for i in range(45):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        screen.blit(bg_snapshot, (0, 0))

        # pulsing red overlay
        pulse = abs(math.sin(i * 0.15))
        alpha = int(160 * pulse)
        overlay.fill((180, 0, 0, alpha))
        screen.blit(overlay, (0, 0))

        # "GENJUTSU" text
        font = pygame.font.SysFont("Segoe UI", 48, bold=True)
        txt = font.render("幻 術  ─  G E N J U T S U", True, (255, 60, 60))
        txt.set_alpha(int(255 * pulse))
        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        pygame.display.flip()
        clock.tick(60)



class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("忍 SHINOBI TACTICS 忍")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 52, bold=True)
        self.font_big   = pygame.font.SysFont("Segoe UI", 36, bold=True)
        self.font_med   = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_sm    = pygame.font.SysFont("Segoe UI", 18)

        # State
        self.scene = "MENU"            # MENU | SELECT | BATTLE | GAME_OVER
        self.net = None
        self.player_id = None
        self.game_state = None         # latest state from server
        self.my_char = None
        self.opp_char = None
        self.particles = []
        self.shake_timer = 0
        self.shake_offset = (0, 0)
        self.anim_time = 0
        self.status_msg = ""
        self.status_timer = 0
        self.disconnected = False
        self.hand_sign_enabled = HAS_HAND_SIGNS   # toggle hand-sign mini-game
        self.kirin_effect = None  # KirinDragonEffect when active

        # ── Sound effects ──
        try:
            pygame.mixer.init()
            self.sfx_enabled = True
        except Exception:
            self.sfx_enabled = False
        self.sfx_cache = {}   # {relative_path: pygame.mixer.Sound}

        # Animated sprites  {char_name: AnimatedSprite}
        self.anim_sprites = {}
        self.player_anim = None   # AnimatedSprite for player
        self.enemy_anim = None    # AnimatedSprite for enemy

        # ── MENU widgets ──
        cx = WIDTH // 2
        self.ip_input = TextInput(cx - 150, 300, 300, 44, placeholder="Server IP (e.g. localhost)")
        self.btn_connect = Button(cx - 100, 370, 200, 50, "  CONNECT", (40, 120, 200))

        # ── SELECT widgets ──
        self.char_buttons = []
        spacing = 210
        start_x = (WIDTH - spacing * 4 + (spacing - 180)) // 2
        for i, name in enumerate(CHARACTERS):
            x = start_x + i * spacing
            col = CHARACTERS[name]["color"]
            self.char_buttons.append(Button(x, 350, 180, 55, name, col, font_size=20))

        # ── BATTLE widgets ──
        bw, bh = 140, 50
        panel_y = HEIGHT - 90
        bx_start = (WIDTH - bw * 4 - 30) // 2
        self.battle_buttons = [
            Button(bx_start,            panel_y, bw, bh, " ATTACK",   (60, 130, 200)),
            Button(bx_start + bw + 10,  panel_y, bw, bh, " JUTSU",   (160, 60, 200)),
            Button(bx_start + 2*(bw+10),panel_y, bw, bh, " ULTIMATE", (200, 50, 50)),
            Button(bx_start + 3*(bw+10),panel_y, bw, bh, " HEAL",    (40, 160, 80)),
        ]

        # ── HP bars ──
        self.hp_player = HPBar(40, HEIGHT - 150, 220, 22)
        self.hp_enemy  = HPBar(WIDTH - 260, 50, 220, 22)

        # ── GAME OVER ──
        self.btn_play_again = Button(cx - 110, 420, 220, 55, "PLAY AGAIN", (40, 160, 80))

    # ── Sprite loading ─────────────────────────────────────────────
    def _get_anim_sprite(self, char_name) -> "AnimatedSprite":
        """Get or create an AnimatedSprite for a character."""
        if char_name in self.anim_sprites:
            return self.anim_sprites[char_name]
        data = CHARACTERS.get(char_name, {})
        anim = AnimatedSprite(char_name, data)
        if anim.has_anims:
            anim.play("idle", loop=True)
        self.anim_sprites[char_name] = anim
        return anim

    # ── Main loop ──────────────────────────────────────────────────
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.anim_time += dt
            mouse = pygame.mouse.get_pos()

            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    running = False

            # Network poll
            if self.net and self.net.connected:
                for msg in self.net.poll():
                    self._handle_server_msg(msg)

            if not self.net or not self.net.connected:
                if self.scene not in ("MENU",):
                    if not self.disconnected:
                        self.disconnected = True
                        self.status_msg = "Disconnected from server."
                        self.status_timer = 5

            # Update shakes
            if self.shake_timer > 0:
                self.shake_timer -= dt
                self.shake_offset = (random.randint(-6, 6), random.randint(-6, 6))
            else:
                self.shake_offset = (0, 0)

            # Status message timer
            if self.status_timer > 0:
                self.status_timer -= dt

            # ── Draw per scene ──
            self.screen.fill(C_BG)

            if self.scene == "MENU":
                self._scene_menu(events, mouse, dt)
            elif self.scene == "SELECT":
                self._scene_select(events, mouse, dt)
            elif self.scene == "BATTLE":
                self._scene_battle(events, mouse, dt)
            elif self.scene == "GAME_OVER":
                self._scene_game_over(events, mouse, dt)

            # Status overlay
            if self.status_timer > 0 and self.status_msg:
                alpha = min(255, int(self.status_timer * 255))
                txt = self.font_med.render(self.status_msg, True, C_YELLOW)
                txt.set_alpha(alpha)
                self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 30)))

            pygame.display.flip()

        if self.net:
            self.net.close()
        pygame.quit()

    # ── Server message handler ─────────────────────────────────────
    def _handle_server_msg(self, msg):
        mtype = msg.get("type")

        if mtype == "STATE":
            old_state = self.game_state
            self.game_state = msg
            phase = msg.get("phase")

            if phase == "SELECT" and self.scene != "SELECT":
                self.scene = "SELECT"
                self.status_msg = "Both players connected! Select your character."
                self.status_timer = 3

            elif phase == "BATTLE":
                if self.scene != "BATTLE":
                    self.scene = "BATTLE"
                    # Identify my char and opponent's
                    if self.player_id == "P1":
                        self.my_char = msg.get("char_p1")
                        self.opp_char = msg.get("char_p2")
                    else:
                        self.my_char = msg.get("char_p2")
                        self.opp_char = msg.get("char_p1")
                    # Initialize animated sprites
                    if self.my_char:
                        self.player_anim = self._get_anim_sprite(self.my_char)
                    if self.opp_char:
                        self.enemy_anim = self._get_anim_sprite(self.opp_char)

                    # Update Move Names for buttons
                    if self.my_char:
                        moves = CHARACTERS.get(self.my_char, {}).get("move_names", [])
                        if len(moves) == 4:
                            for idx, btn in enumerate(self.battle_buttons):
                                btn.text = moves[idx]

                    # Special Intro Video: Itachi vs Sasuke
                    participants = {self.my_char, self.opp_char}
                    if "Itachi" in participants and "Sasuke" in participants:
                        play_cutscene(self.screen, "Sasuke vs Itachi starting scene.mp4")

                # Process last_action for effects
                action = msg.get("last_action")
                if action and old_state:
                    self._process_action(action)

            elif phase == "GAME_OVER":
                winner = msg.get("winner")
                if self.player_id == "P1":
                    self.my_char = msg.get("char_p1")
                    self.opp_char = msg.get("char_p2")
                else:
                    self.my_char = msg.get("char_p2")
                    self.opp_char = msg.get("char_p1")
                self.scene = "GAME_OVER"

        elif mtype == "NOT_YOUR_TURN":
            reason = msg.get("reason")
            self.status_msg = reason if reason else "Wait — it's not your turn!"
            self.status_timer = 2

        elif mtype == "OPPONENT_DISCONNECTED":
            self.status_msg = "Opponent disconnected!"
            self.status_timer = 5
            self.game_state = msg
            self.scene = "MENU"
            self.disconnected = True

    def _play_sfx(self, char_name, action_type):
        """Play a sound effect for a character's action if one exists."""
        if not self.sfx_enabled:
            return
        char_data = CHARACTERS.get(char_name, {})
        sfx_map = char_data.get("sfx", {})
        rel_path = sfx_map.get(action_type)
        if not rel_path:
            return
        if rel_path not in self.sfx_cache:
            full_path = os.path.join(AUDIO, rel_path)
            if not os.path.isfile(full_path):
                return
            try:
                self.sfx_cache[rel_path] = pygame.mixer.Sound(full_path)
            except Exception:
                return
        try:
            self.sfx_cache[rel_path].play()
        except Exception:
            pass

    def _process_action(self, action):
        """Trigger visual effects and sprite animations for a received action."""
        act = action.get("action")
        by = action.get("by")
        reflected = action.get("reflected", False)

        if act in ("ATTACK", "JUTSU", "ULTIMATE"):
            # ── Play attack sound effect ──
            attacker_char = action.get("attacker_char", "")
            self._play_sfx(attacker_char, act)

            if reflected:
                # ── Genjutsu counter: attack was reflected! ──
                # Defender plays genjutsu anim, attacker takes the hit
                if by == self.player_id:
                    # We attacked but it was reflected — we get hit
                    px, py = 150, HEIGHT - 250
                    if self.player_anim:
                        self.player_anim.play("hit", loop=False, on_finish="idle")
                    if self.enemy_anim:
                        self.enemy_anim.play("guard", loop=False, on_finish="idle")
                else:
                    # Enemy attacked us but our shield reflected it
                    px, py = WIDTH - 180, 130
                    if self.enemy_anim:
                        self.enemy_anim.play("hit", loop=False, on_finish="idle")
                    if self.player_anim:
                        self.player_anim.play("guard", loop=False, on_finish="idle")

                # Red particles on the attacker who gets hit
                for _ in range(25):
                    self.particles.append(Particle(
                        px + random.randint(-30, 30),
                        py + random.randint(-30, 30),
                        (255, 40, 40)
                    ))
                self.shake_timer = 0.5

                # Play genjutsu counter screen flash
                self._play_genjutsu_counter_effect()

            else:
                # ── Normal attack ──
                # Particles at target location
                if by == self.player_id:
                    px, py = WIDTH - 180, 130
                    if self.player_anim:
                        anim_key = act.lower()
                        self.player_anim.play(anim_key, loop=False, on_finish="idle")
                    if self.enemy_anim:
                        self.enemy_anim.play("hit", loop=False, on_finish="idle")
                else:
                    px, py = 150, HEIGHT - 250
                    if self.enemy_anim:
                        anim_key = act.lower()
                        self.enemy_anim.play(anim_key, loop=False, on_finish="idle")
                    if self.player_anim:
                        self.player_anim.play("hit", loop=False, on_finish="idle")

                col = CHARACTERS.get(action.get("attacker_char", ""), {}).get("accent", C_CYAN)
                for _ in range(20):
                    self.particles.append(Particle(px + random.randint(-20, 20), py + random.randint(-20, 20), col))
                self.shake_timer = 0.3

            # Special: Itachi Genjutsu animation for JUTSU
            if act == "JUTSU" and action.get("attacker_char") == "Itachi":
                is_vs_sasuke = action.get("special_cutscene") == "tsukuyomi"
                play_genjutsu_anim(self.screen, is_vs_sasuke)

            # ── Kirin lightning dragon effect ──
            if act == "ULTIMATE" and action.get("attacker_char") == "Sasuke":
                # Dragon always strikes the character who is NOT Sasuke
                # Figure out which side is the non-Sasuke target
                if self.my_char == "Sasuke" and by == self.player_id:
                    # I am Sasuke and I attacked → hit enemy (top-right)
                    tx, ty = WIDTH - 160, 180
                elif self.opp_char == "Sasuke" and by != self.player_id:
                    # Enemy is Sasuke and they attacked → hit me (bottom-left)
                    tx, ty = 150, HEIGHT - 290
                elif self.my_char == "Sasuke" and by != self.player_id:
                    # I am Sasuke but enemy somehow triggered it → hit me
                    tx, ty = 150, HEIGHT - 290
                else:
                    # Enemy is Sasuke, I triggered view → hit enemy
                    tx, ty = WIDTH - 160, 180
                self.kirin_effect = KirinDragonEffect(tx, ty, duration=2.0)
                self.shake_timer = 1.5  # extended shake for Kirin

        elif act == "HEAL":
            if by == self.player_id:
                px, py = 150, HEIGHT - 250
                if self.player_anim:
                    self.player_anim.play("heal", loop=False, on_finish="idle")
            else:
                px, py = WIDTH - 180, 130
                if self.enemy_anim:
                    self.enemy_anim.play("heal", loop=False, on_finish="idle")
            for _ in range(15):
                self.particles.append(Particle(px + random.randint(-20, 20), py + random.randint(-10, 10), C_GREEN))

    def _play_genjutsu_counter_effect(self):
        """Quick screen flash when genjutsu counter reflects an attack."""
        clock = pygame.time.Clock()
        bg_snapshot = self.screen.copy()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        for i in range(35):
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            self.screen.blit(bg_snapshot, (0, 0))

            pulse = abs(math.sin(i * 0.2))
            alpha = int(140 * pulse)
            overlay.fill((180, 0, 0, alpha))
            self.screen.blit(overlay, (0, 0))

            # "COUNTER" text
            font = pygame.font.SysFont("Segoe UI", 52, bold=True)
            txt = font.render("GENJUTSU COUNTER!", True, (255, 60, 60))
            txt.set_alpha(int(255 * pulse))
            self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

            pygame.display.flip()
            clock.tick(60)

    

    # ── MENU ───────────────────────────────────────────────────────
    def _scene_menu(self, events, mouse, dt):
        # Animated background lines
        for i in range(30):
            y = (self.anim_time * 30 + i * 25) % HEIGHT
            alpha = int(20 + 10 * math.sin(i + self.anim_time))
            pygame.draw.line(self.screen, (40, 40, 60), (0, int(y)), (WIDTH, int(y)))

        # Title
        glow = int(180 + 60 * math.sin(self.anim_time * 2))
        title = self.font_title.render("忍  SHINOBI TACTICS  忍", True, (glow, glow, 255))
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 140)))

        sub = self.font_sm.render("Multiplayer Anime Battle", True, C_GREY)
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 200)))

        # Decorative kanji
        deco_font = pygame.font.SysFont("Segoe UI", 120)
        for i, ch in enumerate("忍術"):
            x_pos = 80 + i * (WIDTH - 160)
            alpha = int(30 + 15 * math.sin(self.anim_time + i))
            txt = deco_font.render(ch, True, (50, 50, 80))
            txt.set_alpha(alpha)
            self.screen.blit(txt, txt.get_rect(center=(x_pos, HEIGHT // 2)))

        # IP input
        label = self.font_sm.render("Server Address:", True, C_GREY)
        self.screen.blit(label, (WIDTH // 2 - 150, 275))
        for ev in events:
            result = self.ip_input.handle_event(ev)
            if result == "SUBMIT":
                self._try_connect()
        self.ip_input.draw(self.screen, dt)

        # Connect button
        self.btn_connect.update(mouse, dt)
        self.btn_connect.draw(self.screen)
        for ev in events:
            if self.btn_connect.clicked(ev):
                self._try_connect()

        # Footer
        footer = self.font_sm.render("Enter IP and press CONNECT to join a battle", True, C_GREY)
        self.screen.blit(footer, footer.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

    def _try_connect(self):
        ip = self.ip_input.text.strip() or "localhost"
        net = Network(ip)

        # ── Run blocking connect in a background thread ───────────
        result = {"done": False, "ok": False}

        def _bg_connect():
            result["ok"] = net.connect()
            result["done"] = True

        t = threading.Thread(target=_bg_connect, daemon=True)
        t.start()

        # ── Keep Pygame alive with a "Connecting…" overlay ────────
        spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        connect_start = time.time()
        font_con = pygame.font.SysFont("Segoe UI", 30, bold=True)
        font_hint = pygame.font.SysFont("Segoe UI", 18)

        while not result["done"]:
            dt = self.clock.tick(FPS) / 1000.0
            elapsed = time.time() - connect_start

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    net.close()
                    pygame.quit()
                    sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    # Cancel connection attempt
                    net.close()
                    self.status_msg = "Connection cancelled."
                    self.status_timer = 3
                    self.net = None
                    return

            # Dark overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            # Spinner + text
            spin_idx = int(elapsed * 10) % len(spinner_chars)
            spin = spinner_chars[spin_idx]
            txt = font_con.render(f"{spin}  Connecting to {ip}…", True, C_CYAN)
            self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))

            hint = font_hint.render("Press ESC to cancel", True, C_GREY)
            self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

            pygame.display.flip()

        # ── Connection finished ───────────────────────────────────
        if result["ok"]:
            self.net = net
            self.player_id = net.player_id
            self.disconnected = False
            self.status_msg = f"Connected as {self.player_id}! Waiting for opponent…"
            self.status_timer = 5
        else:
            self.status_msg = "Connection failed. Check IP and try again."
            self.status_timer = 4
            self.net = None

    # ── CHARACTER SELECT ───────────────────────────────────────────
    def _scene_select(self, events, mouse, dt):
        title = self.font_big.render("SELECT YOUR FIGHTER", True, C_WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 60)))

        # Draw character cards
        spacing = 210
        start_x = (WIDTH - spacing * 4 + (spacing - 180)) // 2
        for i, (name, data) in enumerate(CHARACTERS.items()):
            x = start_x + i * spacing
            card_rect = pygame.Rect(x - 10, 100, 200, 230)

            # Card bg
            pygame.draw.rect(self.screen, C_PANEL, card_rect, border_radius=14)
            pygame.draw.rect(self.screen, data["color"], card_rect, width=2, border_radius=14)

            # Sprite preview (first idle frame)
            anim = self._get_anim_sprite(name)
            frame = anim.get_frame()
            # Scale to fit preview area keeping aspect ratio
            fw, fh = frame.get_size()
            scale = min(100 / max(fw, 1), 130 / max(fh, 1))
            pw, ph = int(fw * scale), int(fh * scale)
            preview = pygame.transform.smoothscale(frame, (max(1, pw), max(1, ph)))
            self.screen.blit(preview, preview.get_rect(center=(x + 90, 210)))

            # Name
            ntxt = self.font_med.render(name, True, data["accent"])
            self.screen.blit(ntxt, ntxt.get_rect(center=(x + 90, 300)))

        # Buttons
        for btn in self.char_buttons:
            btn.update(mouse, dt)
            btn.draw(self.screen)
            for ev in events:
                if btn.clicked(ev):
                    self.my_char = btn.text
                    self.net.send({"action": "SELECT_CHAR", "character": btn.text})
                    self.status_msg = f"You chose {btn.text}! Waiting for opponent…"
                    self.status_timer = 5
                    for b in self.char_buttons:
                        b.enabled = False

        # Player info
        pid_txt = self.font_sm.render(f"You are: {self.player_id}", True, C_CYAN)
        self.screen.blit(pid_txt, (20, HEIGHT - 35))

    # ── BATTLE ─────────────────────────────────────────────────────
    def _scene_battle(self, events, mouse, dt):
        if not self.game_state:
            return

        gs = self.game_state
        is_my_turn = gs.get("turn") == self.player_id

        if self.player_id == "P1":
            my_hp, opp_hp = gs["hp_p1"], gs["hp_p2"]
            my_shield = gs.get("genjutsu_shield_p1", False)
            opp_shield = gs.get("genjutsu_shield_p2", False)
        else:
            my_hp, opp_hp = gs["hp_p2"], gs["hp_p1"]
            my_shield = gs.get("genjutsu_shield_p2", False)
            opp_shield = gs.get("genjutsu_shield_p1", False)

        # ── Apply screen shake ──
        ox, oy = self.shake_offset

        # ── Background (battle arena feel) ──
        # Dark gradient from bottom
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(15 + 10 * t)
            g = int(15 + 5 * t)
            b = int(25 + 15 * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))

        # Grid lines for arena feel
        for i in range(0, WIDTH, 40):
            pygame.draw.line(self.screen, (30, 30, 50), (i + ox, 0), (i + ox, HEIGHT), 1)
        for i in range(0, HEIGHT, 40):
            pygame.draw.line(self.screen, (30, 30, 50), (0, i + oy), (WIDTH, i + oy), 1)

        # ── Update animations ──
        if self.player_anim:
            self.player_anim.update(dt)
        if self.enemy_anim:
            self.enemy_anim.update(dt)

        # ── Enemy (top right) ──
        if self.opp_char:
            opp_data = CHARACTERS.get(self.opp_char, {})
            # Name plate
            name_plate = pygame.Rect(WIDTH - 270 + ox, 12 + oy, 240, 32)
            pygame.draw.rect(self.screen, C_PANEL, name_plate, border_radius=8)
            pygame.draw.rect(self.screen, opp_data.get("color", C_GREY), name_plate, width=2, border_radius=8)
            ntxt = self.font_med.render(self.opp_char, True, opp_data.get("accent", C_WHITE))
            self.screen.blit(ntxt, ntxt.get_rect(center=name_plate.center))

            # HP bar
            self.hp_enemy.update(opp_hp, dt)
            self.hp_enemy.rect.x = WIDTH - 260 + ox
            self.hp_enemy.rect.y = 50 + oy
            self.hp_enemy.draw(self.screen)

            # Animated sprite
            if self.enemy_anim:
                frame = self.enemy_anim.get_frame()
                bob = int(3 * math.sin(self.anim_time * 2.5))
                # Scale to fit battle area
                fw, fh = frame.get_size()
                target_h = 180
                scale = target_h / max(fh, 1)
                sw, sh = int(fw * scale), int(fh * scale)
                scaled = pygame.transform.smoothscale(frame, (max(1, sw), max(1, sh)))
                spr_rect = scaled.get_rect(midbottom=(WIDTH - 160 + ox, 260 + bob + oy))
                self.screen.blit(scaled, spr_rect)

            # Genjutsu shield indicator (enemy)
            if opp_shield:
                shield_pulse = abs(math.sin(self.anim_time * 3))
                shield_alpha = int(100 + 80 * shield_pulse)
                shield_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (180, 0, 0, shield_alpha), (60, 60), 55, 3)
                pygame.draw.circle(shield_surf, (255, 40, 40, shield_alpha // 2), (60, 60), 50, 2)
                self.screen.blit(shield_surf, (WIDTH - 220 + ox, 150 + oy))
                stxt = self.font_sm.render("GENJUTSU", True, (255, 60, 60))
                stxt.set_alpha(shield_alpha)
                self.screen.blit(stxt, stxt.get_rect(center=(WIDTH - 160 + ox, 275 + oy)))

        # ── Player (bottom left) ──
        if self.my_char:
            my_data = CHARACTERS.get(self.my_char, {})
            # Name plate
            name_plate = pygame.Rect(30 + ox, HEIGHT - 180 + oy, 240, 32)
            pygame.draw.rect(self.screen, C_PANEL, name_plate, border_radius=8)
            pygame.draw.rect(self.screen, my_data.get("color", C_GREY), name_plate, width=2, border_radius=8)
            ntxt = self.font_med.render(self.my_char, True, my_data.get("accent", C_WHITE))
            self.screen.blit(ntxt, ntxt.get_rect(center=name_plate.center))

            # HP bar
            self.hp_player.update(my_hp, dt)
            self.hp_player.rect.x = 40 + ox
            self.hp_player.rect.y = HEIGHT - 145 + oy
            self.hp_player.draw(self.screen)

            # Animated sprite (flipped to face right)
            if self.player_anim:
                frame = self.player_anim.get_frame()
                bob = int(3 * math.sin(self.anim_time * 2))
                # Scale to fit battle area
                fw, fh = frame.get_size()
                target_h = 180
                scale = target_h / max(fh, 1)
                sw, sh = int(fw * scale), int(fh * scale)
                scaled = pygame.transform.smoothscale(frame, (max(1, sw), max(1, sh)))
                sprite_flip = pygame.transform.flip(scaled, True, False)
                spr_rect = sprite_flip.get_rect(midbottom=(150 + ox, HEIGHT - 200 + bob + oy))
                self.screen.blit(sprite_flip, spr_rect)

            # Genjutsu shield indicator (player)
            if my_shield:
                shield_pulse = abs(math.sin(self.anim_time * 3))
                shield_alpha = int(100 + 80 * shield_pulse)
                shield_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (180, 0, 0, shield_alpha), (60, 60), 55, 3)
                pygame.draw.circle(shield_surf, (255, 40, 40, shield_alpha // 2), (60, 60), 50, 2)
                self.screen.blit(shield_surf, (90 + ox, HEIGHT - 330 + oy))
                stxt = self.font_sm.render("GENJUTSU", True, (255, 60, 60))
                stxt.set_alpha(shield_alpha)
                self.screen.blit(stxt, stxt.get_rect(center=(150 + ox, HEIGHT - 195 + oy)))

        # ── Command Panel ──
        panel_rect = pygame.Rect(0, HEIGHT - 110, WIDTH, 110)
        pygame.draw.rect(self.screen, C_PANEL, panel_rect)
        pygame.draw.line(self.screen, C_PANEL_EDGE, (0, HEIGHT - 110), (WIDTH, HEIGHT - 110), 2)

        for btn in self.battle_buttons:
            btn.enabled = is_my_turn
            btn.update(mouse, dt)
            btn.draw(self.screen)

        for ev in events:
            if not is_my_turn:
                continue
            for i, btn in enumerate(self.battle_buttons):
                if btn.clicked(ev):
                    actions = ["ATTACK", "JUTSU", "ULTIMATE", "HEAL"]
                    act = actions[i]

                    # ── Hand-sign challenge for JUTSU / ULTIMATE ──
                    hand_sign_success = True
                    if act in ("JUTSU", "ULTIMATE") and self.hand_sign_enabled:
                        seq = HAND_SIGN_SEQUENCES.get(self.my_char, {}).get(act, [])
                        if seq:
                            hand_sign_success = run_hand_sign_challenge(
                                self.screen, seq, action_type=act
                            )
                            if not hand_sign_success:
                                self.status_msg = "HAND SIGNS FAILED — ATTACK MISSED!"
                                self.status_timer = 3

                    if act == "JUTSU" and self.my_char == "Itachi":
                        if hand_sign_success:
                            # Play genjutsu anim locally too
                            is_vs_sasuke = self.opp_char == "Sasuke"
                            play_genjutsu_anim(self.screen, is_vs_sasuke)

                    if hand_sign_success:
                        self.net.send({"action": act})
                    else:
                        self.net.send({"action": act, "dmg": 0})

        # ── Turn indicator ──
        turn_text = "YOUR TURN" if is_my_turn else "OPPONENT'S TURN"
        turn_color = C_CYAN if is_my_turn else C_RED
        pulse = int(200 + 55 * math.sin(self.anim_time * 4))
        turn_col = tuple(min(255, max(0, c + pulse - 200)) if c == max(turn_color) else c for c in turn_color)
        banner = self.font_big.render(turn_text, True, turn_col)
        self.screen.blit(banner, banner.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

        # ── Kirin lightning dragon effect ──
        if self.kirin_effect:
            self.kirin_effect.update(dt)
            self.kirin_effect.draw(self.screen)
            if not self.kirin_effect.alive:
                self.kirin_effect = None

        # ── Particles ──
        alive = []
        for p in self.particles:
            p.update(dt)
            p.draw(self.screen)
            if p.alive:
                alive.append(p)
        self.particles = alive

        # ── Player labels ──
        p_label = self.font_sm.render(f"You: {self.player_id}", True, C_CYAN)
        self.screen.blit(p_label, (20, 10))

    # ── GAME OVER ──────────────────────────────────────────────────
    def _scene_game_over(self, events, mouse, dt):
        gs = self.game_state
        winner = gs.get("winner") if gs else None
        i_won = winner == self.player_id

        # Dramatic background
        for y in range(HEIGHT):
            t = y / HEIGHT
            if i_won:
                r, g, b = int(10 + 30 * t), int(30 + 50 * t), int(10 + 20 * t)
            else:
                r, g, b = int(40 + 30 * t), int(10 + 10 * t), int(10 + 10 * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))

        # Result text
        if i_won:
            txt = self.font_title.render("⚔  VICTORY  ⚔", True, (80, 255, 120))
        else:
            txt = self.font_title.render("✖  DEFEAT  ✖", True, (255, 80, 80))
        pulse = 1.0 + 0.05 * math.sin(self.anim_time * 3)
        txt = pygame.transform.smoothscale(txt, (int(txt.get_width() * pulse), int(txt.get_height() * pulse)))
        self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 180)))

        # Show final characters
        if self.my_char:
            anim = self._get_anim_sprite(self.my_char)
            frame = anim.get_frame()
            fw, fh = frame.get_size()
            scale = min(130 / max(fw, 1), 170 / max(fh, 1))
            spr_s = pygame.transform.smoothscale(frame, (max(1, int(fw * scale)), max(1, int(fh * scale))))
            self.screen.blit(spr_s, spr_s.get_rect(center=(WIDTH // 2 - 120, 330)))
        if self.opp_char:
            anim = self._get_anim_sprite(self.opp_char)
            frame = anim.get_frame()
            fw, fh = frame.get_size()
            scale = min(130 / max(fw, 1), 170 / max(fh, 1))
            spr_s = pygame.transform.smoothscale(frame, (max(1, int(fw * scale)), max(1, int(fh * scale))))
            self.screen.blit(spr_s, spr_s.get_rect(center=(WIDTH // 2 + 120, 330)))

        vs_txt = self.font_big.render("VS", True, C_WHITE)
        self.screen.blit(vs_txt, vs_txt.get_rect(center=(WIDTH // 2, 330)))

        # Play again
        self.btn_play_again.update(mouse, dt)
        self.btn_play_again.draw(self.screen)
        for ev in events:
            if self.btn_play_again.clicked(ev):
                # Reconnect
                self.scene = "MENU"
                self.game_state = None
                self.my_char = None
                self.opp_char = None
                self.particles = []
                if self.net:
                    self.net.close()
                    self.net = None
                for b in self.char_buttons:
                    b.enabled = True



if __name__ == "__main__":
    game = Game()
    game.run()
