"""
hand_sign_config.py  –  Hand-sign sequences for each character's jutsu.

Each entry maps a character name → {action → [sign_sequence]}.
The player must perform the signs in order to successfully execute the move.
Signs: "fist", "open_palm", "peace", "point_up", "thumbs_up", "rock"
"""

HAND_SIGN_SEQUENCES = {
    "Sasuke": {
        "JUTSU":    ["fist", "peace", "point_up"],      # Chidori: Tiger → Snake → Bird
        "ULTIMATE": ["point_up"],                        # Kirin: raise hand skyward
    },
    "Itachi": {
        "JUTSU":    ["peace", "fist"],                   # Genjutsu: Snake → Tiger
        "ULTIMATE": ["open_palm", "peace", "fist"],      # Tsukuyomi: Ram → Snake → Tiger
    },
    "Tanjiro": {
        "JUTSU":    ["open_palm", "fist"],               # Water Breathing: Ram → Tiger
        "ULTIMATE": ["open_palm", "point_up", "fist"],   # Sun Breathing: Ram → Bird → Tiger
    },
    "Zenitsu": {
        "JUTSU":    ["fist", "point_up"],                # Thunder: Tiger → Bird
        "ULTIMATE": ["fist", "peace", "point_up"],       # Godspeed: Tiger → Snake → Bird
    },
}

# Display-friendly emoji for each sign (used in the UI overlay)
SIGN_DISPLAY = {
    "fist":      ("🤜", "FIST"),
    "open_palm": ("🖐", "PALM"),
    "peace":     ("✌️", "PEACE"),
    "point_up":  ("☝️", "POINT"),
    "thumbs_up": ("👍", "THUMB"),
    "rock":      ("🤘", "ROCK"),
}

# Time limits (seconds per sign)
TIME_PER_SIGN = {
    "JUTSU":    5.0,
    "ULTIMATE": 4.0,
}

# Webcam index (0 = default/droidcam, 1 = external/usb)
CAMERA_INDEX = 1
