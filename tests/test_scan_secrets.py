import unittest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from scan_secrets import scan_text

class TestSecretsMatcher(unittest.TestCase):
    def test_openai_key(self):
        text = "openai_key = 'sk-proj-1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuv'"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'OpenAI API Key' for r in results))

    def test_google_key(self):
        text = "google_key = 'AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q'"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'Google API Key' for r in results))

    def test_private_key(self):
        text = "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQD\n-----END PRIVATE KEY-----"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'Private Key' for r in results))

    def test_db_connection(self):
        text = "db = 'postgresql://user:pass@localhost:5432/db'"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'Database Connection' for r in results))

    def test_github_token(self):
        # Test ghp_ format
        text_ghp = "github_token = 'ghp_123456789012345678901234567890123456'"
        results_ghp = scan_text(text_ghp)
        self.assertTrue(any(r['type'] == 'GitHub Token' for r in results_ghp))
        self.assertEqual(results_ghp[0]['matched_value'], 'ghp_123456789012345678901234567890123456')

        # Test github_pat_ format
        text_pat = "github_pat = 'github_pat_1234567890123456789012345678901234567890123456789012345678901234567890123456789012'"
        results_pat = scan_text(text_pat)
        self.assertTrue(any(r['type'] == 'GitHub Token' for r in results_pat))
        self.assertEqual(results_pat[0]['matched_value'], 'github_pat_1234567890123456789012345678901234567890123456789012345678901234567890123456789012')

    def test_aws_key(self):
        text = "aws_key = 'AKIA1234567890ABCDEF'"
        results = scan_text(text)
        self.assertTrue(any(r['type'] == 'AWS Access Key ID' for r in results))
        self.assertEqual(results[0]['matched_value'], 'AKIA1234567890ABCDEF')

    def test_empty_input(self):
        self.assertEqual(scan_text(""), [])

    def test_no_secrets(self):
        self.assertEqual(scan_text("This text contains no secrets at all."), [])

    def test_multiple_secrets(self):
        text = (
            "openai_key = 'sk-proj-1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuv'\n"
            "google_key = 'AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q'\n"
            "github_token = 'ghp_123456789012345678901234567890123456'\n"
            "aws_key = 'AKIA1234567890ABCDEF'\n"
        )
        results = scan_text(text)
        self.assertEqual(len(results), 4)
        types = [r['type'] for r in results]
        self.assertIn('OpenAI API Key', types)
        self.assertIn('Google API Key', types)
        self.assertIn('GitHub Token', types)
        self.assertIn('AWS Access Key ID', types)

    def test_word_boundaries_false_positives(self):
        # OpenAI key embedded in longer words should not match
        text_openai_prefix = "abcsk-proj-1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuv"
        self.assertEqual(scan_text(text_openai_prefix), [])

        text_openai_suffix = "sk-proj-1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvxyz"
        self.assertEqual(scan_text(text_openai_suffix), [])

        # Google key embedded in longer words should not match
        text_google_prefix = "abcAIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q"
        self.assertEqual(scan_text(text_google_prefix), [])

        text_google_suffix = "AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Qxyz"
        self.assertEqual(scan_text(text_google_suffix), [])

        # GitHub token embedded in longer words should not match
        text_github_prefix = "abcghp_123456789012345678901234567890123456"
        self.assertEqual(scan_text(text_github_prefix), [])

        text_github_suffix = "ghp_123456789012345678901234567890123456xyz"
        self.assertEqual(scan_text(text_github_suffix), [])

        text_github_pat_prefix = "abcgithub_pat_1234567890123456789012345678901234567890123456789012345678901234567890123456789012"
        self.assertEqual(scan_text(text_github_pat_prefix), [])

        text_github_pat_suffix = "github_pat_1234567890123456789012345678901234567890123456789012345678901234567890123456789012xyz"
        self.assertEqual(scan_text(text_github_pat_suffix), [])

        # AWS key embedded in longer words should not match
        text_aws_prefix = "abcAKIA1234567890ABCDEF"
        self.assertEqual(scan_text(text_aws_prefix), [])

        text_aws_suffix = "AKIA1234567890ABCDEFxyz"
        self.assertEqual(scan_text(text_aws_suffix), [])

if __name__ == '__main__':
    unittest.main()
