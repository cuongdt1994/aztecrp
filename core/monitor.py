"""
Main monitoring class - extracted from the original file
"""

import asyncio
import logging
import re
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

import aiohttp
import psutil
from packaging.version import parse as parse_version

from ..config.settings import Config
from ..services.node_service import NodeService
from ..services.validator_service import ValidatorService
from ..services.network_service import NetworkService
from ..services.system_service import SystemService
from .utils import parse_timestamp

logger = logging.getLogger(__name__)

class AztecMonitor:
    """Main monitoring class for Aztec nodes"""
    
    def __init__(self):
        self.service_name = Config.SERVICE_NAME
        self.last_alert_time = {}
        self.alert_cooldown = Config.ALERT_COOLDOWN
        self.monitoring_active = False
        self.monitor_thread = None
        self.bot_version = Config.BOT_VERSION
        
        # Initialize services
        self.node_service = NodeService()
        self.validator_service = ValidatorService()
        self.network_service = NetworkService()
        self.system_service = SystemService()
        
        # Cache settings
        self.version_cache = {}
        self.cache_expiry = Config.CACHE_EXPIRY
        self.cache = {}
    
    def check_authorization(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id in Config.AUTHORIZED_USERS
    
    async def get_service_status(self) -> Dict:
        """Get service status"""
        return await self.system_service.get_service_status(self.service_name)
    
    def get_system_resources(self) -> Dict:
        """Get system resource usage"""
        return self.system_service.get_system_resources()
    
    async def get_node_current_version(self) -> Optional[str]:
        """Get current node version"""
        return await self.node_service.get_current_version()
    
    async def check_node_update(self) -> Dict[str, Any]:
        """Check for node updates"""
        return await self.node_service.check_update()
    
    async def update_node_version(self, target_version: str) -> Dict[str, Any]:
        """Update node to target version"""
        return await self.node_service.update_version(target_version)
    
    async def get_validator_status(self) -> Dict[str, Any]:
        """Get validator status"""
        return await self.validator_service.get_status()
    
    async def get_peer_status(self) -> Dict[str, Any]:
        """Get peer status"""
        return await self.network_service.get_peer_status()
    
    async def check_rpc_health(self, exec_rpc: str, beacon_rpc: str = None) -> Dict[str, Any]:
        """Check RPC health"""
        return await self.network_service.check_rpc_health(exec_rpc, beacon_rpc)
    
    async def check_port_open(self, port: int, ip_address: str = None) -> Dict[str, Any]:
        """Check if port is open"""
        return await self.network_service.check_port_open(port, ip_address)
    
    async def get_sync_status(self, local_port: int = 8080) -> Dict:
        """Get synchronization status"""
        return await self.network_service.get_sync_status(local_port)
    
    async def get_aztec_logs(self, lines: int = 50, log_level: Optional[str] = None, 
                           component: Optional[str] = None) -> List[Dict]:
        """Get Aztec container logs"""
        return await self.system_service.get_aztec_logs(lines, log_level, component)
    
    def start_monitoring(self, check_interval: int = 300):
        """Start automatic monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
            
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started automatic monitoring with {check_interval}s interval")

    def stop_monitoring(self):
        """Stop automatic monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("Stopped automatic monitoring")

    def _monitor_loop(self, check_interval: int):
        """Monitoring loop running in background thread"""
        async def monitor_task():
            while self.monitoring_active:
                try:
                    # Check miss rate
                    alert_result = await self.validator_service.check_miss_rate_alert()
                    
                    if alert_result and alert_result.get("alert"):
                        logger.warning(f"High miss rate detected: {alert_result['miss_rate']:.1f}%")
                        # Send alert logic would go here
                    
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(60)
        
        try:
            asyncio.run(monitor_task())
        except Exception as e:
            logger.error(f"Monitor loop crashed: {e}")
