# Asset audit and migration decisions

Base commit: `31925a14750a374277ce103ece253b8f611199a8`. Checkout branch: `improve-animation-assets`.

The upstream tree contains 2,192 PNGs (687,356,137 bytes), and approximately 745 MB total files. A filtered sparse checkout materialized 1,221 PNGs totaling about 15 MB, the Python modules, four original MP3s, the small intro, and MediaPipe model. All upstream asset hashes were compared to the planning snapshot and are unchanged. `upstream-assets.json` records every original asset path, Git blob hash, and byte size. `asset-inventory.json` records local dimensions, alpha bounds, hashes, order/gaps, duplicates, missing mappings, and unmaterialized paths.

## Findings

- Sasuke `idle` switches from idle into running poses. `attack_1` includes effect-only fragments and source-style changes; it cannot be treated as a contiguous body animation.
- Sasuke `kirin` local frames mix fire, lightning, and smoke fragments. The original loader fits each fragment to a character's full height.
- Healing folders contain UI/HP bars and effect strips. Natural numeric order is also broken by lexical sorting beyond frame 99.
- Zenitsu `sixfold` contains detached lightning pieces. `idle_new` and several new large frames have a different style/resolution from the earlier pixel bodies.
- Tanjiro `special_1` includes frames containing several tiny poses/fragments in one image. Missing ultimate/hit/guard/down/victory folders are silent failures in the original player.
- A shared mutable player causes mirror-match actors to overwrite and double-update one another.
- Reaction, particles, sound, and damage feedback start immediately on state receipt. Terminal state messages skip battle presentation entirely.
- Large eager loads, per-frame size fitting, and arbitrary caps compound these errors. Removing the caps without curation would expose more corrupted sequences.

`legacy-review.json` names the sequences actually inspected and distinguishes complete local reviews from subset reviews. Numbered sheets are reproducible with `tools/audit_assets.py`. **971 original PNGs were not downloaded or visually reviewed, and many other legacy sheets remain unreviewed.** Their filenames and dimensions are not being treated as evidence of animation correctness. No blanket artwork-quality classification or deletion was applied to that material.

## Chosen migration

All original sprite folders are quarantined from runtime loading. Each mapped action now has a reviewed replacement from a retained generated pose master. There are 64 exported poses and 59 referenced body poses across 36 required clips. The unused overhead source cell is not accepted as a runtime frame. Per-sheet scale, body anchors, source facing, explicit order/durations, and release/impact markers are recorded in `assets/animations.json`.

The replacement body track contains no legacy fragments or UI. Projectiles and elemental effects are separate code-native tracks. Healing uses an actual kneeling recovery body pose and green effect track. Defeat/victory are intentional terminal poses. The source masters and exporter support further pose refinement without destroying originals.

This adapts Astra's full legacy-frame audit step: exhaustive inspection of retired, unreferenced source collections is deferred, while all runtime replacements are reviewed and validated. The unchecked legacy-audit item remains visible in `plan.md`; no implementation quality claim depends on those unseen images.

## Runtime and media references

The game loads only the manifest body frames, new arena, generated WAV cues, and optionally the existing `Sasuke vs Itachi starting scene.mp4`. Old `CHARACTERS.anim_map` values are preserved only for audit tooling. Stale ultimate-video names and their blocking playback paths were removed. The unused 49 MB Genjutsu video is unnecessary for the new presentation.

The four original MP3s remain untouched; new move/release/impact/heal/block cues cover all characters. MediaPipe and its model remain optional. Missing dependencies cause live hand-sign moves to miss and leave offline asset review available.

The compact build omits original sprite folders, unused MP3s, and the large unused video. The patch preserves them in the Git repository. This separates runtime download size from decoded memory; it does not claim the source repository has been reduced by deleting originals.

See `verification.md` for measured results and remaining physical-device checks.
