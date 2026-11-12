"""Deterministic policy smoke comparison; not a proof of competitive balance."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from combat_rules import CHARACTERS, unavailable, resolve
from server import GameState


def choose(s, pid, policy):
    if policy == 'basic': return 'ATTACK'
    other = 'P2' if pid == 'P1' else 'P1'
    r, e = s.resources[pid], s.resources[other]
    choices = []
    if e['charge'] == 3 and e['chakra'] >= 80: choices.append('GUARD')
    if s.hp[pid] <= 40: choices.append('HEAL')
    choices += ['ULTIMATE', 'JUTSU', 'ATTACK']
    return next(a for a in choices if not unavailable(r, a, s.hp[pid]))


def main():
    results = dict(mixed_wins=0, basic_wins=0, draws=0, matches=0)
    for c1 in CHARACTERS:
        for c2 in CHARACTERS:
            for mixed in ('P1', 'P2'):
                s = GameState(); s.characters = dict(P1=c1, P2=c2)
                winner = None
                for turn in range(100):
                    pid = 'P1' if turn % 2 == 0 else 'P2'
                    resolve(s, pid, choose(s, pid, 'mixed' if pid == mixed else 'basic'))
                    if min(s.hp.values()) <= 0:
                        winner = max(s.hp, key=s.hp.get); break
                results['matches'] += 1
                results['draws' if winner is None else 'mixed_wins' if winner == mixed else 'basic_wins'] += 1
    print(json.dumps(results, indent=2))


if __name__ == '__main__': main()
