# Bluesky Twitch Live Bot

**Version: 0.2.0**

A Windows bot that automatically posts to your Bluesky account whenever you go live on Twitch.

## Purpose and Goals

This bot monitors your Twitch channel status and automatically posts a notification to your Bluesky account when you start streaming. It runs as a background service on Windows and starts automatically when your computer boots.

## Features

- 🔴 **Live Stream Detection**: Monitors your Twitch channel for live status
- 🦋 **Bluesky Integration**: Posts notifications to your Bluesky account
- 🚀 **Auto-start**: Runs automatically when Windows boots
- ⚡ **Lightweight**: Minimal resource usage
- 🛡️ **Smart Posting**: Prevents duplicate posts for the same stream
- 🌟 **New Hotkey Feature**: Added hotkey functionality
- 핫 **Hotkey Override (New!)**: Press `Shift + \` to trigger an immediate Bluesky post, regardless of current stream status or posting cooldowns. Useful for manual announcements or testing.

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows 10/11
- Twitch Developer Account (for API access)
- Bluesky Account with App Password

### Environment Setup

1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd "bsky bot"
   ```

2. **Create virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set up configuration:**
   - Copy `config.example.json` to `config.json`
   - Fill in your Twitch and Bluesky credentials

5. **Set up auto-start:**
   ```powershell
   python setup_autostart.py
   ```

## Configuration

Create a `config.json` file with your credentials:

```json
{
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
```

## Usage

### Manual Run
```powershell
python main.py
```

### Hotkey Usage
- While the bot is running (either manually or as a service), press `Shift + \` at any time to trigger an immediate post to Bluesky.
- If your stream is live, it will post the current stream details.
- If your stream is offline, it will post a generic "Online!" message with a link to your Twitch channel.

### Windows Service
The bot will automatically start when Windows boots after running the setup script.

### Logs
Check `logs/bot.log` for activity and error messages.

## API Setup

### Twitch API
1. Go to [Twitch Developer Console](https://dev.twitch.tv/console)
2. Create a new application
3. Get your Client ID and Client Secret
4. Add them to `config.json`

### Bluesky API
1. Go to your Bluesky Settings
2. Generate an App Password
3. Add your handle and app password to `config.json`

## Project Structure

```
bsky-bot/
├── main.py              # Main bot application
├── config.py            # Configuration management
├── twitch_monitor.py    # Twitch API integration
├── bluesky_poster.py    # Bluesky posting functionality
├── scheduler.py         # Windows task scheduling
├── setup_autostart.py  # Auto-start setup script -- run as admin
├── config.json          # User configuration (create from example)
├── config.example.json  # Configuration template
├── requirements.txt     # Python dependencies
├── logs/               # Log files directory
└── tests/              # Test files

```

## Current Version: 0.2.0

### Features
- Basic Twitch live monitoring
- Bluesky posting integration
- Windows auto-start capability
- Configuration management

## Contributing

1. Update `steps.txt` with planned changes
2. Make changes following the Git discipline rules
3. Update version in `VERSION` file
4. Update this README if needed
5. Run tests before committing

## License

MIT License - see LICENSE file for details 