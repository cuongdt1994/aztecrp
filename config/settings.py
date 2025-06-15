#!/usr/bin/env python3
"""Configuration settings for Aztec Monitor Bot"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Version information
__version__ = "0.0.5"

# Bot Configuration
BOT_TOKEN = os.getenv("AZTEC_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("AZTEC_BOT_TOKEN environment variable not set. Please set it in .env or as an environment variable.")

AUTHORIZED_USERS = [int(uid) for uid in os.getenv("AZTEC_AUTHORIZED_USERS", "").split(",") if uid]
if not AUTHORIZED_USERS:
    raise ValueError("AZTEC_AUTHORIZED_USERS environment variable not set or empty. Please specify at least one authorized user ID.")

# Service Configuration
SERVICE_NAME = os.getenv("AZTEC_SERVICE_NAME", "aztec.service")
LOG_LINES = int(os.getenv("AZTEC_LOG_LINES", 50))
LOG_FILE = os.path.join(os.path.expanduser("~"), "aztec_monitor.log")

# API URLs
BOT_REMOTE_VERSION_URL = "https://raw.githubusercontent.com/cuongdt1994/aztec-guide/refs/heads/main/version.json"
REMOTE_FILE_URL = "https://raw.githubusercontent.com/cuongdt1994/aztec-guide/refs/heads/main/aztec_monitor_bot.py"
NODE_DOCKER_API = "https://hub.docker.com/v2/repositories/aztecprotocol/aztec/tags"
AZTEC_NETWORK_API = "https://aztec.nethermind.io/api/peers?page_size=20000&latest=true"
VALIDATOR_API_BASE = "https://dashtec.xyz/api/validators"

# Monitoring Configuration
MIN_NODE_VERSION = "0.87.0"
CACHE_EXPIRY = 300  # 5 minutes
ALERT_COOLDOWN = 1800  # 30 minutes
DEFAULT_MONITOR_INTERVAL = 300  # 5 minutes

# RPC Configuration
DEFAULT_LOCAL_RPC_PORT = 8080
REMOTE_RPC = "https://aztec-rpc.cerberusnode.com"
