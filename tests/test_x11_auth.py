import unittest
from x11_auth import find_wildcard_auth
class AuthTests(unittest.TestCase):
    def test_wildcard_matches_display(self):
        self.assertEqual(find_wildcard_auth([(65535,b'',b'0',b'MIT-MAGIC-COOKIE-1',b'test')],0),(b'MIT-MAGIC-COOKIE-1',b'test'))
    def test_other_display_rejected(self):
        self.assertIsNone(find_wildcard_auth([(65535,b'',b'1',b'MIT-MAGIC-COOKIE-1',b'test')],0))
    def test_nonwildcard_rejected(self):
        self.assertIsNone(find_wildcard_auth([(256,b'other',b'0',b'MIT-MAGIC-COOKIE-1',b'test')],0))
