#!/usr/bin/env python3
"""System service for monitoring system resources and status"""

import psutil
import logging
from typing import Dict
from core.utils import run_command
from config.settings import SERVICE_NAME

logger = logging.getLogger(__name__)

class SystemService:
    """Service for system monitoring operations"""
    
    def __init__(self):
        self.service_name = SERVICE_NAME
    
    async def get_service_status(self) -> Dict:
        """Get service status"""
        success, output = await run_command(
            f"systemctl is-active {self.service_name}"
        )
        is_active = success and output == "active"

        success, output = await run_command(
            f"systemctl is-enabled {self.service_name}"
        )
        is_enabled = success and output == "enabled"

        success, status_output = await run_command(
            f"systemctl status {self.service_name} --no-pager -l"
        )
        return {
            "active": is_active,
            "enabled": is_enabled,
            "status_output": status_output if success else "Cannot get status details",
        }

    def get_system_resources(self) -> Dict:
        """Get system resource usage"""
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "cores": psutil.cpu_count(),
            },
            "memory": {
                "total": (mem := psutil.virtual_memory()).total,
                "available": mem.available,
                "percent": mem.percent,
                "used": mem.used,
            },
            "disk": {
                "total": (disk := psutil.disk_usage("/")).total,
                "free": disk.free,
                "used": disk.used,
                "percent": (disk.used / disk.total) * 100,
            },
        }
