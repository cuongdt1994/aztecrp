"""
Main bot command and message handlers
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from telegram import Update
from telegram.ext import ContextTypes

from ..config.settings import Config
from ..core.utils import escape_markdown_v2
from ..ui.menus import MainMenu

if TYPE_CHECKING:
    from ..core.monitor import AztecMonitor

logger = logging.getLogger(__name__)

class BotHandlers:
    """Handles bot commands and user input"""
    
    def __init__(self, monitor: 'AztecMonitor'):
        self.monitor = monitor
        self.main_menu = MainMenu()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        user_id = update.effective_user.id
        if not self.monitor.check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access!")
            return

        # Get quick status for welcome
        try:
            service_status = await self.monitor.get_service_status()
            current_version = await self.monitor.get_node_current_version()
            
            status_icon = "🟢" if service_status["active"] else "🔴"
            version_text = f"v{current_version}" if current_version else "Unknown"
            
            welcome_text = f"""🚀 Aztec Node Monitor

{status_icon} Service: {'Running' if service_status['active'] else 'Stopped'}
📦 Version: {version_text}
⏰ {datetime.now().strftime('%H:%M %d/%m/%Y')}

Choose an option to get started:"""
            
        except Exception as e:
            logger.error(f"Error getting status in start command: {e}")
            welcome_text = """🚀 Aztec Node Monitor

Welcome to your node monitoring dashboard!

Choose an option to get started:"""

        await update.message.reply_text(
            escape_markdown_v2(welcome_text),
            reply_markup=self.main_menu.create(),
            parse_mode="MarkdownV2",
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        user_id = update.effective_user.id
        if not self.monitor.check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access!")
            return
        
        help_text = f"""🤖 Aztec Monitor Bot Help

**Available Commands:**
• `/start` - Show main menu
• `/help` - Show this help message
• `/status` - Quick status check

**Features:**
• 🎯 Validator monitoring
• 📊 System resource tracking
• 🏗️ Node version management
• 📝 Log analysis with filtering
• 🔧 Network diagnostics
• ⚙️ Automated monitoring

**Version:** {Config.BOT_VERSION}
**Service:** {Config.SERVICE_NAME}

Use the inline menu buttons for easy navigation!"""
        
        await update.message.reply_text(
            escape_markdown_v2(help_text),
            parse_mode="MarkdownV2"
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command for quick status check"""
        user_id = update.effective_user.id
        if not self.monitor.check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access!")
            return
        
        try:
            # Get basic status info
            service_status = await self.monitor.get_service_status()
            resources = self.monitor.get_system_resources()
            current_version = await self.monitor.get_node_current_version()
            
            status_icon = "🟢" if service_status["active"] else "🔴"
            cpu_icon = "🟢" if resources["cpu"]["percent"] < 70 else "🟡" if resources["cpu"]["percent"] < 90 else "🔴"
            mem_icon = "🟢" if resources["memory"]["percent"] < 70 else "🟡" if resources["memory"]["percent"] < 90 else "🔴"
            
            status_text = f"""📊 Quick Status Check

{status_icon} Service: {'Running' if service_status['active'] else 'Stopped'}
📦 Version: {current_version or 'Unknown'}

{cpu_icon} CPU: {resources['cpu']['percent']:.1f}%
{mem_icon} Memory: {resources['memory']['percent']:.1f}%

⏰ {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}

Use /start for full menu access."""
            
            await update.message.reply_text(
                escape_markdown_v2(status_text),
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text(
                f"❌ Error getting status: {str(e)}"
            )
    
    async def handle_user_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user text input based on context"""
        user_id = update.effective_user.id
        if not self.monitor.check_authorization(user_id):
            await update.message.reply_text("❌ Unauthorized access!")
            return
        
        # Handle different input contexts
        if context.user_data.get("awaiting_port"):
            await self._handle_port_input(update, context)
        elif context.user_data.get("awaiting_monitor_interval"):
            await self._handle_monitor_interval_input(update, context)
        elif context.user_data.get("awaiting_rpc_check"):
            await self._handle_rpc_input(update, context)
        elif context.user_data.get("awaiting_port_check"):
            await self._handle_port_check_input(update, context)
        else:
            await update.message.reply_text(
                "ℹ️ Please use the menu buttons to interact with the bot."
            )
    
    async def _handle_port_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle port input for sync status"""
        port_text = update.message.text.strip()
        if not port_text.isdigit():
            await update.message.reply_text("❌ Invalid port number! Please enter a valid number.")
            return
        
        port = int(port_text)
        context.user_data["awaiting_port"] = False
        
        msg = f"🔍 Checking sync status on port `{port}`..."
        await update.message.reply_text(escape_markdown_v2(msg), parse_mode="MarkdownV2")
        
        try:
            status = await self.monitor.get_sync_status(local_port=port)
            local = status["local"]
            remote = status["remote"]
            synced = status["synced"]
            
            if local is None or remote is None:
                text = f"❌ Could not fetch sync status.\n🧱 Local block: {local or 'N/A'}\n🌐 Remote block: {remote or 'N/A'}"
            elif synced:
                text = f"✅ Node is fully synced!\n\n🧱 Local: {local}\n🌐 Remote: {remote}"
            else:
                percent = f"{(local / remote * 100):.2f}%" if local and remote else "N/A"
                text = f"⏳ Syncing...\n\n🧱 Local: {local}\n🌐 Remote: {remote}\n📈 Progress: {percent}"

            await update.message.reply_text(escape_markdown_v2(text), parse_mode="MarkdownV2")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error checking sync status: {str(e)}")
    
    async def _handle_monitor_interval_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle monitor interval input"""
        interval_text = update.message.text.strip()
        context.user_data["awaiting_monitor_interval"] = False
        
        try:
            interval = int(interval_text)
            if interval < 60:
                await update.message.reply_text("❌ Minimum interval is 60 seconds!")
                return
            
            if self.monitor.monitoring_active:
                self.monitor.stop_monitoring()
            
            self.monitor.start_monitoring(interval)
            
            success_text = f"""✅ Custom Monitoring Started!

⏱️ Check Interval: {interval} seconds ({interval//60} minutes)
🔍 Miss Rate Alert: > 30%
🔕 Alert Cooldown: 30 minutes

Your custom monitoring interval has been applied."""
            
            await update.message.reply_text(
                escape_markdown_v2(success_text), 
                parse_mode="MarkdownV2"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid interval! Please enter a valid number in seconds.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error setting interval: {str(e)}")
    
    async def _handle_rpc_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle RPC check input"""
        input_text = update.message.text.strip()
        context.user_data["awaiting_rpc_check"] = False
        
        try:
            if "," in input_text:
                parts = input_text.split(",", 1)
                exec_rpc = parts[0].strip()
                beacon_rpc = parts[1].strip()
            else:
                exec_rpc = input_text.strip()
                beacon_rpc = None
            
            if not (exec_rpc.startswith("http://") or exec_rpc.startswith("https://")):
                await update.message.reply_text("❌ Execution RPC must start with http:// or https://")
                return
            
            if beacon_rpc and not (beacon_rpc.startswith("http://") or beacon_rpc.startswith("https://")):
                await update.message.reply_text("❌ Beacon RPC must start with http:// or https://")
                return
            
            checking_msg = f"🔍 Checking RPC health...\n\n⏳ Testing execution RPC: {exec_rpc}"
            if beacon_rpc:
                checking_msg += f"\n⏳ Testing beacon RPC: {beacon_rpc}"
            checking_msg += "\n\nPlease wait..."
            await update.message.reply_text(checking_msg)
            
            result = await self.monitor.check_rpc_health(exec_rpc, beacon_rpc)
            if result["success"]:
                text = result["message"]
            else:
                text = f"❌ RPC Health Check Failed\n\n{result['message']}"
            
            await update.message.reply_text(
                escape_markdown_v2(text),
                parse_mode="MarkdownV2"
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error processing RPC check: {str(e)}")
    
    async def _handle_port_check_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle port check input"""
        input_text = update.message.text.strip()
        context.user_data["awaiting_port_check"] = False
        
        try:
            # Parse input: port or ip:port
            if ":" in input_text:
                parts = input_text.rsplit(":", 1)
                ip_address = parts[0]
                port = int(parts[1])
            else:
                ip_address = None
                port = int(input_text)
            
            if not (1 <= port <= 65535):
                await update.message.reply_text("❌ Port number must be between 1 and 65535!")
                return
            
            checking_msg = f"🔍 Checking port {port}"
            if ip_address:
                checking_msg += f" on {ip_address}"
            checking_msg += "...\n\n⏳ Please wait..."
            await update.message.reply_text(checking_msg)
            
            result = await self.monitor.check_port_open(port, ip_address)
            
            if result["success"]:
                status_icon = "🟢" if result["is_open"] else "🔴"
                status_text = "OPEN" if result["is_open"] else "CLOSED"
                text = f"""🔍 Port Check Result

{status_icon} Status: {status_text}
🌐 IP Address: {result['ip_address']}
🔌 Port: {result['port']}

{result['message']}"""
                
                if result["is_open"]:
                    text += f"""

✅ Port {port} is accessible from the internet
• Services can accept incoming connections
• Port forwarding is working correctly
• No firewall blocking this port"""
                else:
                    text += f"""

❌ Port {port} is not accessible from the internet

Possible causes:
• Port is not open/listening
• Firewall blocking the port
• Router not forwarding the port
• Service not running on this port

To fix:
• Check if service is running
• Configure port forwarding on router
• Allow port through firewall"""
            else:
                text = f"""🔍 Port Check Result

❌ Error checking port {port}

{result['message']}"""
            
            await update.message.reply_text(
                escape_markdown_v2(text),
                parse_mode="MarkdownV2"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid input! Please enter a valid port number or ip:port format.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error processing input: {str(e)}")
