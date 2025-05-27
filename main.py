"""
Main Bluesky Twitch Live Bot Application.
Monitors Twitch for live status and posts notifications to Bluesky.
"""

import logging
import time
import signal
import sys
import os
from datetime import datetime
from typing import Optional
import keyboard # Added for hotkey detection

from config import Config, ConfigurationError
from twitch_monitor import TwitchMonitor, TwitchAPIError
from bluesky_poster import BlueSkyPoster, BlueSkyPostError


class LiveBot:
    """Main bot class that coordinates monitoring and posting."""
    
    def __init__(self, config_file: str = "config.json", mock_mode: bool = False):
        """
        Initialize the live bot.
        
        Args:
            config_file: Path to configuration file
            mock_mode: Run in mock mode (no actual posting)
        """
        self.config_file = config_file
        self.mock_mode = mock_mode
        self.running = False
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        try:
            self.config = Config(config_file)
            self.logger.info(f"Loaded configuration for user: {self.config.twitch_username}")
        except ConfigurationError as e:
            self.logger.error(f"Configuration error: {e}")
            raise
        
        # Initialize components
        self.twitch_monitor = TwitchMonitor(
            self.config.twitch_client_id,
            self.config.twitch_client_secret,
            self.config.twitch_username
        )
        
        if mock_mode:
            from bluesky_poster import MockBlueSkyPoster
            self.bluesky_poster = MockBlueSkyPoster(
                self.config.bluesky_handle,
                self.config.bluesky_app_password
            )
            self.logger.info("Running in MOCK MODE - no actual posts will be made")
        else:
            self.bluesky_poster = BlueSkyPoster(
                self.config.bluesky_handle,
                self.config.bluesky_app_password
            )
            self.logger.info("Running in REAL MODE - posts will be made to Bluesky")
        
        # State tracking
        self._last_live_status = False
        self._startup_time = datetime.now()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # File handler
        file_handler = logging.FileHandler(
            f"logs/bot_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def test_connections(self) -> bool:
        """
        Test connections to both Twitch and Bluesky.
        
        Returns:
            True if both connections successful
        """
        self.logger.info("Testing connections...")
        
        # Test Twitch connection
        try:
            is_live = self.twitch_monitor.is_live()
            status = "LIVE" if is_live else "OFFLINE"
            self.logger.info(f"✅ Twitch connection successful - Channel is {status}")
        except TwitchAPIError as e:
            self.logger.error(f"❌ Twitch connection failed: {e}")
            return False
        
        # Test Bluesky connection
        try:
            if self.bluesky_poster.test_connection():
                self.logger.info("✅ Bluesky connection successful")
            else:
                self.logger.error("❌ Bluesky connection failed")
                return False
        except BlueSkyPostError as e:
            self.logger.error(f"❌ Bluesky connection failed: {e}")
            return False
        
        return True
    
    def run_once(self) -> None:
        """Run one monitoring cycle."""
        try:
            # Check current live status
            current_live_status = self.twitch_monitor.is_live()
            
            # Check if status changed
            if current_live_status != self._last_live_status:
                if current_live_status:
                    # Just went live
                    self.logger.info("🔴 Stream went LIVE!")
                    self._handle_went_live()
                else:
                    # Just went offline
                    self.logger.info("⚫ Stream went OFFLINE")
                    self._handle_went_offline()
                
                self._last_live_status = current_live_status
            else:
                # No change in status
                status = "LIVE" if current_live_status else "OFFLINE"
                self.logger.debug(f"Stream status unchanged: {status}")
                
        except TwitchAPIError as e:
            self.logger.error(f"Error checking Twitch status: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in monitoring cycle: {e}")
    
    def _handle_went_live(self) -> None:
        """Handle when the stream goes live."""
        try:
            # Get stream information
            stream_info = self.twitch_monitor.get_stream_info()
            
            if stream_info:
                stream_title = stream_info.get('title')
                game_name = stream_info.get('game_name')
                viewer_count = stream_info.get('viewer_count', 0)
                
                self.logger.info(f"Stream details - Title: {stream_title}, Game: {game_name}, Viewers: {viewer_count}")
                
                # Post to Bluesky
                stream_url = self.twitch_monitor.get_stream_url()
                success = self.bluesky_poster.post_live_notification(
                    username=self.config.twitch_username,
                    stream_url=stream_url,
                    stream_title=stream_title,
                    game_name=game_name
                )
                
                if success:
                    self.logger.info("🦋 Successfully posted live notification to Bluesky")
                else:
                    self.logger.warning("🦋 Bluesky post was skipped (likely duplicate)")
            else:
                self.logger.warning("No stream info available despite live status")
                
        except BlueSkyPostError as e:
            self.logger.error(f"Failed to post to Bluesky: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error handling live event: {e}")
    
    def _handle_went_offline(self) -> None:
        """Handle when the stream goes offline."""
        # Currently we don't post when going offline, but we could add this feature
        self.logger.info("Stream ended - no notification posted")
    
    def _trigger_manual_post(self):
        """Manually triggers a Bluesky post, typically via hotkey."""
        self.logger.info("Hotkey pressed! Manually triggering Bluesky post.")
        try:
            # Get stream information
            stream_info = self.twitch_monitor.get_stream_info()
            
            if stream_info:
                stream_title = stream_info.get('title')
                game_name = stream_info.get('game_name')
                
                self.logger.info(f"Stream details for manual post - Title: {stream_title}, Game: {game_name}")
                
                # Post to Bluesky
                stream_url = self.twitch_monitor.get_stream_url()
                success = self.bluesky_poster.post_live_notification(
                    username=self.config.twitch_username,
                    stream_url=stream_url,
                    stream_title=stream_title,
                    game_name=game_name,
                    is_manual_override=True # Indicate this is a manual post
                )
                
                if success:
                    self.logger.info("🦋 Successfully posted manual live notification to Bluesky")
                else:
                    # The poster might still skip if it deems it a duplicate,
                    # even with override, depending on its internal logic.
                    self.logger.warning("🦋 Manual Bluesky post was skipped (check poster logic for override)")
            else:
                # If not live, we can still post a generic message or do nothing
                self.logger.info("Twitch stream is not currently live. Posting a generic message or configured template.")
                # Decide if you want to post a "Hey I'm here" message even if not live
                # For now, let's use the existing template but adjust if no stream_url
                stream_url = f"https://twitch.tv/{self.config.twitch_username}" # Fallback URL
                success = self.bluesky_poster.post_live_notification(
                    username=self.config.twitch_username,
                    stream_url=stream_url,
                    stream_title="Online!", # Generic title
                    game_name="Chatting",    # Generic game
                    is_manual_override=True
                )
                if success:
                    self.logger.info("🦋 Successfully posted generic manual notification to Bluesky")
                else:
                    self.logger.warning("🦋 Generic manual Bluesky post was skipped")

        except BlueSkyPostError as e:
            self.logger.error(f"Failed to post manually to Bluesky: {e}")
        except TwitchAPIError as e:
            self.logger.error(f"Twitch API error during manual post: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error handling manual post: {e}")
    
    def run(self) -> None:
        """Run the bot main loop."""
        self.logger.info("🚀 Starting Bluesky Twitch Live Bot")
        self.logger.info(f"Monitoring Twitch user: {self.config.twitch_username}")
        self.logger.info(f"Posting to Bluesky: {self.config.bluesky_handle}")
        self.logger.info(f"Check interval: {self.config.check_interval} seconds")
        
        # Test connections before starting
        if not self.test_connections():
            self.logger.error("❌ Connection tests failed - aborting")
            return
        
        # Get initial status
        try:
            self._last_live_status = self.twitch_monitor.is_live()
            status = "LIVE" if self._last_live_status else "OFFLINE"
            self.logger.info(f"Initial stream status: {status}")
        except TwitchAPIError as e:
            self.logger.error(f"Failed to get initial status: {e}")
            self._last_live_status = False
        
        # Main monitoring loop
        self.running = True
        cycle_count = 0
        
        # Setup hotkey listener
        try:
            keyboard.add_hotkey('shift+\\\\', self._trigger_manual_post) # Using '\\\\' for backslash
            self.logger.info(r"Hotkey 'Shift + \\' registered for manual posting.")
        except Exception as e:
            self.logger.error(f"Failed to register hotkey: {e}. Manual posting via hotkey will not be available.")

        while self.running:
            try:
                cycle_count += 1
                self.logger.debug(f"Monitoring cycle #{cycle_count}")
                
                self.run_once()
                
                # Log periodic status
                if cycle_count % 10 == 0:  # Every 10 cycles
                    uptime = datetime.now() - self._startup_time
                    status = "LIVE" if self._last_live_status else "OFFLINE"
                    self.logger.info(f"Bot healthy - Uptime: {uptime}, Stream: {status}, Cycles: {cycle_count}")
                
                # Sleep until next check
                time.sleep(self.config.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                # Continue running despite errors
                time.sleep(self.config.check_interval)
        
        self.logger.info("🛑 Bot shutdown complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bluesky Twitch Live Bot")
    parser.add_argument("--config", default="config.json", help="Configuration file path")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no actual posting)")
    parser.add_argument("--test", action="store_true", help="Test connections and exit")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--create-config", action="store_true", help="Create example config file")
    
    args = parser.parse_args()
    
    # Create example config if requested
    if args.create_config:
        from config import create_example_config
        create_example_config()
        return
    
    try:
        bot = LiveBot(config_file=args.config, mock_mode=args.mock)
        
        if args.test:
            # Just test connections and exit
            success = bot.test_connections()
            sys.exit(0 if success else 1)
        elif args.once:
            # Run one monitoring cycle and exit
            bot.run_once()
        else:
            # Run the main monitoring loop
            bot.run()
            
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        print("Run with --create-config to create an example configuration file")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 