"""Shared, deterministic combat rules. Only the server applies mutations."""
ACTIONS = ('ATTACK', 'JUTSU', 'ULTIMATE', 'HEAL', 'GUARD')
CHARACTERS = ('Sasuke', 'Itachi', 'Tanjiro', 'Zenitsu')
COST = dict(ATTACK=0, JUTSU=30, ULTIMATE=80, HEAL=25, GUARD=0)
COOLDOWN = dict(ATTACK=0, JUTSU=1, ULTIMATE=0, HEAL=3, GUARD=2)
DAMAGE = dict(ATTACK=15, JUTSU=28, ULTIMATE=50)
DESCRIPTIONS = ('15 DMG / +10 CH', '28 DMG / 30 CH', '50 DMG / 80 CH', '+20 HP / 25 CH', '70% BLOCK / +15 CH')


def initial_resources():
    return {p: dict(chakra=30, charge=0, cooldowns={a: 0 for a in ACTIONS},
                    guarding=False, last_move=None) for p in ('P1', 'P2')}


def unavailable(resource, action, hp=100):
    if action not in ACTIONS: return 'Unknown move'
    cd = resource['cooldowns'][action]
    if cd: return f'Cooldown: {cd} own turn(s)'
    if resource['chakra'] < COST[action]: return f'Need {COST[action]} chakra'
    if action == 'ULTIMATE' and resource['charge'] < 3: return 'Land 3 offensive moves to charge ultimate'
    if action == 'HEAL' and hp >= 100: return 'Health already full'
    return ''


def resolve(state, pid, action, success=True):
    """Apply an already validated turn, returning presentation metadata."""
    other = 'P2' if pid == 'P1' else 'P1'
    r, enemy = state.resources[pid], state.resources[other]
    char = state.characters[pid]
    # Decrement only after the player's next accepted move, never on rejected input.
    r['cooldowns'] = {a: max(0, n-1) for a, n in r['cooldowns'].items()}
    r['guarding'] = False
    state.genjutsu_shield[pid] = False
    offensive = action in DAMAGE
    failed = offensive and action != 'ATTACK' and not success
    r['chakra'] -= COST[action] // 2 if failed else COST[action]
    r['cooldowns'][action] = COOLDOWN[action]
    info = dict(action=action, by=pid, target=other, dmg=0, reflected=False,
                attacker_char=char, defender_char=state.characters[other], missed=failed)
    if action == 'GUARD':
        r['guarding'] = True
    elif action == 'HEAL':
        amount = min(20, 100-state.hp[pid])
        state.hp[pid] += amount
        info['amount'] = amount
    elif not failed:
        dmg = DAMAGE[action]
        if action == 'JUTSU' and char == 'Itachi': dmg = 18
        if action == 'JUTSU' and char == 'Zenitsu' and enemy['last_move'] == 'HEAL': dmg += 12
        if enemy['guarding']:
            # Chidori pierces half of Guard's reduction.
            reduction = 35 if action == 'JUTSU' and char == 'Sasuke' else 70
            dmg = max(1, (dmg * (100-reduction) + 50)//100)
            enemy['guarding'] = False
            enemy['chakra'] = min(100, enemy['chakra']+15)
            info['blocked'] = True
        if state.genjutsu_shield[other]:
            state.genjutsu_shield[other] = False
            dmg = min(20, dmg)
            state.hp[pid] = max(0, state.hp[pid]-dmg)
            info['reflected'] = True
        else:
            state.hp[other] = max(0, state.hp[other]-dmg)
        info['dmg'] = dmg
        if action == 'ATTACK': r['chakra'] = min(100, r['chakra']+10)
        if action == 'ULTIMATE': r['charge'] = 0
        else: r['charge'] = min(3, r['charge']+1)
        if action == 'JUTSU' and char == 'Itachi': state.genjutsu_shield[pid] = True
        if action == 'JUTSU' and char == 'Tanjiro':
            info['self_heal'] = min(8, 100-state.hp[pid])
            state.hp[pid] += info['self_heal']
    # A shield lasts exactly one opponent action, including a heal, guard or miss.
    state.genjutsu_shield[other] = False
    r['last_move'] = action
    return info
