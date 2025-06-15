#!/usr/bin/env python3
"""Validator service for managing validator operations"""

import re
import logging
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from core.utils import run_command
from config.settings import VALIDATOR_API_BASE

logger = logging.getLogger(__name__)

class ValidatorService:
    """Service for validator monitoring operations"""
    
    def __init__(self):
        self.validator_api_base = VALIDATOR_API_BASE

    async def get_validator_owner_address(self) -> Optional[str]:
        """Get validator owner address from container logs"""
        try:
            success, output = await run_command(
                'docker ps --filter ancestor=aztecprotocol/aztec:latest --format "{{.ID}}"'
            )
            if not success or not output.strip():
                logger.error("No Aztec container found")
                return None
            
            container_ids = [cid.strip() for cid in output.strip().splitlines() if cid.strip()]
            if not container_ids:
                return None
            
            container_id = container_ids[0]
            logger.debug(f"Using container ID: {container_id}")
            
            success, grep_output = await run_command(
                f'bash -c "docker logs {container_id} 2>&1 | grep -i owner | head -n 1"'
            )
            
            if not success or not grep_output.strip():
                logger.warning("No owner address found in container logs")
                return None
            
            pattern = r'with owner (0x[a-fA-F0-9]{40})'
            match = re.search(pattern, grep_output, re.IGNORECASE)
            if match:
                owner_address = match.group(1)
                logger.info(f"Found validator owner address: {owner_address}")
                return owner_address
            else:
                logger.warning("No owner address found in container logs")
                return None
        except Exception as e:
            logger.error(f"Error getting owner address: {e}")
            return None

    async def fetch_validator_data(self, validator_address: str) -> Optional[Dict[str, Any]]:
        """Fetch validator data from Aztec network API"""
        try:
            url = f"{self.validator_api_base}/{validator_address.lower()}"
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 404:
                        logger.warning(f"Validator not found: {validator_address}")
                        return None
                    else:    
                        logger.error(f"API request failed with status: {response.status}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching validator data: {e}")
            return None
        except asyncio.TimeoutError:
            logger.error("Timeout while fetching validator data")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching validator data: {e}")
            return None

    def format_validator_info(self, validator_data: Dict[str, Any]) -> str:
        """Format validator information for display"""
        try:
            index = validator_data.get("index", "Unknown")
            address = validator_data.get("address", "Unknown")
            status = validator_data.get("status", "Unknown")
            balance = validator_data.get("balance", "0.00 STK")
            slashed = validator_data.get("slashed", False)
            total_success = validator_data.get("totalAttestationsSucceeded", 0)
            total_missed = validator_data.get("totalAttestationsMissed", 0)
            total_proposed = validator_data.get("totalBlocksProposed", 0)
            total_blockmined = validator_data.get("totalBlocksMined", 0)
            total_blockmissed = validator_data.get("totalBlocksMissed", 0)
            total_epochs = validator_data.get("totalParticipatingEpochs", 0)
        
            status_icon = "🟢" if status == "Active" else "🔴" if status == "Inactive" else "🟡"
            slashed_icon = "⚠️" if slashed else "✅"    
        
            success_total = total_success + total_missed
            success_rate = (total_success / success_total * 100) if success_total > 0 else 0
            miss_rate = 100 - success_rate
        
            total_blocks = total_blockmined + total_proposed + total_blockmissed
            proposal_missrate = (total_blockmissed / total_blocks * 100) if total_blocks > 0 else 0
        
            validator_info = f"""🎯 Validator Status: {status} {status_icon}
🏷️ Index: {index}
💰 Balance: {balance}
{slashed_icon} Slashed: {'Yes' if slashed else 'No'}

📊 Attestations Performance:
• Total Attestations: {success_total}
• Successful: {total_success}
• Missed: {total_missed}
• Success Rate: {success_rate:.1f}%
• Miss Rate: {miss_rate:.1f}%

📈 Epoch and Proposal Participation:
• Total Epochs: {total_epochs}
• Blocks Proposed: {total_proposed}
• Blocks Mined: {total_blockmined}
• Blocks Missed: {total_blockmissed}
• Proposal Miss Rate: {proposal_missrate:.1f}%

🔗 Address: {address[:10]}...{address[-8:]}"""
        
            return validator_info
        except Exception as e:
            logger.error(f"Error formatting validator info: {e}")
            return f"❌ Error formatting validator data: {str(e)}"

    async def get_validator_status(self) -> Dict[str, Any]:
        """Get complete validator status"""
        result = {
            "success": False,
            "validator_found": False,
            "validator_data": None,
            "message": ""
        }
        
        try:
            validator_address = await self.get_validator_owner_address()
            if not validator_address:
                result["message"] = """❌ Validator Address Not Found
            
Could not retrieve validator owner address from container logs.

Possible causes:
• Container not running
• No validator address in logs yet
• Container logs not accessible

Try restarting the service or check container status."""
                return result
            
            validator_data = await self.fetch_validator_data(validator_address)
            
            if validator_data:
                result["success"] = True
                result["validator_found"] = True
                result["validator_data"] = validator_data
                result["message"] = self.format_validator_info(validator_data)
            else:
                result["success"] = False
                result["validator_found"] = False
                result["message"] = f"❌ Validator not found in network for address: {validator_address}"
            
            return result
        except Exception as e:
            logger.error(f"Error getting validator status: {e}")
            result["message"] = f"❌ Error checking validator status: {str(e)}"
            return result
