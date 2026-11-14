# Shinobi Tactics — technique-specific attack animation plan

Implementation owner: GPT-6.1 Sol
Prepared: 14 November 2026
Status: IMPLEMENTED locally; all eight moves reviewed. Final package verification recorded in outputs/jutsu-choreography/verification-summary.md.
Repository: https://github.com/RUSHAB3979/Shinobi-Tactics

## 1. User correction and definition of success

The user rejected generic portrait cinematics as the main improvement. The requested animation must depict the technique itself: Chidori visibly gathers lightning in Sasuke’s hand and becomes a charging hand thrust; Kirin forms a lightning dragon in the sky before Sasuke directs it down. Apply this specificity to all eight existing Jutsu/Ultimate moves.

The fighter’s changing pose, the source of the power, its path and the target reaction must tell the story. A nameplate, portrait zoom, glowing circle, screen shake or stock lightning overlay cannot substitute for that choreography. Brief technique-relevant close-ups are permitted only when they clarify an action (palm charging, raised hand commanding the storm, eye casting an illusion). Do not put the same face intro before every move.

Acceptance question: with names and audio hidden, can a viewer distinguish Chidori from Kirin, Genjutsu from Tsukuyomi, and Sixfold from Godspeed? If not, the move is unfinished.

This is a 2D Pygame presentation improvement. Preserve the roster, turn system, damage rules, hand-sign inputs and English voice preference. Do not change engines or add balance rules to imitate anime lore.

## 2. Current state and safe starting point

Inspected local branch: `improve-animation-assets`, HEAD `99e801f7216dc013710d6be24f1513aa47878b6a`, with uncommitted cinematic-pass changes. Recheck Git status and remote refs before editing. The previously reviewed `feat/strategic-combat` branch is separate; do not silently merge it or discard its chakra/Guard mechanics if it becomes the implementation base.

Read current instructions, `pyproject.toml`, `uv.lock`, this plan and `game-feel-glowup` skill. Use the existing Python 3.12 `.venv` through `agent-env`; one heavy process at a time, two CPU threads on this laptop. Preserve unrelated changes. Use a separate worktree if another editing session is active, and deliberately transfer the relevant uncommitted changes rather than assuming a new worktree contains them.

Existing useful code:

| File | Current role / required work |
| --- | --- |
| `assets/animations.json`, `animation.py` | Per-character body frames, pivots, sockets and events. Author actual poses here; do not just stretch the old clip. |
| `assets/curated/*/powers/` | Existing power poses; audit individually for reuse. |
| `power_visuals.py` | Existing Chidori hand effect, Kirin dragon, illusions, water/flame/thunder. Improve choreography and synchronization; primitives alone do not satisfy the art target. |
| `assets/vfx/kirin/` | Eight existing dragon frames. Review shape, scale and continuity before reusing. |
| `battle_presentation.py`, `client.py` | Action queue, body/effect clocks, authoritative impact and reaction. Keep one contact event. |
| `special_cinematics.py`, `assets/cinematics/` | Rejected generic portrait-first solution. Remove its mandatory 1.05/1.45-second intro from the normal attack path. Preserve artwork as optional source material; do not delete broadly. |
| `combat_audio.py`, `combat_feedback.py`, `battle_style.py` | Existing English audio, contact sounds, shake, hitstop and HUD. Reuse, then synchronize to the redesigned moves. |
| `tests/`, `tools/verify_feedback.py`, `tools/verify_battle.py` | Existing verification harnesses; update for the new timeline and chosen branch. |

The previous cinematic pass passed 52 tests and 96 render cases. Those checks establish technical behavior, not user approval of its visuals. The earlier historical plan is preserved at `docs/animation-plan-2026-11-09.md`; this document supersedes its visual priorities. Its old audio counts and missing-Chidori note are stale: the user-supplied Chidori voice is present; Kirin has no verified named voice.

## 3. Online reference board and evidence boundaries

Research accessed 14 November 2026. Sources are reference material, not permission to copy their footage/assets. Numerical timings and the staging below are proposed game adaptations, not frame-accurate reproductions of the anime. Pages and indexed descriptions were researched; no full episode or trailer was watched frame-by-frame in this planning pass. Do not invent timestamps. Before final pose production, Sol should inspect available official illustrations/trailers and record actual shot observations; if playback is unavailable, record that limitation.

| ID | Reference | What to study / confidence |
| --- | --- | --- |
| R1 | [Official Chidori database](https://naruto-official.com/en/news/01_1715) | Primary source: identifies Chidori as a concentrated-chakra, high-speed thrust. Use the linked illustration to study the attacking hand and forward posture. |
| R2 | [Official manga artist interview: Kirin](https://naruto-official.com/en/news/01_1494) | Primary source includes the Kirin illustration from Volume 43, chapter 391. Study its dragon silhouette and layered outlined lightning. |
| R3 | [The End — episode 138 synopsis](https://naruto.fandom.com/wiki/The_End) | Secondary episode guide: clouds, guided lightning and destruction at the hideout. Use for reference-scene identification; cross-check the sequence against licensed episode/manga access before claiming exact poses. |
| R4 | [Official Naruto anniversary retrospective](https://naruto-official.com/en/news/01_1287) | Primary source describes Itachi trapping Kakashi in Tsukuyomi. Illusion staging should establish mental capture, not a physical lightning hit. |
| R5 | [STORM development: expressions and technique scale](https://naruto-official.com/en/news/01_1909) | Primary production principles: posture and environmental response communicate power. The combination-technique Kirin is a different context; do not copy its Susanoo/black-flame additions into this move. |
| R6 | [STORM development: elemental effects](https://naruto-official.com/en/news/01_1719) | Primary production principles: distinguish water, fire and other effects by behavior; use restrained impact holds. |
| R7 | [SEGA character introductions on PlayStation Blog](https://blog.playstation.com/2021/09/17/20210917-demonslayer/) | Primary publisher reference with Tanjiro and Zenitsu character media. Establish water-sword motion and Zenitsu’s concentrated thunder-breathing identity. Does not establish every move below. |
| R8 | [Official Hinokami Chronicles site](https://demonslayer-hinokami.sega.com/) | Official roster/media reference, including Entertainment District variants. Use its character trailers as visual starting points. |
| R9 | [Zenitsu technique descriptions](https://kimetsu-no-yaiba.fandom.com/wiki/Zenitsu_Agatsuma) | Secondary index distinguishes repeated Thunderclap variants from Godspeed and Seventh Form. Do not substitute the Seventh Form’s dragon for Godspeed. |

Whirlpool’s exact rotation and the chosen Sun Breath form need pose-reference validation before final artwork. `SUN BREATH` is a broad game label, not a precise form name. Default to a clearly documented Hinokami Kagura-inspired sword sweep; do not silently rename it or claim it exactly reproduces a named form. Genjutsu is likewise a broad label: the crow treatment below is an adaptation for the existing game mechanic.

## 4. Shared animation and asset requirements

Build each sequence as preparation → formation → release/travel → contact → recovery. The table timings below start at move presentation time zero and exclude any optional voice-only recovery hold. They are initial tuning targets, not mandatory extra delays.

- Body animation must contain distinct silhouettes: stance, weight transfer, hand/weapon action, commitment and follow-through. Rough target: 10–16 meaningful body keys for a complex move, with extra transition/smear frames where useful. More near-duplicate frames is not quality.
- Keep editable sources. Export transparent body, weapon, elemental and foreground/background layers separately. Generated artwork is source material requiring cleanup, consistent anatomy, outfit, scale, registration and temporal continuity; a generated contact sheet is not a validated animation.
- Establish a per-character model sheet and source resolution before generating frames. Match the existing fighter style and pixel density; do not graft a detailed anime hand onto a tiny unrelated body. Inspect at 1024×640 actual game size.
- Define `root`, `hand`, `weapon_tip` and `head/eye` anchors as needed. One common transform drives body, sockets, VFX and camera. Palm lightning must follow the palm every frame, including mirrored play.
- Camera framing may show a hand or upper body using an authored detailed insert, but return to a readable view of attacker and defender before contact. Keep HUD fixed and inputs/network polling responsive.
- Events may include cosmetic `charge`, `form`, `release`, `accent_1..6`, `impact`, `recover`. Only `impact` changes displayed HP and triggers the authoritative recipient reaction. Cosmetic markers cannot apply extra damage.
- Do not duplicate the old generic intro plus a new technique build-up. Replace that dependency with a single move timeline. If retaining `perform`, give it a documented move-specific purpose; otherwise remove the unused path and update tests.
- Scale effect energy by phase: small local origin, recognizable formation, committed release, short high-contrast contact, decaying aftermath. Avoid constant full-screen flashes.

## 5. Per-technique choreography

### A. Sasuke — Chidori (pilot, highest priority)

Reference: R1; R2 also contains a Chidori collision example. Target total: 1.8–2.2 seconds.

1. 0.00–0.25: Sasuke plants his forward foot, bends knees and lowers his center of gravity. The attack hand is clearly visible near his hip; the other arm can briefly brace the wrist.
2. 0.25–0.75: Pinpoint sparks converge into the palm. A compact blue-white electrical core grows; irregular branching arcs crawl around the fingers and forearm. Light touches sleeve, face and ground. A short palm-focused shot is optional, never a generic portrait.
3. 0.75–1.20: He drives forward with shoulder and torso leading, attacking arm initially drawn back. Charge remains attached to the hand. Feet push off; speed lines and a short trail follow his route, not a beam to the opponent.
4. Contact around 1.20: Distinct bare-hand thrust into the target’s torso position. Show a concentrated electrical burst at the palm-target intersection, then the defender recoils once. No sword contact and no detached thrown orb.
5. 1.20–2.00: Follow-through, hand withdrawal, residual crackles and a planted recovery. Avoid visibly skating backward to idle; use authored retreat steps or a brief recovery cut.

Assets: crouch/brace, palm formation, push-off, run/drive, extended thrust, recoil and recovery poses; 6–8 electrical formation shapes; contact burst; short sleeve/ground glow. Existing Chidori voice begins with formation; electricity rises into release, contact sound fires once.

Pass gate: freeze any charge/travel frame and the lightning’s origin is visibly the hand. Silhouette-only footage still reads as a thrust. Both facings contact the actual recipient.

### B. Sasuke — Kirin (second pilot)

References: R2/R3; use R5 only for scale principles. Target total: 2.7–3.2 seconds.

1. 0.00–0.50: Sasuke stops and raises one arm toward the sky. Clouds gather above the arena; establish the vertical relationship between caster, sky and target. Compress environmental preparation cosmetically; do not add a weather resource or prerequisite.
2. 0.50–1.35: Lightning branches converge inside clouds into a recognizable dragon head and neck. Reveal horns, open jaw, silhouette and electrical body progressively. Give the fully formed dragon a readable 0.15–0.25-second hold.
3. 1.35–1.70: Sasuke sweeps his raised hand down. This visible command releases the dragon. Keep the caster grounded; no melee dash.
4. 1.70–2.05: Dragon dives from above toward the target with accelerating vertical motion. Its jaw/contact anchor reaches the target at the single impact marker. Do not slide a small dragon sideways across the screen.
5. 2.05–3.00: Strong downward strike, short contact hold, outward ground discharge, bounded dust/cracks and fading cloud illumination. Restore the arena gradually.

Assets: arm-raise, sky-command and follow-through poses; cloud formation layers; at least distinct forming/held/diving/contact dragon states, with body and jaw anchors; ground discharge. Reuse the eight existing dragon frames only if they support these phases. Sound: cloud rumble → electrical build-up → diving crack → contact thunder. Do not substitute the Chidori voice for missing Kirin speech.

Pass gate: at normal playback the viewer can identify sky formation, dragon, downward hand command, descent and contact as separate beats. Dragon stays below HUD or is composed in world space without covering health bars.

### C. Itachi — Genjutsu

References: R4/R7-style character readability; crow-cast details are a game adaptation. Target: 1.6–2.1 seconds.

1. Quiet stance with an eye or two-finger casting gesture; eye emphasis belongs to the cast, not an unrelated face introduction.
2. A silhouette breaks into crows/feathers or a brief double image, drawing the opponent’s attention. Stagger wing poses and depth rather than scattering identical icons.
3. A short distortion reaches the opponent, whose pose stiffens at contact. Dark/crimson ripples settle around the target. Preserve readable bodies and their positions.
4. Resolve into the existing reflection-ready shield indicator. Reflection readiness follows the server state; the crow animation itself grants nothing.

Assets: gesture, composed hold, crow dissolution/reassembly body masks, 4–6 crow wing silhouettes, subtle distortion layer. Use an illusion pulse and wing noise rather than heavy ground destruction. When a later move is reflected, show a brief illusion break and send reaction/audio to the attacker according to the result; do not replay a full cast.

Pass gate: visually reads as deception/mental capture and distinguishes the cast from the later counter.

### D. Itachi — Tsukuyomi

Reference: R4; red-moon realm treatment adapts the existing art direction. Target: 2.3–2.8 seconds.

1. Brief Mangekyou activation attached to Itachi’s actual cast (roughly 0.2 seconds), then a visual connection to the defender.
2. Arena dissolves into a crimson/black illusion realm. Keep Itachi and the target spatially readable; create layered silhouettes, restrained time-smear or shadow duplicates.
3. Target is held in a distinct immobilized pose; short symbolic shadow/blade passes imply mental assault without physical lightning, gore or six gameplay hits.
4. One illusion-collapse/contact marker updates HP and triggers the target reaction. The red realm cracks/fades back to the arena; no crater or explosive knockback.

Assets: eye activation tied to body pose, cast and hold, restrained-target silhouette, realm layers and dissolve masks. Sound should thin out into a muffled pulse, then resolve sharply at contact.

Pass gate: clearly a realm-changing illusion, not Genjutsu with a larger eye symbol.

### E. Tanjiro — Whirlpool

Reference starting points: R7/R8; validate the exact torso rotation against suitable footage before final poses. Target: 1.7–2.1 seconds.

1. Lower stance, coil hips and shoulders in opposite directions, katana positioned to initiate a rotational cut.
2. Uncoil into a clear circular sword sweep. Build a blue-white water ribbon from the blade path, passing behind and then in front of the body with appropriate occlusion.
3. Spiral expands into the opponent’s space, with contact on the blade/water cutting arc. Use splash and directional recoil rather than lightning cracks.
4. Land/settle from rotation; ribbon separates into droplets and dissipates.

Assets: coiled pose, quarter/half/three-quarter rotational keys, contact and settle; blade-tip trail with foam edges and droplets. This is a ground-arena adaptation; do not flood the map or present it as a water projectile detached from the sword.

Pass gate: water follows the sword and body rotation; hiding water still reveals a coherent rotational attack.

### F. Tanjiro — Sun Breath

References: R8 media; exact form remains an explicit adaptation choice. Target: 2.0–2.5 seconds.

1. Audible breath and grounded preparation; both hands visibly hold the katana.
2. Blade edge develops warm embers. Tanjiro pivots into a committed rising-to-descending sword arc, with one clear change in body orientation.
3. Fire-colored ribbon traces the blade’s actual motion, broadening through the swing. One focused slash contacts the defender.
4. Follow-through and recovery, with small drifting embers. No fireball from the palm and no generic explosion covering the sword.

Assets: breathing/preparation, two-handed lift, pivot, sweeping contact and follow-through poses; flame ribbon with red outer edge and warm core. Distinguish visually from Whirlpool by trajectory, acceleration and residual particles, not just hue.

Pass gate: sword, grip and arc remain readable through the fire. Document the chosen choreography without inventing a canonical form name.

### G. Zenitsu — Sixfold

References: R7/R8/R9. Target: 1.8–2.3 seconds.

1. Low iaido stance, hand on hilt, weight on loaded legs. Show breath and a brief stillness before acceleration.
2. Six visibly separate directional dash accents with alternating positions and pauses of contrast. Author a path through arena space; do not fake sixfold by drawing six crescents while the same sprite glides linearly.
3. Accents 1–5 build the attack; final pass contains the sole authoritative contact. Coordinate foot push-off, drawn sword and trailing electrical streaks.
4. End in a distinct landing/re-sheathing pose with dust and residual charge fading.

Assets: crouch/hilt grip, push-off, directional dash keys/smears, final slash, landing and sheath. Render sparse readable afterimages; do not make all six routes simultaneously bright.

Pass gate: six accents can be counted in slowed footage, but the normal-speed sequence still reads as one rapid technique. Damage remains one event.

### H. Zenitsu — Godspeed

References: R7/R8/R9. Target: 1.8–2.3 seconds.

1. Deeper still crouch and leg loading than Sixfold, tight electrical tension at feet/hilt, restrained camera framing on the stance.
2. One decisive explosive launch: a narrow, bright track and short smear show the body crossing the gap at extreme speed. Do not reuse Sixfold’s zigzag pattern.
3. One decisive sword pass/contact, then resolve Zenitsu beyond or alongside the target in a coherent finishing pose. Return to the normal root only through a believable settle/cut.
4. Afterimage fades behind the route; thunder follows the visual attack, with contact timing preserved.

Assets: deep load, push-off, elongated dash smear, slash, brake/landing and sheath. No lightning dragon: that would confuse Godspeed with a different technique and with Kirin.

Pass gate: silence → one fast burst → finishing pose is immediately distinct from Sixfold’s repeated accents.

## 6. Integration rules and implementation order

- [x] P0 — Recheck working branch, existing edits and actual active move names. Record baseline frames and make a list of reusable body/VFX assets. Retire the mandatory generic portrait intro without deleting unrelated changes. Capture the correction in implementation notes.
- [x] P1 — Storyboard Chidori and Kirin: 6–8 annotated panels each, showing body silhouette, hand/dragon origin, motion path, target and timing. Produce rough in-engine animatics with actual changing body poses, not final particles first.
- [x] P2 — Finish Chidori end-to-end. Validate palm attachment, forward thrust, mirrored contact, miss, reflection, voice and reduced motion. Produce a normal-speed clip plus slowed pose inspection. Do not batch-generate the rest before this pilot meets the visual gate.
- [x] P3 — Finish Kirin end-to-end. Validate formation above the battlefield, command gesture, dragon scale and vertical dive. Compare the two Sasuke moves side-by-side with labels hidden.
- [x] P4 — Implement the two Itachi techniques, then Tanjiro’s two sword techniques, then Zenitsu’s two speed techniques. Give each its own choreography and asset set. Check off each only after actual-renderer review.
- [x] P5 — Run integration, performance, motion and audio checks. Provide updated playable files, eight full-motion clips, eight reduced-motion clips and concise provenance. Do not stop at a design gallery.

Sol should execute sequentially and update this plan with completed work, evidence and remaining issues. User approval is not required for routine implementation choices; use the visual gates internally rather than repeatedly stopping to ask permission. Do not push, publish or merge unless the user authorizes that action.

Timeline implementation: make the animation manifest the authority for local pose/event timing. If new cosmetic markers require extending the queue, preserve ordered markers, duplicate suppression and long-frame partitioning. Voice holds may extend recovery, not accelerate speech or move contact independently of the body clip. Keep audio from clipping and preserve mute/missing-device behavior.

For any resource/Guard version of the game: honor `blocked`, `missed` and `reflected` results. Guard uses a block pose/sound and restrained contact effect; reflection selects the real recipient and shows a clear counter cue. Do not reverse the entire Kirin dragon simply because damage is reflected if that obscures the illusion counter. Preserve the server result and make the counter visually explicit.

## 7. Acceptance and verification

Visual gates for every move:

- [x] Body-only playback is coherent; important motion is not hidden by VFX or cut-ins.
- [x] Technique origin is obvious: palm / sky / gaze / sword / legs.
- [x] Forming, release, contact and recovery have different readable silhouettes.
- [x] VFX adhere to transformed sockets and do not jump on mirroring or trimming.
- [x] Labels-off comparison distinguishes all eight moves.
- [x] No generic portrait pre-roll remains in the default flow.
- [x] Normal-speed playback looks intentional, not just a pleasing freeze frame.

Technical checks:

- [x] One authoritative impact per action, visible HP at contact, no duplicate playback after repeated snapshots.
- [x] Long frame versus small-step simulation agrees through charge, release, hitstop and finish; queued specials do not overlap clocks or voices incorrectly.
- [x] Both sides, hit/miss/reflection and Guard when supported. Misses avoid destruction on the defender; reflected KO reaches correct result poses.
- [x] Reduced motion keeps readable formation/contact but suppresses shake, rapid camera travel and repeated screen flashes. Preserve Sixfold’s identity with subdued sequential accents rather than six rapid camera cuts.
- [x] Rematch/disconnect clears body overrides, effects, camera and pending markers.
- [x] Existing Python suite plus focused new behavior tests passes; adapt obsolete cinematic timing tests rather than deleting event invariants.
- [x] Repeat the 96-case renderer matrix if all eight powers change; extend with guarded-hit cases if available. Run representative real TCP exchanges on the actual implementation branch.
- [x] Measure headless median/p95/p99 render cost, cache growth and memory. Target a 16.7 ms frame budget where practical; never label a headless timing as verified live 60 FPS. Keep atlases, particles and caches bounded.
- [x] Check actual normal-speed video playback and representative keyframes, not merely successful encoding. State whether audio was reconstructed or recorded live.

Deliverables: completed `plan.md` checklist; updated runtime body/VFX assets and manifest; source/provenance notes; eight short final attack clips plus reduced-motion variants; test/performance evidence; a working game build or checkout. Final report must separate actual changes from remaining visual/asset gaps.

## 8. Prompt to give Sol

> Read `plan.md` and implement the technique-specific attack animation plan. The user rejected the generic portrait-first cinematics: prioritize actual jutsu choreography. Start with Chidori forming lightning in Sasuke’s palm and becoming a bare-hand thrust, then Kirin forming a dragon in the sky and diving on his downward command. Complete and inspect these pilots before expanding to all eight specials. Preserve current mechanics, unrelated edits, English audio and authoritative impact timing. Follow the asset, body-pose, reduced-motion and verification gates; deliver actual game-renderer evidence and update the checklist. Do not treat extra glow, camera shake, portrait zooms or translated static sprites as completed attack animation.

## Implementation record — 14 November 2026

- Working branch and both remote refs rechecked; main remains 58fc520, strategic-combat d3d01ce. Presentation work stays on the current animation branch.
- Removed mandatory portrait intro from runtime. Added 36 registered body keys: 12 Chidori, 12 Kirin, 12 Whirlpool; retimed and choreographed the other five specials with existing body artwork.
- Sasuke pilots: 24 render cases passed, both full-motion clips played through in the browser. Phase boards and body-only strips are in the jutsu-choreography review folder.
- 55 unit/integration tests passed, including current-frame rear/front water binding, real Sixfold endpoints and pre-release Kirin formation.
- Two real TCP-client scenarios passed: Itachi/Sasuke reflection and reflected-Kirin KO; Zenitsu heal/miss/ultimate KO.
- Asset validator passed: 36 clips, 128 body poses, 8 Kirin frames, 64 sampled cues and existing generated/impact layers.
- Reproduction sources and limitations are documented in docs/choreography-implementation.md. Official illustration fetches timed out; no claim of full-episode pose comparison.
- Refreshed final 96-case export passed after the water attachment fix. Median render 2.87 ms, p95 5.13 ms, p99 6.60 ms headlessly. This is not a live FPS measurement.
- Fresh extracted build passed 55 tests and the asset validator; final review page contains all eight attacks, reduced-motion clips, phase boards and body-only strips.
