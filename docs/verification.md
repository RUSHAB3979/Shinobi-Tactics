Chidori voice update (2026-11-11): user-supplied callout added. See sasuke-voice-update.md. Kirin remains effects-only.

# Verification record — updated 10 November 2026

## Current visual glowup — 10 November 2026

48 automated tests pass. All 96 power/outcome/side/motion combinations pass with the new foreground roots, light layers and HUD. Fresh real two-client TCP checks pass for Itachi/Sasuke reflection and Tanjiro healing, misses and lethal ultimates. New tests check command-title fit, bounded lighting texture caches and reduced-motion ambient suppression. Stable HUD tests now use the redesigned top health panels.

The final matrix measured median 3.103 ms, p95 5.620 ms and p99 6.902 ms per headless update/draw. Peak process RSS was 115.1 MiB. Encoding is excluded; compositor/vsync and physical speakers remain unverified. The latest sixteen MP4s and eight-power reel are in the delivery's `glowup/` gallery, with before/after and menu images. Research, asset provenance, exact generation prompt and composition rationale are in `docs/glowup-art-direction.md`.

The shipped font and new painted arena are validated along with the existing 36 clips, 116 body poses, eight Kirin frames and 94 WAV assets (63 sampled, 24 fallback, seven impact layers). There are no new runtime dependencies. Prior reports below preserve the earlier builds' evidence.

## Current battle impact build — 10 November 2026

45 automated tests pass, including hit/miss/reflection feedback, stable HUD pixels during camera recoil, reduced motion, bounded/cleared aftermath, contact audio/mute, and consistent camera time across a long frame versus 60 Hz steps. All 96 power × side × hit/miss/reflection × motion cases pass. Two real two-client TCP scenarios pass: Itachi/Sasuke reflection and Tanjiro healing/lethal ultimates. Earlier results below are historical measurements, not additional claims about this build.

Runtime assets validate: 36 clips, 116 body poses, eight Kirin frames, 63 sampled audio cues (11 English voice clips), 24 generated fallbacks and seven original impact layers. All eight powers have motion and distinct effects. Camera shake moves the entire world; HUD and commands stay steady. Action-scaled hitstop, knockback, ground marks, shockwaves, rubble, water mist, fire embers and illusion implosions add contact/aftermath. No destruction occurs on misses or healing. Effects expire after 3.2 seconds and are capped at six impacts. Reduced motion suppresses camera/knockback/fast debris and uses a 25 ms pause.

The final 96-case renderer run recorded median 2.550 ms, p95 4.831 ms and p99 6.339 ms per update/draw; peak process RSS 1022.2 MiB. These are headless CPU costs, excluding video encoding/compositor/vsync. They do not establish live display FPS. Raw results: `docs/evidence/feedback-matrix.json` and `feedback-tcp-*.json`.

The delivery's `battle-impact/index.html` contains sixteen 3.6-second MP4 clips and a 28.8-second eight-power reel. Audio is reconstructed from the game's emitted start/release/contact events using the same selected WAVs, voice ducking, contact panning and new weight layer. Export peaks remain below full scale. Browser playback and reduced-motion selection were checked. Physical speakers and live display/camera remain unverified.

English voice gaps remain explicit: no verified Sasuke English callouts; Itachi's two powers use general English battle lines rather than named calls. Source licenses and reuse limits remain recorded in `docs/audio-research.md` and the audio manifest. No remote publication was performed.

## Power upgrade follow-up

The three Astra findings are addressed in `docs/power-upgrade.md`. The current build has 116 referenced body images, 36 clips, eight Kirin effect frames and 24 WAVs. Two dedicated power clips per character replace the shared generic casting/slash sequences (eight powers total, eight unique poses each).

- 29 unit/integration tests pass, including new regressions for Chidori's bare hand/contact socket, mirrored attachments, reduced-motion contact, distinct Itachi effects, unique pose sets, six ordered accents, reflected/missed Kirin, and effect clipping below the HUD.
- The new power fixture suite passes all 96 hit/miss/reflection × side × motion-mode cases and exports 16 GIFs, eight six-phase sheets, and a reel. These assertions establish state/queue outcomes and review regressions; phase sheets and actual-renderer clips were also inspected for visual quality.
- The final complete 32-case render matrix recorded 2,920 frames, median 1.643 ms, p95 3.523 ms, p99 4.149 ms and peak RSS 132.5 MiB including image-export buffers. An isolated one-game benchmark recorded startup 0.117 s, median 1.470 ms, p95 2.650 ms, p99 3.227 ms and peak RSS 50.9 MiB. This is a heavier renderer than the first implementation; these headless CPU costs remain below a 16.7 ms frame budget but do not establish live display FPS.
- All five TCP scenarios were rerun with the upgraded renderer. Fresh raw reports use the `power-` prefix in `docs/evidence/` to preserve the earlier evidence.
- The 21.4-second review reel uses the actual fixture-rendered frames and a synthesized soundtrack assembled from the same release/hit WAVs, with the same event times. It is a review artifact, not a runtime cutscene or external generated video.

The extracted delivery is validated separately. Physical camera accuracy, speakers, live Wayland/vsync, and positive optional-video decoding remain unverified. No remote push is implied.

## Original implementation record — 9 November 2026

Implementation base: `31925a14750a374277ce103ece253b8f611199a8`; branch `improve-animation-assets`. No remote push is implied by these local artifacts.

## Checks

- 21 automated tests: natural order beyond 99, variable dt/event ordering, loop wrapping, repeated playback, terminal holds, independent mirror actors, explicit fallback, impact-time HP, duplicate/repeated actions, snapshot queues, long-frame actor synchronization, reflection and reflected KO, duplicate clicks, missing camera dependencies, disconnect, rematch, video file/decoder absence, and no audio device.
- Runtime validation: 36 clips, 59 referenced body poses, 24 valid WAV cues, and a decoded arena. All body references point to the curated character directories.
- Five actual two-TCP-client scenarios: four mirror matches plus Itachi vs Sasuke. Each verifies HP timing from both perspectives and duplicate snapshots. Mirror scenarios include miss/heal/lethal ultimate/results; the special scenario includes Genjutsu shield, reflected Kirin, and KO. Separate integration tests cover reflected KO.
- Full matrix: 32 character × move × attacking-side cases, 2908 rendered frames. Body comparison sheets and source atlases were visually inspected. Numbered action proof frames and GIFs were produced for both battle perspectives.
- Asset export, audio synthesis, core dependency installation, and optional dependency fallback are reproducible. The delivered ZIP is checked after extraction with runtime validation and tests.

## Target laptop measurements

Headless SDL rendering on the user's Intel i3 laptop, 1024×640. These are CPU render/update costs, not a claim of live display FPS. The original baseline uses only the available sparse source subset, whereas the new build uses its complete runtime body library.

| Scope | Startup | Median frame | p95 | p99 | Peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original, sparse Sasuke subset | 0.197 s | 4.459 ms | 6.732 ms | 7.983 ms | 65.2 MiB |
| New renderer, one game/two Sasuke actors | 0.093 s | 0.386 ms | 0.746 ms | 1.094 ms | 43.8 MiB |
| New all-moves export matrix | — | 0.495 ms | 0.912 ms | 1.246 ms | 109.4 MiB |

The GIF-export and two-client harnesses retain image frames and therefore have higher memory use than the isolated renderer. Do not compare their RSS directly to the original one-game baseline. Exact raw reports are in `docs/evidence/`.

## Visual evidence

- `evidence/all-moves.png`: battle contact sheet for all characters and commands.
- `evidence/*-comparison.png`: idle, attack, jutsu, ultimate, heal, hit, guard, defeat, and victory poses.
- `evidence/poses/*.gif`: all 36 body clip previews.
- `evidence/before-sparse.png` and `after-impact.png`: explicitly scoped before/after samples, not full-source baseline footage.
- The delivered preview gallery shows the 16 battle-action GIFs; local verification tools regenerate all detailed evidence under `work/`.

## Remaining checks and deliberate limits

Live Wayland/compositor/vsync timing, physical speaker playback, live webcam/MediaPipe accuracy, and positive OpenCV decoding of the optional intro were not exercised. Unit/integration checks cover missing media/dependencies and no audio device. Use the offline preview and then a two-client desktop match to judge the final feel on a real display.

971 legacy PNGs were not materialized; the original large/mixed collections were quarantined, not exhaustively reviewed or deleted. All runtime replacement frames were reviewed and validated. The original full-tree memory/performance baseline is not established.

The new library uses deliberate key poses and layered motion/effects. Further artist-authored in-between poses and move-specific sound recording remain possible refinements; this delivery does not claim frame-by-frame equivalence to a commercial fighting game.


## Downloaded audio verification — 10 November 2026

The downloaded-audio follow-up adds 63 sampled WAVs and 11 selected English voice clips across three characters. All 12 offensive moves and four recovery actions have sample effects. Sasuke's English attack calls and named Itachi Genjutsu/Tsukuyomi calls remain unverified. See `audio-research.md` for coverage, sources and terms.

37 unit/integration tests pass. They cover waveform decode/headroom for every sampled cue, one-shot audio events with duplicate snapshots, miss without contact, reflected block, speech ducking/mute, longer voice recovery holds, missing audio device/sample, and cleanup on turn changes/disconnects. Runtime asset validation also checks the new sampled manifest references.

The old real TCP tool had a fixed three-second completion window; a voiced Tanjiro ultimate plus the ending pose exceeded that window. The tool now polls both clients for the action and waits for completion with a bounded six simulated seconds. Fresh Tanjiro, Zenitsu and Itachi/Sasuke reflection results are recorded with the audio delivery. Browser playback was checked against a local server and reached readyState 4 with no media error; actual speaker output remains unverified.

The audio delivery includes raw source archives, per-master and archive SHA-256 values, imported-cue measurements, a 16-move full/effects/voice audition page, and updated game/audio ZIPs. All online recording selections retain source credits and their distinct license status. No public deployment or repository push was performed.
