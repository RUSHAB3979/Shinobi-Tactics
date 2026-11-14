# Technique choreography implementation

The regular game now begins each power with its actual body animation. Mandatory portrait pre-roll and its separate intro clock have been removed from the client/queue. Optional portrait artwork is retained as source material and is not used for normal power playback.

## Implemented

- Chidori: 12 newly registered body keys, 0.75s palm formation, short dash, bare-hand contact at 1.20s, withdrawal/recovery cut at 1.60s. Irregular branching discharge follows the palm. The user-supplied Chidori voice remains intact and may extend recovery.
- Kirin: 12 newly registered body keys, skyward arm raise, cloud build, dragon formation beginning at 0.55s, readable held dragon, downward hand command/release at 1.55s and descending jaw contact at 2.05s. Cached rotated dragon frames support the dive. Reflection leaves the dragon directed at the original opponent and depicts an illusion return to the actual damage recipient.
- Genjutsu: retimed seal/gesture poses, caster fading into a crow stream, target hold and illusion ripples. The cast and later reflected attack remain separate server actions.
- Tsukuyomi: retimed eye-cast poses, red-moon realm, restrained target/ghost silhouettes and an illusion collapse. Its contact treatment no longer uses the generic physical burst.
- Whirlpool: 12 new body keys include rear/front rotation and a two-handed cutting arc. Water wraps behind and in front of the body; both layers bind to the current frame before drawing.
- Sun Breath: existing eight two-handed sword keys retimed for breath, lift, pivot, airborne descending slash and recovery; the fire arc follows the weapon angle and grip.
- Sixfold: six real directional movement segments/endpoints, matched cosmetic accents, a final sword pass, and one HP/contact event. Eight unique body poses are sequenced over ten frame entries.
- Godspeed: deep loaded stance followed by one fast approach and finishing pose, distinct from Sixfold. Reduced motion retains restrained cues and contact without rapid traversal.

New art: 36 body keys exported from three retained AI-generated source atlases. Existing Itachi, Sun Breath and Zenitsu body art is reused and retimed deliberately. There is no claim that all eight moves have newly drawn body art or that this is a frame-for-frame anime reproduction.

## Reproduction

Use the existing Python 3.12 venv. `tools/export_powers.py` reproduces the earlier library; run `tools/export_choreography.py` afterward to restore the new registrations and retimed clip definitions. `assets/sources/choreography/registration.json` holds editable socket, timing and grid data; `retimed-clips.json` preserves the reused-frame choreography. Scale is constant per atlas, determined from its model pose rather than per-frame bounds.

`tools/storyboard_techniques.py --output PATH` captures phase boards and body-only strips from the real renderer. `tools/verify_feedback.py --output PATH` checks 96 cases and exports eight full-motion plus eight reduced-motion clips. `--character Sasuke` runs the two pilots only. `tools/preview_battle.py` is an offline art reviewer; the normal server/client match uses the same presentation code.

## Reference scope

Research references remain in plan.md: official Chidori database, Kirin manga interview, Naruto developer breakdowns, SEGA character media. Direct requests for the two official manga illustrations timed out in this session. Implementation therefore uses the verified descriptions, the inspected existing character/dragon artwork and the documented 2D adaptations; no claim of frame-by-frame episode comparison is made. No third-party footage was imported as runtime animation.

## Verification

See the current review folder for test, render and TCP results. Clips use audio reconstructed from actual emitted combat events, not live speaker capture. Physical webcam recognition, speakers and compositor/vsync are outside this automated verification. This branch does not include the separate strategic-combat resource/Guard changes.
