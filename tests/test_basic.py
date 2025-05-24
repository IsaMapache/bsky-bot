"""
Basic unit tests for Bluesky Twitch Live Bot.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, ConfigurationError
from twitch_monitor import TwitchMonitor, TwitchAPIError
from bluesky_poster import MockBlueSkyPoster


class TestConfig(unittest.TestCase):
    """Test configuration management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "twitch": {
                "username": "testuser",
                "client_id": "test_client_id",
                "client_secret": "test_client_secret"
            },
            "bluesky": {
                "handle": "test.bsky.social",
                "app_password": "test-password"
            },
            "settings": {
                "check_interval": 60,
                "post_template": "🔴 I'm live! https://twitch.tv/{username}"
            }
        }
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Mock the file reading
        with patch('builtins.open'), patch('json.load', return_value=self.test_config), patch('os.path.exists', return_value=True):
            config = Config("test_config.json")
            
            self.assertEqual(config.twitch_username, "testuser")
            self.assertEqual(config.twitch_client_id, "test_client_id")
            self.assertEqual(config.bluesky_handle, "test.bsky.social")
            self.assertEqual(config.check_interval, 60)
    
    def test_missing_config_file(self):
        """Test error when config file is missing."""
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(ConfigurationError):
                Config("nonexistent.json")
    
    def test_get_formatted_post(self):
        """Test post template formatting."""
        with patch('builtins.open'), patch('json.load', return_value=self.test_config), patch('os.path.exists', return_value=True):
            config = Config("test_config.json")
            formatted = config.get_formatted_post()
            self.assertIn("testuser", formatted)
            self.assertNotIn("{username}", formatted)


class TestTwitchMonitor(unittest.TestCase):
    """Test Twitch API monitoring."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = TwitchMonitor("test_client", "test_secret", "testuser")
    
    @patch('requests.post')
    def test_get_access_token(self, mock_post):
        """Test access token retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token", "expires_in": 3600}
        mock_post.return_value = mock_response
        
        token = self.monitor._get_access_token()
        self.assertEqual(token, "test_token")
    
    @patch('requests.get')
    @patch.object(TwitchMonitor, '_get_access_token')
    def test_stream_offline(self, mock_token, mock_get):
        """Test stream offline detection."""
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response
        
        is_live = self.monitor.is_live()
        self.assertFalse(is_live)
    
    @patch('requests.get')
    @patch.object(TwitchMonitor, '_get_access_token')
    def test_stream_online(self, mock_token, mock_get):
        """Test stream online detection."""
        mock_token.return_value = "test_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{
                "id": "123",
                "title": "Test Stream",
                "game_name": "Just Chatting",
                "viewer_count": 100
            }]
        }
        mock_get.return_value = mock_response
        
        is_live = self.monitor.is_live()
        self.assertTrue(is_live)
        
        stream_info = self.monitor.get_stream_info()
        self.assertEqual(stream_info["title"], "Test Stream")
    
    def test_stream_url(self):
        """Test stream URL generation."""
        url = self.monitor.get_stream_url()
        self.assertEqual(url, "https://twitch.tv/testuser")


class TestBlueSkyPoster(unittest.TestCase):
    """Test Bluesky posting functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.poster = MockBlueSkyPoster("test.bsky.social", "test-password")
    
    def test_mock_posting(self):
        """Test mock posting functionality."""
        success = self.poster.post("Test post")
        self.assertTrue(success)
        self.assertEqual(len(self.poster.posted_messages), 1)
        self.assertEqual(self.poster.posted_messages[0]['text'], "Test post")
    
    def test_duplicate_prevention(self):
        """Test duplicate post prevention."""
        # First post should succeed
        success1 = self.poster.post("Test duplicate")
        self.assertTrue(success1)
        
        # Immediate duplicate should be blocked
        success2 = self.poster.post("Test duplicate")
        self.assertFalse(success2)
        
        # Forced duplicate should succeed
        success3 = self.poster.post("Test duplicate", force=True)
        self.assertTrue(success3)
    
    def test_live_notification(self):
        """Test live notification posting."""
        success = self.poster.post_live_notification(
            username="testuser",
            stream_url="https://twitch.tv/testuser",
            stream_title="Test Stream",
            game_name="Just Chatting"
        )
        
        self.assertTrue(success)
        self.assertEqual(len(self.poster.posted_messages), 1)
        
        post_text = self.poster.posted_messages[0]['text']
        self.assertIn("live on Twitch", post_text)
        self.assertIn("Test Stream", post_text)
        self.assertIn("Just Chatting", post_text)
        self.assertIn("twitch.tv/testuser", post_text)


if __name__ == "__main__":
    unittest.main() 