"""
Telegram inline keyboard menu definitions
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class MainMenu:
    """Main navigation menu"""
    
    def create(self) -> InlineKeyboardMarkup:
        """Create main menu keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎯 Validator", callback_data="validator_status"),
                InlineKeyboardButton("📊 System", callback_data="system_menu"),
            ],
            [
                InlineKeyboardButton("🏗️ Node", callback_data="node_management"),
                InlineKeyboardButton("📝 Logs", callback_data="logs_menu"),
            ],
            [
                InlineKeyboardButton("🔧 Tools", callback_data="tools_menu"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu"),
            ]
        ])

class SystemMenu:
    """System monitoring submenu"""
    
    def create(self) -> InlineKeyboardMarkup:
        """Create system menu keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Service Status", callback_data="status"),
                InlineKeyboardButton("💻 Resources", callback_data="resources"),
            ],
            [
                InlineKeyboardButton("🔄 Sync Status", callback_data="sync_custom"),
                InlineKeyboardButton("🌐 Peer Status", callback_data="peer_status"),
            ],
            [
                InlineKeyboardButton("⚡ Quick Actions", callback_data="quick_actions"),
                InlineKeyboardButton("🔙 Back", callback_data="main_menu"),
            ]
        ])

class NodeMenu:
    """Node management submenu"""
    
    def create(self) -> InlineKeyboardMarkup:
        """Create node management menu keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📦 Current version", callback_data="node_current_version"),
            ],
            [
                InlineKeyboardButton("🔍 Check Updates", callback_data="node_check_update"),
                InlineKeyboardButton("🚀 Quick Update", callback_data="node_quick_update"),
            ],
            [
                InlineKeyboardButton("📋 Browse Versions", callback_data="node_version_list"),
                InlineKeyboardButton("🗑️ Clear Cache", callback_data="node_clear_cache"),
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            ]
        ])

class LogsMenu:
    """Logs filtering submenu"""
    
    def create(self) -> InlineKeyboardMarkup:
        """Create logs menu keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📄 All Logs", callback_data="logs_all"),
                InlineKeyboardButton("ℹ️ INFO", callback_data="logs_info"),
            ],
            [
                InlineKeyboardButton("⚠️ WARN", callback_data="logs_warn"),
                InlineKeyboardButton("❌ ERROR", callback_data="logs_error"),
            ],
            [
                InlineKeyboardButton("🐛 DEBUG", callback_data="logs_debug"),
                InlineKeyboardButton("💀 FATAL", callback_data="logs_fatal"),
            ],
            [
                InlineKeyboardButton("🔧 Components", callback_data="components_menu"),
                InlineKeyboardButton("🎨 Clean View", callback_data="logs_clean"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
        ])

class ComponentsMenu:
    """Component filtering submenu"""
    
    def create(self) -> InlineKeyboardMarkup:
        """Create components menu keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Validator", callback_data="comp_validator"),
                InlineKeyboardButton("📦 Archiver", callback_data="comp_archiver"),
            ],
            [
                InlineKeyboardButton("🌐 P2P Client", callback_data="comp_p2p-client"),
                InlineKeyboardButton("⛓️ Sequencer", callback_data="comp_sequencer"),
            ],
            [
                InlineKeyboardButton("🔗 Prover", callback_data="comp_prover"),
                InlineKeyboardButton("📡 Node", callback_data="comp_node"),
            ],
            [
                InlineKeyboardButton("🔄 PXE Client", callback_data="comp_pxe"),
                InlineKeyboardButton("🌐 World State", callback_data="comp_world_state"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="logs_menu")],
        ])

class ToolsMenu:
    """Tools and diagnostics submenu"""
    
    def create(self) -> InlineKeyboardMarkup:
        """Create tools menu keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔗 RPC Health", callback_data="rpc_check"),
                InlineKeyboardButton("🔍 Port Check", callback_data="port_check"),
            ],
            [
                InlineKeyboardButton("🏗️ Node Management", callback_data="node_management"),
                InlineKeyboardButton("📊 Monitor Control", callback_data="monitor_menu"),
            ],
            [
                InlineKeyboardButton("📋 System Info", callback_data="system_menu"),
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            ]
        ])

class SettingsMenu:
    """Settings and configuration submenu"""
    
    def create(self) -> InlineKeyboardMarkup:
        """Create settings menu keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📦 Bot Version", callback_data="bot_current_version"),
                InlineKeyboardButton("🔄 Check Bot Update", callback_data="bot_check_update"),
            ],
            [
                InlineKeyboardButton("⚙️ Bot Settings", callback_data="bot_settings"),
                InlineKeyboardButton("📊 Statistics", callback_data="bot_stats"),
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data="main_menu")
            ]
        ])

class MonitorMenu:
    """Monitoring control submenu"""
    
    def __init__(self, monitor_active: bool = False):
        self.monitor_active = monitor_active
    
    def create(self) -> InlineKeyboardMarkup:
        """Create monitor menu keyboard"""
        status_text = "🟢 Stop Monitor" if self.monitor_active else "🔴 Start Monitor"
        status_callback = "stop_monitor" if self.monitor_active else "start_monitor"
        
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Monitor Status", callback_data="monitor_status"),
                InlineKeyboardButton(status_text, callback_data=status_callback),
            ],
            [
                InlineKeyboardButton("⚙️ Custom Interval", callback_data="monitor_custom"),
                InlineKeyboardButton("🔔 Test Alert", callback_data="test_alert"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="tools_menu")]    
        ])
