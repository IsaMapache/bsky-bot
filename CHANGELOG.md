# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-05-26

### Added
- Hotkey feature (`Shift + \`) to manually trigger a Bluesky post.
  - Posts current stream details if live.
  - Posts a generic "Online!" message if offline.
- `keyboard` library dependency for hotkey detection.

### Changed
- Updated `bluesky_poster.py` to allow overriding duplicate post checks for manual posts.

## [0.1.0] - 2024-01-XX

### Added
- Initial project setup with Git repository
- Basic project structure and documentation
- Dependencies planned: atproto for Bluesky, requests for Twitch API
- Windows auto-start capability design
- Configuration management system design
- Twitch live stream monitoring functionality design
- Bluesky posting integration design
- Comprehensive README with setup instructions
- Development discipline with steps.txt tracking

### Features
- Monitor Twitch channel for live status
- Automatically post to Bluesky when going live
- Windows Task Scheduler integration for auto-start
- Smart posting to prevent duplicates
- Configurable check intervals and post templates
- Logging and error handling

### Technical
- Python 3.8+ compatibility
- AT Protocol SDK integration
- Twitch Helix API integration
- Windows-specific implementation 

## [0.3.1] - 2025-01-30

### Fixed
- **Hotkey Functionality**: Fixed hotkey registration issues
  - Improved hotkey detection with multiple fallback combinations
  - Better error handling for hotkey registration failures
  - Enhanced logging for hotkey status

### Added
- **Enhanced Terminal Output**: Improved user experience with better status display
  - Clear bot status dashboard when starting
  - Visual feedback when hotkey is triggered
  - Real-time hotkey status indicators
  - Prominent manual post notifications

### Changed
- Hotkey now tries multiple key combinations for better compatibility
- Added comprehensive terminal feedback for manual posts
- Improved logging messages with emojis for better readability
- Better cleanup of hotkey handlers on shutdown

## [0.3.0] - 2025-01-30

### Added
- **Link Preview Embeds**: Posts now include rich link preview cards with stream metadata
  - Automatically fetches title, description, and thumbnail from Twitch stream URLs
  - Creates proper website card embeds in Bluesky posts
  - Includes both clickable links AND preview cards for better user experience
- Added `beautifulsoup4` dependency for HTML parsing

### Changed
- Enhanced `BlueSkyPoster.post_live_notification()` to generate link previews
- Updated `BlueSkyPoster.post()` method to accept optional embed parameter
- Improved logging to indicate when link previews are included
- Updated MockBlueSkyPoster for comprehensive testing with embeds

### Technical
- Added `_fetch_link_preview()` method to extract OpenGraph metadata
- Handles thumbnail image upload for preview cards
- Graceful fallback when link preview fetching fails 