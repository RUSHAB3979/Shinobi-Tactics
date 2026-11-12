"""Sampled combat audio: separate voice, anticipation, release, and contact buses."""
import json
from pathlib import Path
import wave

import pygame


class CombatAudio:
    def __init__(self, root):
        self.root = Path(root)
        path = self.root / "assets/audio/combat.json"
        self.moves = json.loads(path.read_text())["characters"] if path.is_file() else {}
        self.cache = {}
        self.channels = {}
        self.volume = .45
        self.enabled = True
        self.voice_lengths = {}
        self.contact_pan = .5

    def pan_contact(self, x):
        self.contact_pan = max(0., min(1., x))

    @staticmethod
    def impact_layer(character, action, stage='impact'):
        if stage == 'block': return 'counter'
        if action.lower() == 'heal': return None
        if action.lower() == 'attack': return 'slash'
        if character == 'Itachi': return 'illusion'
        if character == 'Tanjiro': return 'fire' if action.lower() == 'ultimate' else 'water'
        return 'thunder' if action.lower() == 'ultimate' else 'electric'

    def voice_duration(self, character, action):
        entry = self.moves.get(character, {}).get(action.lower(), {}).get("voice")
        if not entry or not self.enabled or self.volume <= 0 or not pygame.mixer.get_init():
            return 0.
        if entry not in self.voice_lengths:
            try:
                with wave.open(str(self.root / entry)) as stream:
                    self.voice_lengths[entry] = stream.getnframes()/stream.getframerate()
            except (OSError, wave.Error):
                self.voice_lengths[entry] = 0.
        return self.voice_lengths[entry]

    def _ready(self):
        if not self.enabled or not pygame.mixer.get_init():
            return False
        if not self.channels:
            pygame.mixer.set_num_channels(max(8, pygame.mixer.get_num_channels()))
            pygame.mixer.set_reserved(5)
            self.channels = {name: pygame.mixer.Channel(i) for i, name in enumerate(
                ("voice", "start", "release", "impact", "weight"))}
        return True

    def update(self, volume, enabled):
        self.volume = max(0., min(1., volume))
        self.enabled = enabled
        if not pygame.mixer.get_init():
            self.channels.clear()
            return
        if not enabled:
            self.stop()
            return
        if self.channels:
            duck = .48 if self.channels["voice"].get_busy() else 1.
            for name, channel in self.channels.items():
                gain = self.volume * (.72 if name == "voice" else (.22 if name == "weight" else .45) * duck)
                if name in ('impact', 'weight'):
                    channel.set_volume(gain*(1-.4*self.contact_pan),gain*(.6+.4*self.contact_pan))
                else:
                    channel.set_volume(gain)

    def stop(self):
        if pygame.mixer.get_init():
            for channel in self.channels.values():
                channel.stop()

    def _play(self, entry, bus):
        if not entry or not self._ready():
            return False
        path = self.root / entry
        if not path.is_file():
            return False
        try:
            if entry not in self.cache:
                self.cache[entry] = pygame.mixer.Sound(str(path))
            self.channels[bus].play(self.cache[entry])
            self.update(self.volume, self.enabled)
        except (pygame.error, OSError):
            return False
        return True

    def play(self, character, action, stage):
        """Contact is requested only by the authoritative presentation event."""
        if not self._ready():
            return
        action = action.lower()
        move = self.moves.get(character, {}).get(action, {})
        if stage == "start":
            self.stop()  # A new turn cannot inherit a previous character's dialogue.
            self._play(move.get("voice"), "voice")
            self._play(move.get("start"), "start")
        elif stage in ("release", "impact", "block"):
            bus = "impact" if stage == "block" else stage
            if stage in ('impact', 'block'):
                layer = self.impact_layer(character, action, stage)
                if layer: self._play(f'assets/audio/impact/{layer}.wav', 'weight')
            if self._play(move.get(stage), bus):
                return
            # Keep earlier builds and missing optional samples playable.
            cue = "block" if stage == "block" else (
                "heal" if action == "heal" else "hit" if stage == "impact" else action)
            if stage != "release" or action != "heal":
                self._play(f"assets/audio/generated/{character.lower()}-{cue}.wav", bus)
