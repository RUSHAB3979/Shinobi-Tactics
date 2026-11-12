# Asset provenance

## New assets created 9 November 2026

- `sources/sasuke-poses.png`, `sources/tanjiro-poses.png`, `sources/itachi-poses.png`, and `sources/zenitsu-poses.png`: generated with the built-in imagegen tool for this project. Brief: coherent transparent 4×4 body-pose sheets for idle, anticipation, strike, recovery, casting, healing, recoil, guard, defeat, and victory; sharp pixel art; consistent outfits; no external VFX. Zenitsu received a cleanup edit for halo/gutter artifacts. These are retained source masters, not fetched sprite packs.
- `curated/*/pose_*.png`: deterministic atlas extraction and nearest-neighbor export from those masters, using `tools/export_sprites.py`. Crop exceptions and alpha quantization are recorded in that tool. Source art remains unchanged.
- `arena.png`: generated with the built-in imagegen tool. Brief: restrained moonlit Japanese shrine courtyard, open diagonal stone plaza, low-contrast forest, no characters or HUD.
- `audio/generated/*.wav`: original synthesized cues authored for this project by `tools/build_audio.py`; fixed random seeds, standard-library waveform generation, no sampled recordings.
- Move icons and layered combat effects: code-native Pygame drawing in `client.py` and `battle_visuals.py`.

Sasuke and Itachi depict characters from Naruto; Tanjiro and Zenitsu depict characters from Demon Slayer. This provenance record does not assert ownership of those underlying characters or grant rights to their IP.

## Power upgrade — 10 November 2026

- `sources/powers/{sasuke,itachi,tanjiro,zenitsu}.png`: generated with the built-in imagegen tool, using each existing pose master as a visual reference. Each has 16 sequential body drawings: eight for Jutsu and eight for Ultimate, with coherent costume, facing, and fixed scale. Sasuke explicitly uses bare hands and a sheathed sword for Chidori. The exporter removes low-alpha quantization noise, preserves original masters, records reviewed gutter splits for Tanjiro and Zenitsu swords, and authors hand/weapon attachment points.
- `sources/powers/kirin.png`: generated and edited with the built-in imagegen tool as an eight-frame lightning-dragon apparition/strike/dispersal sheet. The selected edit retains opaque horns/jaws inside transparent cell gutters. An earlier crowded variant was rejected and is not a runtime source.
- `curated/*/powers/*.png`, `vfx/kirin/*.png`: deterministic extraction with `tools/export_powers.py`. No third-party sprite/video downloads were used. Google Flow was available but not needed for this in-engine animation workflow.
- `power_visuals.py`: original procedural crows/wing cycles, illusion moon, lightning, water vortex, flame ribbons, six slash accents, Godspeed draw-cut, afterimages, and impact choreography. `tools/build_audio.py` adds eight distinct layered release-to-impact power cues; all are synthesized, not sampled recordings.

## Existing repository material

Original character folders, MP3s, model, and videos came from the repository at commit `31925a14750a374277ce103ece253b8f611199a8`. Their original authors and licenses were not supplied in the repository. They have not been relabeled as original or licensed replacements. Legacy character folders and MP3s are preserved and excluded from runtime use. The optional existing Sasuke/Itachi intro and MediaPipe model remain available; the large unused Genjutsu video is not needed by the new build.

The repository's existing ownership and licensing terms are not changed by this file. No third-party sprite downloads were introduced.

## Downloaded audio — 10 November 2026

The runtime now prefers 63 sampled cues built from 46 retained masters. `audio/combat.json` records each master, original filename, source page, uploader/author, license status, checksum, and every edit recipe. Full download/archive checksums and original-source links are included in the audio delivery. `docs/audio-research.md` lists exact per-move coverage and unverified voice gaps.

StarNinjas sword attacks/clashes, rubberduck 100 CC0 SFX #2, and Augmentality (Brandon Morris; submitted by HaelDB) spell sounds are used under the CC0 option shown on their OpenGameArt source pages. Those sampled effects are distinct from the project's original synthesized fallbacks.

Itachi's English recordings come from Ultimate Ninja Storm 4 (CyberConnect2 / Bandai Namco), archive uploaded by bigbingchillin. Tanjiro, Hinokami Tanjiro, Zenitsu Entertainment District English voices and selected battle effects come from The Hinokami Chronicles 2 (CyberConnect2 / Aniplex), archives uploaded by Theoracle1185. Game/voice recordings retain their underlying copyright; uploader credit is not a rights grant. Source terms restrict commercial and marketplace use. This local prototype integration does not assert public-release clearance or ownership of the recordings. No AI voice imitation was used.

Sasuke has no newly selected English voice. Itachi's Genjutsu/Tsukuyomi lines are general battle dialogue, not named callouts. See the manifest and research record rather than assuming every voice is an exact named attack.


## Original impact layers — 10 November 2026

`audio/impact/*.wav`: seven original synthesized contact layers (slash, electricity, thunder, water, fire, illusion and counter), reproducibly generated by `tools/build_impact_audio.py` with seeded noise and oscillators. These contain no sampled performance and do not change the rights/status of the separate downloaded recordings.


## Visual glowup — 10 November 2026

`arena-glowup.png`: original environment generated using the built-in image-generation tool. Prompt, research links and composition decisions are recorded in `docs/glowup-art-direction.md`; the previous arena remains available. `fonts/SpaceGrotesk-Bold.otf`: unmodified Space Grotesk, SIL Open Font License 1.1; copyright and full terms in `fonts/OFL-SpaceGrotesk.txt`.
