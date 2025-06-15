"""
Menu navigation and callback query handlers
"""

import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import ContextTypes

from ..ui.menus import (
    MainMenu, SystemMenu, NodeMenu, LogsMenu, 
    ToolsMenu, SettingsMenu, ComponentsMenu
)

if TYPE_CHECKING:
    from ..core.monitor import AztecMonitor

logger = logging.getLogger(__name__)

class MenuHandlers:
    """Handles menu navigation and callback queries"""
    
    def __init__(self, monitor: 'AztecMonitor'):
        self.monitor = monitor
        
        # Initialize menu classes
        self.main_menu = MainMenu()
        self.system_menu = SystemMenu()
        self.node_menu = NodeMenu()
        self.logs_menu = LogsMenu()
        self.tools_menu = ToolsMenu()
        self.settings_menu = SettingsMenu()
        self.components_menu = ComponentsMenu()
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Main callback query handler"""
        query = update.callback_query
        user_id = query.from_user.id

        if not self.monitor.check_authorization(user_id):
            await query.answer("❌ Unauthorized access!", show_alert=True)
            return

        await query.answer()
        
        try:
            # Route to appropriate handler based on callback data
            if query.data == "main_menu":
                await self._handle_main_menu(query)
            elif query.data == "system_menu":
                await self._handle_system_menu(query)
            elif query.data == "node_management":
                await self._handle_node_menu(query)
            elif query.data == "logs_menu":
                await self._handle_logs_menu(query)
            elif query.data == "tools_menu":
                await self._handle_tools_menu(query)
            elif query.data == "settings_menu":
                await self._handle_settings_menu(query)
            elif query.data == "components_menu":
                await self._handle_components_menu(query)
            else:
                # Route to system handlers for specific actions
                from .system_handlers import SystemHandlers
                system_handlers = SystemHandlers(self.monitor)
                await system_handlers.handle_callback(query, context)
                
        except Exception as e:
            logger.error(f"Error in button handler: {e}")
            await query.edit_message_text(
                f"❌ An error occurred: {str(e)}",
                reply_markup=self.main_menu.create()
            )
    
    async def _handle_main_menu(self, query):
        """Handle main menu display"""
        text = "🏠 *Main Menu*\n\nSelect a category:"
        await query.edit_message_text(
            text,
            reply_markup=self.main_menu.create(),
            parse_mode="MarkdownV2",
        )
    
    async def _handle_system_menu(self, query):
        """Handle system menu display"""
        text = """📊 *System Monitoring*

Monitor your Aztec node's core components and performance metrics

Select an option:"""
        await query.edit_message_text(
            text,
            reply_markup=self.system_menu.create(),
            parse_mode="MarkdownV2",
        )
    
    async def _handle_node_menu(self, query):
        """Handle node management menu display"""
        text = """🏗️ *Node Management*

Manage your Aztec node version and updates efficiently

Features:
• Quick update to latest version
• Browse all available versions  
• Smart caching for faster responses
• Detailed update progress tracking

Select an option:"""
        await query.edit_message_text(
            text,
            reply_markup=self.node_menu.create(),
            parse_mode="MarkdownV2",
        )
    
    async def _handle_logs_menu(self, query):
        """Handle logs menu display"""
        text = """📝 *Log Analysis*

View and filter Aztec node logs with advanced options

Features:
• Filter by log level (INFO, WARN, ERROR, etc.)
• Component-specific filtering
• Clean view without ANSI codes
• Real-time log monitoring

Select an option:"""
        await query.edit_message_text(
            text,
            reply_markup=self.logs_menu.create(),
            parse_mode="MarkdownV2",
        )
    
    async def _handle_tools_menu(self, query):
        """Handle tools menu display"""
        text = """🔧 *Tools & Diagnostics*

Access network diagnostics, monitoring tools, and utilities

Features:
• RPC health checking
• Port connectivity testing
• Monitoring controls
• System diagnostics

Select an option:"""
        await query.edit_message_text(
            text,
            reply_markup=self.tools_menu.create(),
            parse_mode="MarkdownV2",
        )
    
    async def _handle_settings_menu(self, query):
        """Handle settings menu display"""
        text = """⚙️ *Settings & Maintenance*

Configure bot settings, check for updates, and view system information

Select an option:"""
        await query.edit_message_text(
            text,
            reply_markup=self.settings_menu.create(),
            parse_mode="MarkdownV2",
        )
    
    async def _handle_components_menu(self, query):
        """Handle components menu display"""
        text = """🔧 *Component Logs*

Filter logs by specific Aztec node components

Select a component:"""
        await query.edit_message_text(
            text,
            reply_markup=self.components_menu.create(),
            parse_mode="MarkdownV2",
        )
