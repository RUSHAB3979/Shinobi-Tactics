"""
extract_sprites.py  –  Full Animation Extraction (Fast, numpy-based)
Extracts ALL animation frames from each JUS sprite sheet.
Outputs: assets/<character>/<anim_name>/frame_XX.png

Run once:  python extract_sprites.py
"""

import os
import shutil
import numpy as np
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1, 1))

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
os.makedirs(ASSETS, exist_ok=True)

BG_THRESHOLD = 60
SPRITE_SCALE = 3  # 3x scale for JUS sprites


# ═══════════════════════════════════════════════════════════════════
#  FAST NUMPY HELPERS
# ═══════════════════════════════════════════════════════════════════

def load_sheet_array(path):
    """Load sprite sheet as numpy RGBA array (H, W, 4)."""
    surf = pygame.image.load(path).convert_alpha()
    arr = pygame.surfarray.pixels3d(surf)     # (W, H, 3)
    alpha = pygame.surfarray.pixels_alpha(surf)  # (W, H)
    # Combine into (H, W, 4)
    rgba = np.zeros((arr.shape[1], arr.shape[0], 4), dtype=np.uint8)
    rgba[:, :, :3] = np.transpose(arr, (1, 0, 2))
    rgba[:, :, 3] = alpha.T
    del arr, alpha  # release surface locks
    return rgba, surf


def make_fg_mask(rgba, bg_rgb):
    """Return boolean mask (H, W) where True = foreground pixel."""
    bg = np.array(bg_rgb, dtype=np.int16)
    diff = np.abs(rgba[:, :, :3].astype(np.int16) - bg)
    dist = diff.sum(axis=2)  # colour distance
    return (dist >= BG_THRESHOLD) & (rgba[:, :, 3] > 30)


def find_row_bands(mask, min_pixels=5):
    """Find contiguous horizontal bands with content."""
    row_counts = mask.sum(axis=1)  # pixels per row
    has_content = row_counts >= min_pixels

    bands = []
    in_band = False
    start = 0
    for y in range(len(has_content)):
        if has_content[y] and not in_band:
            start = y
            in_band = True
        elif not has_content[y] and in_band:
            bands.append((start, y - 1))
            in_band = False
    if in_band:
        bands.append((start, len(has_content) - 1))
    return bands


def find_col_bands(mask_slice, gap_threshold=3):
    """Find contiguous vertical bands (columns) with content in a horizontal slice."""
    col_counts = mask_slice.sum(axis=0)  # pixels per column
    has_content = col_counts > 0

    sprites = []
    in_sprite = False
    start = 0
    gap = 0

    for x in range(len(has_content)):
        if has_content[x]:
            if not in_sprite:
                start = x
                in_sprite = True
            gap = 0
        else:
            gap += 1
            if in_sprite and gap >= gap_threshold:
                end = x - gap
                sprites.append((start, end))
                in_sprite = False

    if in_sprite:
        sprites.append((start, len(has_content) - 1))
    return sprites


def extract_sprite_rects(mask, y0, y1, x_start=0, x_end=None, gap=3):
    """Find individual sprite bounding boxes in a band."""
    if x_end is None:
        x_end = mask.shape[1]

    band_mask = mask[y0:y1 + 1, x_start:x_end]
    col_bands = find_col_bands(band_mask, gap_threshold=gap)

    rects = []
    for cx0, cx1 in col_bands:
        # Find tight vertical bounds within this column range
        sub = band_mask[:, cx0:cx1 + 1]
        row_has = sub.any(axis=1)
        ys = np.where(row_has)[0]
        if len(ys) == 0:
            continue
        ty = ys[0]
        by = ys[-1]
        pad = 1
        rects.append((
            max(0, x_start + cx0 - pad),
            max(0, y0 + ty - pad),
            cx1 - cx0 + 1 + pad * 2,
            by - ty + 1 + pad * 2,
        ))
    return rects


def crop_and_clean(rgba, rect, bg_rgb, scale=SPRITE_SCALE):
    """Crop, remove bg, scale up, return pygame Surface."""
    x, y, w, h = rect
    # Clamp
    H, W = rgba.shape[:2]
    x2 = min(x + w, W)
    y2 = min(y + h, H)
    x = max(0, x)
    y = max(0, y)
    w = x2 - x
    h = y2 - y
    if w <= 0 or h <= 0:
        return None

    crop = rgba[y:y2, x:x2].copy()

    # Remove bg
    bg = np.array(bg_rgb, dtype=np.int16)
    diff = np.abs(crop[:, :, :3].astype(np.int16) - bg).sum(axis=2)
    is_bg = diff < BG_THRESHOLD
    crop[is_bg, 3] = 0

    # Convert to pygame surface
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # Write pixel data
    px_arr = pygame.surfarray.pixels3d(surf)
    px_arr[:, :, :] = np.transpose(crop[:, :, :3], (1, 0, 2))
    del px_arr
    alpha_arr = pygame.surfarray.pixels_alpha(surf)
    alpha_arr[:, :] = crop[:, :, 3].T
    del alpha_arr

    # Scale up
    scaled = pygame.transform.scale(surf, (w * scale, h * scale))
    return scaled


def save_frames(frames, char_name, anim_name):
    """Save frames to assets/<char>/<anim>/frame_XX.png"""
    out_dir = os.path.join(ASSETS, char_name, anim_name)
    os.makedirs(out_dir, exist_ok=True)
    saved = 0
    for i, surf in enumerate(frames):
        if surf is None:
            continue
        path = os.path.join(out_dir, f"frame_{i:02d}.png")
        pygame.image.save(surf, path)
        saved += 1
    return saved


# ═══════════════════════════════════════════════════════════════════
#  CHARACTER EXTRACTORS
# ═══════════════════════════════════════════════════════════════════

def extract_character(sheet_filename, bg_rgb, char_name, anim_names,
                      x_scan_end=None, min_band_height=20, max_band_height=None,
                      skip_first_n_bands=0, gap_threshold=3):
    """Generic extraction for a JUS sprite sheet."""
    path = os.path.join(BASE, sheet_filename)
    if not os.path.isfile(path):
        print(f"  [SKIP] {sheet_filename} not found")
        return 0

    rgba, surf = load_sheet_array(path)
    h, w = rgba.shape[:2]
    print(f"  Sheet: {w}x{h}")

    # Create mask (optionally limit x range for scan)
    if x_scan_end:
        scan_mask = make_fg_mask(rgba[:, :x_scan_end], bg_rgb)
        # Pad to full width for extraction
        full_mask = make_fg_mask(rgba, bg_rgb)
    else:
        scan_mask = make_fg_mask(rgba, bg_rgb)
        full_mask = scan_mask

    # Find row bands
    bands = find_row_bands(scan_mask, min_pixels=5)
    print(f"  Raw bands: {len(bands)}")

    # Split tall bands into sub-bands
    refined = []
    for y0, y1 in bands:
        ht = y1 - y0 + 1
        if ht > 100:
            # Find internal empty rows (rows with <3 fg pixels)
            band_rows = scan_mask[y0:y1 + 1].sum(axis=1)
            sub_start = 0
            in_sub = False
            found_split = False
            for ry in range(len(band_rows)):
                if band_rows[ry] >= 3:
                    if not in_sub:
                        sub_start = ry
                        in_sub = True
                else:
                    if in_sub and ry - sub_start > 10:
                        refined.append((y0 + sub_start, y0 + ry - 1))
                        found_split = True
                    in_sub = False
                    sub_start = ry + 1
            if in_sub and len(band_rows) - sub_start > 10:
                refined.append((y0 + sub_start, y1))
                found_split = True

            # If no splits found (dense grid), estimate row height
            # from the first sprite's bounding box and split evenly
            if not found_split:
                print(f"  Dense grid detected (y={y0}-{y1}, {ht}px). Estimating rows...")
                # Find height of first sprite
                first_rects = extract_sprite_rects(full_mask, y0, min(y0 + 120, y1), gap=gap_threshold)
                if first_rects:
                    row_h = first_rects[0][3] + 4  # sprite height + small gap
                    print(f"  Estimated row height: {row_h}px")
                    for ry in range(y0, y1, row_h):
                        refined.append((ry, min(ry + row_h - 1, y1)))
                else:
                    refined.append((y0, y1))
        else:
            refined.append((y0, y1))

    # Filter: skip labels (<min_band_height) and skip first N bands
    sprite_bands = []
    for y0, y1 in refined:
        ht = y1 - y0 + 1
        if ht < min_band_height:
            continue
        if max_band_height and ht > max_band_height:
            continue
        sprite_bands.append((y0, y1))

    if skip_first_n_bands > 0:
        sprite_bands = sprite_bands[skip_first_n_bands:]

    print(f"  Animation rows: {len(sprite_bands)}")

    total = 0
    for i, (y0, y1) in enumerate(sprite_bands):
        name = anim_names[i] if i < len(anim_names) else f"anim_{i:02d}"
        rects = extract_sprite_rects(full_mask, y0, y1,
                                     x_end=x_scan_end, gap=gap_threshold)
        if not rects:
            continue
        frames = [crop_and_clean(rgba, r, bg_rgb) for r in rects]
        frames = [f for f in frames if f is not None]
        if not frames:
            continue
        n = save_frames(frames, char_name, name)
        total += n
        print(f"  {name}: {n} frames (y={y0}-{y1})")

    # Copy first idle frame as backward-compat idle.png
    idle_dir = os.path.join(ASSETS, char_name, "idle")
    dest = os.path.join(ASSETS, f"{char_name}_idle.png")
    if os.path.isdir(idle_dir):
        files = sorted(os.listdir(idle_dir))
        if files:
            shutil.copy2(os.path.join(idle_dir, files[0]), dest)

    return total


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    # ── SASUKE ─────────────────────────────────────────────────────
    print("\n=== SASUKE ===")
    n = extract_character(
        "DS _ DSi - Jump Ultimate Stars - Fighters - Sasuke Uchiha.png",
        bg_rgb=(128, 128, 255),
        char_name="sasuke",
        anim_names=[
            "idle", "walk", "run", "jump", "fall",
            "crouch", "dodge", "guard", "hit", "down",
            "attack_1", "attack_2", "attack_3", "attack_combo",
            "special_1", "special_2", "special_3", "chidori_charge",
            "chidori", "chidori_run",
            "air_attack", "air_special",
            "grab", "throw", "victory", "taunt",
        ],
        min_band_height=15,
        gap_threshold=2,
    )
    print(f"  SASUKE TOTAL: {n} frames")

    # ── TANJIRO ────────────────────────────────────────────────────
    print("\n=== TANJIRO ===")
    n = extract_character(
        "kamado_tanjiro_jus_sprite_by_imhomiejaydev_df2yz5i.png",
        bg_rgb=(173, 216, 230),
        char_name="tanjiro",
        anim_names=[
            "idle", "run", "dash", "down_slash",
            "crouch", "attack_1", "attack_2", "water_surface",
            "attack_3", "special_1", "special_2",
            "air_attack", "air_special",
            "hit", "down", "guard", "ultimate",
            "grab", "throw", "victory",
        ],
        min_band_height=15,
        gap_threshold=3,
    )
    print(f"  TANJIRO TOTAL: {n} frames")

    # ── ITACHI ─────────────────────────────────────────────────────
    print("\n=== ITACHI ===")
    n = extract_character(
        "itachi___jump_ultimate_stars__free_version__by_ichinaruke95_dj8cln6.png",
        bg_rgb=(0, 128, 0),
        char_name="itachi",
        anim_names=[
            "idle", "intro", "walk", "run",
            "attack_1", "attack_2", "attack_combo",
            "fireball_start", "fireball", "fireball_run",
            "genjutsu_start", "genjutsu",
            "shuriken", "shuriken_run",
            "special_1", "special_2",
            "jump", "air_attack",
            "hit", "down", "guard",
            "grab", "throw", "tsukuyomi",
            "susanoo", "susanoo_attack",
            "taunt", "victory",
        ],
        x_scan_end=600,
        min_band_height=15,
        gap_threshold=3,
    )
    print(f"  ITACHI TOTAL: {n} frames")

    # ── ZENITSU ────────────────────────────────────────────────────
    print("\n=== ZENITSU ===")
    n = extract_character(
        "zenitsu_agatsuma_jus___sprite_sheet_by_pedronickmugen_dekskha.png",
        bg_rgb=(0, 128, 0),
        char_name="zenitsu",
        anim_names=[
            "idle", "run", "dash", "jump", "guard",
            "hit", "down", "ultimate",
            "attack_b", "forward_b", "down_b", "up_b",
            "attack_y", "forward_y", "up_y", "down_y",
            "jump_b", "jump_y",
            "koma_attack", "victory",
        ],
        x_scan_end=500,
        min_band_height=25,
        max_band_height=80,
        skip_first_n_bands=0,
        gap_threshold=3,
    )
    print(f"  ZENITSU TOTAL: {n} frames")

    print("\nDone! Check assets/<character>/<animation>/ folders.")
    pygame.quit()
