# Shinobi Tactics

A two-player, turn-based Pygame battle game featuring Sasuke, Tanjiro, Itachi, and Zenitsu. Each power has a registered body sequence of eight to twelve distinct poses, attached elemental effects, and synchronized impact feedback. Chidori uses a bare-hand charge and thrust; Kirin descends as an animated lightning dragon; Genjutsu sends crows and grants the counter shield; Tsukuyomi stages a red-moon illusion. Whirlpool, Sun Breath, Sixfold, and Godspeed have separate sword/dash choreography. Reduced motion keeps contact readable with a cut to the contact position.

## Setup

Use Python 3.12 and uv. `.python-version`, `pyproject.toml`, and `uv.lock` install packages into `.venv`, not system Python or Conda base. On the KARMA workstation, prefix commands with `agent-env` for the predictable tool environment.

```bash
uv sync --frozen
```

The core build needs no webcam or video package. Enable hand-sign recognition with `uv sync --frozen --extra camera`. The MediaPipe model `hand_landmarker.task` belongs beside `client.py` and is included in the repository/build. Set `CAMERA_INDEX` in `hand_sign_config.py` for your webcam. Optional intros use `uv sync --frozen --extra video`; ffpyplayer is no longer required. Install both extras together if using both.

## Review the art immediately

```bash
uv run --frozen python tools/preview_battle.py
```

This offline review uses fixtures and never connects to a server or opens a camera. **1–4** play Attack/Jutsu/Ultimate/Heal, **N** changes character, **Tab** changes attacking side, **Space** pauses, **M** toggles sound, **R** toggles reduced motion, **Esc** quits.

For frame inspection:

```bash
uv run --frozen python tools/preview_animations.py
```

Tab selects character, Up/Down selects clip, Space pauses, Left/Right steps frames, F flips, B toggles root/bounds, R restarts, and +/- changes speed. Export GIFs and comparison sheets with `--export work/previews`.

## Play a network match

Start the server, then open two clients and connect to `localhost` (or the host's LAN address):

```bash
uv run --frozen python server.py
uv run --frozen python client.py
```

Run the client command in a second terminal for the other player. The server defaults to port 5555. For local-only hosting use `SHINOBI_HOST=127.0.0.1`; `SHINOBI_PORT` selects another server port for verification tools. The normal client uses port 5555.

Select a character and click a move button on your turn. Attack deals 15 damage, Jutsu 25, Ultimate 50, and Recover restores up to 20 HP. Itachi's Jutsu is available once and grants the existing reflection shield. Damage and turn decisions remain server-authoritative.

Jutsu and Ultimate require the configured hand signs. Missing camera dependencies/model or a failed challenge cause a miss. Offline art review previews those moves without a webcam; live play does not silently bypass the challenge.

In the client, **M** toggles sound, **+/-** adjusts volume, **R** enables reduced motion, and **V** enables optional intros (off by default). The existing Sasuke/Itachi intro is silent and skippable with Esc. Missing media/OpenCV falls back to battle. Combat ultimates use in-engine presentation and need no videos.

Both clients and server must use this version: snapshots now contain match and action IDs so duplicate state messages cannot replay a move.

## Downloaded combat audio

All 12 offensive moves and four recoveries use sampled effects, with 11 English voice clips across Itachi, Tanjiro and Zenitsu plus the user-supplied Chidori callout for Sasuke. Kirin remains effects-only; the supplied Chidori recording's language and original rights were not independently verified. Itachi's Genjutsu/Tsukuyomi use general battle lines. See `docs/audio-research.md` for exact coverage, sources and rights status. Game-rip recordings are not represented as CC0 or cleared for public release.

`combat_audio.py` separates voices, charge/release and contact, ducks effects under speech, and keeps longer lines audible during recovery. Existing M mute and +/- volume apply to both. Rebuild the sampled WAVs with `uv run --frozen python tools/import_combat_audio.py` (FFmpeg required only for rebuilding). The game has no speech-recognition or FFmpeg runtime dependency.

## Asset workflow

- `assets/sources/`: retained pose-sheet masters, including the new 4×3 technique sheets.
- `assets/curated/`: exported body poses used by the game.
- `assets/animations.json`: ordered clips, durations, anchors, facing, event markers.
- `assets/sources/powers/`: new power-pose sheets and the Kirin effect master.
- `assets/sources/choreography/`: new body source sheets, registration data and retimed clip definitions.
- `tools/export_choreography.py`: reproduce the current technique export after the base power exporter.
- `assets/vfx/kirin/`: eight exported dragon effect frames.
- `power_visuals.py`: move-specific choreography, hand/weapon attachments, trails, illusions, elements, and impacts; re-exported by `battle_visuals.py`.
- `assets/audio/generated/`: reproducible fallback WAV cues.
- `assets/audio/sampled/`, `assets/audio/combat.json`: sampled combat audio and per-move source recipes.
- `assets/sources/audio/`: selected downloaded masters with checksums in the audio manifest.
- `assets/arena.png`: cached battle environment.
- `docs/asset-audit.md`: findings and quarantine decisions.
- `docs/animation-format.md`: timing contract and schema.
- `assets/ATTRIBUTION.md`: provenance.

Original sprite folders remain untouched in a full Git checkout. The new runtime never loads those mixed folders. The compact ZIP omits them and the unused large Genjutsu video; it includes runtime assets, sources, tooling, docs, and the optional small intro/model.

```bash
uv run --frozen python tools/export_sprites.py Sasuke
uv run --frozen python tools/export_powers.py
uv run --frozen python tools/build_audio.py
uv run --frozen python tools/validate_assets.py
```

Export each base character after changing its source sheet, then run `export_powers.py` to apply the power clips from their separate masters. Inspect changed frames, pivots, and attachment points. Do not fit each pose independently to a fixed height or map unreviewed folders to actions.

## Verification

```bash
uv run --frozen python -m unittest discover -s tests -v
uv run --frozen python tools/verify_battle.py
uv run --frozen python tools/verify_battle.py --reflection --output work/reflection
uv run --frozen python tools/verify_matrix.py
uv run --frozen python tools/verify_powers.py
uv run --frozen python tools/benchmark_render.py
```

`verify_battle.py` starts a temporary loopback server and two real TCP clients, verifies impact timing and terminal transitions, and exports proof frames/GIF. Use `--character Tanjiro`, `Itachi`, or `Zenitsu` for other mirror matches. The matrix covers all four moves for all four characters on both sides. Headless SDL checks do not establish live display/vsync, audible speaker output, or webcam accuracy.

`verify_powers.py` covers all eight powers × both sides × normal/reduced motion × hit/miss/reflection (96 cases). It exports normal and reduced-motion GIFs, six-phase contact sheets, and a combined reel under `work/powers/`. These fixtures test presentation; the network tool tests the real server protocol. See `docs/power-upgrade.md` for the review fixes and remaining device checks.

`tools/audit_assets.py` inventories local legacy PNGs, writes numbered contact sheets, and records gaps, duplicates, missing mappings, and sparse files. `tools/capture_baseline.py` requires Git and the original sparse source subset; recorded baseline metrics do not represent the full 745 MB tree.

See `plan.md` and `docs/verification.md` for measurements and remaining manual checks.


### Battle impact preview

The updated battle renderer shakes the complete world at contact while keeping the HUD steady. Powers have stronger hit pauses, knockback, shockwaves and elemental aftermath; illusions use inward shards. Sound uses recorded effects and available English voices with seven original low impact layers and directional contact audio. Press R for reduced motion, M to mute, and +/- for volume.

For offline review: `uv run --frozen python tools/preview_battle.py` (N character, 1–4 moves, Tab side, Space pause). Run `uv run --frozen python tools/verify_feedback.py` to reproduce the 96-case matrix and sixteen sound-aligned MP4 clips; this export tool requires FFmpeg, while gameplay does not. `docs/audio-research.md` records source terms and the remaining Sasuke/named-Itachi English voice gaps.


### Visual glowup

The current build uses the painted Shattered Shrine arena, foreground fighters, a top health HUD, technique banners and larger command cards. Elemental attacks illuminate their contact point and the floor. Space Grotesk ships with its OFL license. See `docs/glowup-art-direction.md` for the online research, exact art prompt and design decisions. The delivery's `glowup/index.html` is the latest preview; earlier galleries are historical comparisons.

### Technique choreography

Specials now begin with technique-specific body movement and effects: Chidori palm charge/thrust, Kirin sky formation/command/dive, illusions, rotational sword cuts and distinct thunder dashes. Reduced motion is available with `R`. See [implementation and reference notes](docs/choreography-implementation.md) and [current plan](plan.md).
