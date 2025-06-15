#!/usr/bin/env python3
"""
Main entry point for Aztec Node Monitor Bot
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from .config.settings import Config
from .core.monitor import AztecMonitor
from .handlers.bot_handlers import BotHandlers
from .handlers.menu_handlers import MenuHandlers
from .handlers.system_handlers import SystemHandlers

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)

class AztecMonitorBot:
    """Main bot application class"""
    
    def __init__(self):
        self.monitor = AztecMonitor()
        self.application: Optional[Application] = None
        self.bot_handlers = BotHandlers(self.monitor)
        self.menu_handlers = MenuHandlers(self.monitor)
        self.system_handlers = SystemHandlers(self.monitor)
        
    async def setup_handlers(self):
        """Setup all bot handlers"""
        if not self.application:
            return
            
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.bot_handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.bot_handlers.help_command))
        self.application.add_handler(CommandHandler("status", self.bot_handlers.status_command))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.menu_handlers.button_handler))
        
        # Message handlers for user input
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.bot_handlers.handle_user_input
            )
        )
        
        logger.info("All handlers registered successfully")
    
    async def start_bot(self):
        """Start the bot application"""
        try:
            # Create application
            self.application = Application.builder().token(Config.BOT_TOKEN).build()
            
            # Setup handlers
            await self.setup_handlers()
            
            # Start monitoring if enabled
            if Config.AUTO_START_MONITORING:
                self.monitor.start_monitoring(Config.DEFAULT_MONITOR_INTERVAL)
                logger.info("Auto-monitoring started")
            
            # Start the bot
            logger.info("Starting Aztec Monitor Bot...")
            await self.application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def stop_bot(self):
        """Stop the bot application"""
        try:
            if self.monitor.monitoring_active:
                self.monitor.stop_monitoring()
                logger.info("Monitoring stopped")
            
            if self.application:
                await self.application.stop()
                logger.info("Bot stopped")
                
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

async def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start bot
    bot = AztecMonitorBot()
    
    try:
        await bot.start_bot()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.stop_bot()

if __name__ == "__main__":
    asyncio.run(main())
