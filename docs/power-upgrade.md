# Power-animation upgrade — 10 November 2026

This pass addresses Astra's three presentation findings and expands all eight power moves. The runtime uses new drawn sprite sequences and layered animation in Pygame, with no cinematic decoder or network-blocking playback loop.

## Review findings resolved

| Finding | Change | Evidence/check |
| --- | --- | --- |
| Chidori contacts with the katana pose | Separate eight-pose bare-hand sequence, sheathed sword, palm socket for charge and contact | Regression checks the contact frame, absence of weapon attachment, hand position, movement, and mirroring; Chidori phase sheet/reel |
| Reduced motion swings across the arena | Intentional cut to the contact position, no traversal/afterimages/shake; dimmed effects and slower crow/water motion | Both-side contact regression and all-power reduced-motion exports |
| Tsukuyomi shares Genjutsu's eye effect | Genjutsu has a crow swarm, wing cycles, target eye and the existing counter shield; Tsukuyomi has a slow red-black scene fade, red moon, illusion pillars, eye seal and petals | Rendered distinction test in both motion modes; separate phase sheets and GIFs |

## Move choreography

| Move | Body and effect sequence |
| --- | --- |
| Chidori | Seal → lowered hand charge → low sprint → open-palm thrust → recovery; hand-bound lightning, charge branches and approach trail |
| Kirin | Seal → raised summon → sky-point hold → downward command; charged storm bank, eight-frame descending lightning dragon, branching contact strike and dispersal |
| Genjutsu | Seal → finger point → release → retract; animated crows, target eye distortion, and persistent authoritative shield state |
| Tsukuyomi | Uncover eye → commanding palm → recovery; red moon, restrained scene fade, illusion pillars and target seal; no rapid alternating screen flash |
| Whirlpool | Breath → low sword coil → sweeping cut → follow-through; rotating layered water ribbons, foam, and blade-tip spray |
| Sun Breath | Breath → overhead windup → forward cut → low finisher; warm flame ribbons, white-hot arc and blade-bound embers |
| Sixfold | Sheath grip → low launch → draw cut → resheath; six ordered slash/lightning accents during approach, one server impact |
| Godspeed | Deep crouch → explosive sprint → broad draw cut → resheath; afterimages, a pressure trail and one decisive lightning arc |

All powers have eight unique body poses, explicit durations/markers, per-frame hand sockets, and weapon sockets where applicable. New exports add 64 body frames and eight dragon frames. The entire runtime now references 116 body images across the existing 36 clips. Source masters and extraction rules are retained. Each power also has a distinct synthesized release-to-impact sound cue; sound design is reproducible and does not use downloaded recordings.

## Validation and limits

- 29 automated tests include the eight new power regressions, plus existing queue, HP, terminal state, camera/dependency fallback, and duplicate-action checks.
- `tools/verify_powers.py`: 96 presentation cases (eight powers × two sides × two motion modes × hit/miss/reflection), 16 normal/reduced GIFs, eight six-phase sheets and a combined actual-renderer reel.
- `tools/verify_matrix.py`: all 32 character/move/side cases; tests state completion and exports battle images/GIFs.
- `tools/verify_battle.py`: real loopback server and two TCP clients for each character mirror match and the Itachi/Sasuke reflection scenario. These supplement fixtures and do not exercise physical hand recognition.
- Runtime asset validation covers body images, attachment bounds, eight dragon images, WAVs and arena. No body frame comes from the quarantined legacy folders.

All tests are headless. Physical camera accuracy, audible playback quality on the user's speakers, compositor/vsync behavior, and positive optional-intro decoding remain device checks. The eight poses per power are authored key-pose animation with continuous movement/effects between them; this does not claim a new hand-drawn sprite at every 60 Hz display update. Review normal and reduced clips at actual game size when judging final feel.

Regenerate after art changes in this order: base `export_sprites.py` for each changed base character, `export_powers.py`, `build_audio.py`, tests/asset validation, power and battle previews. Do not run only the base exporter and expect the power overrides to remain applied.
