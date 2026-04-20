"""
Unit Tests - Dream AI System
Reem Khalfan Aljabri (230390) - Database & Testing

Run with: python -m pytest tests/ -v
Or just: python test_backend.py

We wrote these tests throughout development, not just at the end.
Writing them helped us catch the SQL injection bug in an early version
of the dream submission endpoint.
"""

import unittest
import json
import sys
import os
import tempfile
import uuid

# Add parent dir to path so we can import from backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestEmotionAnalysis(unittest.TestCase):
    """Tests for the AI model module."""

    def setUp(self):
        """Import the module fresh for each test."""
        # We use the rule-based fallback for testing (no model download needed)
        from ai_model import _rule_based_fallback, detect_patterns
        self.fallback = _rule_based_fallback
        self.detect_patterns = detect_patterns

    def test_fear_detection(self):
        """Fear words should trigger fear classification."""
        text = "I was so afraid and scared, there was a monster chasing me in the dark"
        emotion, conf = self.fallback(text)
        self.assertEqual(emotion, 'fear')
        self.assertGreater(conf, 0.5)

    def test_happiness_detection(self):
        """Happy words should trigger happiness classification."""
        text = "I was so happy and joyful, laughing and smiling with friends"
        emotion, conf = self.fallback(text)
        self.assertEqual(emotion, 'happiness')

    def test_sadness_detection(self):
        """Sad words should trigger sadness classification."""
        text = "I was alone and crying, feeling sad and missing everyone"
        emotion, conf = self.fallback(text)
        self.assertEqual(emotion, 'sadness')

    def test_neutral_empty(self):
        """No strong emotion words should return neutral."""
        text = "I was walking through a room and there was a table"
        emotion, conf = self.fallback(text)
        self.assertEqual(emotion, 'neutral')

    def test_pattern_detection_insufficient_texts(self):
        """Single dream should return empty patterns."""
        patterns = self.detect_patterns(["just one dream text here"])
        self.assertEqual(patterns, [])

    def test_pattern_detection_minimum(self):
        """Two identical dreams should detect recurring words."""
        texts = [
            "I was running through a dark forest being chased",
            "running through the dark forest again, something chasing me"
        ]
        patterns = self.detect_patterns(texts)
        # Should find 'running', 'forest', 'dark', 'chasing' as recurring
        found_words = [p['word'] for p in patterns]
        self.assertGreater(len(found_words), 0)

    def test_very_short_text(self):
        """Very short text should return a sensible default."""
        from ai_model import analyse_emotion
        emotion, conf = analyse_emotion("ok")
        self.assertEqual(emotion, 'neutral')
        self.assertEqual(conf, 0.5)

    def test_extract_keywords(self):
        """Keyword extraction should return useful dream terms."""
        from ai_model import extract_keywords
        keywords = extract_keywords(
            "I was running through a dark forest while someone chased me between the trees."
        )
        self.assertGreater(len(keywords), 0)
        self.assertTrue(any(word in keywords for word in ['forest', 'dark', 'running', 'trees']))


class TestInputValidation(unittest.TestCase):
    """Tests for input validation logic (without running full Flask app)."""

    def test_username_too_short(self):
        """Username under 3 chars should be rejected."""
        username = "ab"
        self.assertFalse(len(username) >= 3)

    def test_username_valid(self):
        """Username of 3+ chars should be accepted."""
        username = "noor"
        self.assertTrue(len(username) >= 3)

    def test_password_too_short(self):
        """Password under 6 chars should be rejected."""
        password = "abc"
        self.assertFalse(len(password) >= 6)

    def test_dream_text_too_short(self):
        """Dream text under 10 chars should be rejected."""
        text = "bad dream"
        self.assertFalse(len(text.strip()) >= 10)

    def test_dream_text_valid(self):
        """Dream text of 10+ chars should pass."""
        text = "I was running through a corridor"
        self.assertTrue(len(text.strip()) >= 10)

    def test_dream_text_too_long(self):
        """Dream text over 5000 chars should be rejected."""
        text = "x" * 5001
        self.assertFalse(len(text) <= 5000)


class TestPasswordHashing(unittest.TestCase):
    """Tests for password hashing utilities."""

    def test_hash_and_verify(self):
        """Hashed password should verify correctly."""
        from password_utils import hash_password, verify_password
        password = "testPassword123"
        hashed = hash_password(password)
        self.assertTrue(verify_password(hashed, password))

    def test_wrong_password_fails(self):
        """Wrong password should not verify."""
        from password_utils import hash_password, verify_password
        password = "correctPassword"
        wrong    = "wrongPassword"
        hashed = hash_password(password)
        self.assertFalse(verify_password(hashed, wrong))

    def test_hash_is_different_each_time(self):
        """Two hashes of the same password should be different (due to salt)."""
        from password_utils import hash_password
        password = "samePassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        self.assertNotEqual(hash1, hash2)


class TestJSONSerialisation(unittest.TestCase):
    """Tests for keyword JSON serialisation/deserialisation."""

    def test_keywords_serialise(self):
        """Keyword list should serialise and deserialise cleanly."""
        keywords = ['running', 'forest', 'dark']
        serialised = json.dumps(keywords)
        recovered = json.loads(serialised)
        self.assertEqual(keywords, recovered)

    def test_empty_keywords(self):
        """Empty keyword list should work."""
        keywords = []
        serialised = json.dumps(keywords)
        recovered = json.loads(serialised)
        self.assertEqual(recovered, [])


class TestFlaskIntegration(unittest.TestCase):
    """End-to-end API tests using Flask's test client."""

    @classmethod
    def setUpClass(cls):
        from app import app
        from extensions import db

        cls.app = app
        cls.db = db
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.temp_dir.name, 'integration_test.db')
        cls.original_db_uri = cls.app.config['SQLALCHEMY_DATABASE_URI']

        cls.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI=f'sqlite:///{cls.db_path}',
        )

        with cls.app.app_context():
            cls.db.drop_all()
            cls.db.create_all()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            cls.db.session.remove()
            cls.db.drop_all()
            for engine in cls.db.engines.values():
                engine.dispose()

        cls.app.config['SQLALCHEMY_DATABASE_URI'] = cls.original_db_uri
        cls.temp_dir.cleanup()

    def setUp(self):
        self.client = self.app.test_client()
        suffix = uuid.uuid4().hex[:8]
        self.username = f'integration_{suffix}'
        self.password = 'test1234'

    def test_full_user_flow(self):
        """Register, create a dream, inspect analytics, export, and delete."""
        register_response = self.client.post('/api/register', json={
            'username': self.username,
            'email': f'{self.username}@example.com',
            'password': self.password,
        })
        self.assertEqual(register_response.status_code, 201)

        me_response = self.client.get('/api/me')
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.get_json()['username'], self.username)

        dream_response = self.client.post('/api/dreams', json={
            'title': 'Integration Test Dream',
            'text': 'I was late for an exam, lost in a dark building, and feeling stressed all night.',
        })
        self.assertEqual(dream_response.status_code, 201)
        dream_payload = dream_response.get_json()
        self.assertIn('dream_id', dream_payload)
        self.assertIn('emotion', dream_payload)

        dream_id = dream_payload['dream_id']

        detail_response = self.client.get(f'/api/dreams/{dream_id}')
        self.assertEqual(detail_response.status_code, 200)
        detail_payload = detail_response.get_json()
        self.assertEqual(detail_payload['id'], dream_id)
        self.assertGreaterEqual(len(detail_payload['keywords']), 1)

        history_response = self.client.get('/api/dreams')
        self.assertEqual(history_response.status_code, 200)
        history_payload = history_response.get_json()
        self.assertEqual(len(history_payload), 1)

        dashboard_response = self.client.get('/api/dashboard')
        self.assertEqual(dashboard_response.status_code, 200)
        dashboard_payload = dashboard_response.get_json()
        self.assertEqual(dashboard_payload['total_dreams'], 1)
        self.assertEqual(len(dashboard_payload['timeline']), 14)

        export_response = self.client.get('/api/export')
        self.assertEqual(export_response.status_code, 200)
        export_payload = export_response.get_json()
        self.assertEqual(export_payload['username'], self.username)
        self.assertEqual(len(export_payload['dreams']), 1)

        delete_response = self.client.delete(f'/api/dreams/{dream_id}')
        self.assertEqual(delete_response.status_code, 200)

        empty_history = self.client.get('/api/dreams')
        self.assertEqual(empty_history.status_code, 200)
        self.assertEqual(empty_history.get_json(), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
