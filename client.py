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

import pygame

from pathlib import Path
from animation import ClipLibrary, AnimationPlayer
from battle_presentation import PresentationQueue
from combat_audio import CombatAudio
from combat_feedback import CombatFeedback
from battle_style import BattleStyle
from video_overlay import VideoOverlay
from battle_visuals import CombatEffect, create_arena, ACTOR_ROOTS
from hand_sign_config import HAND_SIGN_SEQUENCES

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
# anim_map preserves the legacy source mappings for audit tooling only.
# Runtime animation uses assets/animations.json exclusively.
CHARACTERS = {
    "Sasuke": {
        "color": (130, 80, 200), "accent": (180, 120, 255),
        "sprite_folder": "sasuke",
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
        "sprite_folder": "tanjiro",
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
        "sprite_folder": "itachi",
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
        "sprite_folder": "zenitsu",
        "anim_map": {
            "idle": "idle_new", "attack": "attack_1", "jutsu": "sixfold",
            "ultimate": "godspeed", "hit": "hit", "down": "down",
            "guard": "guard", "heal": "healing", "run": "run",
            "dash": "dash", "victory": "victory",
        },
        "move_names": ["SLASH", "SIXFOLD", "GODSPEED", "RECOVER"],
    },
}

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
        self.font = pygame.font.Font(str(Path(BASE_DIR)/"assets/fonts/SpaceGrotesk-Bold.otf"),font_size)
        self.hovered = False
        self.text_cache = {}
        self.enabled = True
        self._anim_t = 0

    def update(self, mouse_pos, dt):
        self.hovered = self.rect.collidepoint(mouse_pos) and self.enabled
        self._anim_t += dt

    def draw(self, surf):
        col = self.hover_color if self.hovered else self.base_color
        if not self.enabled:
            col = tuple(round(c*.30+18) for c in self.base_color)

        x,y,w,h=self.rect
        points=[(x,y),(x+w-12,y),(x+w,y+12),(x+w,y+h),(x+12,y+h),(x,y+h-12)]
        pygame.draw.polygon(surf,(25,39,56) if self.hovered else (12,23,37),points)
        pygame.draw.lines(surf,col,False,[(x,y+h-12),(x,y),(x+w-12,y),(x+w,y+12)],2)
        pygame.draw.line(surf,(64,79,94),(x+12,y+h),(x+w,y+h),1)

        # Text
        key = (self.text,self.enabled)
        if key not in self.text_cache:
            self.text_cache[key] = self.font.render(self.text,True,self.text_color if self.enabled else (150,165,185))
        txt_surf = self.text_cache[key]
        txt_rect = txt_surf.get_rect(center=(self.rect.centerx+(8 if hasattr(self,"icon") else 0),self.rect.centery))
        if hasattr(self,"icon"):
            x,y=self.rect.x+14,self.rect.centery
            color=self.text_color if self.enabled else (130,150,175)
            if self.icon==0:
                pygame.draw.line(surf,color,(x-4,y+7),(x+5,y-7),2)
                pygame.draw.line(surf,color,(x-6,y+1),(x+1,y+6),2)
            elif self.icon==1:
                pygame.draw.circle(surf,color,(x,y),6,2)
                pygame.draw.circle(surf,color,(x,y),2)
            elif self.icon==2:
                pygame.draw.lines(surf,color,False,[(x+4,y-8),(x-4,y+1),(x+2,y+1),(x-3,y+8)],2)
            else:
                pygame.draw.line(surf,color,(x-6,y),(x+6,y),2)
                pygame.draw.line(surf,color,(x,y-6),(x,y+6),2)
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
        self.font = pygame.font.SysFont(None,16,bold=True)

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
        txt = self.font.render(f"{self.current}/{self.max_hp}", True, C_WHITE)
        surf.blit(txt, txt.get_rect(center=self.rect.center))


class TextInput:
    """Minimal text input box."""
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.font = pygame.font.SysFont(None, 22)
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



class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SHINOBI TACTICS")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.Font(str(Path(BASE_DIR)/"assets/fonts/SpaceGrotesk-Bold.otf"),48)
        self.font_big   = pygame.font.Font(str(Path(BASE_DIR)/"assets/fonts/SpaceGrotesk-Bold.otf"),32)
        self.font_med   = pygame.font.Font(str(Path(BASE_DIR)/"assets/fonts/SpaceGrotesk-Bold.otf"),20)
        self.font_sm    = pygame.font.Font(str(Path(BASE_DIR)/"assets/fonts/SpaceGrotesk-Bold.otf"),12)

        # State
        self.scene = "MENU"            # MENU | SELECT | BATTLE | GAME_OVER
        self.net = None
        self.player_id = None
        self.game_state = None         # latest state from server
        self.my_char = None
        self.opp_char = None
        self.feedback = CombatFeedback()
        self.style = BattleStyle()
        self.world = pygame.Surface((WIDTH, 530)).convert()
        self.anim_time = 0
        self.status_msg = ""
        self.status_timer = 0
        self.disconnected = False
        self.videos_enabled = False
        self.video = VideoOverlay()
        self.clip_library = ClipLibrary(BASE_DIR)
        self.presentation = PresentationQueue(self._presentation_timing)
        self.effect = None
        self.submission_pending = False
        self.ending_timer = None
        self.reduced_motion = False
        self.volume = 0.45
        self.arena = create_arena(BASE_DIR, (WIDTH, HEIGHT))
        self.menu_background = self.arena.copy()
        tint = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        tint.fill((8,12,24,135))
        self.menu_background.blit(tint,(0,0))
        self.portraits = {}

        # ── Sound effects ──
        try:
            pygame.mixer.init()
            self.sfx_enabled = True
        except Exception:
            self.sfx_enabled = False
        self.audio = CombatAudio(BASE_DIR)

        # Selection preview players; battle actors are separate instances.
        self.anim_sprites = {}
        self.player_anim = None
        self.enemy_anim = None

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

        for i, button in enumerate(self.battle_buttons):
            button.icon = i
            button.rect = pygame.Rect(24+i*246,545,238,62)

        # ── HP bars ──
        self.hp_player = HPBar(40, HEIGHT - 150, 220, 22)
        self.hp_enemy  = HPBar(WIDTH - 260, 50, 220, 22)

        # ── GAME OVER ──
        self.btn_play_again = Button(cx - 110, 420, 220, 55, "PLAY AGAIN", (40, 160, 80))

    # ── Sprite loading ─────────────────────────────────────────────
    def _get_anim_sprite(self, char_name):
        """Selection previews may be cached; battle actors always have their own player."""
        if char_name not in self.anim_sprites:
            self.anim_sprites[char_name] = AnimationPlayer(self.clip_library, char_name)
        return self.anim_sprites[char_name]

    def _timing(self, character, action):
        clip = self.clip_library.data["characters"][character]["clips"][action]
        markers = {event["name"]: event["time"] for event in clip.get("events", [])}
        return {**markers, "duration": sum(frame["duration"] for frame in clip["frames"])}

    def _presentation_timing(self, character, action):
        timing = self._timing(character, action)
        self.audio.update(self.volume, self.sfx_enabled)
        timing["duration"] = max(timing["duration"], self.audio.voice_duration(character, action)+.06)
        return timing

    def _poll_network(self):
        if self.net and self.net.connected:
            for msg in self.net.poll():
                self._handle_server_msg(msg)
        return bool(self.net and self.net.connected and self.scene == "BATTLE")

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

            self._poll_network()
            for ev in events:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_m:
                        self.sfx_enabled = not self.sfx_enabled and pygame.mixer.get_init() is not None
                        if not self.sfx_enabled and pygame.mixer.get_init():
                            pygame.mixer.stop()
                    elif ev.key == pygame.K_v:
                        self.videos_enabled = not self.videos_enabled
                    elif ev.key == pygame.K_ESCAPE and self.video.active:
                        self.video.close()
                    elif ev.key == pygame.K_r:
                        self.reduced_motion = not self.reduced_motion
                    elif ev.key in (pygame.K_MINUS, pygame.K_EQUALS):
                        self.volume = max(0, min(1, self.volume + (0.1 if ev.key == pygame.K_EQUALS else -0.1)))

            if not self.net or not self.net.connected:
                if self.scene not in ("MENU",):
                    if not self.disconnected:
                        self.disconnected = True
                        self.status_msg = "Disconnected from server."
                        self.status_timer = 5

            self.audio.update(self.volume, self.sfx_enabled)

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
        self.video.close()
        pygame.quit()

    # ── Server message handler ─────────────────────────────────────
    def _handle_server_msg(self, msg):
        mtype = msg.get("type")
        if mtype == "STATE":
            self.game_state = msg
            phase = msg.get("phase")
            if phase == "SELECT":
                if self.scene != "SELECT":
                    self.presentation.reset()
                    self.feedback.reset()
                    self.audio.stop()
                    self.player_anim = self.enemy_anim = None
                    self.effect = None
                    self.ending_timer = None
                    self.submission_pending = False
                    self.scene = "SELECT"
                return
            if phase in ("BATTLE", "GAME_OVER"):
                if self.player_anim is None:
                    self.my_char = msg["char_p1" if self.player_id == "P1" else "char_p2"]
                    self.opp_char = msg["char_p2" if self.player_id == "P1" else "char_p1"]
                    self.player_anim = AnimationPlayer(self.clip_library, self.my_char)
                    self.enemy_anim = AnimationPlayer(self.clip_library, self.opp_char)
                    self.presentation.reset()
                    self.feedback.reset()
                    self.audio.stop()
                    for btn, name in zip(self.battle_buttons, CHARACTERS[self.my_char]["move_names"]):
                        btn.text = name
                    self.hp_player.display = self.hp_enemy.display = 100
                    self.scene = "BATTLE"
                    if self.videos_enabled and {self.my_char,self.opp_char} == {"Sasuke","Itachi"}:
                        self.video.start(Path(VIDEOS)/"Sasuke vs Itachi starting scene.mp4")
                if "match_id" not in msg or (msg.get("last_action") and "id" not in msg["last_action"]):
                    self.status_msg = "Update server.py: animation protocol requires action IDs."
                    self.status_timer = 5
                    return
                accepted = self.presentation.enqueue(msg)
                action = msg.get("last_action")
                if accepted and action["by"] == self.player_id:
                    self.submission_pending = False
                if phase == "GAME_OVER" and not action and not self.presentation.busy:
                    self.scene = "GAME_OVER"
        elif mtype == "NOT_YOUR_TURN":
            self.submission_pending = False
            self.status_msg = msg.get("reason", "Wait for your turn.")
            self.status_timer = 2
        elif mtype == "OPPONENT_DISCONNECTED":
            self.audio.stop()
            self.video.close()
            self.presentation.reset()
            self.feedback.reset()
            self.effect = None
            self.player_anim = self.enemy_anim = None
            self.submission_pending = False
            self.ending_timer = None
            self.status_msg = "Opponent disconnected."
            self.status_timer = 5
            self.scene = "MENU"
            if self.net:
                self.net.close()
            for button in self.char_buttons:
                button.enabled = True

    def _actor(self, pid):
        return self.player_anim if pid == self.player_id else self.enemy_anim

    def _root(self, pid):
        return ACTOR_ROOTS["left" if pid == self.player_id else "right"]

    def _play_sfx(self, character, action):
        self.audio.update(self.volume, self.sfx_enabled)
        stage = "block" if action.lower() == "block" else "impact" if action.lower() in ("hit", "heal") else "release"
        self.audio.play(character, action, stage)

    def _presentation_event(self, kind, snapshot):
        action = snapshot["last_action"]
        by = action["by"]
        other = "P2" if by == "P1" else "P1"
        char = snapshot["char_p1" if by == "P1" else "char_p2"]
        act = action["action"]
        self.audio.update(self.volume, self.sfx_enabled)
        if kind == "start":
            self.audio.play(char, act, "start")
            self._actor(by).play(act.lower())
            self._actor(other).play("idle", loop=True)
            recipient = by if action.get("reflected") or act == "HEAL" else other
            self.effect = CombatEffect(char, act, self._root(by), self._root(recipient),
                self._timing(char, act.lower()), miss=act != "HEAL" and action.get("dmg",0) == 0,
                reflected=action.get("reflected",False), contact_target=self._root(other))
        elif kind == "release":
            if char == "Itachi" and action.get("dmg",0)>0:
                self._actor(other).play("guard", loop=True)
            if act != "HEAL":
                self.audio.play(char, act, "release")
        elif kind == "impact":
            self.effect.impact()
            self.audio.pan_contact(self.effect.target[0]/WIDTH)
            if act == "HEAL":
                self.status_msg = "RECOVER"
                self.audio.play(char, act, "impact")
            elif action.get("dmg",0) == 0:
                self.status_msg = "MISS"
            else:
                reflected = action.get("reflected",False)
                recipient = by if reflected else other
                self._actor(recipient).play("hit")
                if reflected: self._actor(other).play("guard")
                self.status_msg = "GENJUTSU COUNTER" if reflected else f"{action['dmg']} DAMAGE"
                self.feedback.hit(char, act, self._root(other if reflected else by),
                                  self._root(recipient), reflected)
                self.presentation.pause_remaining = self.feedback.hitstop(act, self.reduced_motion)
                self.audio.play(char, act, "block" if reflected else "impact")
            self.status_timer = .7
        elif kind == "finish" and snapshot["phase"] == "GAME_OVER":
            self.ending_timer = .85
            for pid in ("P1","P2"):
                self._actor(pid).play("victory" if pid == snapshot["winner"] else "down")

    def _advance_actors(self, dt):
        if self.player_anim: self.player_anim.update(dt)
        if self.enemy_anim: self.enemy_anim.update(dt)
        if self.effect: self.effect.update(dt)
        if self.ending_timer is not None:
            self.ending_timer -= dt
            if self.ending_timer <= 0:
                self.scene = "GAME_OVER"
                self.ending_timer = None

    def _advance_presentation(self, dt):
        self.presentation.update(dt, on_event=self._presentation_event,
                                 on_advance=self._advance_actors, on_clock=self.feedback.update)

    # ── MENU ───────────────────────────────────────────────────────
    def _scene_menu(self, events, mouse, dt):
        self.screen.blit(self.menu_background,(0,0))
        self.style.atmosphere(self.screen,dt,self.reduced_motion)
        self.style.text(self.screen,"THE SHATTERED SHRINE",(512,83),12,(223,185,115),True)
        self.style.text(self.screen,"SHINOBI",(512,139),48,(239,239,228),True)
        self.style.text(self.screen,"TACTICS",(512,195),48,(223,185,115),True)
        pygame.draw.line(self.screen,(151,124,80),(376,235),(648,235),1)
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
        font_con = pygame.font.SysFont(None, 30, bold=True)
        font_hint = pygame.font.Font(str(Path(BASE_DIR)/"assets/fonts/SpaceGrotesk-Bold.otf"),12)

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
        self.screen.blit(self.menu_background,(0,0))
        title = self.font_big.render("SELECT YOUR FIGHTER", True, C_WHITE)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 60)))

        # Draw character cards
        spacing = 210
        start_x = (WIDTH - spacing * 4 + (spacing - 180)) // 2
        for i, (name, data) in enumerate(CHARACTERS.items()):
            x = start_x + i * spacing
            card_rect = pygame.Rect(x - 10, 100, 200, 230)

            # Card bg
            pygame.draw.rect(self.screen, (12,21,34), card_rect, border_radius=4)
            pygame.draw.line(self.screen, data["accent"],card_rect.topleft,card_rect.topright,3)
            pygame.draw.line(self.screen,(59,75,92),card_rect.bottomleft,card_rect.bottomright)

            # Sprite preview (first idle frame)
            anim = self._get_anim_sprite(name)
            anim.update(dt)
            anim.draw(self.screen,(x+90,275),scale=.85)

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
        if self.video.active:
            self.video.update(dt)
            if self.video.active:
                self.video.draw(self.screen,self.font_sm)
                return
        self._advance_presentation(dt)
        gs = self.game_state
        is_my_turn = (gs.get("turn") == self.player_id and gs.get("phase") == "BATTLE"
                      and not self.presentation.busy and not self.submission_pending
                      and self.ending_timer is None)
        self.world.blit(self.arena, (0,0))
        self.style.atmosphere(self.world,dt,self.reduced_motion)
        actor_positions = {pid:self._root(pid) for pid in ("P1","P2")}
        if self.effect and self.presentation.active:
            by = self.presentation.active["last_action"]["by"]
            actor_positions[by] = self.effect.movement(self.reduced_motion)
        if self.effect and self.presentation.active:
            actor = self._actor(by)
            facing = "right" if by == self.player_id else "left"
            self.effect.bind(actor,actor_positions[by],facing,self.reduced_motion)
        if self.effect:
            self.effect.reduced = self.reduced_motion
            self.effect.draw_background(self.world,.45 if self.reduced_motion else 1)
        self.feedback.draw_ground(self.world, self.reduced_motion)
        if self.effect and self.presentation.active:
            for position,alpha in self.effect.trail_positions():
                actor.draw(self.world,position,facing=facing,opacity=alpha)
        self.style.lighting(self.world,self.effect,self.reduced_motion)
        for pid in ("P1","P2"):
            x,y = actor_positions[pid]
            dx,dy = self.feedback.displacement(self._root(pid), self.reduced_motion)
            x,y = x+dx,y+dy
            pygame.draw.ellipse(self.world,(13,23,33),(x-43,y-4,86,12))
            opacity = self.effect.caster_opacity if self.effect and self.presentation.active and pid==by else 255
            if self.effect and self.presentation.active and self.effect.character=="Itachi" and self.effect.action=="ULTIMATE" and pid!=by and self.effect.timing['release']<self.effect.age<self.effect.timing['impact']:
                for offset in (-20,20):
                    self._actor(pid).draw(self.world,(x+offset,y),facing="right" if pid==self.player_id else "left",opacity=45)
            self._actor(pid).draw(self.world,(x,y),
                                  facing="right" if pid == self.player_id else "left",opacity=opacity)
            if self.presentation.visible_shields[pid]:
                pygame.draw.ellipse(self.world,(210,70,105),(x-45,y-150,90,145),2)
        if self.effect:
            self.effect.draw(self.world,.45 if self.reduced_motion else 1)
        self.feedback.draw_front(self.world, self.reduced_motion)
        self.screen.blit(self.arena, (0,0))
        self.screen.set_clip(pygame.Rect(0,0,WIDTH,530))
        self.screen.blit(self.world, self.feedback.camera(self.reduced_motion))
        self.screen.set_clip(None)
        other = "P2" if self.player_id == "P1" else "P1"
        acting = self.presentation.active["last_action"]["by"] if self.presentation.active else gs.get("turn")
        for name,pid,bar,x,side in ((self.my_char,self.player_id,self.hp_player,24,"YOU"),
                                    (self.opp_char,other,self.hp_enemy,630,"RIVAL")):
            if name not in self.portraits:
                frame = self.clip_library.data["characters"][name]["clips"]["idle"]["frames"][0]
                image = self.clip_library.image(frame["path"])
                top = image.get_bounding_rect(min_alpha=128).top
                head = pygame.Rect(round(frame["anchor"][0])-20,top,40,40).clip(image.get_rect())
                self.portraits[name] = pygame.transform.scale(image.subsurface(head),(40,40))
            bar.update(self.presentation.visible_hp[pid],dt)
            self.style.health(self.screen,name,self.portraits[name],bar,x,side,
                              acting==pid,self.presentation.visible_shields[pid])
        pygame.draw.polygon(self.screen,(15,23,35),[(512,22),(546,55),(512,88),(478,55)])
        self.style.text(self.screen,"VS",(512,55),18,(223,185,115),True)
        if self.effect and self.presentation.active:
            index = 1 if self.effect.action == "JUTSU" else 2
            self.style.technique(self.screen,self.effect,
                CHARACTERS[self.effect.character]["move_names"][index],self.reduced_motion)
        self.style.commands(self.screen,self.battle_buttons,is_my_turn,mouse,dt)
        for event in events:
            if not is_my_turn or self.submission_pending:
                continue
            for i,btn in enumerate(self.battle_buttons):
                if btn.clicked(event):
                    act=["ATTACK","JUTSU","ULTIMATE","HEAL"][i]
                    self.submission_pending=True
                    success=True
                    if act in ("JUTSU","ULTIMATE"):
                        try:
                            from hand_sign_ui import run_hand_sign_challenge
                            success=run_hand_sign_challenge(self.screen,
                                HAND_SIGN_SEQUENCES[self.my_char][act],action_type=act,
                                on_tick=self._poll_network)
                        except (ImportError,RuntimeError,FileNotFoundError) as exc:
                            success=False
                            self.status_msg=f"Hand signs unavailable: {type(exc).__name__}. Attack misses."
                            self.status_timer=3
                        self.clock.tick()  # Challenge time is not battle animation time.
                    if self.net and self.net.connected and self.scene=="BATTLE":
                        self.net.send({"action":act} if success else {"action":act,"dmg":0})
                    else:
                        self.submission_pending=False
                    break
        text=("RESOLVING MOVE" if self.presentation.busy else "WAITING FOR SERVER" if self.submission_pending
              else "YOUR TURN" if is_my_turn else "OPPONENT'S TURN")
        pygame.draw.polygon(self.screen,(10,17,28),[(386,492),(638,492),(626,519),(398,519)])
        self.style.text(self.screen,text,(512,505),10,(223,185,115) if is_my_turn else (180,196,209),True)
        hint=f"V intros {'ON' if self.videos_enabled else 'OFF'}  |  M sound {'ON' if self.sfx_enabled else 'OFF'}  |  R motion {'LOW' if self.reduced_motion else 'FULL'}  |  +/- volume"
        self.screen.blit(self.font_sm.render(hint,True,(155,175,195)),(380,615))

    # ── GAME OVER ──────────────────────────────────────────────────
    def _scene_game_over(self, events, mouse, dt):
        if self.player_anim: self.player_anim.update(dt)
        if self.enemy_anim: self.enemy_anim.update(dt)
        gs = self.game_state
        winner = gs.get("winner") if gs else None
        i_won = winner == self.player_id

        self.screen.blit(self.menu_background,(0,0))

        # Result text
        if i_won:
            txt = self.font_title.render("VICTORY", True, (80, 255, 120))
        else:
            txt = self.font_title.render("DEFEAT", True, (255, 80, 80))
        pulse = 1.0 + 0.05 * math.sin(self.anim_time * 3)
        txt = pygame.transform.scale(txt, (int(txt.get_width() * pulse), int(txt.get_height() * pulse)))
        self.screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 180)))

        # Keep the same logical scale and root for standing and prone poses.
        if self.player_anim:
            self.player_anim.draw(self.screen,(WIDTH//2-130,380),facing="right")
        if self.enemy_anim:
            self.enemy_anim.draw(self.screen,(WIDTH//2+130,380),facing="left")

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
                self.video.close()
                self.presentation.reset()
                self.feedback.reset()
                self.audio.stop()
                self.player_anim = self.enemy_anim = None
                self.effect = None
                self.ending_timer = None
                self.submission_pending = False
                if self.net:
                    self.net.close()
                    self.net = None
                for b in self.char_buttons:
                    b.enabled = True



if __name__ == "__main__":
    game = Game()
    game.run()
