#!/usr/bin/env python3
"""Network service for peer and RPC operations"""

import re
import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from core.utils import run_command, parse_timestamp
from config.settings import AZTEC_NETWORK_API

logger = logging.getLogger(__name__)

class NetworkService:
    """Service for network monitoring operations"""
    
    def __init__(self):
        self.aztec_network_api = AZTEC_NETWORK_API

    async def get_local_peer_id(self) -> Optional[str]:
        """Get peer ID of Aztec container from Docker logs"""
        try:
            success, output = await run_command(
                'docker ps --filter ancestor=aztecprotocol/aztec:latest --format "{{.ID}}"'
            )
            if not success or not output.strip():
                logger.error("No Aztec container found")
                return None

            container_ids = [
                cid.strip() for cid in output.strip().splitlines() if cid.strip()
            ]
            if not container_ids:
                logger.error("No container IDs found after parsing output")
                return None

            container_id = container_ids[0]
            logger.debug(f"Using container ID: {container_id}")
            
            success, grep_output = await run_command(
                f'bash -c "docker logs {container_id} 2>&1 | grep -i peerId | head -n 1"'
            )
            
            if grep_output is None or grep_output.strip() == "":
                logger.error("Container logs empty")
                return None
            
            patterns = [
                r'"peerId":"([^"]+)"',
                r'peerId.*?([a-zA-Z0-9]{30,})',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, grep_output, re.IGNORECASE)
                if matches:
                    peer_id = matches[0].strip()
                    logger.info(f"Found local peer ID: {peer_id}")
                    return peer_id
        
            logger.warning("Could not extract peer ID from grep output")
            logger.debug(f"Grep output: {grep_output}")
            return None
        except Exception as e:
            logger.error(f"Error getting local peer ID: {e}")
            return None

    async def fetch_network_peers(self) -> Optional[Dict[str, Any]]:
        """Fetch peer data from Aztec network API"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(self.aztec_network_api) as response:
                    if response.status == 200:
                        data = await response.json()
                        peers_count = len(data.get("peers", []))
                        logger.info(f"Fetched {peers_count} peers from network")
                        return data
                    else:
                        logger.error(f"API request failed with status: {response.status}")
                        response_text = await response.text()
                        logger.debug(f"Response: {response_text[:200]}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching peers: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching network peers: {e}")
            return None

    def format_peer_info(self, peer_data: Dict[str, Any]) -> str:
        """Format peer information for display"""
        try:
            peer_id = peer_data.get("id", "Unknown")
            created_at = peer_data.get("created_at", "")
            last_seen = peer_data.get("last_seen", "")
            client = peer_data.get("client", "Unknown")
            created_date = parse_timestamp(created_at)
            last_seen_date = parse_timestamp(last_seen)
            
            location_info = "Location not available"
            try:
                multi_addresses = peer_data.get("multi_addresses", [])
                if multi_addresses and isinstance(multi_addresses, list) and len(multi_addresses) > 0:
                    ip_info = multi_addresses[0].get("ip_info", [])
                    if ip_info and isinstance(ip_info, list) and len(ip_info) > 0:
                        geo_data = ip_info[0]
                        city = geo_data.get("city_name", "").strip()
                        country = geo_data.get("country_name", "").strip()
                        latitude = geo_data.get("latitude", "")
                        longitude = geo_data.get("longitude", "")
                        
                        location_parts = []
                        if city:
                            location_parts.append(city)
                        if country:
                            location_parts.append(country)
                        if location_parts:
                            location_info = ", ".join(location_parts)
                        if latitude and longitude:
                            location_info += f"\n📍 Lat: {latitude}, Lng: {longitude}"
            except Exception as e:
                logger.debug(f"Error parsing location info: {e}")
                location_info = "Location parsing error"
            
            peer_info = f"""
🌐 Peer Status: CONNECTED ✅
📍 Location: {location_info}
🆔 Peer ID: {peer_id}
🤖 Client: {client}
⏰ First seen: {created_date}
👁️ Last seen: {last_seen_date}"""
            return peer_info
        except Exception as e:
            logger.error(f"Error formatting peer info: {e}")
            return f"❌ Error formatting peer data: {str(e)}"

    async def get_peer_status(self) -> Dict[str, Any]:
        """Get comprehensive peer status information"""
        result = {
            "success": False,
            "message": "",
            "peer_found": False,
            "local_peer_id": None,
            "peer_data": None,
        }
        
        try:
            result["local_peer_id"] = await self.get_local_peer_id()

            if not result["local_peer_id"]:
                result["message"] = """❌ Could not retrieve local peer ID

Possible causes:
- Container not running
- No peerId in logs yet
- Container logs not accessible

Try restarting the service or check container status."""
                return result

            network_data = await self.fetch_network_peers()

            if not network_data:
                result["message"] = f"""⚠️ Network API Error

🆔 Local Peer ID: {result['local_peer_id'][:16]}...
❌ Could not fetch peer data from Aztec network API

This might be temporary. Your node could still be working correctly."""
                return result

            peers = network_data.get("peers", [])
            if not peers:
                result["message"] = f"""⚠️ No Network Peers Found

🆔 Local Peer ID: {result['local_peer_id'][:16]}...
📊 Network returned empty peer list

This might indicate network issues or API problems."""
                return result

            local_peer = None
            for peer in peers:
                if peer.get("id") == result["local_peer_id"]:
                    local_peer = peer
                    break

            if local_peer:
                result["success"] = True
                result["peer_found"] = True
                result["peer_data"] = local_peer
                result["message"] = self.format_peer_info(local_peer)
            else:
                result["success"] = True
                result["peer_found"] = False
                result["message"] = f"""❌ Peer Status: NOT FOUND

🆔 Local Peer ID: {result['local_peer_id'][:16]}...{result['local_peer_id'][-8:]}
⚠️ Your peer is not visible in the Aztec network
📊 Total network peers: {len(peers)}

Possible reasons:
- Node recently started (discovery takes time)
- Network connectivity issues
- Firewall blocking P2P connections
- Node not fully synchronized yet

Wait a few minutes and try again."""

            return result

        except Exception as e:
            logger.error(f"Error in get_peer_status: {e}")
            result["message"] = f"❌ Unexpected error checking peer status: {str(e)}"
            return result

    async def check_rpc_health(self, exec_rpc: str, beacon_rpc: str = None) -> Dict[str, Any]:
        """Check RPC and Beacon health"""
        result = {
            "success": False,
            "exec_rpc": exec_rpc,
            "beacon_rpc": beacon_rpc,
            "exec_status": {"healthy": False, "block_number": None, "http_code": None},
            "beacon_status": {"healthy": False, "version": None, "http_code": None, "head_slot": None},
            "blob_status": {"success_rate": 0, "total_blobs": 0, "errors": 0},
            "message": ""
        }
    
        try:
            exec_payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }
        
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                try:
                    async with session.post(exec_rpc, json=exec_payload) as response:
                        result["exec_status"]["http_code"] = response.status
                        if response.status == 200:
                            data = await response.json()
                            block_hex = data.get("result")
                            if block_hex:
                                block_number = int(block_hex, 16)
                                result["exec_status"]["healthy"] = True
                                result["exec_status"]["block_number"] = block_number
                            else:
                                result["exec_status"]["healthy"] = False
                        else:
                            result["exec_status"]["healthy"] = False
                except Exception as e:
                    logger.error(f"Error checking Exec RPC: {e}")
                    result["exec_status"]["healthy"] = False
                    result["exec_status"]["http_code"] = "unreachable"
            
                if beacon_rpc:
                    try:
                        version_url = f"{beacon_rpc}/eth/v1/node/version"
                        async with session.get(version_url) as response:
                            result["beacon_status"]["http_code"] = response.status
                            if response.status == 200:
                                data = await response.json()
                                version = data.get("data", {}).get("version")
                                if version:
                                    result["beacon_status"]["healthy"] = True
                                    result["beacon_status"]["version"] = version
                                
                                    head_url = f"{beacon_rpc}/eth/v1/beacon/headers/head"
                                    async with session.get(head_url) as head_response:
                                        if head_response.status == 200:
                                            head_data = await head_response.json()
                                            head_slot = head_data.get("data", {}).get("header", {}).get("message", {}).get("slot")
                                            if head_slot:
                                                result["beacon_status"]["head_slot"] = int(head_slot)
                                                await self._check_blob_sidecars(session, beacon_rpc, int(head_slot), result)
                                            else:
                                                result["beacon_status"]["healthy"] = False
                                        else:
                                            result["beacon_status"]["healthy"] = False
                    except Exception as e:
                        logger.error(f"Beacon RPC error: {e}")
                        result["beacon_status"]["healthy"] = False
                        result["beacon_status"]["http_code"] = "unreachable"
        
            result["message"] = self._format_rpc_health_message(result)
            result["success"] = True
        
        except Exception as e:
            logger.error(f"RPC health check error: {e}")
            result["message"] = f"❌ Error checking RPC health: {str(e)}"
        return result

    async def _check_blob_sidecars(self, session, beacon_rpc: str, head_slot: int, result: Dict):
        """Check blob sidecars"""
        total_slots = 10
        slots_with_blobs = 0
        total_blobs = 0
        errors = 0
        
        for i in range(total_slots):
            slot = head_slot - i
            try:
                blob_url = f"{beacon_rpc}/eth/v1/beacon/blob_sidecars/{slot}"
                async with session.get(blob_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        blob_count = len(data.get("data", []))
                        if blob_count > 0:
                            slots_with_blobs += 1
                            total_blobs += blob_count
                    elif response.status == 404:
                        pass
                    else:
                        errors += 1
            except Exception:
                errors += 1
        
        success_rate = (slots_with_blobs / total_slots) * 100 if total_slots > 0 else 0
        result["blob_status"] = {
            "success_rate": success_rate,
            "total_blobs": total_blobs,
            "errors": errors,
            "slots_checked": total_slots,
            "slots_with_blobs": slots_with_blobs
        }

    def _format_rpc_health_message(self, result: Dict) -> str:
        """Format RPC health message"""
        exec_status = result["exec_status"]
        beacon_status = result["beacon_status"]
        blob_status = result["blob_status"]
    
        if exec_status["healthy"]:
            exec_line = f"✅ Execution RPC: Healthy (Block: {exec_status['block_number']})"
        else:
            http_code = exec_status.get("http_code", "unknown")
            exec_line = f"❌ Execution RPC: Unhealthy (HTTP: {http_code})"
    
        beacon_line = "ℹ️ Beacon RPC: Not provided"
        blob_line = ""
        blob_details = ""
    
        if result["beacon_rpc"]:
            if beacon_status["healthy"]:
                version = beacon_status.get("version", "unknown")
                beacon_line = f"✅ Beacon RPC: Healthy (Version: {version})"
                if beacon_status.get("head_slot"):
                    success_rate = blob_status["success_rate"]
                    if success_rate >= 75:
                        blob_icon = "🟢"
                        blob_status_text = "HEALTHY"
                    elif success_rate >= 25:
                        blob_icon = "🟡"
                        blob_status_text = "WARNING"
                    else:
                        blob_icon = "🔴"
                        blob_status_text = "CRITICAL"
                    blob_line = f"{blob_icon} Blob Success: {blob_status['slots_with_blobs']}/{blob_status['slots_checked']} slots ({success_rate:.1f}%) - {blob_status_text}"
                    blob_details = f"📊 Total Blobs: {blob_status['total_blobs']} | Errors: {blob_status['errors']}"
                else:
                    blob_line = "⚠️ Blob Check: Could not get head slot"
            else:
                http_code = beacon_status.get("http_code", "unknown")
                beacon_line = f"❌ Beacon RPC: Unhealthy (HTTP: {http_code})"
    
        message_parts = [
            "🔍 RPC Health Check Results",
            "",
            exec_line,
            beacon_line
        ]
    
        if blob_line:
            message_parts.extend(["", blob_line])
        if blob_details:
            message_parts.append(blob_details)
    
        message_parts.extend([
            "",
            "📋 Status Guide:",
            "• 🟢 HEALTHY: ≥75% blob success",
            "• 🟡 WARNING: 25%-75% blob success", 
            "• 🔴 CRITICAL: <25% blob success"
        ])
    
        return "\n".join(message_parts)

    async def get_public_ip(self) -> Optional[str]:
        """Get current public IP address"""
        try:
            urls = [
                "https://api.ipify.org",
                "https://ipinfo.io/ip",
                "https://checkip.amazonaws.com"
            ]
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                for url in urls:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                ip = (await response.text()).strip()
                                if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
                                    return ip
                    except Exception:
                        continue
            return None
        except Exception as e:
            logger.error(f"Error getting public IP: {e}")
            return None

    async def check_port_open(self, port: int, ip_address: str = None) -> Dict[str, Any]:
        """Check if port is open using YouGetSignal API"""
        result = {
            "success": False,
            "port": port,
            "ip_address": ip_address,
            "is_open": False,
            "message": "",
            "response_html": ""
        }
        
        try:
            if not ip_address:
                ip_address = await self.get_public_ip()
                if not ip_address:
                    result["message"] = "❌ Could not determine public IP address"
                    return result
            result["ip_address"] = ip_address

            url = "https://ports.yougetsignal.com/check-port.php"
            data = {
                "remoteAddress": ip_address,
                "portNumber": str(port)
            }
            headers = {
                "Accept": "text/javascript, text/html, application/xml, text/xml, */*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9,vi;q=0.8,zh-CN;q=0.7,zh;q=0.6",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://www.yougetsignal.com",
                "Referer": "https://www.yougetsignal.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "X-Prototype-Version": "1.6.0",
                "X-Requested-With": "XMLHttpRequest"
            }
        
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            ) as session:
                async with session.post(url, data=data, headers=headers) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        result["response_html"] = html_content
                
                        is_open = await self.parse_port_check_response(html_content, port)
                        result["is_open"] = is_open
                        result["success"] = True
                        if is_open:
                            result["message"] = f"✅ Port {port} is OPEN on {ip_address}"
                        else:
                            result["message"] = f"❌ Port {port} is CLOSED on {ip_address}"
                    else:
                        result["message"] = f"❌ API request failed with status: {response.status}"
        except aiohttp.ClientError as e:
            logger.error(f"Network error checking port {port}: {e}")
            result["message"] = f"❌ Network error: {str(e)}"
        except asyncio.TimeoutError:
            logger.error(f"Timeout checking port {port}")
            result["message"] = f"❌ Timeout while checking port {port}"
        except Exception as e:
            logger.error(f"Unexpected error checking port {port}: {e}")
            result["message"] = f"❌ Unexpected error: {str(e)}"
        return result

    async def parse_port_check_response(self, html_content: str, port: int) -> bool:
        """Parse HTML response to determine if port is open"""
        try:
            open_patterns = [
                rf'<img src="/img/flag_greengif".*?>.*?Port.*?{port}.*?is open',
                rf'Port.*?{port}.*?is open',
                r'<img src="/img/flag_greengif"',
                r'flag_greengif'
            ]
            closed_patterns = [
                rf'<img src="/img/flag_redgif".*?>.*?Port.*?{port}.*?is closed',
                rf'Port.*?{port}.*?is closed',
                r'<img src="/img/flag_redgif"',
                r'flag_redgif'
            ]
            
            html_lower = html_content.lower()
            for pattern in open_patterns:
                if re.search(pattern, html_lower, re.IGNORECASE | re.DOTALL):
                    return True
            for pattern in closed_patterns:
                if re.search(pattern, html_lower, re.IGNORECASE | re.DOTALL):
                    return False
            if "is open" in html_lower:
                return True
            if "is closed" in html_lower:
                return False            
            
            logger.warning(f"Could not parse port check response for port {port}")
            return False
        except Exception as e:
            logger.error(f"Error parsing port check response: {e}")
            return False
