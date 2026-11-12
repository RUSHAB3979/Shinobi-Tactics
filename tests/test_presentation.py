import unittest
from battle_presentation import PresentationQueue


def snapshot(identity=1, **changes):
    state=dict(match_id="test-match",phase="BATTLE",turn="P2",hp_p1=100,hp_p2=85,
               char_p1="Sasuke",char_p2="Sasuke",winner=None,
               last_action=dict(id=identity,action="ATTACK",by="P1",dmg=15))
    state.update(changes)
    return state


class PresentationTests(unittest.TestCase):
    def queue(self):
        return PresentationQueue(lambda *_:dict(release=.18,impact=.34,duration=.72))

    def test_hp_changes_at_impact_only(self):
        q=self.queue()
        q.enqueue(snapshot())
        q.update(.33)
        self.assertEqual(q.visible_hp["P2"],100)
        q.update(.01)
        self.assertEqual(q.visible_hp["P2"],85)

    def test_duplicate_and_repeated_moves(self):
        q=self.queue()
        self.assertTrue(q.enqueue(snapshot()))
        self.assertFalse(q.enqueue(snapshot()))
        self.assertTrue(q.enqueue(snapshot(2,hp_p2=70)))
        events=q.update(2)
        self.assertEqual([k for k,_ in events],["start","release","impact","finish"]*2)
        self.assertEqual(q.visible_hp["P2"],70)
        self.assertFalse(q.busy)

    def test_does_not_calculate_damage(self):
        for state in [snapshot(hp_p2=100),snapshot(hp_p1=85,hp_p2=100),
                      snapshot(hp_p1=100,hp_p2=100)]:
            q=self.queue()
            q.enqueue(state)
            q.update(1)
            self.assertEqual(q.visible_hp,{"P1":state["hp_p1"],"P2":state["hp_p2"]})

    def test_reset_allows_new_match(self):
        q=self.queue()
        q.enqueue(snapshot())
        q.update(.2)
        q.reset()
        self.assertFalse(q.busy)
        self.assertEqual(q.visible_hp["P2"],100)
        self.assertTrue(q.enqueue(snapshot()))

    def test_variable_dt_preserves_order(self):
        for dt in [1/30,1/60,1/120,.7,2]:
            q=self.queue()
            q.enqueue(snapshot())
            events=[]
            for _ in range(round(2/dt)+1): events.extend(q.update(dt))
            self.assertEqual([k for k,_ in events],["start","release","impact","finish"])


if __name__=="__main__":unittest.main()
