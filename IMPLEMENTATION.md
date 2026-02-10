# Apple Music Telegram Bot - Implementation Summary

## What Was Implemented

This repository now contains a complete Apple Music Telegram Download Bot based on the V2 branch of WorldObservationLog/AppleMusicDecrypt (commit 7dafeffb838a48ad717afa32f685a1eb76870a3e).

## Complete File List

### Root Files
- `bot.py` - Telegram bot entry point
- `main.py` - Original CLI entry point (preserved)
- `config.example.toml` - Example configuration with Telegram section
- `pyproject.toml` - Poetry dependencies (includes Telethon)
- `requirements.txt` - Pip requirements for non-Poetry users
- `Dockerfile` - Docker container configuration
- `README.md` - Comprehensive documentation
- `LICENSE.txt` - License file
- `.gitignore` - Git ignore rules

### Source Files (src/)

**Core Files:**
- `__init__.py` - Package initialization
- `api.py` - Apple Music API client (WebAPI class)
- `cmd.py` - Interactive CLI shell (original)
- `config.py` - Configuration management (MODIFIED with Telegram section)
- `exceptions.py` - Custom exceptions
- `flags.py` - Download flags
- `logger.py` - Logging system
- `measurer.py` - Speed measurement
- `metadata.py` - Song metadata handling
- `mp4.py` - MP4 processing
- `quality.py` - Quality settings
- `qemu.py` - QEMU instance management
- `rip.py` - Core download/decrypt logic
- `save.py` - File saving
- `task.py` - Task management
- `types.py` - Type definitions and codecs
- `url.py` - Apple Music URL parser
- `utils.py` - Utility functions
- `telegram_bot.py` - **NEW** Telegram bot implementation

**gRPC Files (src/grpc/):**
- `__init__.py`
- `manager.proto` - Protocol buffer definition
- `manager.py` - Wrapper-manager gRPC client
- `manager_pb2.py` - Generated protobuf code
- `manager_pb2.pyi` - Type stubs
- `manager_pb2_grpc.py` - Generated gRPC code

**Legacy Files (src/legacy/):**
- `__init__.py`
- `decrypt.py` - Legacy Widevine decryption
- `mp4.py` - Legacy MP4 processing
- `pssh.py` - PSSH box handling
- `proto/WidevineCencHeader.proto` - Widevine protobuf
- `proto/WidevineCencHeader_pb2.py` - Generated code
- `proto/WidevineCencHeader_pb2.pyi` - Type stubs

**Model Files (src/models/):**
- `__init__.py`
- `album_meta.py` - Album metadata models
- `album_tracks.py` - Album tracks models
- `artist_albums.py` - Artist albums models
- `artist_info.py` - Artist info models
- `artist_songs.py` - Artist songs models
- `playlist_info.py` - Playlist info models
- `plsylist_tracks.py` - Playlist tracks models
- `song_data.py` - Song data models
- `song_lyrics.py` - Song lyrics models
- `tracks_meta.py` - Tracks metadata models

### Tools (tools/)
- `install-deps.sh` - Dependency installation script
- `login.py` - Apple Music login utility
- `logout.py` - Apple Music logout utility

## Key Features Implemented

### 1. Telegram Bot (src/telegram_bot.py)
- **Telethon-based** for 2GB file upload support
- **Commands:**
  - `/start` - Welcome message
  - `/help` - Help information
  - `/dl <url>` - Download with default codec
  - `/dl <url> -c <codec>` - Download with specific codec
  - `/codec` - Interactive codec selection
  - `/status` - Check wrapper-manager status
  - `/queue` - View download queue
- **Auto-detection:** Automatically processes Apple Music URLs sent as messages
- **Authorization:** User ID whitelist support
- **Queue Management:** Handles multiple concurrent requests
- **Progress Updates:** Real-time status updates during download/upload
- **File Upload:** Uploads audio, lyrics, and cover art to Telegram
- **Cleanup:** Automatically removes files after upload

### 2. Configuration (src/config.py)
Added new `Telegram` configuration class:
```python
class Telegram(BaseModel):
    apiId: int = 0              # Telegram API ID
    apiHash: str = ""           # Telegram API Hash
    botToken: str = ""          # Bot token from @BotFather
    sessionName: str = "apple_music_bot"
    authorizedUsers: list[int] = []  # Authorized user IDs
    defaultCodec: str = "alac"  # Default download codec
```

### 3. Supported Codecs
- ALAC - Apple Lossless
- EC3 - Dolby Atmos
- AC3 - Dolby Digital
- AAC - Standard AAC
- AAC-Binaural - AAC with binaural audio
- AAC-Downmix - AAC downmixed
- AAC-Legacy - Legacy AAC decryption

### 4. Docker Support
- Complete Dockerfile for containerized deployment
- Volume mounts for config and downloads
- Python 3.11 slim base image

## How It Works

### Architecture Flow
1. User sends Apple Music URL to Telegram bot
2. Bot parses URL using `AppleMusicURL.parse_url()`
3. Bot calls appropriate rip function:
   - `rip_song()` for songs
   - `rip_album()` for albums
   - `rip_playlist()` for playlists
   - `rip_artist()` for artist discographies
4. Files are downloaded to `downloads/` directory
5. Bot monitors directory for new files
6. New files are uploaded to Telegram with metadata
7. Local files are cleaned up after upload

### Integration Points
- **creart dependency injection** - Same pattern as original CLI
- **WebAPI** - Apple Music API client
- **WrapperManager** - gRPC communication with wrapper-manager
- **rip.py** - Core download/decrypt logic (unchanged)
- **Telethon** - Telegram MTProto API for file uploads

## Security

### Implemented Security Measures
- **URL validation:** Uses `startswith()` check before regex parsing
- **User authorization:** Whitelist-based access control
- **Input sanitization:** All URLs validated through AppleMusicURL parser
- **CodeQL scanning:** 0 security alerts

### Security Review Results
- ✅ No SQL injection vulnerabilities
- ✅ No command injection vulnerabilities
- ✅ No path traversal vulnerabilities
- ✅ Proper URL validation
- ✅ Safe file operations

## Setup Requirements

### Prerequisites
1. **Python 3.11+**
2. **Wrapper-manager instance** (AppleMusicDecrypt backend)
3. **Telegram API credentials:**
   - API ID and Hash from https://my.telegram.org
   - Bot token from @BotFather
4. **Telegram user ID** for authorization

### Configuration Steps
1. Copy `config.example.toml` to `config.toml`
2. Fill in wrapper-manager settings (`[instance]` or `[localInstance]`)
3. Fill in Telegram settings (`[telegram]`)
4. Configure download preferences (`[download]`)
5. Run with `python bot.py` or Docker

## Testing Status

### What Was Tested
✅ Python syntax validation (all files compile)
✅ Import structure (no circular dependencies)
✅ Code review completed
✅ Security scan (CodeQL) passed

### What Cannot Be Tested Without Setup
❌ End-to-end download flow (needs wrapper-manager)
❌ Telegram bot functionality (needs API credentials)
❌ Apple Music API integration (needs account)

## Differences from Original V2

### Modified Files
1. **src/config.py** - Added `Telegram` configuration class
2. **config.example.toml** - Added `[telegram]` section
3. **pyproject.toml** - Added `telethon` dependency

### New Files
1. **src/telegram_bot.py** - Complete bot implementation
2. **bot.py** - Bot entry point
3. **requirements.txt** - Pip requirements
4. **Dockerfile** - Docker support
5. **.gitignore** - Git ignore rules
6. **README.md** - Updated documentation

### Preserved Files
- All original V2 source files intact
- CLI functionality preserved (main.py)
- No breaking changes to existing code

## Next Steps for Deployment

1. **Get wrapper-manager running:**
   - Follow AppleMusicDecrypt V2 documentation
   - Can run locally with QEMU or remote instance

2. **Get Telegram credentials:**
   - Visit https://my.telegram.org for API ID/Hash
   - Message @BotFather to create bot and get token
   - Message @userinfobot to get your user ID

3. **Configure the bot:**
   - Edit `config.toml` with your settings
   - Add your user ID to `authorizedUsers`

4. **Run the bot:**
   ```bash
   # With pip
   pip install -r requirements.txt
   python bot.py
   
   # With Poetry
   poetry install
   poetry run python bot.py
   
   # With Docker
   docker build -t apple-music-bot .
   docker run -d -v $(pwd)/config.toml:/app/config.toml apple-music-bot
   ```

5. **Test the bot:**
   - Send `/start` to your bot
   - Try downloading a song: `/dl https://music.apple.com/us/song/...`

## Support

For issues:
- Check README.md for detailed documentation
- Review config.example.toml for configuration options
- Refer to AppleMusicDecrypt V2 docs for wrapper-manager setup
- Open GitHub issues for bugs

## Credits

- Based on AppleMusicDecrypt V2 by WorldObservationLog
- Uses Telethon by LonamiWebs
- Uses pywidevine for Widevine decryption
