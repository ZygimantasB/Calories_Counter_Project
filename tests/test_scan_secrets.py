import unittest
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
from scan_secrets import scan_text

class TestSecretsMatcher(unittest.TestCase):
    def test_openai_key(self):
        text = "openai_key = 'sk-proj-1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz'"
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

if __name__ == '__main__':
    unittest.main()
