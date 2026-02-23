"""
hand_sign_ui.py  –  Pygame overlay for the hand-sign mini-game.

Opens the webcam, shows the required sign sequence, and gives the player
a time limit to perform each sign correctly via MediaPipe detection.
Returns True (success) or False (failure).
"""

import time
import math
import sys
import platform

import cv2
import pygame

from hand_signs import HandSignDetector
from hand_sign_config import SIGN_DISPLAY, TIME_PER_SIGN, CAMERA_INDEX


# ── Layout constants ──────────────────────────────────────────────
CAM_W, CAM_H = 640, 480
OVERLAY_PAD = 30

# Colours
_WHITE  = (240, 240, 240)
_BLACK  = (0, 0, 0)
_CYAN   = (0, 220, 240)
_GREEN  = (50, 220, 80)
_RED    = (220, 50, 50)
_GREY   = (120, 120, 140)
_DARK   = (20, 20, 30)
_YELLOW = (230, 200, 50)
_PANEL  = (25, 25, 40)

# Minimum hold time (seconds) – sign must be held steady to register
HOLD_TIME = 0.40


def run_hand_sign_challenge(
    screen: pygame.Surface,
    sign_sequence: list[str],
    action_type: str = "JUTSU",
) -> bool:
    """
    Blocking call — runs the hand-sign mini-game on *screen*.
    Returns True if the player completes all signs, False on timeout/failure.

    *sign_sequence*: list of sign names, e.g. ["fist", "peace", "point_up"]
    *action_type*:   "JUTSU" or "ULTIMATE" (controls time per sign)
    """
    if not sign_sequence:
        return True  # nothing required

    # ── Open webcam (try multiple backends on Windows) ─────────
    cap = None
    if platform.system() == "Windows":
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            attempt = cv2.VideoCapture(CAMERA_INDEX, backend)
            if attempt.isOpened():
                cap = attempt
                break
            attempt.release()
    if cap is None:
        cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        cap.release()
        # No webcam → show error and FAIL the challenge (attack misses)
        _show_camera_error(screen)
        return False

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

    detector = HandSignDetector()
    clock = pygame.time.Clock()

    scr_w, scr_h = screen.get_size()
    cam_x = (scr_w - CAM_W) // 2
    cam_y = (scr_h - CAM_H) // 2 - 20

    time_per_sign = TIME_PER_SIGN.get(action_type, 5.0)
    total_time = time_per_sign * len(sign_sequence)

    current_idx = 0                 # which sign we're waiting for
    start_time = time.time()
    hold_start = None               # when the correct sign started being held
    detected_sign = None
    success = False
    finished = False

    # Pre-render fonts once
    font_title = pygame.font.SysFont("Segoe UI", 36, bold=True)
    font_sign  = pygame.font.SysFont("Segoe UI", 28, bold=True)
    font_sm    = pygame.font.SysFont("Segoe UI", 20)
    font_big   = pygame.font.SysFont("Segoe UI", 52, bold=True)
    font_hint  = pygame.font.SysFont("Segoe UI", 22)

    # ── Main loop ─────────────────────────────────────────────────
    while not finished:
        dt = clock.tick(30) / 1000.0
        elapsed = time.time() - start_time
        remaining = max(0.0, total_time - elapsed)

        # ── Events ────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                cap.release()
                detector.release()
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                # ESC = give up
                finished = True
                success = False

        if finished:
            break

        # ── Timeout check ─────────────────────────────────────────
        if remaining <= 0:
            finished = True
            success = False
            break

        # ── Read webcam ───────────────────────────────────────────
        ret, frame = cap.read()
        if not ret:
            finished = True
            success = True  # camera died mid-challenge, be gracious
            break

        # Mirror the frame so it feels natural
        frame = cv2.flip(frame, 1)

        # ── Detect sign ───────────────────────────────────────────
        detected_sign, annotated = detector.detect(frame)

        # Check if detected sign matches the expected one
        expected = sign_sequence[current_idx]
        if detected_sign == expected:
            if hold_start is None:
                hold_start = time.time()
            elif time.time() - hold_start >= HOLD_TIME:
                # Sign held long enough – advance!
                current_idx += 1
                hold_start = None
                if current_idx >= len(sign_sequence):
                    finished = True
                    success = True
                    break
        else:
            hold_start = None

        # ── Render ────────────────────────────────────────────────
        # Dark overlay behind everything
        overlay = pygame.Surface((scr_w, scr_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # Title
        title = font_title.render("⚡ PERFORM HAND SIGNS ⚡", True, _CYAN)
        screen.blit(title, title.get_rect(center=(scr_w // 2, cam_y - 50)))

        # ── Webcam feed ───────────────────────────────────────────
        # Convert BGR → RGB, then to Pygame surface
        frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        # OpenCV frame is (H, W, 3) — pygame needs (W, H) so swapaxes
        cam_surf = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        # Border glow
        border_rect = pygame.Rect(cam_x - 4, cam_y - 4, CAM_W + 8, CAM_H + 8)
        pygame.draw.rect(screen, _CYAN, border_rect, width=3, border_radius=6)
        screen.blit(cam_surf, (cam_x, cam_y))

        # ── Sign sequence display (above cam) ─────────────────────
        seq_y = cam_y - 20
        total_seq_w = len(sign_sequence) * 80
        seq_start_x = (scr_w - total_seq_w) // 2

        for i, sname in enumerate(sign_sequence):
            sx = seq_start_x + i * 80
            emoji, label = SIGN_DISPLAY.get(sname, ("?", sname))

            if i < current_idx:
                # Completed
                col = _GREEN
                bg = (30, 80, 40)
            elif i == current_idx:
                # Current – pulse
                pulse = int(200 + 55 * math.sin(elapsed * 6))
                col = (0, pulse, 240)
                bg = (20, 40, 60)
            else:
                col = _GREY
                bg = (40, 40, 50)

            card = pygame.Rect(sx, seq_y - 65, 70, 60)
            pygame.draw.rect(screen, bg, card, border_radius=10)
            pygame.draw.rect(screen, col, card, width=2, border_radius=10)

            # Label text
            ltxt = font_sign.render(label, True, col)
            screen.blit(ltxt, ltxt.get_rect(center=(sx + 35, seq_y - 42)))

            # Check mark for completed
            if i < current_idx:
                check = font_sign.render("✓", True, _GREEN)
                screen.blit(check, check.get_rect(center=(sx + 55, seq_y - 60)))

            # Arrow between signs
            if i < len(sign_sequence) - 1:
                arr = font_sm.render("→", True, _GREY)
                screen.blit(arr, arr.get_rect(center=(sx + 75, seq_y - 42)))

        # ── Detected sign feedback (on webcam) ────────────────────
        if detected_sign:
            d_emoji, d_label = SIGN_DISPLAY.get(detected_sign, ("?", detected_sign))
            is_match = detected_sign == expected
            fb_col = _GREEN if is_match else _YELLOW
            fb_text = f"Detected: {d_label}"
            if is_match and hold_start:
                held = time.time() - hold_start
                pct = min(1.0, held / HOLD_TIME)
                fb_text += f"  ■ HOLD {int(pct * 100)}%"

            fb_surf = font_hint.render(fb_text, True, fb_col)
            fb_bg = pygame.Surface((fb_surf.get_width() + 20, fb_surf.get_height() + 10), pygame.SRCALPHA)
            fb_bg.fill((0, 0, 0, 160))
            screen.blit(fb_bg, (cam_x + 10, cam_y + CAM_H - 45))
            screen.blit(fb_surf, (cam_x + 20, cam_y + CAM_H - 40))
        else:
            no_hand = font_hint.render("Show your hand to the camera!", True, _RED)
            screen.blit(no_hand, (cam_x + 10, cam_y + CAM_H - 40))

        # ── Timer bar (below webcam) ──────────────────────────────
        bar_y = cam_y + CAM_H + 15
        bar_w = CAM_W
        bar_h = 18
        bar_rect = pygame.Rect(cam_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(screen, _DARK, bar_rect, border_radius=8)

        ratio = remaining / total_time
        fill_w = int(bar_w * ratio)
        if fill_w > 0:
            # Color: green → yellow → red as time runs out
            if ratio > 0.5:
                t = (ratio - 0.5) * 2
                bar_col = (int(230 * (1 - t)), 200, 50)
            else:
                t = ratio * 2
                bar_col = (220, int(50 + 150 * t), 50)
            fill_rect = pygame.Rect(cam_x, bar_y, fill_w, bar_h)
            pygame.draw.rect(screen, bar_col, fill_rect, border_radius=8)

        pygame.draw.rect(screen, _GREY, bar_rect, width=2, border_radius=8)

        # Timer text
        t_txt = font_sm.render(f"{remaining:.1f}s", True, _WHITE)
        screen.blit(t_txt, t_txt.get_rect(center=(cam_x + bar_w // 2, bar_y + bar_h // 2)))

        # ── ESC hint ──────────────────────────────────────────────
        esc = font_sm.render("Press ESC to cancel", True, _GREY)
        screen.blit(esc, esc.get_rect(center=(scr_w // 2, bar_y + 45)))

        pygame.display.flip()

    # ── Result flash ──────────────────────────────────────────────
    _show_result_flash(screen, success, font_big, clock)

    cap.release()
    detector.release()
    return success


def _show_result_flash(screen, success, font_big, clock):
    """Brief success / failure flash overlay."""
    scr_w, scr_h = screen.get_size()
    if success:
        text = "✅  SIGNS COMPLETE!"
        color = _GREEN
        bg_tint = (0, 60, 20, 180)
    else:
        text = "❌  SIGNS FAILED — MISS!"
        color = _RED
        bg_tint = (60, 0, 0, 180)

    for i in range(40):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        overlay = pygame.Surface((scr_w, scr_h), pygame.SRCALPHA)
        alpha = min(255, int(bg_tint[3] * (1 - i / 40)))
        overlay.fill((*bg_tint[:3], alpha))
        screen.blit(overlay, (0, 0))

        scale = 1.0 + 0.15 * math.sin(i * 0.3)
        txt = font_big.render(text, True, color)
        txt = pygame.transform.smoothscale(
            txt, (int(txt.get_width() * scale), int(txt.get_height() * scale))
        )
        txt_alpha = max(0, 255 - int(i * 6))
        txt.set_alpha(txt_alpha)
        screen.blit(txt, txt.get_rect(center=(scr_w // 2, scr_h // 2)))

        pygame.display.flip()
        clock.tick(60)


def _show_camera_error(screen):
    """Show an error overlay when the camera cannot be opened."""
    scr_w, scr_h = screen.get_size()
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("Segoe UI", 44, bold=True)
    font_med = pygame.font.SysFont("Segoe UI", 22)

    lines = [
        ("📷  CAMERA NOT FOUND", _RED, font_big),
        ("", None, None),
        ("Cannot open webcam — hand signs cannot be verified.", _WHITE, font_med),
        ("Attack will MISS.  Connect a camera and try again.", _YELLOW, font_med),
    ]

    for i in range(90):  # ~1.5 seconds at 60 fps
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                return  # any key to dismiss early

        overlay = pygame.Surface((scr_w, scr_h), pygame.SRCALPHA)
        fade = min(255, int(200 * min(1.0, i / 15)))
        overlay.fill((40, 0, 0, fade))
        screen.blit(overlay, (0, 0))

        y_offset = scr_h // 2 - 60
        for text, color, font in lines:
            if font is None:
                y_offset += 15
                continue
            pulse = 1.0 + 0.03 * math.sin(i * 0.2)
            txt = font.render(text, True, color)
            if font == font_big:
                txt = pygame.transform.smoothscale(
                    txt, (int(txt.get_width() * pulse), int(txt.get_height() * pulse))
                )
            screen.blit(txt, txt.get_rect(center=(scr_w // 2, y_offset)))
            y_offset += 45

        pygame.display.flip()
        clock.tick(60)
