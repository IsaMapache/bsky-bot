"""
Twitch API monitoring for live stream detection.
Handles authentication and stream status checking using Twitch Helix API.
"""

import requests
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class TwitchAPIError(Exception):
    """Raised when there's an issue with Twitch API."""
    pass


class TwitchMonitor:
    """Monitor Twitch channel for live status."""
    
    def __init__(self, client_id: str, client_secret: str, username: str):
        """
        Initialize Twitch monitor.
        
        Args:
            client_id: Twitch application client ID
            client_secret: Twitch application client secret
            username: Twitch username to monitor
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username.lower()  # Twitch usernames are case-insensitive
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Cache for stream info to detect changes
        self._last_stream_info: Optional[Dict[str, Any]] = None
        
        self.logger = logging.getLogger(f"{__name__}.{self.username}")
    
    def _get_access_token(self) -> str:
        """
        Get or refresh access token for Twitch API.
        
        Returns:
            Valid access token
            
        Raises:
            TwitchAPIError: If unable to get access token
        """
        # Check if we have a valid token that hasn't expired
        if (self._access_token and self._token_expires_at and 
            datetime.now() < self._token_expires_at - timedelta(minutes=5)):
            return self._access_token
        
        self.logger.info("Getting new Twitch access token")
        
        try:
            response = requests.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                raise TwitchAPIError(f"Failed to get access token: {response.status_code} - {response.text}")
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self.logger.info("Successfully obtained Twitch access token")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            raise TwitchAPIError(f"Network error getting access token: {e}")
        except KeyError as e:
            raise TwitchAPIError(f"Invalid response format: missing {e}")
    
    def _get_user_id(self) -> str:
        """
        Get Twitch user ID from username.
        
        Returns:
            Twitch user ID
            
        Raises:
            TwitchAPIError: If unable to get user ID
        """
        token = self._get_access_token()
        
        try:
            response = requests.get(
                "https://api.twitch.tv/helix/users",
                headers={
                    "Client-ID": self.client_id,
                    "Authorization": f"Bearer {token}"
                },
                params={"login": self.username},
                timeout=10
            )
            
            if response.status_code != 200:
                raise TwitchAPIError(f"Failed to get user info: {response.status_code} - {response.text}")
            
            data = response.json()
            users = data.get("data", [])
            
            if not users:
                raise TwitchAPIError(f"User '{self.username}' not found on Twitch")
            
            return users[0]["id"]
            
        except requests.exceptions.RequestException as e:
            raise TwitchAPIError(f"Network error getting user ID: {e}")
    
    def is_live(self) -> bool:
        """
        Check if the channel is currently live.
        
        Returns:
            True if the channel is live, False otherwise
            
        Raises:
            TwitchAPIError: If unable to check stream status
        """
        try:
            stream_info = self.get_stream_info()
            return stream_info is not None
        except TwitchAPIError:
            raise
        except Exception as e:
            raise TwitchAPIError(f"Unexpected error checking live status: {e}")
    
    def get_stream_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current stream information.
        
        Returns:
            Stream information dict if live, None if offline
            
        Raises:
            TwitchAPIError: If unable to get stream info
        """
        token = self._get_access_token()
        
        try:
            response = requests.get(
                "https://api.twitch.tv/helix/streams",
                headers={
                    "Client-ID": self.client_id,
                    "Authorization": f"Bearer {token}"
                },
                params={"user_login": self.username},
                timeout=10
            )
            
            if response.status_code != 200:
                raise TwitchAPIError(f"Failed to get stream info: {response.status_code} - {response.text}")
            
            data = response.json()
            streams = data.get("data", [])
            
            if streams:
                stream_info = streams[0]
                self.logger.debug(f"Stream is live: {stream_info.get('title', 'No title')}")
                return stream_info
            else:
                self.logger.debug("Stream is offline")
                return None
                
        except requests.exceptions.RequestException as e:
            raise TwitchAPIError(f"Network error getting stream info: {e}")
    
    def has_stream_changed(self) -> bool:
        """
        Check if the stream status has changed since last check.
        
        Returns:
            True if stream status changed, False otherwise
        """
        try:
            current_info = self.get_stream_info()
            
            # Compare with last known state
            if self._last_stream_info is None and current_info is None:
                # Still offline
                return False
            elif self._last_stream_info is None and current_info is not None:
                # Just went live
                self._last_stream_info = current_info
                return True
            elif self._last_stream_info is not None and current_info is None:
                # Just went offline
                self._last_stream_info = None
                return True
            elif (self._last_stream_info is not None and current_info is not None and
                  self._last_stream_info.get("id") != current_info.get("id")):
                # Different stream (rare but possible)
                self._last_stream_info = current_info
                return True
            else:
                # No change
                return False
                
        except TwitchAPIError:
            # On error, assume no change to avoid spam
            self.logger.error("Error checking stream change, assuming no change")
            return False
    
    def wait_for_live(self, check_interval: int = 60, max_duration: int = 0) -> bool:
        """
        Wait for the channel to go live.
        
        Args:
            check_interval: Seconds between checks
            max_duration: Maximum seconds to wait (0 = infinite)
            
        Returns:
            True if went live, False if timed out
        """
        start_time = time.time()
        
        while True:
            try:
                if self.is_live():
                    return True
                    
                # Check timeout
                if max_duration > 0 and time.time() - start_time > max_duration:
                    return False
                    
                time.sleep(check_interval)
                
            except TwitchAPIError as e:
                self.logger.error(f"Error checking live status: {e}")
                time.sleep(check_interval)
    
    def get_stream_url(self) -> str:
        """Get the stream URL for this channel."""
        return f"https://twitch.tv/{self.username}"


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python twitch_monitor.py <client_id> <client_secret> <username>")
        sys.exit(1)
    
    logging.basicConfig(level=logging.INFO)
    
    monitor = TwitchMonitor(sys.argv[1], sys.argv[2], sys.argv[3])
    
    try:
        is_live = monitor.is_live()
        print(f"Channel {sys.argv[3]} is {'LIVE' if is_live else 'OFFLINE'}")
        
        if is_live:
            info = monitor.get_stream_info()
            print(f"Title: {info.get('title', 'No title')}")
            print(f"Game: {info.get('game_name', 'No game')}")
            print(f"Viewers: {info.get('viewer_count', 0)}")
            
    except TwitchAPIError as e:
        print(f"Error: {e}")
        sys.exit(1) 