# Shinobi Tactics — asset and animation improvement plan

**Implementation owner:** GPT‑6.1 Sol
**Prepared:** 9 November 2026
**Repository:** https://github.com/RUSHAB3979/Shinobi-Tactics
**Inspected snapshot:** GitHub `main` tree `7932ad67802784f538ff4f25933323c49d9f09e9` (tree hash, not a commit hash). Recheck HEAD before implementation.
**Status:** Core asset and animation overhaul implemented and verified headlessly; remaining desktop/device and legacy-audit checks are listed below.

## Downloaded audio follow-up — 10 November 2026

- [x] Research and preserve English voice archives for Itachi, Tanjiro, Hinokami Tanjiro, and Zenitsu Entertainment District; record sources, counts, checksums, and source terms.
- [x] Map downloaded effects to all 12 offensive moves and four recovery actions; import 63 sampled cues and retain 46 source masters.
- [x] Integrate separate voice/anticipation/release/contact buses, speech ducking, mute/volume, missing-device fallback, and recovery holds for longer lines.
- [x] Verify 37 automated tests and per-sample decode/headroom; prepare a 16-move listening preview and downloadable source archives.
- [ ] Acquire verified English Chidori/Kirin callouts. Sasuke currently has sampled effects without selected English voice.
- [ ] Acquire named English Genjutsu/Tsukuyomi calls; current Itachi selection uses general English battle lines.
- [ ] Human listening check on the laptop, including Whirlpool identification, levels and Hinokami Kagura for Sun Breath. See `docs/audio-research.md`.

## Astra review follow-up — 10 November 2026

- [x] Replace Chidori's katana contact with a dedicated bare-hand sequence and moving palm attachment.
- [x] Preserve melee contact in reduced motion, with a contact-position cut and restrained effects.
- [x] Give Tsukuyomi a separate red-moon illusion treatment, distinct from Genjutsu's crow cast and shield.
- [x] Upgrade all eight powers with eight unique drawn poses each, authored hand/weapon attachments, and move-specific choreography; add an eight-frame Kirin dragon.
- [x] Add focused regression coverage and normal/reduced actual-renderer previews for all powers and their hit/miss/reflection outcomes.
- [x] Retain generated source masters, reproduce exports/audio, and document the updated build and verification scope in `docs/power-upgrade.md`.

The runtime now references 116 body poses across 36 clips, plus eight separate dragon frames and 24 audio cues. The original legacy-audit and physical-device limitations below remain open; this pass does not turn them into completed checks.


## Implementation follow-up — 9 November 2026

- Working base: `31925a14750a374277ce103ece253b8f611199a8`, local branch `improve-animation-assets`.
- Completed the Sasuke pilot before expanding all four characters. Delivered 64 exported body poses (59 referenced), 36 clips, a new arena, 24 original audio cues, explicit pivots/facing/timing, independent actors, queued action IDs, synchronized impact feedback, nonblocking optional intro, and offline viewers.
- Validation: 21 automated checks, runtime asset validation, five actual two-TCP-client scenarios, and all 32 character/move/side cases. See `docs/verification.md` and `docs/evidence/` for the measured scope.
- P0 deviation: retired original folders are quarantined. The local source subset was inventoried; 971 large original PNGs remain unmaterialized/unreviewed. Every runtime replacement has been reviewed. No unseen legacy clip is accepted by the new manifest.
- Baseline and performance measurements are headless and explicitly scoped; live display/vsync, camera, speaker output, and positive optional video decoding remain unverified. No original full-source baseline or exhaustive legacy cleanup is claimed.
- Original source folders remain intact. The compact build omits unused legacy material; source masters, provenance, tests, docs, and tools are included. No remote repository update was performed.
- Next work: run a desktop two-client match with physical camera/audio, assess feel and optional intro decoding, then refine any poses/cues based on that review. Resume legacy-source archaeology only if those retired assets are needed.

## Objective and scope

Make every playable move visually correct, readable, and satisfying. Repair asset selection, frame sequencing, character consistency, and impact timing before adding stronger effects. Preserve the current Python/Pygame, two-player, turn-based game and its four characters: Sasuke, Tanjiro, Itachi, and Zenitsu. Keep the 1024×640 battle layout initially. This is not a conversion into a real-time fighting game.

Deliver a coherent sprite library, reliable animation playback, distinct move effects and sound, a finished arena presentation, and reproducible previews and checks. Keep current damage, healing, turn rules, and hand-sign mechanics unless a narrowly scoped presentation integration requires changes. Changes to balance are outside this plan.

## Evidence and limitations

Reviewed `client.py`, `server.py`, `hand_sign_config.py`, `README.md`, the complete GitHub file tree, and twelve representative PNGs. The tree contains no dependency manifest, lockfile, test suite, or repository `AGENTS.md`. README contains only the project title. The initial full clone was stopped because the current tree contains roughly 745 MB of files; source and sample inspection continued remotely. No runnable checkout was retained, no game session was played, and no runtime performance claim is established. Full visual auditing is task P0, not a completed check.

### Confirmed defects

| Problem | Evidence | Required outcome |
| --- | --- | --- |
| Non-character images are played as character frames | `assets/sasuke/attack_1/frame_29.png` and `frame_54.png` show isolated purple effect fragments; sampled Zenitsu `sixfold` frames 29 and 77 show yellow effect fragments. | Separate body animation, weapon/projectile, and VFX tracks; an effect must never replace the character body. |
| Healing collection includes unrelated UI | `assets/sasuke/healing/frame_100.png` depicts an HP bar. This is one sample, not proof about all healing frames. | Audit every healing folder; replace incorrect collections with a character recovery pose plus a separate healing effect. |
| Inconsistent source style and dimensions | Sasuke idle frame 0 is 75×171; attack frame 0 is 414×964 with a visibly different rendering style. Itachi idle is 229×465; Zenitsu `idle_new` frame 0 is 712×1300. | Choose and enforce a consistent sprite style, logical size, and anchor. Resizing alone cannot fix style differences. |
| Arbitrary clip truncation | `AnimatedSprite._load_all` slices attacks to 30 frames, healing to 20, idle to 12. Sasuke `chidori_new` has 79 files, `kirin` 73; Zenitsu `sixfold` 78, `godspeed` 80. | Explicitly curate complete clips with startup, action, and recovery; do not simply remove caps and play every file. |
| Numeric frame order is broken | Loader uses lexicographic `sorted(os.listdir(...))`; healing folders have 178 files named `frame_00` through `frame_177`. `frame_100` precedes `frame_11`. | Explicit manifest order or natural numeric sorting, with a regression check crossing frame 99. |
| Missing mappings fail silently | Tanjiro maps `ultimate`, `hit`, `down`, `guard`, and `victory` to nonexistent directories. Sasuke and Zenitsu also map nonexistent `victory` folders. `play()` leaves the previous clip running if lookup fails. | Resolve every required mapping; log actionable errors and provide intentional fallbacks. |
| Frame advancement depends on render stalls | `AnimatedSprite.update` advances at most one frame per update even when `dt` spans multiple frame durations. | Consume elapsed time correctly; preserve one-shot event ordering under variable frame rate. |
| Scale and facing are inferred incorrectly | `_scene_battle` normalizes every image to 180 px height, smoothscales each frame, flips only the local player, and adds bobbing during all actions. | Stable body scale, per-clip anchors and source-facing metadata, deliberate motion, crisp rendering. |
| Attack and reaction have no shared timing | `_process_action` starts attacker, defender hit animation, particles, sound, and shake immediately. HP display follows received state immediately. | A shared presentation timeline with release/impact/recovery events. |
| Mirror matches share playback state | `_get_anim_sprite` caches mutable `AnimatedSprite` by character name; both sides can receive the same instance and update it twice. | Share immutable frame surfaces, but give each actor an independent player. |
| Cinematics interrupt the main loop | `play_cutscene`, `play_genjutsu_anim`, and counter flash run their own loops. Itachi genjutsu can play locally before send and again on receipt. | One nonblocking presentation sequence per confirmed action; keep network and quit events responsive. |
| Finishing blows skip battle presentation | `_handle_server_msg` goes straight to `GAME_OVER`, bypassing `_process_action` in that branch. Result rendering does not advance character animations. | Show the finishing impact, defeat, and victory before presenting the result screen. |
| Media declarations are inconsistent | Character metadata names `chidori.mp4`, `sun_breathing.mp4`, `tsukuyomi.mp4`, and `thunderclap.mp4`; tree contains only `Itachi Genjutsu .mp4` and `Sasuke vs Itachi starting scene.mp4`. Audio exists only for Sasuke/Itachi jutsu and ultimate. | Trace actual call sites, remove stale references or provide intentional alternatives; complete move audio coverage. |

Sources: [client.py](https://github.com/RUSHAB3979/Shinobi-Tactics/blob/main/client.py), [server.py](https://github.com/RUSHAB3979/Shinobi-Tactics/blob/main/server.py), [assets](https://github.com/RUSHAB3979/Shinobi-Tactics/tree/main/assets). These links follow `main`; record the actual implementation commit in the audit.

## Art direction

Default direction: cohesive 2D pixel-art anime sprites with clear silhouettes, restrained palettes, crisp edges, and readable attacks. Keep character outfits, body proportions, lighting, and pixel density consistent across idle, attack, reaction, and ultimate. Use the strongest coherent existing source set as the reference after P0. Do not upscale disconnected low-quality fragments and call them new animation.

- Character bodies remain visible through the whole move. Detached slashes, lightning, water, fire, and projectiles are separate layers.
- Use one documented logical scale per character, derived from its standing body, not each frame’s full bounding box. Preserve crouching, leaning, airborne poses, and large weapon arcs naturally.
- Give every frame a stable foot/root anchor and explicit offsets. Preserve the original pivot when trimming transparent margins. Separate effect anchors from body anchors.
- Use nearest-neighbor scaling for pixel art. Prefer integer scale and coherent source resolution; verify the result at actual game size rather than only enlarged contact sheets.
- Attacks need anticipation, a clear release/contact pose, and recovery. Stronger feedback means better timing and silhouette, not constant shake or a longer flash.
- Keep backgrounds lower contrast than characters and VFX. Keep HP, turn status, and command labels readable during ultimates.
- Keep editable sources, export settings, and provenance for replacement assets. Prefer repairing usable assets first. Use original or appropriately licensed replacements; do not pull random sprite-sheet images without tracing their source.
- If image generation is used later, consult the available imagegen skill. Generate reference sheets or coherent source art, then inspect and align exported frames individually. Treat generated strips as unvalidated source material, not ready-to-play clips.

## Execution rules for GPT‑6.1 Sol

1. Start by reading current project instructions, checking `pwd`, Git status, and dependency manifests. Preserve unrelated changes. Use a separate worktree if another editing session is active.
2. Work sequentially through P0–P6. Limit heavy work to one task and two CPU threads on this Intel i3/Intel integrated GPU laptop. Do not install CUDA or packages into system Python/Conda base.
3. Use `agent-env` for generic tools; follow an existing project environment if present. If absent, create a project-local environment and a reproducible dependency manifest. Separate core Pygame requirements from optional video/webcam packages.
4. Keep this plan in the implementation checkout as `plan.md`. Update checkboxes, actual file paths, validation evidence, and the next task as work progresses.
5. Complete the Sasuke ATTACK pilot before mass-producing replacements. Carry the validated approach across all four characters.
6. No blanket renaming/deletion of source folders. Keep original assets until every consumer is migrated. Do not execute a generic image-normalization script over the entire asset library.
7. Suggested new file names below are proposals, not files that already exist. Keep refactoring focused on asset loading, animation, and presentation; avoid rewriting unrelated networking or webcam recognition.

## P0 — Baseline and complete asset audit

**Dependencies:** None. **Priority:** Critical.

- [x] Obtain a working checkout and record the commit. If transfer size is an issue, use a documented partial/sparse Git workflow and fetch only needed character assets first; do not assume the planning workspace is a cloned repository.
- [x] Read all five Python modules and verify the actual import requirements. Document launch/setup commands and optional dependency fallbacks. Bind any test server to loopback or use a local fixture.
- [x] Create `tools/audit_assets.py`: inventory PNG dimensions, alpha bounds, count/order/gaps, byte size, duplicate hashes, folder mappings, and audio/video references. Flag suspicious frames without automatically deleting them.
- [ ] Produce numbered contact sheets and scrub-able previews for every mapped action, including every frame of long clips. Review unused folders as possible sources. Label each frame/sequence as body, VFX, projectile, UI, mixed extraction, duplicate, or unusable; record uncertainty.
- [x] Write `docs/asset-audit.md` and a machine-readable inventory. Record which assets are used at runtime versus merely present on disk. Document each missing clip and its proposed source/replacement.
- [ ] Capture a reproducible baseline of representative actions, mirror matches, both sides, and game-over transitions. Record startup time, peak process memory, and frame-time distribution before optimization.

**Acceptance:** Every currently mapped action has a reviewed source or an explicit missing-asset entry. The audit includes the known effect-only and HP-bar contamination. No unreviewed long folder is accepted merely because its filename matches a move.

## P1 — Explicit clip data and a trustworthy animation player

**Dependencies:** P0. **Priority:** Critical.

Primary integration points: `CHARACTERS`, `AnimatedSprite`, `_get_anim_sprite`, `_scene_select`, `_scene_battle`, `_scene_game_over` in `client.py`.

- [x] Define `assets/animations.json` and a small loader/player module, e.g. `animation.py`. Each clip specifies explicit frame paths/order, frame durations, loop/hold/return behavior, source facing, logical scale, frame anchors/offsets, and named events. Distinguish character and VFX tracks in the schema.
- [x] Document the manifest format in `docs/animation-format.md`. Use seconds or milliseconds consistently; validate positive durations, valid frame paths, event bounds, and completion targets.
- [x] Curate a complete Sasuke attack sequence from reviewed frames or author missing poses. Remove global frame-count caps only when manifest-driven sequences replace them.
- [x] Implement elapsed-time-based advancement with deterministic handling of long `dt`, loops, completion, and events crossed between rendered frames. Each impact/release event fires once per playback. Visual pauses must not stop network polling.
- [x] Cache loaded immutable images separately from per-actor animation state. Create distinct player and enemy animation instances even when both select Sasuke.
- [x] Replace per-frame height fitting with character scale and authored pivots. Mirror around the actor anchor; transform effect/weapon offsets correctly. Suppress generic idle bob during attacks and defeat.
- [x] Cache scaled/flipped surfaces at the configured scale. Load only required sequences instead of eagerly decoding every unused directory.
- [x] Use an explicit visible fallback for missing assets during development and an actionable diagnostic. Never silently continue an unrelated attack because another clip was missing.
- [x] Add a lightweight `tools/preview_animations.py` viewer: character/action selector, play/pause, frame step, speed adjustment, side flip, root/bounds overlay, checkerboard background, and visible event markers. It must work without a server or camera.

**Acceptance:** Sasuke idle → attack → recovery → idle is complete and coherent on both sides, without disappearing into an effect-only image, resizing between poses, or drifting at the feet. Numeric ordering, frame-rate independence, one-shot events, and independent mirror-match players have automated checks.

## P2 — Action timeline and one complete combat example

**Dependencies:** P1. **Priority:** Critical.

Primary integration points: `_process_action`, `_handle_server_msg`, HP bars, battle button gating, cutscene helpers; narrow additions to `server.py` if needed for action IDs.

- [x] Introduce a presentation controller, e.g. `battle_presentation.py`, with stages: startup → release/travel → impact → recovery → settle. Support layered body, projectile/VFX, sound, camera, and reaction tracks.
- [x] Drive the pilot Sasuke ATTACK through this controller. For melee, use a readable approach/strike/return or an explicitly stylized slash reaching the opponent; do not show a remote sword swing causing unexplained damage.
- [x] Trigger defender recoil, hit spark, hit sound, displayed HP change, and brief impact pause at the authored impact event. Preserve server-authoritative HP separately from presentation HP; the client must not recalculate damage.
- [x] Queue confirmed actions instead of overwriting an active animation. Add a server-generated monotonic action identifier scoped to the match (or an equally reliable event identity) and ignore duplicate presentations. Do not deduplicate by character/action name because repeated moves are valid.
- [x] Disable command submission while a challenge/submission is pending or presentation is active; keep polling network and processing quit/disconnect events. Handle snapshots arriving during playback without dropping actions.
- [x] Support miss (`dmg == 0`), heal, guard/reflection, and KO branches. A miss must not show a successful impact or HP loss. Reflected effects must resolve against the actual recipient, including Kirin.
- [x] Replace blocking cinematic/flash loops with update/draw state driven by the main loop. Route local and received Itachi genjutsu through one presentation path, avoiding double playback. Keep optional video skip and missing-decoder fallback functional.
- [x] Defer result-screen presentation until the terminal action, defeat, and winner pose finish. Continue updating animations on the result screen.

**Initial tuning ranges, not fixed requirements:** normal attack total 0.45–0.85 s; jutsu 0.8–1.5 s; ultimate 1.5–2.5 s; impact pause 35–70 ms; brief decaying shake around 2–5 px. Adjust after preview. Optional video playback should not be mandatory for every ultimate.

**Acceptance:** A recorded two-client Sasuke attack shows visible contact before damage feedback. Repeated state messages do not replay it, identical successive attacks still play, and lethal/reflected/missed actions show the correct result. Rendering at 30/60/120 Hz and occasional long frames preserves event order.

## P3 — Rebuild the complete playable character library

**Dependencies:** P2. **Priority:** High. Work one character at a time.

Each character requires coherent idle, ATTACK, JUTSU, ULTIMATE, heal, hit, guard/counter where applicable, down/defeat, and victory. Run/walk/dash clips are required only where used for staging. Do not spend this pass rebuilding unused jumps, grabs, or miscellaneous `anim_*` folders.

| Character | Proposed visual treatment | Required audit/replacement work |
| --- | --- | --- |
| Sasuke | Katana anticipation and slash; Chidori hand charge, blue lightning approach and contact burst; Kirin sky cue, descending lightning silhouette, impact and fade. | Rebuild the mixed `attack_1` body sequence; classify `chidori_new`, `chidori_charge`, `chidori_run`, and `kirin`; replace invalid healing; supply victory. Ensure Kirin targets the correct actor after reflection. |
| Tanjiro | Clean sword arc; Whirlpool as a water ribbon with rotational flow; Sun Breath as a distinct warm flame arc and decisive finisher. | Review `special_1`, `special_2`, `water_surface`, and attacks visually before assigning move names. Author missing ultimate/hit/down/guard/victory and a recovery pose. Do not rename `down_slash` to defeat without inspection. |
| Itachi | Kunai release plus separately travelling projectile; Genjutsu eye/crow distortion and a readable shield state; Tsukuyomi brief red-black scene treatment with clear target reaction. | Keep body, projectile, and overlays separate; use one coherent source style; review `genjutsu_start`, `genjutsu`, `tsukuyomi`, and reaction clips. Replace heal-to-idle placeholder with intentional recovery presentation. |
| Zenitsu | Crouched/sheathing anticipation, directional slash, lightning trail; Sixfold as six readable visual accents; Godspeed as a stronger charge and decisive dash/impact. | Classify mixed `attack_1`, `sixfold`, and `godspeed` collections; keep lightning separate from the body; harmonize `idle_new` with combat poses; replace invalid healing and add victory. Six visual strikes still use the existing single server damage result. |

- [x] Sasuke library completed and reviewed.
- [x] Tanjiro library completed and reviewed.
- [x] Itachi library completed and reviewed.
- [x] Zenitsu library completed and reviewed.
- [x] Every character receives a final comparison sheet at the same logical scale and a preview reel showing all required transitions.
- [x] Record source/author/license or generation-and-editing provenance in `assets/ATTRIBUTION.md`; store editable sources separately from runtime exports.

**Acceptance per character:** Correct costume/silhouette/palette across states; no foreign UI pixels, orphaned effect fragments, cropping, accidental empty frames, unintended style jumps, or unexplained facing changes. All mapped actions play a complete startup/action/recovery or intentional terminal hold. Missing assets are repaired, not hidden by arbitrary aliases.

## P4 — Impact effects, audio, arena, and UI assets

**Dependencies:** P3 (prototype effects may be developed during the pilot). **Priority:** Medium.

- [x] Build reusable effect types for slash, kunai trail/contact, lightning, water, flame, genjutsu, healing, block, and KO. Use distinct shape/motion as well as color. Specify layering and actor-relative/world-relative anchors.
- [x] Add/review short release, travel, hit, block, heal, and ultimate sounds; sync playback to timeline markers. Balance levels, cap simultaneous voices, prevent duplicate audio, and preserve a muted/no-audio fallback. Complete Tanjiro and Zenitsu coverage.
- [x] Replace the empty grid arena with one coherent low-contrast environment and anchored contact shadows that support the existing diagonal battle layout. Keep foreground effects from obscuring commands and HP.
- [x] Use portraits and move icons consistent with the sprite art. Keep each icon accompanied by readable text; replace unreliable emoji/system-font glyphs with bundled suitable assets where necessary.
- [x] Add adjustable effect intensity/reduced motion, volume/mute, and cutscene skip. Avoid prolonged full-screen flashes. Strong feedback must remain readable at reduced intensity.
- [x] Resolve stale video declarations. Prefer compact in-engine animation where sufficient; keep optional existing clips only when correctly mapped and intentionally used. Do not add large videos to compensate for missing combat poses.

**Acceptance:** Every move has a recognizable visual identity and a synchronized audio cue; body silhouettes and HUD remain legible. Reduced motion and muted audio preserve all gameplay information.

## P5 — Verification and performance on the target laptop

**Dependencies:** P4. **Priority:** Required before completion.

- [x] Asset validation: all referenced files exist and decode; durations and pivots are valid; no missing required action; manifest order is explicit; no unreviewed effect/UI frame appears on a body track.
- [x] Playback tests: numeric ordering through 100+, variable `dt`, loop wrapping, terminal holds, completion transitions, missing-file diagnostics, event firing exactly once, and mirror-match independence.
- [x] Presentation integration tests: HP feedback at impact, miss, reflection, heal at full HP, repeated/duplicate messages, queued actions, finishing blow, reflected KO, disconnect during animation, rematch state reset.
- [x] Manual preview matrix: all four characters × ATTACK/JUTSU/ULTIMATE/HEAL on both screen sides; all reactions and result states; each same-character matchup; Itachi vs Sasuke special interaction.
- [x] Optional dependencies: without video decoder, without video file, without sound device, and without webcam. Preserve documented hand-sign behavior; provide an offline preview fixture to test presentation without changing live challenge rules.
- [ ] Record frame times, asset-load latency, peak memory, and effects-heavy sequences at 1024×640. Target smooth 60 FPS on the user's laptop; report median/p95/p99 and stalls rather than only an average. Compare against P0 and state any unmet target.
- [x] Cache background layers and avoid per-frame image decode, scaling, font creation, and large surface allocation where profiling identifies them. Cap particles; load actor assets on demand. Consider atlases only after profiling shows a benefit.
- [x] Re-run relevant checks after fixes and keep before/after recordings from the same scenario. Use a seeded preview mode for reproducible comparisons.

**Acceptance:** No known missing mappings, corrupted body clips, incorrect damage feedback, stuck states, or mirror-match interference. Runtime checks and visual checks both pass. Performance limitations are measured and explicitly documented; automated tests alone do not establish visual quality.

## P6 — Handoff and completion

**Dependencies:** P5.

- [x] Update README with environment setup, server/client launch, optional media/webcam setup, preview and validation commands, and controls.
- [x] Deliver `docs/asset-audit.md`, `docs/animation-format.md`, provenance, manifests, curated source/export assets, relevant tests, preview tools, and before/after evidence.
- [ ] Remove unused runtime assets only after checking all references and retaining required editable originals; summarize download-size and decoded-memory changes separately.
- [x] Update this plan with actual completion status and remaining limitations. Summarize changes, checks run, checks not run, and visual evidence.

## Definition of done

All four characters and all four player commands have complete, correct, distinct presentations. Characters retain their identity and body throughout animation; feet/pivots/facing are stable; hit, sound, HP, and camera feedback agree with impact. Misses, reflection, KO, mirror matches, and rematches work. The asset library is documented and reproducible, the animation viewer makes future edits reviewable, and the game runs acceptably on the target laptop with measured evidence.

## Resume prompt for GPT‑6.1 Sol

> Read `plan.md` and the project's current instructions. Implement the unchecked tasks in dependency order, starting with P0. Verify the repository and preserve unrelated edits. The known defects include mixed body/VFX/UI frames, inconsistent source art, arbitrary truncation, lexical frame sorting, missing mappings, shared mirror-match animation state, immediate hit feedback, and skipped finishing-blow animation. First establish a complete asset audit, then deliver and verify the Sasuke ATTACK pilot before expanding the roster. Update this plan after each milestone with changed paths, checks, visual evidence, and the next task. Keep Pygame and the current turn-based mechanics. Work within the Intel i3 CPU budget. Do not mark implementation complete based only on generated assets or tests; inspect playback and verify both clients.


## Battle impact follow-up — 10 November 2026

Implemented whole-world directional camera impulses with a stable HUD, action-scaled hitstop (45/65/95 ms), contact knockback, elemental ground marks, shockwaves, debris/mist/embers and illusion implosions. Aftermath is capped at six impacts and fades after 3.2 seconds. Reduced motion disables camera/knockback/fast debris and shortens hitstop. Damage, reflection, turn rules and animation contact markers remain server-authoritative.

Seven reproducible original low impact sounds now layer beneath the recorded effects. Contact audio pans toward the recipient, voice ducking/master mute still apply, and reflected attacks use a counter layer. Misses and recovery never trigger destruction. A presentation clock callback keeps shake and aftermath consistent through hit pauses and long frames.

Verification: 45 automated tests; 96 power/outcome/side/motion cases; two fresh real TCP scenarios (Itachi/Sasuke reflection and Tanjiro heal/ultimate/KO). Current preview: `battle-impact/index.html` in the delivery, with sixteen 3.6-second normal/reduced clips and an eight-power reel. Tools: `tools/verify_feedback.py`, `tools/preview_battle.py`, `tools/build_impact_audio.py`.

Remaining work is the already-recorded English voice gaps, final human listening on physical speakers, live display/vsync and optional camera/video hardware checks. No remote publication or balance change was performed.


## Full visual glowup — 10 November 2026

Implemented a new painted shrine arena, foreground fighter composition, unified top health HUD and command cards, bundled typography, menu/selection styling, ultimate technique cut-ins, cached elemental contact/ground light, vignette and low-motion-aware ambient particles. Research and the exact generated-art prompt are in `docs/glowup-art-direction.md`. The latest delivery review is `glowup/index.html`; earlier previews are retained for comparison. 48 automated tests cover the existing combat/audio regressions plus command text fit, bounded lighting caches and reduced ambient motion. Full power/TCP checks and package validation are recorded in the current verification report.
