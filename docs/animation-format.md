# Animation and presentation format

`assets/animations.json` version 1 is the only runtime body-animation source. The legacy `CHARACTERS.anim_map` in `client.py` is retained as audit metadata; it is not consulted by the player.

Each character has named `clips`. Required names are `idle`, `attack`, `jutsu`, `ultimate`, `heal`, `hit`, `guard`, `down`, and `victory`. Frames are an explicitly ordered list, never a directory listing. A frame contains `path` relative to the checkout, `duration` in seconds, and an `[x,y]` anchor in image pixels. Optional `offset` is measured in the same units. Clip fields are `source_facing` (`left` or `right`), `loop`, `hold`, `finish` (default `idle`), and `events` with a name and time in seconds from clip start.

```json
{
  "source_facing": "right",
  "loop": false,
  "finish": "idle",
  "frames": [
    {"path": "assets/curated/sasuke/pose_02.png", "duration": 0.14, "anchor": [88, 170]}
  ],
  "events": [{"name": "release", "time": 0.1}]
}
```

The illustration above is a schema example, not the complete attack. Live action clips require `release` and `impact` markers strictly before the clip end. `ClipLibrary.validate()` checks path existence, positive finite durations, anchors, event bounds, facing, and completion targets. `tools/validate_assets.py` additionally checks all four characters, required markers, decoded body frames, WAVs, and arena.

`AnimationPlayer` is mutable per actor. `ClipLibrary` shares only loaded images and transformed surfaces. Use one player for each participant even in a mirror match. `update(dt)` consumes elapsed seconds across frame boundaries and loops; `drain_events()` returns crossed markers once per playback. `down` and `victory` hold their terminal pose. Missing actions log an error and explicitly switch to idle.

`draw(surface, root, facing, scale)` mirrors the image and its anchor together. Export uses one fixed scale per source sheet. It does not fit each pose to a target height. Foot anchors are derived from reviewed alpha bounds; very low alpha noise is excluded from bounds. Frame stepping and bounds overlays are available in `tools/preview_animations.py`.

`PresentationQueue` queues authoritative server snapshots by `(match_id, action.id)`. It reads release/impact/duration from the same manifest. The server computes all HP and turn outcomes; the client delays only the displayed snapshot values until impact. Duplicate snapshots are ignored while distinct repeated attacks remain valid. The client runs body motion, effects, hit sound, reactions, and camera feedback from these markers. A 45 ms impact pause freezes presentation only; the main loop still polls the network.

Effects are separate tracks in `power_visuals.py`, re-exported by `battle_visuals.py`, with source, contact, and actual damage-recipient anchors. Reflection is an explicit branch. Sixfold has six ordered visual accents but one authoritative server damage event. Reduced motion removes camera shake, afterimages, and cross-arena body travel; it cuts to a contact position so melee still reaches the target, dims foreground effects, and slows crow/water motion.

Power frames add `sockets`, a mapping from `hand` or `weapon` to image-pixel `[x,y]` coordinates. `AnimationPlayer.socket(name, root, facing, scale)` applies exactly the same pivot/offset/mirroring as body drawing. `CombatEffect.bind` receives the current body root and socket positions each rendered frame. Chidori's charge is placed at the bare hand; sword spray/embers use the weapon socket. Do not use a fixed world coordinate for these attachments. Missing sockets use a chest-level fallback for base clips such as recoil, not for authored power poses.

`draw_background` renders clouds or the Tsukuyomi scene before actors; afterimages are drawn behind the actor; `draw` renders foreground effects after bodies. Both reusable effect layers stop at y=530, before the command panel; HUD elements are drawn afterward. Effects do not own blocking loops or calculate damage.

Generate base exports with `uv run --frozen python tools/export_sprites.py CHARACTER`, then apply `uv run --frozen python tools/export_powers.py`. The exporters record reviewed crop exceptions for swords extending into gutters. The latter exports 64 unique power poses at a fixed sheet scale, reviewed hand/weapon sockets, and eight Kirin VFX frames. Original base cell 3 remains excluded. Preserve both source atlases when refining poses.

The optional intro is a separate `VideoOverlay`, enabled with V, silent, skippable with ESC, and disabled by default. It imports OpenCV only when requested and leaves network/quit processing in the main loop. Combat ultimates use in-engine presentation and do not require video files.
