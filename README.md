# Apple Music Telegram Download Bot

A powerful Telegram bot for downloading music from Apple Music, built on the AppleMusicDecrypt V2 codebase with Telethon for handling large file uploads (up to 2GB).

## Features

- 🎵 Download songs, albums, playlists, and entire artist discographies from Apple Music
- 🔊 Multiple codec support: ALAC (lossless), Dolby Atmos (EC3), AAC, and more
- 📤 Large file support (up to 2GB) via Telethon's MTProto API
- 🎨 Automatic metadata and cover art embedding
- 📝 Lyrics download (.lrc/.ttml format)
- 🔒 User authorization system
- 📊 Download queue management
- 🎯 Interactive codec selection
- 🤖 Intuitive bot commands and auto-URL detection

## Supported Codecs

- **ALAC** - Apple Lossless (best quality, larger files)
- **EC3** - Dolby Atmos (immersive audio)
- **AC3** - Dolby Digital
- **AAC** - Standard AAC
- **AAC-Binaural** - AAC with binaural audio
- **AAC-Downmix** - AAC downmixed
- **AAC-Legacy** - Legacy AAC decryption

## Prerequisites

### 1. Wrapper-Manager

This bot requires a running instance of the AppleMusicDecrypt wrapper-manager for decryption. You have two options:

- **Remote instance**: Run wrapper-manager on a separate server
- **Local instance**: Use QEMU to run wrapper-manager locally (see config)

Refer to the [AppleMusicDecrypt documentation](https://github.com/WorldObservationLog/AppleMusicDecrypt) for wrapper-manager setup.

### 2. Telegram API Credentials

You need to obtain Telegram API credentials:

1. **API ID and API Hash**:
   - Visit https://my.telegram.org
   - Log in with your phone number
   - Go to "API development tools"
   - Create a new application
   - Copy your `api_id` and `api_hash`

2. **Bot Token**:
   - Open Telegram and message [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow the instructions
   - Copy the bot token provided

3. **Your User ID** (for authorization):
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram
   - Copy your user ID

## Installation

### Option 1: Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/saungpapa/AMD.git
cd AMD
```

2. Create your configuration:
```bash
cp config.example.toml config.toml
nano config.toml  # Edit with your settings
```

3. Build and run with Docker:
```bash
docker build -t apple-music-bot .
docker run -d --name apple-music-bot \
  -v $(pwd)/config.toml:/app/config.toml \
  -v $(pwd)/downloads:/app/downloads \
  apple-music-bot
```

### Option 2: Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/saungpapa/AMD.git
cd AMD
```

2. Install Python 3.11+:
```bash
# Ensure Python 3.11 or higher is installed
python --version
```

3. Install dependencies:
```bash
# Using pip
pip install -r requirements.txt

# Or using Poetry
pip install poetry
poetry install
```

4. Create configuration:
```bash
cp config.example.toml config.toml
nano config.toml  # Edit with your settings
```

5. Run the bot:
```bash
python bot.py

# Or with Poetry
poetry run python bot.py
```

## Configuration

Edit `config.toml` with your settings:

### Telegram Configuration

```toml
[telegram]
# Get from https://my.telegram.org
apiId = 12345678
apiHash = "your_api_hash_here"

# Get from @BotFather
botToken = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"

# Telethon session file name
sessionName = "apple_music_bot"

# Authorized user IDs (empty = allow all)
# Get your ID from @userinfobot
authorizedUsers = [123456789, 987654321]

# Default download codec
defaultCodec = "alac"
```

### Wrapper-Manager Configuration

```toml
[instance]
# Remote wrapper-manager address
url = "127.0.0.1:8080"
secure = false

[localInstance]
# Use local QEMU instance (overrides remote instance)
enable = false
enableHardwareAcceleration = false
memorySize = "512M"
startArgs = "-host 0.0.0.0 -port 32767 -debug"
```

### Download Configuration

```toml
[download]
# Download settings
parallelNum = 1
codecAlternative = true
codecPriority = ["alac", "ec3", "ac3", "aac"]
atmosConventToM4a = true
saveLyrics = true
lyricsFormat = "lrc"
saveCover = true
coverFormat = "jpg"
coverSize = "5000x5000"
```

See `config.example.toml` for all available options.

## Usage

### Bot Commands

- `/start` - Welcome message and usage instructions
- `/help` - Display help information
- `/dl <url>` - Download with default codec
- `/dl <url> -c <codec>` - Download with specific codec
- `/codec` - Change default codec (interactive menu)
- `/status` - Check wrapper-manager connection status
- `/queue` - View active download queue

### Examples

**Download a song with default codec:**
```
/dl https://music.apple.com/us/song/example/123456789
```

**Download an album with Dolby Atmos:**
```
/dl https://music.apple.com/us/album/example/123456789 -c ec3
```

**Download a playlist:**
```
/dl https://music.apple.com/us/playlist/example/pl.12345
```

**Auto-detect URL (just paste it):**
```
https://music.apple.com/us/song/example/123456789
```

### What Gets Uploaded

For each downloaded track, the bot will upload:

1. **Audio file** (.m4a/.mp4) with embedded metadata:
   - Title, Artist, Album
   - Cover art
   - Track number, Genre, Year
   - Lyrics (if available)

2. **Lyrics file** (.lrc/.ttml) as a separate document (if enabled)

3. **Cover art** (.jpg) as a photo (if enabled)

## File Size Limits

Thanks to Telethon's use of Telegram's MTProto API with API ID and Hash:
- **Maximum file size**: 2GB (vs 50MB with bot API)
- **Streaming support**: Files can be streamed directly in Telegram
- **Fast uploads**: Direct MTProto connection for better performance

This is especially important for:
- ALAC lossless files (can be 100MB+ per track)
- Dolby Atmos tracks
- Complete album downloads

## Troubleshooting

### Bot doesn't respond

1. Check that wrapper-manager is running:
   ```bash
   # Use /status command in bot
   ```

2. Verify config.toml settings:
   - API ID, API Hash, and Bot Token are correct
   - Wrapper-manager URL is accessible

### "Unauthorized" error

- Add your user ID to `authorizedUsers` in config.toml
- Get your ID from @userinfobot

### Codec not available

- Try a different codec: `/dl <url> -c aac`
- Some tracks may not have all codecs available
- Enable `codecAlternative` in config for automatic fallback

### Connection errors

- Ensure wrapper-manager is running and accessible
- Check firewall settings if using remote instance
- For local instance, ensure QEMU is properly configured

### Downloads folder fills up

- Downloaded files are automatically deleted after upload
- Manually clear `downloads/` folder if needed

## CLI Mode

The bot preserves the original CLI functionality. Run the CLI version:

```bash
python main.py
```

## Project Structure

```
AMD/
├── bot.py                  # Telegram bot entry point
├── main.py                 # CLI entry point
├── config.toml             # Your configuration (create from example)
├── config.example.toml     # Example configuration
├── pyproject.toml          # Poetry dependencies
├── requirements.txt        # Pip dependencies
├── Dockerfile              # Docker configuration
├── .gitignore
├── LICENSE.txt
├── README.md
├── src/
│   ├── telegram_bot.py     # Telegram bot implementation
│   ├── api.py              # Apple Music API client
│   ├── rip.py              # Download/decrypt logic
│   ├── config.py           # Configuration management
│   ├── url.py              # URL parser
│   ├── mp4.py              # MP4 processing
│   ├── metadata.py         # Metadata handling
│   ├── save.py             # File saving
│   ├── grpc/               # Wrapper-manager communication
│   ├── legacy/             # Legacy AAC decryption
│   └── models/             # Data models
└── tools/                  # Utility scripts
    ├── login.py
    └── logout.py
```

## Development

### Running in Development

```bash
# Install dependencies
poetry install

# Run bot
poetry run python bot.py

# Run CLI
poetry run python main.py
```

### Building Docker Image

```bash
docker build -t apple-music-bot .
```

## Credits

- Based on [AppleMusicDecrypt V2](https://github.com/WorldObservationLog/AppleMusicDecrypt) by WorldObservationLog
- Uses [Telethon](https://github.com/LonamiWebs/Telethon) for Telegram Bot API
- Uses [pywidevine](https://github.com/WorldObservationLog/pywidevine) for Widevine decryption

## License

See [LICENSE.txt](LICENSE.txt) for details.

## Disclaimer

This tool is for educational purposes only. Downloading copyrighted content without permission may violate Apple Music's Terms of Service and copyright laws in your jurisdiction. Use responsibly and only for content you have the right to access.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Refer to [AppleMusicDecrypt documentation](https://github.com/WorldObservationLog/AppleMusicDecrypt) for wrapper-manager setup

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
