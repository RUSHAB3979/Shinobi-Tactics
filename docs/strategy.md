# Strategy rules, version 2

Both clients and the server must be updated together. The server ignores client damage overrides. Webcam success is reported by the client; these rules do not provide tamper-proof gesture attestation.

Start with 100 HP, 30 chakra, zero ultimate charge. Chakra caps at 100.

| Move | Effect | Chakra | Subsequent own turns unavailable |
|---|---|---|---|
| Attack | 15 damage, gain 10 chakra | Free | 0 |
| Jutsu | 28 damage, character effect | 30 | 1 |
| Ultimate | 50 damage; requires 3 successful offensive moves; consumes charge | 80 | 0 |
| Recover | Heal up to 20; unavailable at full HP | 25 | 3 |
| Guard | Reduce next hit by 70%; gain 15 chakra when hit | Free | 2 |

Damage reduction rounds to the nearest integer, half up. Guard expires when you take your next accepted turn. Invalid commands spend nothing and do not advance cooldowns. Cooldowns decrease on your accepted actions, then the chosen move gets its new cooldown. Reflected and guarded offensive moves count toward charge; misses do not. Failed Jutsu/Ultimate signs cost half chakra, consume the turn and apply cooldown, but preserve existing ultimate charge.

Character Jutsu:
- Sasuke: Guard reduction is 35% instead of 70% (18 damage through Guard).
- Itachi: 18 damage and a one-opponent-action reflection shield. The shield returns at most 20 damage instead of damaging Itachi. It expires even if the opponent guards, heals or misses. It can be used again after earning chakra and waiting through cooldown.
- Tanjiro: 28 damage and up to 8 self-healing, including when countered.
- Zenitsu: 40 damage if the opponent's immediately preceding action was Recover; otherwise 28.

The HUD exposes both players' chakra, ultimate charge and Guard. Buttons expose costs and remaining restrictions. Hover Jutsu/Ultimate to see the required hand signs. Opponent Guard and Zenitsu's Recover opportunity have explicit reminders.

Counterplay: save Guard for expensive techniques, use Chidori into Guard, bait Itachi's shield with a non-offensive action, and avoid predictable Recover against Zenitsu. Basic attacks build resources while stronger moves convert them into pressure.

Validation: unit/integration tests cover costs, cooldowns, reset, failures, Guard, character effects, fixed damage and presentation. `tools/verify_battle.py` exercises two real TCP clients, including legal resource-aware techniques and terminal rendering; `--reflection` checks a counter match. `tools/simulate_strategy.py` compares policies over 32 character/starting-position combinations. Initial result: mixed policy 32 wins, basic spam 0. These simulations assume successful gestures and do not establish webcam reliability, balanced character win rates or competitive depth against human opponents.
