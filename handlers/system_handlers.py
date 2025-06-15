"""
System-specific action handlers
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..core.utils import escape_markdown_v2
from ..ui.formatters import StatusFormatter, LogFormatter

if TYPE_CHECKING:
    from ..core.monitor import AztecMonitor

logger = logging.getLogger(__name__)

class SystemHandlers:
    """Handles system-specific actions and callbacks"""
    
    def __init__(self, monitor: 'AztecMonitor'):
        self.monitor = monitor
        self.status_formatter = StatusFormatter()
        self.log_formatter = LogFormatter()
    
    async def handle_callback(self, query, context):
        """Route callback to appropriate handler"""
        data = query.data
        
        if data == "status":
            await self.handle_status(query)
        elif data == "resources":
            await self.handle_resources(query)
        elif data == "validator_status":
            await self.handle_validator_status(query)
        elif data == "peer_status":
            await self.handle_peer_status(query)
        elif data == "sync_custom":
            await self.handle_sync_status_custom(query, context)
        elif data == "rpc_check":
            await self.handle_rpc_check_custom(query, context)
        elif data == "port_check":
            await self.handle_port_check_menu(query, context)
        elif data.startswith("logs_"):
            await self.handle_logs(query, data)
        elif data.startswith("comp_"):
            await self.handle_component_logs(query, data)
        elif data.startswith("node_"):
            await self.handle_node_actions(query, data)
        elif data.startswith("bot_"):
            await self.handle_bot_actions(query, data)
        elif data.startswith("monitor_"):
            await self.handle_monitor_actions(query, data, context)
    
    async def handle_status(self, query):
        """Handle service status display"""
        loading_msg = "🔍 Checking service status...\n⏳ Please wait..."
        await query.edit_message_text(loading_msg, reply_markup=None)
        
        try:
            status = await self.monitor.get_service_status()
            text = self.status_formatter.format_service_status(status)
            
            await query.edit_message_text(
                escape_markdown_v2(text),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="status")],
                    [InlineKeyboardButton("🔙 Back", callback_data="system_menu")]
                ]),
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            error_text = f"❌ Error checking service status: {str(e)}"
            await query.edit_message_text(
                error_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="system_menu")]
                ])
            )
    
    async def handle_resources(self, query):
        """Handle system resources display"""
        try:
            resources = self.monitor.get_system_resources()
            text = self.status_formatter.format_system_resources(resources)
            
            await query.edit_message_text(
                escape_markdown_v2(text),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="resources")],
                    [InlineKeyboardButton("🔙 Back", callback_data="system_menu")]
                ]),
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            error_text = f"❌ Error getting system resources: {str(e)}"
            await query.edit_message_text(
                error_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="system_menu")]
                ])
            )
    
    async def handle_validator_status(self, query):
        """Handle validator status check"""
        loading_msg = """🔍 Checking validator status...
⏳ Getting validator owner address...
⏳ Fetching validator data...
Please wait..."""
        await query.edit_message_text(loading_msg, reply_markup=None)
        
        try:
            status = await self.monitor.get_validator_status()
            text = self.status_formatter.format_validator_status(status)
            
            back_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
                [InlineKeyboardButton("🔄 Retry", callback_data="validator_status")],
            ])
            
            try:
                escaped_text = escape_markdown_v2(text)
                await query.edit_message_text(
                    escaped_text, reply_markup=back_button, parse_mode="MarkdownV2"
                )
            except Exception as e:
                logger.warning(f"Markdown parsing failed, using plain text: {e}")
                plain_text = text.replace("*", "").replace("`", "").replace("\\", "")
                await query.edit_message_text(plain_text, reply_markup=back_button)
                
        except Exception as e:
            logger.error(f"Error in validator status: {e}")
            error_text = f"❌ Error checking validator status: {str(e)}"
            await query.edit_message_text(
                error_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
                ])
            )
    
    async def handle_peer_status(self, query):
        """Handle peer status check"""
        loading_msg = """🔍 Checking peer status...

⏳ Getting local peer ID...
⏳ Fetching network data...
⏳ Comparing with network peers...

Please wait..."""

        await query.edit_message_text(loading_msg, reply_markup=None)

        try:
            status = await self.monitor.get_peer_status()
            text = self.status_formatter.format_peer_status(status)

            back_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
                [InlineKeyboardButton("🔄 Retry", callback_data="peer_status")],
            ])

            try:
                escaped_text = escape_markdown_v2(text)
                await query.edit_message_text(
                    escaped_text, reply_markup=back_button, parse_mode="MarkdownV2"
                )
            except Exception as e:
                logger.warning(f"Markdown parsing failed, using plain text: {e}")
                plain_text = text.replace("*", "").replace("`", "").replace("\\", "")
                await query.edit_message_text(plain_text, reply_markup=back_button)
                
        except Exception as e:
            logger.error(f"Error in peer status: {e}")
            error_text = f"❌ Error checking peer status: {str(e)}"
            await query.edit_message_text(
                error_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
                ])
            )
    
    async def handle_sync_status_custom(self, query, context):
        """Handle custom sync status check"""
        text = "📥 Please enter the port number your Aztec RPC is running on (e.g. 8080, 9000):"
        escaped_text = escape_markdown_v2(text)    
        await query.edit_message_text(escaped_text, parse_mode="MarkdownV2")
        context.user_data["awaiting_port"] = True
    
    async def handle_rpc_check_custom(self, query, context):
        """Handle custom RPC check"""
        text = """🔍 RPC Health Check

Enter RPC details in one of these formats:

Single RPC:
`http://127.0.0.1:8545`
`http://your-ip:8545`

RPC + Beacon:
`http://127.0.0.1:8545,http://127.0.0.1:3500`
`http://your-ip:8545,http://your-ip:3500`

Examples:
• `http://127.0.0.1:8545` - Local execution only
• `http://192.168.1.100:8545,http://192.168.1.100:3500` - Both RPC & Beacon
• `https://eth-sepolia.g.alchemy.com/v2/your-key` - Remote RPC

Please enter your RPC URL(s):"""
        escaped_text = escape_markdown_v2(text)
        await query.edit_message_text(
            escaped_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ]),
            parse_mode="MarkdownV2"
        )
        context.user_data["awaiting_rpc_check"] = True
    
    async def handle_port_check_menu(self, query, context):
        """Handle port check menu"""
        text = """🔍 Port Check Tool

Enter port number to check if it's open on your public IP address.

Common ports:
• 8080 - HTTP Alternative
• 8081 - HTTP Alternative  
• 3000 - Development Server
• 9000 - Various Services
• 22 - SSH
• 80 - HTTP
• 443 - HTTPS

Please enter a port number (1-65535):"""
        
        escaped_text = escape_markdown_v2(text)
        await query.edit_message_text(
            escaped_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
            ]),
            parse_mode="MarkdownV2"
        )
        
        context.user_data["awaiting_port_check"] = True
    
    async def handle_logs(self, query, data):
        """Handle log filtering"""
        log_level = data.replace("logs_", "")
        
        loading_msg = f"📝 Loading {log_level.upper()} logs...\n⏳ Please wait..."
        await query.edit_message_text(loading_msg, reply_markup=None)
        
        try:
            logs = await self.monitor.get_aztec_logs(
                lines=50, 
                log_level=log_level if log_level != "all" else None
            )
            
            if logs and not any("error" in log for log in logs):
                text = self.log_formatter.format_logs(logs, clean_view=(data == "logs_clean"))
            else:
                text = f"❌ No {log_level.upper()} logs found or error retrieving logs"
            
            await query.edit_message_text(
                escape_markdown_v2(text),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data=data)],
                    [InlineKeyboardButton("🔙 Back", callback_data="logs_menu")]
                ]),
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            error_text = f"❌ Error retrieving logs: {str(e)}"
            await query.edit_message_text(
                error_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="logs_menu")]
                ])
            )
    
    async def handle_component_logs(self, query, data):
        """Handle component-specific log filtering"""
        component = data.replace("comp_", "")
        
        loading_msg = f"📝 Loading {component} logs...\n⏳ Please wait..."
        await query.edit_message_text(loading_msg, reply_markup=None)
        
        try:
            logs = await self.monitor.get_aztec_logs(
                lines=50, 
                component=component
            )
            
            if logs and not any("error" in log for log in logs):
                text = self.log_formatter.format_logs(logs)
            else:
                text = f"❌ No {component} logs found or error retrieving logs"
            
            await query.edit_message_text(
                escape_markdown_v2(text),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data=data)],
                    [InlineKeyboardButton("🔙 Back", callback_data="components_menu")]
                ]),
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            error_text = f"❌ Error retrieving {component} logs: {str(e)}"
            await query.edit_message_text(
                error_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back", callback_data="components_menu")]
                ])
            )
    
    async def handle_node_actions(self, query, data):
        """Handle node management actions"""
        # This would be implemented based on the specific node actions
        # For now, just show a placeholder
        await query.edit_message_text(
            f"🏗️ Node action: {data}\n\n(Implementation pending)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="node_management")]
            ])
        )
    
    async def handle_bot_actions(self, query, data):
        """Handle bot management actions"""
        # This would be implemented based on the specific bot actions
        # For now, just show a placeholder
        await query.edit_message_text(
            f"🤖 Bot action: {data}\n\n(Implementation pending)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="settings_menu")]
            ])
        )
    
    async def handle_monitor_actions(self, query, data, context):
        """Handle monitoring actions"""
        # This would be implemented based on the specific monitor actions
        # For now, just show a placeholder
        await query.edit_message_text(
            f"📊 Monitor action: {data}\n\n(Implementation pending)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="tools_menu")]
            ])
        )
