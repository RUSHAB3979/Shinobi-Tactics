> Historical pass: superseded by the technique-specific choreography implementation. Portrait pre-roll is no longer used by the match client. See `choreography-implementation.md`.

# Special attack cinematics

All four fighters now have a character portrait intro for both Jutsu and Ultimate. Jutsu intros last 1.05 seconds; Ultimate intros last 1.45 seconds. Sasuke and Itachi transition to an opening eye with animated Sharingan / Mangekyou iris highlights. Tanjiro uses flowing elemental arcs, and Zenitsu uses a closed-eye concentration portrait with lightning. Portrait shutter, directional drift and exit wipe are disabled in reduced motion, which keeps a stationary fading portrait and open eye.

The queue emits a new `perform` marker after the intro. Actor and effect clocks begin there; release and contact retain their original offsets relative to the body animation. The start voice plays during the intro. Visible health still changes only at the single authoritative impact event. No balance or server changes. Cut-ins stop on rematch/disconnect and remain below health bars and above command buttons.

Melee specials gain a backward weight shift before release; Tanjiro follows a short airborne sword arc and lands at contact. Existing socket attachment, lightning dragon, crows, elemental trails and impact effects remain in the sequence.

## Reference research

- https://naruto-official.com/en/news/01_1909 — developers describe distinct facial expressions, grounded firing posture, and progressive technique scale. Used as direction for portrait-to-attack staging.
- https://naruto-official.com/en/news/01_1719 — developers describe individualized motion, impact freeze frames and element-specific effects. Used as direction for distinct water/fire/lightning/illusion treatments.

These references informed the design; their images and footage were not copied into the game.

## Artwork

Four original AI-generated portrait keyframes created with the built-in image generation tool on 2026-11-14. Stored in `assets/cinematics/`. They depict existing fictional characters; they are not official game artwork. Runtime code animates framing, elemental overlays and a magnified eye detail with an opening shutter; these are not newly hand-drawn full-body frame sequences or 3D cinematics.

Prompt set: `assets/cinematics/prompts.json`. No added runtime dependencies. Pygame caches a single resized portrait per character; rendering does not resize it every frame.

## Review

`agent-env .venv/bin/python -m unittest discover -s tests -q`

`agent-env .venv/bin/python tools/preview_battle.py` opens the explicitly labelled offline art preview (N switches character, 2 Jutsu, 3 Ultimate, Tab switches side, R reduced motion). The regular server/client game uses the same renderer.

`tools/verify_feedback.py` exports 96 side/motion/outcome cases and 16 gameplay-renderer clips with audio reconstructed from event timestamps. This is distinct from live speaker capture.
