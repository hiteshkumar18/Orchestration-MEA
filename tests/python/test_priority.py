"""A priority line ahead of the regular one.

Priority dates start before every regular date still waiting, first come
first served among themselves. Nothing running is stopped for them, and a
waiting date can be moved into the priority line or back.
"""
import time
import unittest
from pathlib import Path

import _path  # noqa: F401
import test_watch_list as watch_list
from watcher import JOB_ACTIVITY


ANA = watch_list.ANA


class PriorityTest(watch_list.Lab):
    # The watch-list tests' stand-in jobs; their tests are not run again here.
    make = watch_list.WatchTest.make
    wait_for = watch_list.WatchTest.wait_for

    def started_order(self, w):
        return [e["run"] for e in sorted(w.state.all().values(), key=lambda e: e["started_at"])]

    def all_done(self, w):
        return self.wait_for(lambda: all(e.get("status") == "done" for e in w.state.all().values()), 60)

    def line(self, w):
        return [r["run"] for r in sorted((r for r in w.snapshot()["runs"] if r.get("line_position")),
                                         key=lambda r: r["line_position"])]

    def test_priority_dates_go_ahead_of_regular_ones(self):
        a = self.project("A", ["260901", "260902", "260903", "260904", "260905"])
        w = self.make(max_concurrent_activity=1)
        w.cfg.add_watch(str(a), ANA)
        d1, d2, d3, p1, p2 = sorted(a.iterdir())
        for d in (d1, d2, d3, p1, p2):
            self.seconds[d.name] = 0.6
        for d in (d1, d2, d3):
            w.dispatch(d, JOB_ACTIVITY)
            time.sleep(0.05)
        self.assertTrue(self.wait_for(lambda: w.state.status(w.state_key(d1.resolve(), JOB_ACTIVITY)) == "running"))
        w.dispatch(p1, JOB_ACTIVITY, priority=True)
        time.sleep(0.05)
        w.dispatch(p2, JOB_ACTIVITY, priority=True)
        self.assertEqual(self.line(w), ["260904", "260905", "260902", "260903"])
        self.assertTrue(self.all_done(w))
        self.assertEqual(self.started_order(w), ["260901", "260904", "260905", "260902", "260903"],
                         "the running date finishes first; priority ones next, in their order")
        self.assertTrue(w.state.get(w.state_key(p1.resolve(), JOB_ACTIVITY))["priority"])
        self.assertFalse(w.state.get(w.state_key(d2.resolve(), JOB_ACTIVITY))["priority"])

    def test_a_waiting_date_can_be_moved_up_and_back(self):
        a = self.project("A", ["260901", "260902", "260903", "260904"])
        w = self.make(max_concurrent_activity=1)
        w.cfg.add_watch(str(a), ANA)
        d1, d2, d3, d4 = sorted(a.iterdir())
        self.seconds.update({"260901": 3, "260902": 0.3, "260903": 0.3, "260904": 0.3})
        for d in (d1, d2, d3, d4):
            w.dispatch(d, JOB_ACTIVITY)
            time.sleep(0.05)
        k = lambda d: w.state_key(d.resolve(), JOB_ACTIVITY)
        self.assertTrue(self.wait_for(lambda: w.state.status(k(d1)) == "running"))

        self.assertEqual(w.set_priority([k(d4)], True), [k(d4)])
        self.assertEqual(self.line(w), ["260904", "260902", "260903"])
        self.assertEqual(w.set_priority([k(d3)], True), [k(d3)])
        self.assertEqual(self.line(w), ["260904", "260903", "260902"], "behind the earlier priority one")
        self.assertEqual(w.set_priority([k(d4)], False), [k(d4)])
        self.assertEqual(self.line(w), ["260903", "260902", "260904"], "back of the regular line")

        self.assertEqual(w.set_priority([k(d1)], True), [], "a running date is left alone")
        self.assertEqual(w.state.status(k(d1)), "running")
        self.assertEqual(w.set_priority([k(d3)], True), [], "already priority")
        self.assertTrue(self.all_done(w))
        self.assertEqual(self.started_order(w), ["260901", "260903", "260902", "260904"])

    def test_queueing_by_hand_as_priority(self):
        a = self.project("A", ["260901", "260902", "260903"])
        w = self.make(max_concurrent_activity=1)
        w.cfg.add_watch(str(a), ANA)
        d1, d2, d3 = sorted(a.iterdir())
        self.seconds.update({"260901": 1.5, "260902": 0.3, "260903": 0.3})
        w.queue_folders([str(d1), str(d2)], user=ANA)
        r = w.queue_folders([str(d3)], user=ANA, priority=True)
        self.assertEqual(len(r["queued"]), 1)
        e = w.state.get(w.state_key(d3.resolve(), JOB_ACTIVITY))
        self.assertTrue(e["priority"])
        self.assertTrue(self.all_done(w))
        self.assertEqual(self.started_order(w), ["260901", "260903", "260902"])

    def test_queued_again_without_priority_is_regular(self):
        a = self.project("A", ["260901"])
        w = self.make(max_concurrent_activity=1)
        w.cfg.add_watch(str(a), ANA)
        d = next(a.iterdir())
        w.dispatch(d, JOB_ACTIVITY, priority=True)
        self.assertTrue(self.all_done(w))
        w.dispatch(d, JOB_ACTIVITY)
        key = w.state_key(d.resolve(), JOB_ACTIVITY)
        self.assertFalse(w.state.get(key)["priority"])
        self.assertNotIn(key, w._priority)
        self.assertTrue(self.all_done(w))


if __name__ == "__main__":
    unittest.main()
