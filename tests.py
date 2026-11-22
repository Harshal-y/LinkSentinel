"""Offline smoke tests for core LinkSentinel validation and scoring."""
import os, tempfile, unittest

TMP = tempfile.NamedTemporaryFile(delete=False); TMP.close()
os.environ['DATABASE_PATH'] = TMP.name
from app import app, normalize_url, url_heuristics, public_ip

class LinkSentinelTests(unittest.TestCase):
    def test_default_https(self):
        self.assertEqual(normalize_url('example.com')[0], 'https://example.com/')
    def test_reject_javascript(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported URL scheme'):
            normalize_url('javascript:alert(1)')
    def test_reject_nonstandard_port(self):
        with self.assertRaisesRegex(ValueError, 'standard HTTP'):
            normalize_url('https://example.com:444')
    def test_reject_credentials(self):
        with self.assertRaisesRegex(ValueError, 'usernames or passwords'):
            normalize_url('https://user:pass@example.com')
    def test_risky_extension(self):
        score, findings = url_heuristics('https://example.com/setup.exe', 'example.com')
        self.assertGreaterEqual(score, 15)
        self.assertTrue(any('download extension' in f['title'] for f in findings))
    def test_private_ip_rejected(self):
        self.assertFalse(public_ip('127.0.0.1'))
        self.assertFalse(public_ip('192.168.1.1'))
    def test_public_ip_allowed(self):
        self.assertTrue(public_ip('1.1.1.1'))
    def test_health(self):
        with app.test_client() as c:
            self.assertEqual(c.get('/health').status_code, 200)

if __name__ == '__main__': unittest.main(verbosity=2)
