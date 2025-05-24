"""
Configuration management for Bluesky Twitch Live Bot.
Handles loading, validation, and accessing configuration settings.
"""

import json
import os
import logging
from typing import Dict, Any, Optional


class ConfigurationError(Exception):
    """Raised when there's an issue with configuration."""
    pass


class Config:
    """Configuration manager for the bot."""
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        if not os.path.exists(self.config_file):
            raise ConfigurationError(f"Configuration file {self.config_file} not found. Please create it from config.example.json")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate that all required configuration fields are present."""
        required_fields = {
            'twitch': ['username', 'client_id', 'client_secret'],
            'bluesky': ['handle', 'app_password'],
            'settings': ['check_interval', 'post_template']
        }
        
        for section, fields in required_fields.items():
            if section not in self._config:
                raise ConfigurationError(f"Missing required section '{section}' in configuration")
            
            for field in fields:
                if field not in self._config[section]:
                    raise ConfigurationError(f"Missing required field '{field}' in section '{section}'")
                
                if not self._config[section][field]:
                    raise ConfigurationError(f"Field '{field}' in section '{section}' cannot be empty")
        
        # Validate specific field types and values
        if not isinstance(self._config['settings']['check_interval'], int) or self._config['settings']['check_interval'] < 30:
            raise ConfigurationError("check_interval must be an integer >= 30 seconds")
        
        if '{username}' not in self._config['settings']['post_template']:
            logging.warning("post_template doesn't contain {username} placeholder")
    
    @property
    def twitch_username(self) -> str:
        """Get Twitch username."""
        return self._config['twitch']['username']
    
    @property
    def twitch_client_id(self) -> str:
        """Get Twitch client ID."""
        return self._config['twitch']['client_id']
    
    @property
    def twitch_client_secret(self) -> str:
        """Get Twitch client secret."""
        return self._config['twitch']['client_secret']
    
    @property
    def bluesky_handle(self) -> str:
        """Get Bluesky handle."""
        return self._config['bluesky']['handle']
    
    @property
    def bluesky_app_password(self) -> str:
        """Get Bluesky app password."""
        return self._config['bluesky']['app_password']
    
    @property
    def check_interval(self) -> int:
        """Get check interval in seconds."""
        return self._config['settings']['check_interval']
    
    @property
    def post_template(self) -> str:
        """Get post template."""
        return self._config['settings']['post_template']
    
    def get_formatted_post(self) -> str:
        """Get the formatted post message with username substituted."""
        return self.post_template.format(username=self.twitch_username)
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.load_config()
        logging.info("Configuration reloaded successfully")


def create_example_config() -> None:
    """Create an example configuration file."""
    example_config = {
        "twitch": {
            "username": "your_twitch_username",
            "client_id": "your_twitch_client_id",
            "client_secret": "your_twitch_client_secret"
        },
        "bluesky": {
            "handle": "yourhandle.bsky.social",
            "app_password": "your-app-password"
        },
        "settings": {
            "check_interval": 60,
            "post_template": "🔴 I'm now live on Twitch! Come join me: https://twitch.tv/{username}"
        }
    }
    
    with open("config.example.json", 'w', encoding='utf-8') as f:
        json.dump(example_config, f, indent=2)
    
    print("Created config.example.json - copy this to config.json and fill in your credentials")


if __name__ == "__main__":
    # Create example config if run directly
    create_example_config() 