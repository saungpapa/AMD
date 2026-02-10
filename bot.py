"""
Apple Music Telegram Bot Entry Point
"""
import asyncio

from creart import add_creator

loop = asyncio.new_event_loop()

# Initialize all creators (same as main.py)
from src.logger import LoggerCreator
add_creator(LoggerCreator)
from src.config import ConfigCreator
add_creator(ConfigCreator)
from src.api import APICreator
add_creator(APICreator)
from src.grpc.manager import WMCreator
add_creator(WMCreator)
from src.measurer import MeasurerCreator
add_creator(MeasurerCreator)

from src.telegram_bot import AppleMusicBot

if __name__ == '__main__':
    bot = AppleMusicBot(loop)
    try:
        loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        loop.stop()
