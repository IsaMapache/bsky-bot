"""
Bluesky posting functionality for live stream notifications.
Handles posting to Bluesky using the AT Protocol SDK.
"""

import logging
from typing import Optional
from datetime import datetime

try:
    from atproto import Client
    from atproto.exceptions import AtProtocolError
except ImportError:
    # Fallback for development/testing
    Client = None
    AtProtocolError = Exception


class BlueSkyPostError(Exception):
    """Raised when there's an issue posting to Bluesky."""
    pass


class BlueSkyPoster:
    """Handle posting notifications to Bluesky."""
    
    def __init__(self, handle: str, app_password: str):
        """
        Initialize Bluesky poster.
        
        Args:
            handle: Bluesky handle (e.g., "user.bsky.social")
            app_password: App-specific password for Bluesky
        """
        if Client is None:
            raise BlueSkyPostError("atproto library not available. Install with: pip install atproto")
        
        self.handle = handle
        self.app_password = app_password
        self._client: Optional[Client] = None
        
        self.logger = logging.getLogger(f"{__name__}.{self.handle}")
        
        # Track last post to prevent duplicates
        self._last_post_content: Optional[str] = None
        self._last_post_time: Optional[datetime] = None
    
    def _get_client(self) -> Client:
        """
        Get authenticated Bluesky client.
        
        Returns:
            Authenticated AT Protocol client
            
        Raises:
            BlueSkyPostError: If unable to authenticate
        """
        if self._client is not None:
            return self._client
        
        try:
            self.logger.info("Logging into Bluesky")
            client = Client()
            profile = client.login(self.handle, self.app_password)
            
            self.logger.info(f"Successfully logged into Bluesky as: {profile.display_name or self.handle}")
            self._client = client
            return self._client
            
        except AtProtocolError as e:
            raise BlueSkyPostError(f"Failed to authenticate with Bluesky: {e}")
        except Exception as e:
            raise BlueSkyPostError(f"Unexpected error authenticating with Bluesky: {e}")
    
    def post(self, text: str, force: bool = False) -> bool:
        """
        Post text to Bluesky.
        
        Args:
            text: Text content to post
            force: Force post even if duplicate
            
        Returns:
            True if post was successful, False if skipped
            
        Raises:
            BlueSkyPostError: If unable to post
        """
        # Check for duplicate posts (unless forced)
        if not force and self._is_duplicate_post(text):
            self.logger.info("Skipping duplicate post")
            return False
        
        try:
            client = self._get_client()
            
            self.logger.info(f"Posting to Bluesky: {text[:50]}...")
            post_response = client.send_post(text)
            
            # Store for duplicate detection
            self._last_post_content = text
            self._last_post_time = datetime.now()
            
            self.logger.info("Successfully posted to Bluesky")
            return True
            
        except AtProtocolError as e:
            raise BlueSkyPostError(f"Failed to post to Bluesky: {e}")
        except Exception as e:
            raise BlueSkyPostError(f"Unexpected error posting to Bluesky: {e}")
    
    def post_live_notification(self, username: str, stream_url: str, 
                              stream_title: Optional[str] = None,
                              game_name: Optional[str] = None) -> bool:
        """
        Post a live stream notification.
        
        Args:
            username: Twitch username
            stream_url: URL to the stream
            stream_title: Optional stream title
            game_name: Optional game being played
            
        Returns:
            True if post was successful, False if skipped
        """
        # Build the post content
        post_lines = ["🔴 I'm live on Twitch rn come slide!~ #blacksygamers #gaming #twitch #streaming https://twitch.tv/VideoGameComrade/"]
        
        if stream_title:
            post_lines.append(f"📺 {stream_title}")
        
        if game_name:
            post_lines.append(f"🎮 Playing {game_name}")
        
        post_lines.append(f"Join me: {stream_url}")
        
        post_text = "\n".join(post_lines)
        
        return self.post(post_text)
    
    def _is_duplicate_post(self, text: str) -> bool:
        """
        Check if this would be a duplicate post.
        
        Args:
            text: Text content to check
            
        Returns:
            True if this appears to be a duplicate
        """
        if self._last_post_content is None:
            return False
        
        # Check if content is identical
        if self._last_post_content == text:
            # Check if it was posted recently (within 2 hours)
            if (self._last_post_time and 
                (datetime.now() - self._last_post_time).total_seconds() < 7200):
                return True
        
        return False
    
    def test_connection(self) -> bool:
        """
        Test the connection to Bluesky.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            client = self._get_client()
            # Try to get our own profile as a test
            profile = client.get_profile(self.handle)
            self.logger.info(f"Connection test successful. Profile: {profile.display_name or self.handle}")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def reset_duplicate_tracking(self) -> None:
        """Reset duplicate post tracking."""
        self._last_post_content = None
        self._last_post_time = None
        self.logger.info("Reset duplicate post tracking")


class MockBlueSkyPoster(BlueSkyPoster):
    """Mock Bluesky poster for testing without actual posting."""
    
    def __init__(self, handle: str, app_password: str):
        """Initialize mock poster."""
        self.handle = handle
        self.app_password = app_password
        self.logger = logging.getLogger(f"{__name__}.mock.{self.handle}")
        
        self._last_post_content: Optional[str] = None
        self._last_post_time: Optional[datetime] = None
        
        # Track all mock posts
        self.posted_messages = []
    
    def _get_client(self):
        """Mock client always succeeds."""
        return self
    
    def post(self, text: str, force: bool = False) -> bool:
        """Mock posting - just log and store."""
        if not force and self._is_duplicate_post(text):
            self.logger.info("Skipping duplicate mock post")
            return False
        
        self.logger.info(f"MOCK POST to Bluesky: {text}")
        self.posted_messages.append({
            'text': text,
            'time': datetime.now()
        })
        
        self._last_post_content = text
        self._last_post_time = datetime.now()
        
        return True
    
    def test_connection(self) -> bool:
        """Mock connection test always succeeds."""
        self.logger.info("Mock connection test successful")
        return True


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python bluesky_poster.py <handle> <app_password>")
        print("Example: python bluesky_poster.py user.bsky.social your-app-password")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    
    # Test with mock poster for safety
    poster = MockBlueSkyPoster(sys.argv[1], sys.argv[2])
    
    try:
        # Test connection
        if poster.test_connection():
            print("✅ Connection test successful")
        else:
            print("❌ Connection test failed")
            sys.exit(1)
        
        # Test posting
        success = poster.post_live_notification(
            username="testuser",
            stream_url="https://twitch.tv/testuser",
            stream_title="Testing Stream",
            game_name="Just Chatting"
        )
        
        if success:
            print("✅ Test post successful")
        else:
            print("❌ Test post failed")
            
    except BlueSkyPostError as e:
        print(f"Error: {e}")
        sys.exit(1) 