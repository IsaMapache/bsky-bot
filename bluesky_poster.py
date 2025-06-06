"""
Bluesky posting functionality for live stream notifications.
Handles posting to Bluesky using the AT Protocol SDK.
"""

import logging
from typing import Optional, Dict
from datetime import datetime

try:
    from atproto import Client, client_utils
    from atproto.exceptions import AtProtocolError
except ImportError:
    # Fallback for development/testing
    Client = None
    client_utils = None
    AtProtocolError = Exception

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None


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
        if Client is None or client_utils is None:
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
    
    def _fetch_link_preview(self, url: str) -> Optional[Dict]:
        """
        Fetch link preview metadata for embedding website cards.
        
        Args:
            url: URL to fetch metadata for
            
        Returns:
            Dict with external embed data or None if failed
        """
        if not requests or not BeautifulSoup:
            self.logger.warning("requests or BeautifulSoup not available for link previews")
            return None
        
        try:
            # Fetch the HTML
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Basic card data
            card = {
                "uri": url,
                "title": "",
                "description": "",
            }
            
            # Try to get title - prefer og:title, fallback to title tag
            title_tag = soup.find("meta", property="og:title")
            if title_tag and title_tag.get("content"):
                card["title"] = title_tag["content"]
            else:
                title_element = soup.find("title")
                if title_element:
                    card["title"] = title_element.get_text().strip()
            
            # Try to get description - prefer og:description, fallback to meta description
            desc_tag = soup.find("meta", property="og:description")
            if desc_tag and desc_tag.get("content"):
                card["description"] = desc_tag["content"]
            else:
                desc_element = soup.find("meta", attrs={"name": "description"})
                if desc_element and desc_element.get("content"):
                    card["description"] = desc_element["content"]
            
            # Try to get image thumbnail
            image_tag = soup.find("meta", property="og:image")
            if image_tag and image_tag.get("content"):
                img_url = image_tag["content"]
                
                # Handle relative URLs
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)
                elif not img_url.startswith("http"):
                    # Relative path
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)
                
                # Download and upload image
                try:
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    img_resp.raise_for_status()
                    
                    # Size limit check (1MB)
                    if len(img_resp.content) <= 1000000:
                        # Upload blob
                        client = self._get_client()
                        blob_resp = client.com.atproto.repo.upload_blob(img_resp.content)
                        card["thumb"] = blob_resp.blob
                    else:
                        self.logger.warning(f"Image too large for thumbnail: {len(img_resp.content)} bytes")
                        
                except Exception as e:
                    self.logger.warning(f"Failed to fetch/upload thumbnail: {e}")
            
            # Truncate fields to reasonable lengths
            card["title"] = card["title"][:300] if card["title"] else ""
            card["description"] = card["description"][:1000] if card["description"] else ""
            
            return {
                "$type": "app.bsky.embed.external",
                "external": card,
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch link preview for {url}: {e}")
            return None

    def post(self, text, force: bool = False, embed: Optional[Dict] = None) -> bool:
        """
        Post text to Bluesky.
        
        Args:
            text: Text content to post (str or TextBuilder)
            force: Force post even if duplicate
            embed: Optional embed data (e.g., link preview, image, etc.)
            
        Returns:
            True if post was successful, False if skipped
            
        Raises:
            BlueSkyPostError: If unable to post
        """
        # Convert TextBuilder to string for duplicate checking
        text_content = text.build_text() if hasattr(text, 'build_text') else text
        
        # Check for duplicate posts (unless forced)
        if not force and self._is_duplicate_post(text_content):
            self.logger.info("Skipping duplicate post")
            return False

        try:
            client = self._get_client()
            
            self.logger.info(f"Posting to Bluesky: {text_content[:50]}...")
            
            # If we have an embed, include it in the post
            if embed:
                self.logger.info("Including link preview embed in post")
                post_response = client.send_post(text, embed=embed)
            else:
                post_response = client.send_post(text)
            
            # Store for duplicate detection
            self._last_post_content = text_content
            self._last_post_time = datetime.now()
            
            self.logger.info("Successfully posted to Bluesky with link preview")
            return True
            
        except AtProtocolError as e:
            raise BlueSkyPostError(f"Failed to post to Bluesky: {e}")
        except Exception as e:
            raise BlueSkyPostError(f"Unexpected error posting to Bluesky: {e}")
    
    def post_live_notification(self, username: str, stream_url: str, 
                              stream_title: Optional[str] = None,
                              game_name: Optional[str] = None,
                              is_manual_override: bool = False) -> bool:
        """
        Post a live stream notification with clickable link and preview embed.
        
        Args:
            username: Twitch username
            stream_url: URL to the stream
            stream_title: Optional stream title
            game_name: Optional game being played
            is_manual_override: If True, bypasses duplicate check for manual posts
            
        Returns:
            True if post was successful, False if skipped
        """
        # Build rich text with clickable link using TextBuilder
        text_builder = client_utils.TextBuilder()
        
        # Main announcement
        text_builder.text("🔴 I'm live on Twitch rn come slide!~\n\n")
        
        # Add stream details if available
        if stream_title and game_name:
            text_builder.text(f"📺 {stream_title}\n\n🎮 Playing {game_name}\n\n")
        elif stream_title:
            text_builder.text(f"📺 {stream_title}\n\n")
        elif game_name:
            text_builder.text(f"🎮 Playing {game_name}\n\n")
        
        # Add hashtags as clickable tags
        text_builder.tag("#blacksygamers", "blacksygamers").text(" ")
        text_builder.tag("#gaming", "gaming").text(" ")
        text_builder.tag("#twitch", "twitch").text(" ")
        text_builder.tag("#streaming", "streaming").text("\n\n")
        
        # Add clickable URL - show the actual URL as clickable text
        text_builder.link(stream_url, stream_url)
        
        # Fetch link preview for embedding
        link_preview = self._fetch_link_preview(stream_url)
        
        return self.post(text_builder, force=is_manual_override, embed=link_preview)
    
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
    
    def _fetch_link_preview(self, url: str) -> Optional[Dict]:
        """Mock link preview - just return a simple mock embed."""
        self.logger.info(f"MOCK: Fetching link preview for {url}")
        return {
            "$type": "app.bsky.embed.external",
            "external": {
                "uri": url,
                "title": "Mock Twitch Stream",
                "description": "Mock description for testing purposes",
                # No thumb for mock
            }
        }
    
    def post_live_notification(self, username: str, stream_url: str, 
                              stream_title: Optional[str] = None,
                              game_name: Optional[str] = None,
                              is_manual_override: bool = False) -> bool:
        """
        Mock version that handles TextBuilder properly by building the text manually.
        Also respects is_manual_override and includes link preview.
        """
        if client_utils is not None:
            # Use the real TextBuilder if available, pass through is_manual_override
            text_builder = client_utils.TextBuilder()
            text_builder.text("🔴 I'm live on Twitch rn come slide!~\n\n")
            if stream_title and game_name:
                text_builder.text(f"📺 {stream_title}\n\n🎮 Playing {game_name}\n\n")
            elif stream_title:
                text_builder.text(f"📺 {stream_title}\n\n")
            elif game_name:
                text_builder.text(f"🎮 Playing {game_name}\n\n")
            text_builder.tag("#blacksygamers", "blacksygamers").text(" ")
            text_builder.tag("#gaming", "gaming").text(" ")
            text_builder.tag("#twitch", "twitch").text(" ")
            text_builder.tag("#streaming", "streaming").text("\n\n")
            text_builder.link(stream_url, stream_url)
            
            # Get mock link preview
            link_preview = self._fetch_link_preview(stream_url)
            
            return self.post(text_builder, force=is_manual_override, embed=link_preview)
        else:
            # Fallback: build the text manually to simulate what TextBuilder would create
            parts = []
            parts.append("🔴 I'm live on Twitch rn come slide!~")
            
            if stream_title and game_name:
                parts.append(f"📺 {stream_title}")
                parts.append(f"🎮 Playing {game_name}")
            elif stream_title:
                parts.append(f"📺 {stream_title}")
            elif game_name:
                parts.append(f"🎮 Playing {game_name}")
            
            parts.append("#blacksygamers #gaming #twitch #streaming")
            parts.append(stream_url)
            
            text_content = "\n\n".join(parts)
            link_preview = self._fetch_link_preview(stream_url)
            return self.post(text_content, force=is_manual_override, embed=link_preview)
    
    def post(self, text, force: bool = False, embed: Optional[Dict] = None) -> bool:
        """Mock posting - just log and store."""
        # Convert TextBuilder to string for logging and duplicate checking
        text_content = text.build_text() if hasattr(text, 'build_text') else text
        
        if not force and self._is_duplicate_post(text_content):
            self.logger.info("Skipping duplicate mock post")
            return False
        
        # For mock display, show what the rich text would look like
        if hasattr(text, 'build_text'):
            # This is a TextBuilder - show both text and the rich text info
            self.logger.info(f"MOCK POST to Bluesky (rich text): {text_content}")
            self.logger.info("Rich text contains links that will be clickable in actual post")
        else:
            self.logger.info(f"MOCK POST to Bluesky: {text_content}")
        
        # Show embed info if present
        if embed:
            embed_type = embed.get("$type", "unknown")
            if embed_type == "app.bsky.embed.external":
                external = embed.get("external", {})
                title = external.get("title", "No title")
                desc = external.get("description", "No description")
                has_thumb = "thumb" in external
                self.logger.info(f"MOCK EMBED: Link preview - Title: '{title}', Description: '{desc}', Has thumbnail: {has_thumb}")
            else:
                self.logger.info(f"MOCK EMBED: Type {embed_type}")
        
        self.posted_messages.append({
            'text': text_content,
            'time': datetime.now(),
            'is_rich_text': hasattr(text, 'build_text'),
            'embed': embed
        })
        
        self._last_post_content = text_content
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
            game_name="Just Chatting",
            is_manual_override=False
        )
        
        if success:
            print("✅ Test post successful")
            # Show the actual post content for verification
            if poster.posted_messages:
                last_post = poster.posted_messages[-1]
                print(f"Posted content:\n{last_post['text']}")
                if last_post.get('is_rich_text'):
                    print("📝 Note: This post contains rich text with clickable links!")
        else:
            print("❌ Test post failed")
            
    except BlueSkyPostError as e:
        print(f"Error: {e}")
        sys.exit(1) 