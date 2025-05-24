# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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