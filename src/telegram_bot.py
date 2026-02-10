"""
Telegram Bot for Apple Music Download using Telethon
Supports file uploads up to 2GB via MTProto API
"""
import asyncio
import os
import time
from pathlib import Path
from typing import Optional, Dict, Set

from creart import it
from loguru import logger
from telethon import TelegramClient, events, Button
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeFilename

from src.api import WebAPI
from src.config import Config
from src.exceptions import CodecNotFoundException
from src.flags import Flags
from src.grpc.manager import WrapperManager
from src.rip import rip_song, rip_album, rip_playlist, rip_artist
from src.types import Codec
from src.url import AppleMusicURL, URLType, Song, Album, Playlist, Artist
from src.utils import check_song_existence

# File extensions for upload classification
AUDIO_EXTENSIONS = {'.m4a', '.mp4', '.aac'}
LYRICS_EXTENSIONS = {'.lrc', '.ttml'}
IMAGE_EXTENSIONS = {'.jpg', '.png'}


class DownloadTask:
    """Represents a download task"""
    def __init__(self, chat_id: int, message_id: int, url: str, codec: str):
        self.chat_id = chat_id
        self.message_id = message_id
        self.url = url
        self.codec = codec
        self.status = "queued"
        self.files_before = set()
        self.files_after = set()
        self.start_time = time.time()


class AppleMusicBot:
    """Apple Music Telegram Bot using Telethon"""
    
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.config = it(Config)
        self.bot: Optional[TelegramClient] = None
        self.download_queue: Dict[str, DownloadTask] = {}
        self.active_downloads: Set[str] = set()
        self.downloads_dir = Path("downloads")
        
        # Ensure downloads directory exists
        self.downloads_dir.mkdir(exist_ok=True)
        
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot"""
        if not self.config.telegram.authorizedUsers:
            return True
        return user_id in self.config.telegram.authorizedUsers
    
    async def start(self):
        """Start the Telegram bot"""
        logger.info("Starting Telegram bot...")
        
        # Initialize Telethon client
        self.bot = TelegramClient(
            self.config.telegram.sessionName,
            self.config.telegram.apiId,
            self.config.telegram.apiHash
        )
        await self.bot.start(bot_token=self.config.telegram.botToken)
        
        logger.info("Bot started successfully!")
        
        # Register handlers
        self.register_handlers()
        
        # Run the bot
        await self.bot.run_until_disconnected()
    
    def register_handlers(self):
        """Register all command and message handlers"""
        
        @self.bot.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            if not self.is_authorized(event.sender_id):
                await event.respond("❌ Unauthorized. Contact the bot owner for access.")
                return
            
            welcome_text = """
🎵 **Apple Music Download Bot**

Welcome! Send me an Apple Music URL to download.

**Commands:**
/help - Show this help message
/dl <url> - Download with default codec
/dl <url> -c <codec> - Download with specific codec
/codec - Change default codec
/status - Check wrapper-manager status
/queue - View download queue

**Supported codecs:**
• alac - Apple Lossless (default)
• ec3 - Dolby Atmos
• ac3 - Dolby Digital
• aac - AAC
• aac-binaural - AAC Binaural
• aac-downmix - AAC Downmix
• aac-legacy - AAC Legacy

Just send me an Apple Music URL and I'll download it with the default codec!
"""
            await event.respond(welcome_text)
        
        @self.bot.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            if not self.is_authorized(event.sender_id):
                await event.respond("❌ Unauthorized")
                return
            
            help_text = """
🎵 **Apple Music Download Bot - Help**

**Basic Usage:**
Simply send any Apple Music URL:
• Song: `https://music.apple.com/us/song/...`
• Album: `https://music.apple.com/us/album/...`
• Playlist: `https://music.apple.com/us/playlist/...`
• Artist: `https://music.apple.com/us/artist/...`

**Commands:**
/dl <url> - Download with default codec
/dl <url> -c <codec> - Download with specific codec
/codec - Change default codec
/status - Check connection status
/queue - View active downloads

**Examples:**
`/dl https://music.apple.com/us/song/123456`
`/dl https://music.apple.com/us/album/123456 -c ec3`

**Supported Codecs:**
• `alac` - Apple Lossless (best quality)
• `ec3` - Dolby Atmos
• `ac3` - Dolby Digital  
• `aac` - AAC
• `aac-binaural` - AAC Binaural
• `aac-downmix` - AAC Downmix
• `aac-legacy` - AAC Legacy

The bot supports files up to 2GB!
"""
            await event.respond(help_text)
        
        @self.bot.on(events.NewMessage(pattern='/status'))
        async def status_handler(event):
            if not self.is_authorized(event.sender_id):
                await event.respond("❌ Unauthorized")
                return
            
            try:
                # Check wrapper-manager connection
                wm = it(WrapperManager)
                wm.status.cache_invalidate()
                st = await wm.status()
                
                status_text = "✅ **Status: Connected**\n\n"
                status_text += f"📡 Wrapper-Manager: Connected\n"
                status_text += f"🌍 Regions: {', '.join(st.regions) if st.regions else 'None'}\n"
                status_text += f"🎵 Active Downloads: {len(self.active_downloads)}\n"
                status_text += f"📥 Queue Length: {len(self.download_queue)}\n"
            except Exception as e:
                status_text = f"❌ **Status: Error**\n\n{str(e)}"
            
            await event.respond(status_text)
        
        @self.bot.on(events.NewMessage(pattern='/queue'))
        async def queue_handler(event):
            if not self.is_authorized(event.sender_id):
                await event.respond("❌ Unauthorized")
                return
            
            if not self.download_queue and not self.active_downloads:
                await event.respond("📭 Queue is empty")
                return
            
            queue_text = "📥 **Download Queue**\n\n"
            
            if self.active_downloads:
                queue_text += "**Active Downloads:**\n"
                for task_id in self.active_downloads:
                    if task_id in self.download_queue:
                        task = self.download_queue[task_id]
                        queue_text += f"• {task.url[:50]}... ({task.codec})\n"
            
            if len(self.download_queue) > len(self.active_downloads):
                queue_text += "\n**Queued:**\n"
                for task_id, task in self.download_queue.items():
                    if task_id not in self.active_downloads:
                        queue_text += f"• {task.url[:50]}... ({task.codec})\n"
            
            await event.respond(queue_text)
        
        @self.bot.on(events.NewMessage(pattern='/codec'))
        async def codec_handler(event):
            if not self.is_authorized(event.sender_id):
                await event.respond("❌ Unauthorized")
                return
            
            current_codec = self.config.telegram.defaultCodec
            buttons = [
                [Button.inline("🎵 ALAC (Lossless)", b"codec:alac")],
                [Button.inline("🔊 EC3 (Atmos)", b"codec:ec3")],
                [Button.inline("🔉 AC3 (Dolby)", b"codec:ac3")],
                [Button.inline("🎧 AAC", b"codec:aac")],
                [Button.inline("🎧 AAC Binaural", b"codec:aac-binaural")],
                [Button.inline("🎧 AAC Downmix", b"codec:aac-downmix")],
                [Button.inline("🎧 AAC Legacy", b"codec:aac-legacy")],
            ]
            
            await event.respond(
                f"🎵 **Codec Settings**\n\nCurrent default: `{current_codec}`\n\nSelect new default:",
                buttons=buttons
            )
        
        @self.bot.on(events.CallbackQuery(pattern=b'codec:'))
        async def codec_callback(event):
            if not self.is_authorized(event.sender_id):
                await event.answer("Unauthorized", alert=True)
                return
            
            codec = event.data.decode('utf-8').split(':')[1]
            self.config.telegram.defaultCodec = codec
            
            await event.answer(f"✅ Default codec set to {codec}")
            await event.edit(f"✅ Default codec changed to: `{codec}`")
        
        @self.bot.on(events.NewMessage(pattern='/dl'))
        async def download_handler(event):
            if not self.is_authorized(event.sender_id):
                await event.respond("❌ Unauthorized")
                return
            
            text = event.message.text
            parts = text.split()
            
            if len(parts) < 2:
                await event.respond("❌ Usage: /dl <url> [-c <codec>]")
                return
            
            url = parts[1]
            codec = self.config.telegram.defaultCodec
            
            # Parse codec flag
            if len(parts) >= 4 and parts[2] == "-c":
                codec = parts[3]
            
            await self.process_download(event, url, codec)
        
        @self.bot.on(events.NewMessage())
        async def message_handler(event):
            # Skip commands
            if event.message.text.startswith('/'):
                return
            
            if not self.is_authorized(event.sender_id):
                return
            
            text = event.message.text.strip()
            
            # Check if it's an Apple Music URL (starts with https://music.apple.com)
            if text.startswith('https://music.apple.com/'):
                url = text.split()[0]  # Get first word (URL)
                codec = self.config.telegram.defaultCodec
                await self.process_download(event, url, codec)
    
    async def process_download(self, event, url: str, codec: str):
        """Process a download request"""
        # Parse URL
        parsed_url = AppleMusicURL.parse_url(url)
        
        if not parsed_url:
            await event.respond("❌ Invalid Apple Music URL")
            return
        
        # Validate codec
        valid_codecs = ["alac", "ec3", "ac3", "aac", "aac-binaural", "aac-downmix", "aac-legacy"]
        if codec not in valid_codecs:
            await event.respond(f"❌ Invalid codec. Valid options: {', '.join(valid_codecs)}")
            return
        
        # Send initial status
        status_msg = await event.respond(f"⏳ Processing {parsed_url.type}...\nCodec: `{codec}`")
        
        # Create download task
        task_id = f"{event.chat_id}_{time.time()}"
        task = DownloadTask(event.chat_id, status_msg.id, url, codec)
        self.download_queue[task_id] = task
        
        try:
            # Get files before download
            task.files_before = self.get_download_files()
            
            # Create flags for download
            flags = Flags()
            
            # Start download based on type
            task.status = "downloading"
            self.active_downloads.add(task_id)
            
            await status_msg.edit(f"📥 Downloading {parsed_url.type}...\nCodec: `{codec}`")
            
            if parsed_url.type == URLType.Song:
                await rip_song(parsed_url, codec, flags)
            elif parsed_url.type == URLType.Album:
                await rip_album(parsed_url, codec, flags)
            elif parsed_url.type == URLType.Playlist:
                await rip_playlist(parsed_url, codec, flags)
            elif parsed_url.type == URLType.Artist:
                await rip_artist(parsed_url, codec, flags)
            
            # Poll for new files with timeout
            max_wait = 300  # 5 minutes max for albums/playlists
            poll_interval = 3
            waited = 0
            last_file_count = -1  # Initialize to -1 to ensure at least two stable intervals
            
            while waited < max_wait:
                await asyncio.sleep(poll_interval)
                waited += poll_interval
                current_files = self.get_download_files()
                new_files = current_files - task.files_before
                current_count = len(new_files)
                
                if current_count > 0 and current_count == last_file_count:
                    # No new files for one interval, likely done
                    await asyncio.sleep(2)  # Final grace period
                    break
                last_file_count = current_count
            
            # Get new files
            task.files_after = self.get_download_files()
            new_files = task.files_after - task.files_before
            
            if not new_files:
                await status_msg.edit(f"⚠️ Download completed but no new files found.\nThe file may already exist.")
                return
            
            # Upload files
            task.status = "uploading"
            await status_msg.edit(f"📤 Uploading {len(new_files)} file(s)...")
            
            uploaded_count = 0
            for file_path in sorted(new_files):
                if file_path.suffix in AUDIO_EXTENSIONS:
                    # Upload audio file
                    await self.upload_audio(event.chat_id, file_path, status_msg)
                    uploaded_count += 1
                elif file_path.suffix in LYRICS_EXTENSIONS:
                    # Upload lyrics
                    await self.upload_document(event.chat_id, file_path)
                    uploaded_count += 1
                elif file_path.suffix in IMAGE_EXTENSIONS:
                    # Upload cover art
                    await self.upload_photo(event.chat_id, file_path)
                    uploaded_count += 1
            
            # Clean up files after upload
            for file_path in new_files:
                try:
                    file_path.unlink()
                    logger.debug(f"Cleaned up: {file_path}")
                except Exception as e:
                    logger.debug(f"Failed to clean up {file_path}: {e}")
            
            # Success message
            await status_msg.edit(f"✅ Upload complete!\n{uploaded_count} file(s) uploaded.")
            
        except CodecNotFoundException as e:
            await status_msg.edit(f"❌ Codec `{codec}` not available for this track.\nTry a different codec with /dl {url} -c <codec>")
        except Exception as e:
            logger.exception(f"Error downloading {url}")
            await status_msg.edit(f"❌ Download failed: {str(e)[:200]}")
        finally:
            # Clean up
            if task_id in self.active_downloads:
                self.active_downloads.remove(task_id)
            if task_id in self.download_queue:
                del self.download_queue[task_id]
    
    def get_download_files(self) -> Set[Path]:
        """Get all files in downloads directory"""
        files = set()
        if self.downloads_dir.exists():
            for file_path in self.downloads_dir.rglob('*'):
                if file_path.is_file():
                    files.add(file_path)
        return files
    
    def _upload_progress_sync(self, status_msg, current, total):
        """Upload progress callback for large files (sync wrapper)"""
        if status_msg and total:
            percent = int(current * 100 / total)
            # Update every 20% to avoid too many edits
            if not hasattr(self, '_last_percent'):
                self._last_percent = 0
            if percent >= self._last_percent + 20:
                self._last_percent = percent
                # Schedule the async update without waiting
                asyncio.create_task(self._upload_progress_async(status_msg, percent))
    
    async def _upload_progress_async(self, status_msg, percent):
        """Async helper to update upload progress"""
        try:
            await status_msg.edit(f"📤 Uploading... {percent}%")
        except:
            pass  # Ignore if we can't edit (e.g., too many edits)
    
    async def upload_audio(self, chat_id: int, file_path: Path, status_msg=None):
        """Upload audio file with metadata"""
        try:
            # Get audio metadata using mutagen
            from mutagen.mp4 import MP4
            
            audio = MP4(str(file_path))
            duration = int(audio.info.length) if audio.info else 0
            title = audio.get('\xa9nam', [file_path.stem])[0] if '\xa9nam' in audio else file_path.stem
            artist = audio.get('\xa9ART', ['Unknown'])[0] if '\xa9ART' in audio else 'Unknown'
            
            # Find cover art
            cover_path = None
            cover_files = list(file_path.parent.glob('cover.*'))
            if cover_files:
                cover_path = str(cover_files[0])
            
            # Initialize progress tracking
            self._last_percent = 0
            
            # Upload with metadata and progress callback
            await self.bot.send_file(
                chat_id,
                str(file_path),
                caption=f"🎵 {title}\n🎤 {artist}",
                attributes=[
                    DocumentAttributeAudio(
                        duration=duration,
                        title=title,
                        performer=artist,
                        voice=False
                    )
                ],
                thumb=cover_path if cover_path else None,
                force_document=False,
                supports_streaming=True,
                progress_callback=lambda c, t: self._upload_progress_sync(status_msg, c, t) if status_msg else None
            )
            
            logger.info(f"Uploaded audio: {file_path.name}")
            
        except Exception as e:
            logger.exception(f"Error uploading audio {file_path}")
            # Fallback: upload as document
            await self.upload_document(chat_id, file_path)
    
    async def upload_document(self, chat_id: int, file_path: Path):
        """Upload file as document"""
        try:
            await self.bot.send_file(
                chat_id,
                str(file_path),
                caption=f"📄 {file_path.name}",
                attributes=[DocumentAttributeFilename(file_path.name)]
            )
            logger.info(f"Uploaded document: {file_path.name}")
        except Exception as e:
            logger.exception(f"Error uploading document {file_path}")
    
    async def upload_photo(self, chat_id: int, file_path: Path):
        """Upload photo/cover art"""
        try:
            await self.bot.send_file(
                chat_id,
                str(file_path),
                caption=f"🖼️ Cover Art"
            )
            logger.info(f"Uploaded photo: {file_path.name}")
        except Exception as e:
            logger.exception(f"Error uploading photo {file_path}")
