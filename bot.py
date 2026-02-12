"""
Apple Music Telegram Bot Entry Point
"""
import asyncio
import sys

import grpc
import grpc.aio
from creart import add_creator, it

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

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

from src.api import WebAPI
from src.config import Config
from src.grpc.manager import WrapperManager
from src.logger import GlobalLogger
from src.qemu import QemuInstance
from src.rip import on_decrypt_success, on_decrypt_failed
from src.telegram_bot import AppleMusicBot
from src.utils import run_sync, safely_create_task, check_dep, config_outdated


async def initialize_bot():
    """Initialize the bot with all required components"""
    # Check dependencies
    dep_installed, missing_dep = check_dep()
    if not dep_installed:
        it(GlobalLogger).logger.error(f"Dependence {missing_dep} was not installed!")
        sys.exit(1)
    
    # Validate Telegram configuration
    config = it(Config)
    if not config.telegram.botToken:
        it(GlobalLogger).logger.error("Telegram bot token not configured! Set telegram.botToken in config.toml")
        sys.exit(1)
    if not config.telegram.apiId or not config.telegram.apiHash:
        it(GlobalLogger).logger.error("Telegram API credentials not configured! Set telegram.apiId and telegram.apiHash in config.toml")
        sys.exit(1)
    
    # Initialize WebAPI
    await run_sync(it(WebAPI).init)
    
    # Initialize wrapper-manager
    local_instance = None
    if config.localInstance.enable:
        # Launch local QEMU instance and keep reference for potential cleanup
        local_instance = QemuInstance()
        await local_instance.launch_instance(loop)
        config.instance.url = "127.0.0.1:32767"
        config.instance.secure = False
        await it(WrapperManager).init(config.instance.url, config.instance.secure)
        
        # Wait for wrapper-manager to be ready with timeout
        max_qemu_wait = 120  # 2 minutes
        qemu_waited = 0
        qemu_ready = False
        while qemu_waited < max_qemu_wait:
            it(WrapperManager).status.cache_invalidate()
            if (await it(WrapperManager).status()).ready:
                qemu_ready = True
                break
            await asyncio.sleep(3)
            qemu_waited += 3
        
        if not qemu_ready:
            it(GlobalLogger).logger.error("QEMU local instance failed to become ready within timeout")
            sys.exit(1)
    else:
        await it(WrapperManager).init(config.instance.url, config.instance.secure)
    
    # Initialize decrypt handlers
    safely_create_task(it(WrapperManager).decrypt_init(on_success=on_decrypt_success, on_failure=on_decrypt_failed))
    
    # Check wrapper-manager connection
    try:
        it(WrapperManager).status.cache_invalidate()
        st_resp = await it(WrapperManager).status()
        if not st_resp.regions:
            it(GlobalLogger).logger.warning("The wrapper-manager instance has no available accounts. Login may be required.")
        it(GlobalLogger).logger.info(f"Regions available on wrapper-manager: {', '.join(st_resp.regions)}")
    except (grpc.aio.AioRpcError, grpc.RpcError):
        it(GlobalLogger).logger.error("Unable to connect to the wrapper-manager")
        sys.exit(1)
    
    it(GlobalLogger).logger.info("Bot initialization complete!")
    
    # Check if configuration is outdated
    if config_outdated():
        it(GlobalLogger).logger.warning("The configuration file is out of date. Please refer to config.example.toml to update it")
    
    return local_instance


if __name__ == '__main__':
    local_instance = None
    try:
        # Initialize all components
        local_instance = loop.run_until_complete(initialize_bot())
        
        # Start the Telegram bot
        bot = AppleMusicBot(loop)
        loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        it(GlobalLogger).logger.info("Bot stopped by user")
        loop.stop()
    except Exception as e:
        it(GlobalLogger).logger.error(f"Bot failed to start: {e}")
        sys.exit(1)
    finally:
        # Cleanup local instance if it was started
        if local_instance and it(Config).localInstance.enable:
            try:
                loop.run_until_complete(local_instance.terminate())
            except Exception:
                pass
