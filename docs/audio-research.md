# Downloaded combat audio — research and coverage

Prepared 10 November 2026 for the requested **English dub character voices**. The game now uses 63 prepared sampled cues: 11 English voice clips and 52 anticipation/release/contact/block/recovery cues. All 12 offensive moves and four recovery slots have sampled effects. Four character-voice archives cover three characters (Itachi, Tanjiro, Zenitsu); the second Tanjiro archive supplies Hinokami Kagura.

**The exact English voice requirement remains incomplete for Sasuke.** No verified English Chidori or Kirin callout was acquired. Genjutsu and Tsukuyomi use Itachi's general English battle lines, not those spoken move names. These gaps are explicit in the manifest and preview. No AI imitation was substituted.

## Move coverage

| Character | Move | Effects | Voice selection |
| --- | --- | --- | --- |
| Sasuke | Katana | Sampled release + contact | No verified English callout selected |
| Sasuke | Chidori | Sampled release + contact | No verified English callout selected |
| Sasuke | Kirin | Sampled release + contact | No verified English callout selected |
| Sasuke | Recover | Sampled recovery | No verified English callout selected |
| Tanjiro | Slash | Sampled release + contact | English game voice pack: Battle effort |
| Tanjiro | Whirlpool | Sampled release + contact | English game voice pack: Whirlpool skill line (source filename and surrounding Sixth Form clips; listen for final selection) |
| Tanjiro | Sun Breath | Sampled release + contact | English game voice pack: Hinokami Kagura callout; Sun Breath family |
| Tanjiro | Recover | Sampled recovery | English game voice pack: Recovery response |
| Itachi | Kunai | Sampled release + contact | English game voice pack: Battle effort |
| Itachi | Genjutsu | Sampled release + contact | English game voice pack: General battle line; not a named Genjutsu callout |
| Itachi | Tsukuyomi | Sampled release + contact | English game voice pack: General battle line; not a named Tsukuyomi callout |
| Itachi | Recover | Sampled recovery | English game voice pack: Recovery response |
| Zenitsu | Slash | Sampled release + contact | English game voice pack: Battle effort |
| Zenitsu | Sixfold | Sampled release + contact | English game voice pack: Sixfold callout |
| Zenitsu | Godspeed | Sampled release + contact | English game voice pack: God-like Speed callout |
| Zenitsu | Recover | Sampled recovery | No verified English callout selected |

Tanjiro's Whirlpool selection is skill 01, take 02, accompanied in the source by Sixth Form and combined skill takes. Tiny English speech recognition struggles with the shouted word; listen in the preview before treating the spelling or pronunciation as independently verified. Hinokami Kagura is used for the game's broader Sun Breath action. Zenitsu's Sixfold and God-like Speed clips were identified in the Entertainment District pack. No offensive phrase is attached to Zenitsu's recovery.

## Downloaded sources used by the game

| ID | Original source / credit | Source license status |
| --- | --- | --- |
| sword | [StarNinjas](https://opengameart.org/content/20-sword-sound-effects-attacks-and-clashes) | CC0-1.0 |
| clash | [StarNinjas](https://opengameart.org/content/20-sword-sound-effects-attacks-and-clashes) | CC0-1.0 |
| sfx100 | [rubberduck](https://opengameart.org/content/100-cc0-sfx-2) | CC0-1.0 |
| spells | [Augmentality (Brandon Morris), submitted by HaelDB](https://opengameart.org/content/spell-sounds) | CC0-1.0 |
| demon | [Theoracle1185](https://sounds.spriters-resource.com/pc_computer/demonslayerkimetsunoyaibathehinokamichronicles2/asset/558618/) | Copyrighted game audio |
| itachi | [bigbingchillin](https://sounds.spriters-resource.com/pc_computer/narutoshippudenultimateninjastorm4/asset/503871/) | Copyrighted game audio |
| tanjiro | [Theoracle1185](https://sounds.spriters-resource.com/pc_computer/demonslayerkimetsunoyaibathehinokamichronicles2/asset/558012/) | Copyrighted game audio |
| hinokami | [Theoracle1185](https://sounds.spriters-resource.com/pc_computer/demonslayerkimetsunoyaibathehinokamichronicles2/asset/557983/) | Copyrighted game audio |
| zenitsu | [Theoracle1185](https://sounds.spriters-resource.com/pc_computer/demonslayerkimetsunoyaibathehinokamichronicles2/asset/558021/) | Copyrighted game audio |

The Sounds Resource archives are original game recordings, not newly licensed voice performances. Their availability does not transfer rights to the underlying recordings. The source's [terms of use](https://sounds.spriters-resource.com/page/tou/) limit commercial/marketplace use and describe use in unpublished, noncommercial works. This is a local prototype asset integration; no public-release clearance is asserted. StarNinjas, rubberduck, and Augmentality effects are separately marked CC0 according to their source pages. Credits for the game archives identify their uploaders, not owners of the recordings.

## Search and selection decisions

- Retrieved Itachi (English), Tanjiro (English), Hinokami Tanjiro (English), and Zenitsu Entertainment District (English) packs from their per-asset pages. Validated archive CRCs, file counts, and SHA-256 checksums. The four archives contain 927 WAV voice files in total, with some material shared between Tanjiro variants.
- Retrieved the 337-file Demon Slayer battle-effects archive. Selected water, kagura/fire, lightning charge, thunder draw, and electrical contact samples for Tanjiro/Zenitsu. These are game effects, not proof that a recording is the anime's exact original sound.
- Downloaded StarNinjas' 20 sword attacks/clashes, rubberduck's 100 effects, and Augmentality's electric, teleport and healing recordings. Composed Sasuke/Itachi elemental and illusion effects from these downloaded samples. Genjutsu's flutter and Tsukuyomi's reversed swell are authored sample edits, not claimed as original anime effects.
- Downloaded and scanned the 349-file [Storm 2 English Chapter 5 dialogue](https://sounds.spriters-resource.com/playstation_3/narutoshippudenultimateninjastorm2/asset/402195/). It contains story dialogue and did not supply verified Chidori/Kirin/Tsukuyomi calls. Kept it as an unused research download. Its Deflate64 ZIP was CRC-checked/extracted with `zipfile-deflate64` in the separate analysis environment.
- Checked the [Sasuke Storm 4 mod source](https://thunderstore.io/c/riskofrain2/p/Zerneas/SasukeShippudenMod/) because its author lists English/Japanese Storm 4 voices and Chidori/Kirin effects. HTTP downloads returned 403; browser downloads did not produce an archive. The linked GitHub repository contains media/docs, no raw audio. No mod code was installed or executed, and no extracted audio from this source is included.
- Soundboard candidates: [Chidori 1](https://www.101soundboards.com/sounds/208283-chidori-1), [Kirin](https://www.101soundboards.com/sounds/24132972-kirin), and [Voicy Chidori](https://www.voicy.network/sounds/Ql2X4IQ1uEeF-dfZENZ_xw-sasuke-uses-chidori). Search titles alone do not establish English language, speaker, or a clean music-free recording. The 101 page remained at automated verification. No verified clip from these candidates was integrated.
- Downloaded the [CC0 generic male effort pack](https://opengameart.org/content/male-gruntyelling-sounds) as a fallback candidate but did not use it: it is not these English dub characters. Existing repository MP3s also remain outside the new selection; their language/provenance was insufficient for this request.
- A normal Zenitsu archive download did not complete. The smaller Entertainment District English archive did complete and supplies the relevant Sixfold/Godspeed lines. No partial file is included in deliverables.

## Processing and implementation

`assets/audio/combat.json` maps every move to its voice/anticipation/release/contact/block samples and records 46 retained source masters with URLs, credits, and SHA-256 hashes. `tools/import_combat_audio.py` checks those masters and deterministically decodes/mixes them with FFmpeg into mono 44.1 kHz, 16-bit PCM WAVs. Outer silence is trimmed with 35 ms padding; per-layer fades avoid clicks; peaks stay below full scale. There is no voice cloning, pitch shifting, or accelerated speech. Resampling standardizes playback; it does not restore detail missing from the original recordings.

`combat_audio.py` reserves separate voice, start, release and impact channels. It lowers effects while a voice is active, applies the existing master volume/mute, stops old audio at a new action/disconnect/rematch, caches decoded sounds, and retains the generated fallback cues if a sample is absent. Audio-device failure remains nonfatal.

Voice begins at action start. Release and contact use the original animation markers. Misses play anticipation/release without contact; reflection plays block. Where speech exceeds the body clip, only the presentation's recovery hold is extended; movement, release/contact markers, damage, hand signs and server rules are unchanged. The longest selected voice lasts about 2.13 seconds.

The browser audition provides all 16 move mixes, effects-only and voice-only comparisons, volume control, the earlier power visual previews, original archive downloads, and the coverage labels. Full mixes use the same release/contact offsets and duck level as the running game; a peak limiter only attenuates if their combined export needs headroom. The historical power reel still has its earlier synthesized soundtrack; use this audio preview for the current selection.

## Verification

- 37 automated tests pass, including eight audio regressions: stage order/deduplication, miss without impact, reflected block, voice recovery hold, ducking/master mute, missing sample/device fallback, audio cleanup, and decoding/headroom across all 63 runtime samples.
- All 63 WAVs decode in Pygame, have nonzero signal, silent endpoints and peak headroom. Per-cue duration/RMS/peak/checksum measurements are in `audio-metrics.json`.
- Runtime asset validation includes all sampled references as well as existing body/VFX/fallback assets.
- Updated real TCP checks wait for presentation completion, since a voiced ultimate plus ending pose can exceed their old fixed three-second budget. Current run results are recorded in `delivery-checks.json`.
- Physical speaker playback and a human ear review remain unverified. English source-pack labels and CPU speech recognition were used to identify candidates; they do not independently certify actor identity or final subjective sound quality.

## Remaining targeted work

1. Acquire verified clean English Sasuke Chidori/Kirin calls and a named Itachi Tsukuyomi/Genjutsu call if available; replace the explicit gaps/general lines in the manifest. Keep publisher/performer/source credits and permission status accurate.
2. Listen to each shortlisted line in the preview on the laptop, especially Whirlpool and the Hinokami Kagura substitution. Check speech intelligibility over the release/contact effects and refine levels/crops if needed.
3. Before publishing a build, resolve rights for game/anime recordings or replace them with cleared original performances and effects. No publishing action was requested or performed.


## Battle impact integration

The latest renderer adds a fifth reserved audio channel for seven original low-frequency contact layers. Impact and weight channels pan toward the actual damage recipient. Voice, anticipation and release retain their positions and ducking. These layers are generated by `tools/build_impact_audio.py`; the original sampled-source manifest remains unchanged. The latest battle-impact preview includes these layers and captures the stronger hitstop; the source audition page retains its earlier source-only mixes.
