#!/usr/bin/env python3
"""Node service for managing Aztec node operations"""

import os
import re
import subprocess
import time
import json
import logging
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from packaging.version import parse as parse_version
from core.utils import run_command
from config.settings import (
    NODE_DOCKER_API, MIN_NODE_VERSION, CACHE_EXPIRY,
    REMOTE_RPC, DEFAULT_LOCAL_RPC_PORT
)

logger = logging.getLogger(__name__)

class NodeService:
    """Service for node management operations"""
    
    def __init__(self):
        self.min_node_version = MIN_NODE_VERSION
        self.node_docker_api = NODE_DOCKER_API
        self.version_cache = {}
        self.cache_expiry = CACHE_EXPIRY
        self.cache = {}

    async def get_node_current_version(self) -> Optional[str]:
        """Get current node version"""
        paths = [
            "/home/ubuntu/.aztec/bin/aztec",
            "/root/.aztec/bin/aztec", 
            f"{os.path.expanduser('~')}/.aztec/bin/aztec",
            "/usr/local/bin/aztec",
            "aztec"
        ]
        
        aztec_cmd = None
        for path in paths:
            if path == "aztec":
                try:
                    subprocess.run(["which", "aztec"], check=True, capture_output=True, timeout=2)
                    aztec_cmd = "aztec"
                    break
                except:
                    continue
            elif os.path.isfile(path) and os.access(path, os.X_OK):
                aztec_cmd = path
                break    
        
        if not aztec_cmd:
            return None
        
        for flag in ["-V", "--version", "-v"]:
            try:
                result = subprocess.run(
                    [aztec_cmd, flag],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stdout + result.stderr
                match = re.search(r'(\d+\.\d+\.\d+)', output)
                if match:
                    return match.group(1)
            except:
                continue
        return None

    async def fetch_available_versions(self, use_cache: bool = True) -> List[str]:
        """Fetch available versions from Docker Hub"""
        current_time = time.time()
        if use_cache and 'versions' in self.version_cache:
            cache_time = self.version_cache.get('timestamp', 0)
            if current_time - cache_time < self.cache_expiry:
                logger.info("Using cached versions")
                return self.version_cache['versions']
        
        try:
            all_versions = []
            page = 1
            page_size = 100
            max_pages = 50
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                while page <= max_pages:
                    url = f"{self.node_docker_api}?page={page}&page_size={page_size}"
                    async with session.get(url) as response:
                        if response.status != 200:
                            logger.error(f"Docker Hub API request failed: {response.status}")
                            break
                        data = await response.json()
                        tags = data.get("results", [])
                    
                        if not tags:
                            break
                        page_versions = self._extract_valid_versions(tags)
                        all_versions.extend(page_versions)
                        if not data.get("next"):
                            break
                        page += 1
                        if len(all_versions) >= 100:
                            break
            
                all_versions.sort(key=parse_version, reverse=True)
                self.version_cache = {
                    'versions': all_versions,
                    'timestamp': current_time
                }
                logger.info(f"Found {len(all_versions)} valid versions")
                return all_versions
        except Exception as e:
            logger.error(f"Error fetching available versions: {e}")
        
        if 'versions' in self.version_cache:
            logger.info("Returning cached versions due to error")
            return self.version_cache['versions']
        return []

    def _extract_valid_versions(self, tags: List[Dict]) -> List[str]:
        """Extract valid versions from Docker tags"""
        valid_versions = []
        min_version_parsed = parse_version(self.min_node_version)
        
        for tag in tags:
            tag_name = tag.get("name", "")
            if any(keyword in tag_name.lower() for keyword in ['nightly', 'dev', 'beta', 'alpha', 'rc', 'latest']):
                continue
            if re.match(r'^\d+\.\d+\.\d+$', tag_name):
                try:
                    tag_version = parse_version(tag_name)
                    if tag_version >= min_version_parsed:
                        valid_versions.append(tag_name)
                except ValueError:
                    logger.debug(f"Error parsing version {tag_name}")
                    continue
        return valid_versions

    async def update_node_version(self, target_version: str) -> Dict[str, Any]:
        """Update node to target version"""
        result = {
            "success": False,
            "message": "",
            "old_version": None,
            "new_version": target_version,
            "command_output": ""
        }
        
        try:
            current_version = await self.get_node_current_version()
            result["old_version"] = current_version
            
            if not re.match(r'^\d+\.\d+\.\d+$', target_version):
                result["message"] = f"❌ Invalid version format: {target_version}\nExpected format: x.y.z (e.g., 0.87.8)"
                return result
            
            available_versions = await self.fetch_available_versions()
            if target_version not in available_versions:
                result["message"] = f"""❌ Version {target_version} not found
Available versions: {', '.join(available_versions[:10])}{'...' if len(available_versions) > 10 else ''}
Please select a valid version from the list."""
                return result
            
            if current_version:
                current_parsed = parse_version(current_version)
                target_parsed = parse_version(target_version)
                if target_parsed == current_parsed:
                    result["message"] = f"ℹ️ Already running version {target_version}"
                    result["success"] = True
                    return result
            
            logger.info(f"Updating node from {current_version} to {target_version}")
            update_command = f"aztec-up -v {target_version}"
            success, output = await run_command(update_command)
            result["command_output"] = output
            
            if success:
                await asyncio.sleep(10)
                new_version = await self.get_node_current_version()
                if new_version == target_version:
                    result["success"] = True
                    result["message"] = f"""✅ Node Update Successful!

📦 Updated: {current_version or 'Unknown'} → {target_version}
🔄 Command: {update_command}
⏰ Time: {time.strftime('%H:%M:%S %d/%m/%Y')}

✨ Your Aztec node has been successfully updated to version {target_version}!

🔍 Verify with: aztec -V"""
                else:
                    result["message"] = f"""⚠️ Update Command Completed but Version Mismatch

📦 Expected: {target_version}
📦 Current: {new_version or 'Unknown'}
🔄 Command: {update_command}

The update command ran successfully, but the version check shows a different result.
This might be normal if the node is still starting up.

Wait a few minutes and check again with: aztec -V"""
            else:
                result["message"] = f"""❌ Node Update Failed

🔄 Command: {update_command}
❌ Error Output:
{output[:500]}{'...' if len(output) > 500 else ''}

Common solutions:
• Check if aztec-up command is available
• Ensure sufficient disk space
• Verify network connectivity
• Check if any Aztec processes are running"""
            
            return result
        except Exception as e:
            logger.error(f"Error updating node version: {e}")
            result["message"] = f"❌ Unexpected error during update: {str(e)}"
            return result

    async def check_node_update(self) -> Dict[str, Any]:
        """Check for node updates"""
        result = {
            "success": False,
            "current_version": None,
            "latest_version": None,
            "update_available": False,
            "message": "",
            "available_versions": [],
            "newer_versions": []
        }
        
        try:
            current_version = await self.get_node_current_version()
            if not current_version:
                result["message"] = "❌ Cannot determine current node version"
                return result
            result["current_version"] = current_version       
            
            available_versions = await self.fetch_available_versions()
            if not available_versions:
                result["message"] = "❌ Cannot fetch available versions from Docker Hub"
                return result
            
            result["available_versions"] = available_versions
            result["latest_version"] = available_versions[0]
            
            current_parsed = parse_version(current_version)
            newer_versions = []
            for version in available_versions:
                if parse_version(version) > current_parsed:
                    newer_versions.append(version)
            
            result["newer_versions"] = newer_versions
            result["success"] = True
            
            if newer_versions:
                result["update_available"] = True
                result["message"] = f"""🔄 Node Update Available!

📦 Current Version: {current_version}
🆕 Latest Version: {result['latest_version']}
📊 Status: {len(newer_versions)} newer version(s) available

🔝 Recent versions: {', '.join(newer_versions[:5])}{'...' if len(newer_versions) > 5 else ''}

⚡ Quick update to latest: aztec-up -v {result['latest_version']}"""
            else:
                result["message"] = f"""✅ Node Up to Date

📦 Current Version: {current_version}
🌐 Latest Version: {result['latest_version']}
📊 Status: No update needed

Your node is running the latest stable version."""
            
            return result            
        except Exception as e:
            logger.error(f"Error checking node update: {e}")
            result["message"] = f"❌ Error checking node update: {str(e)}"
            return result

    async def get_sync_status(self, local_port=DEFAULT_LOCAL_RPC_PORT) -> dict:
        """Get node synchronization status"""
        LOCAL_RPC = f"http://localhost:{local_port}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "node_getL2Tips",
            "params": [],
        }
        
        async def fetch_block_number(session, url):
            try:
                async with session.post(url, json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "result" in data and "proven" in data["result"]:
                            return int(data["result"]["proven"]["number"])
                        else:
                            logger.warning(f"Unexpected response format from {url}: {data}")
                            return None
                    else:
                        logger.warning(f"HTTP {resp.status} from {url}")
                        return None
            except asyncio.TimeoutError:
                logger.warning(f"Timeout when connecting to {url}")
                return None
            except aiohttp.ClientError as e:
                logger.warning(f"Client error for {url}: {e}")
                return None
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Data parsing error for {url}: {e}")
                return None
            except Exception as e:
                logger.warning(f"Unexpected error for {url}: {e}")
                return None
        
        async with aiohttp.ClientSession() as session:
            local_block_number = fetch_block_number(session, LOCAL_RPC)
            remote_block_number = fetch_block_number(session, REMOTE_RPC)
            local_block, remote_block = await asyncio.gather(local_block_number, remote_block_number)
            
            if local_block is not None and remote_block is not None:
                synced = local_block == remote_block
            else:
                synced = False
            
            result = {
                "synced": synced,
                "local": local_block,
                "remote": remote_block,
                "message": f"Local block: {local_block}\nRemote block: {remote_block}",
            }
            return result

    def clear_version_cache(self):
        """Clear version cache to force refresh"""
        self.version_cache.clear()
        logger.info("Version cache cleared")
