import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from scripts.linkedin_sync import normalize_posts, select_since


class LinkedInSyncTests(unittest.TestCase):
    def test_normalize_posts_supports_api_elements_and_deduplicates(self):
        payload = {
            "elements": [
                {"id": "urn:li:share:2", "created": {"time": 1761868800000}, "commentary": "Second post"},
                {"id": "urn:li:share:1", "created": {"time": 1761782400000}, "commentary": "First post"},
                {"id": "urn:li:share:2", "created": {"time": 1761868800000}, "commentary": "Second post"},
            ]
        }
        posts = normalize_posts(payload)
        self.assertEqual([p["id"] for p in posts], ["urn:li:share:2", "urn:li:share:1"])
        self.assertEqual(posts[0]["text"], "Second post")
        self.assertEqual(posts[0]["date"], "2025-10-31")

    def test_normalize_posts_keeps_public_posts_only(self):
        payload = {
            "elements": [
                {"id": "public", "created": {"time": 1761868800000}, "commentary": "Public", "visibility": "PUBLIC"},
                {"id": "private", "created": {"time": 1761868800000}, "commentary": "Private", "visibility": "CONNECTIONS"},
            ]
        }
        posts = normalize_posts(payload)
        self.assertEqual([p["id"] for p in posts], ["public"])

    def test_select_since_excludes_older_posts_and_sorts_newest_first(self):
        posts = [
            {"id": "new", "date": "2026-01-01", "text": "new"},
            {"id": "old", "date": "2025-09-30", "text": "old"},
            {"id": "boundary", "date": "2025-10-01", "text": "boundary"},
        ]
        selected = select_since(posts, date(2025, 10, 1))
        self.assertEqual([p["id"] for p in selected], ["new", "boundary"])


if __name__ == "__main__":
    unittest.main()
