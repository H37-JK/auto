import os
import unittest
from unittest.mock import patch
import autoclick_linux as app


class LinuxTests(unittest.TestCase):
    def test_x11_event_encoding(self):
        from Xlib import X
        from Xlib.protocol import event
        fields = dict(time=X.CurrentTime, root=1, window=2, child=X.NONE,
                      root_x=10, root_y=20, event_x=1, event_y=2,
                      same_screen=1, detail=1)
        for kind, state in ((event.ButtonPress, 0), (event.ButtonRelease, X.Button1Mask)):
            self.assertEqual(len(kind(state=state, **fields)._binary), 32)

    def test_key_edges(self):
        self.assertEqual(app.rising_keys({'F8'}, set()), {'F8'})
        self.assertEqual(app.rising_keys({'F8'}, {'F8'}), set())

    def test_jitter_is_not_cumulative(self):
        for _ in range(1000):
            x, y = app.jitter(100, 200)
            self.assertTrue(95 <= x <= 105)
            self.assertTrue(195 <= y <= 205)

    def test_no_display_fails_without_click(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'DISPLAY'):
                app.run(True)

    def test_wayland_is_rejected(self):
        with patch.dict(os.environ, {'DISPLAY': ':1', 'XDG_SESSION_TYPE': 'wayland'}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'Wayland'):
                app.run(True)


if __name__ == '__main__':
    unittest.main()
