# Bluesky Twitch Live Bot - Setup Guide

This guide will walk you through setting up the bot to automatically post to Bluesky when you go live on Twitch.

## Prerequisites

Before you begin, make sure you have:

- **Windows 10/11** (this bot is designed for Windows)
- **Python 3.8 or higher** installed
- **Twitch account** with streaming capability
- **Bluesky account** with posting capability

## Step 1: Get Your API Credentials

### Twitch API Setup

1. Go to the [Twitch Developer Console](https://dev.twitch.tv/console)
2. Log in with your Twitch account
3. Click "Create an App" or "Register Your Application"
4. Fill in the details:
   - **Name**: Something like "Bluesky Live Bot"
   - **OAuth Redirect URLs**: `http://localhost`
   - **Category**: Choose "Application Integration"
5. Click "Create"
6. Copy your **Client ID** and **Client Secret** (keep these safe!)

### Bluesky API Setup

1. Log into your Bluesky account
2. Go to Settings → Privacy and Security → App Passwords
3. Click "Add App Password"
4. Give it a name like "Live Bot"
5. Copy the generated **App Password** (this is different from your regular password!)

## Step 2: Install and Configure the Bot

### Download and Setup

1. Download or clone this repository to your computer
2. Open PowerShell or Command Prompt as Administrator
3. Navigate to the bot directory:
   ```powershell
   cd "path\to\bsky bot"
   ```

### Install Dependencies

```powershell
pip install -r requirements.txt
```

### Create Configuration

1. Create your configuration file:
   ```powershell
   python main.py --create-config
   ```

2. Copy the example to your actual config:
   ```powershell
   copy config.example.json config.json
   ```

3. Edit `config.json` with your credentials:
   ```json
   {
     "twitch": {
       "username": "YOUR_TWITCH_USERNAME",
       "client_id": "YOUR_TWITCH_CLIENT_ID",
       "client_secret": "YOUR_TWITCH_CLIENT_SECRET"
     },
     "bluesky": {
       "handle": "yourhandle.bsky.social",
       "app_password": "YOUR_BLUESKY_APP_PASSWORD"
     },
     "settings": {
       "check_interval": 60,
       "post_template": "🔴 I'm now live on Twitch! Come join me: https://twitch.tv/{username}"
     }
   }
   ```

## Step 3: Test the Bot

### Test Connections

```powershell
python main.py --test
```

This will verify that:
- Your Twitch credentials work
- Your Bluesky credentials work
- The bot can connect to both services

### Test in Mock Mode

```powershell
python main.py --mock --once
```

This runs the bot once in mock mode (won't actually post) to test the logic.

## Step 4: Set Up Auto-Start

To make the bot start automatically when Windows boots:

```powershell
python setup_autostart.py
```

This will:
- Create a Windows scheduled task
- Set it to run when you log in
- Create a batch file for manual running

### Verify Auto-Start Setup

```powershell
python setup_autostart.py --check
```

## Step 5: Run the Bot

### Manual Run (for testing)

```powershell
python main.py
```

### Run in Background

The bot will now start automatically when you log into Windows. You can also:

- Double-click `run_bot.bat` to start manually
- Check Task Scheduler to manage the automatic startup

## Configuration Options

### Settings Explained

- **check_interval**: How often to check if you're live (in seconds, minimum 30)
- **post_template**: The message template for posts. Use `{username}` as a placeholder

### Custom Post Templates

You can customize your post template:

```json
"post_template": "🔴 LIVE NOW! Playing some games at https://twitch.tv/{username} #twitch #live"
```

## Troubleshooting

### Common Issues

**"Configuration file not found"**
- Make sure you created `config.json` from the example
- Check that the file is in the same directory as `main.py`

**"Failed to get access token"**
- Verify your Twitch Client ID and Client Secret
- Make sure your Twitch app is properly configured

**"Failed to authenticate with Bluesky"**
- Check your Bluesky handle (should include .bsky.social)
- Verify your App Password (not your regular password)

**"Connection test failed"**
- Check your internet connection
- Verify all credentials are correct
- Try running in mock mode first

### Logs

Check the `logs/` directory for detailed error messages:
- `logs/bot_YYYYMMDD.log` contains all bot activity

### Getting Help

1. Check the logs for specific error messages
2. Verify your credentials are correct
3. Test each component individually:
   ```powershell
   python twitch_monitor.py YOUR_CLIENT_ID YOUR_CLIENT_SECRET YOUR_USERNAME
   python bluesky_poster.py YOUR_HANDLE YOUR_APP_PASSWORD
   ```

## Managing the Bot

### Stop Auto-Start

```powershell
python setup_autostart.py --remove
```

### Update Configuration

1. Edit `config.json` with your changes
2. Restart the bot (it will reload the configuration)

### View Bot Status

The bot logs its status every 10 monitoring cycles. Check the console output or log files.

## Security Notes

- Keep your `config.json` file secure (it contains your credentials)
- The bot only needs the permissions you give it
- Your App Password can be revoked anytime from Bluesky settings
- The bot runs locally on your machine only

## What the Bot Does

1. **Monitors** your Twitch channel every 60 seconds (configurable)
2. **Detects** when you go live
3. **Posts** a notification to your Bluesky account
4. **Prevents** duplicate posts for the same stream
5. **Logs** all activity for troubleshooting

The bot is designed to be lightweight and reliable, running quietly in the background until you go live.

## Advanced Usage

### Running Multiple Accounts

You can run multiple instances with different config files:

```powershell
python main.py --config config_account2.json
```

### Custom Check Intervals

Adjust how often the bot checks (minimum 30 seconds):

```json
"check_interval": 30
```

### Mock Mode for Testing

Always test changes in mock mode first:

```powershell
python main.py --mock
```

---

**Need help?** Check the logs, verify your credentials, and make sure you followed each step carefully! 