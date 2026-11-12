# Visual glowup — research and art direction

## Research used

- [Riot Games: Visual Effects](https://www.riotgames.com/en/artedu/visual-effects) describes the balance between spectacle and gameplay clarity, with a consistent style and effects that belong to their character. Applied here as restrained ambient particles, quiet floor space, coherent elemental colors and light attached to the attack/contact location.
- [Arc System Works: Guilty Gear Strive](https://www.guiltygear.com/ggst/en/) presents its visual identity around 2.5D graphics and cinematic camera work. The application here is our own design decision: angular HUD panels, a brief ultimate title cut-in and deliberate composition. This Pygame game remains a 2D sprite renderer; no 3D capability is claimed.
- [GDC: GuiltyGearXrd's Art Style — The X Factor Between 2D and 3D](https://www.gdcvault.com/play/1022031/GuiltyGearXrd-s-Art-Style-The) summarizes Arc System Works' goal of preserving 2D character in a modern renderer. Only the public session summary was consulted, not a claimed viewing of the entire talk. It supports choosing a coherent painted/cel look over trying to simulate photorealism.
- [Bandai Namco: Naruto Storm Connections](https://www.bandainamcoent.com/games/naruto-x-boruto-ultimate-ninja-storm-connections) is the official thematic reference for the ninja battle presentation. No commercial artwork was copied into the new arena or UI.

These are references and design principles, not a claim that the new build reproduces those commercial games' animation or rendering systems.

## Implemented

New original painted shrine arena; foreground fighter positions `(195,450)` / `(810,420)`; unified top health HUD with damage-lag segment; larger command cards; coherent menu/selection/result typography; stationary readable status panels; ultimate ink-banner entrance; socket/contact-bound elemental light with ground spill; subdued vignette and sparse drifting ash. Existing eight-pose power attacks, sampled sound, camera impulses and elemental aftermath remain integrated. Reduced motion removes ambient motion and banner translation, while keeping light intensity lower.

The lighting textures and typography are cached. Fonts ship with the game rather than depending on installed system fonts. No extra runtime Python dependency was added. Combat rules, damage, networking and hand-sign requirements are unchanged.

## New assets and provenance

- `assets/arena-glowup.png`: generated with the built-in image-generation tool, then copied unchanged into the project. The original `arena.png` is retained as a fallback. Runtime scaling uses Pygame smoothscale. Full generation prompt below.
- `assets/fonts/SpaceGrotesk-Bold.otf`: unmodified locally installed Space Grotesk, copyright Google (2016) and Florian Karsten (2018), SIL Open Font License 1.1. Full license is bundled at `assets/fonts/OFL-SpaceGrotesk.txt`.
- The character sprites and recorded voices/effects retain their earlier provenance and documented limits; this pass does not add missing English Sasuke or named Itachi callouts.

## Exact arena generation prompt

Create a premium hand-painted 2D anime fighting-game BACKGROUND asset, landscape 16:10. No characters, no text, no UI, no watermark. An original ruined Japanese mountain shrine courtyard at twilight during an approaching storm. Art direction: dramatic cel-painted anime environment with elegant sharp brushwork, deep midnight indigo and desaturated teal, amber lantern pools, a restrained warm coral sunset opening behind mountains, atmospheric layered silhouettes, wet slate stone courtyard with subtle reflections. Not pixel art, not photoreal, no blurry bloom. Composition essential for gameplay: horizon at 38% from top, broad flat unobstructed open stone fighting floor covering lower 60%, all large architecture/tree trunks to far left/right edges, distant shrine and broken torii at upper center, plenty of calm dark negative space around fighter positions at x19% y65% and x79% y42%. The upper 15% will have a HUD so don't put crucial landmarks there. Cinematic luminous clouds, small hanging paper talismans, ancient lanterns, sculptural roots framing sides, a few red leaves near corners, richly detailed but center floor quiet and readable. Lighting bright enough to distinguish dark-haired fighters on the floor. Deliver a finished game-ready painted environment, not a mockup.

The generated floor begins lower than requested. Instead of placing a fighter over the distant landscape, both actor roots were moved onto the visible courtyard and both-side contact/reflection cases were rechecked.

## Review limits

The previews show the actual Pygame renderer. Audio is reconstructed from its emitted events and selected WAV files. Headless timing is CPU update/draw cost, not live display FPS. Physical speaker listening, live Wayland/vsync and optional camera recognition remain outside the verified scope. The existing audio report records exact English voice gaps and recording reuse terms.
