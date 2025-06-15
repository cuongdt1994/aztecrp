#!/usr/bin/env python3
"""Utility functions for Aztec Monitor Bot"""

import re
import asyncio
import shlex
import logging
from datetime import datetime
from typing import Tuple, Dict, Any
from telegram import InlineKeyboardMarkup

logger = logging.getLogger(__name__)

def parse_timestamp(timestamp_str: str) -> str:
    """Parse timestamp string to readable format"""
    if not timestamp_str:
        return "Unknown"
    try:
        if timestamp_str.endswith("Z"):
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%d-%m-%Y - %H:%M")
    except (ValueError, TypeError) as e:
        logger.debug(f"Error parsing timestamp {timestamp_str}: {e}")
        return timestamp_str[:19] if len(timestamp_str) >= 19 else timestamp_str

def format_bytes(bytes_value: int) -> str:
    """Convert bytes to human-readable format"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.1f} PB"

def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text"""
    ansi_pattern = re.compile(
        r"\x1b\[[0-9;]*[mGKHfJABCD]|\x1b\[[0-9]+[~]|\x1b\[[0-9]*[ABCD]"
    )
    return ansi_pattern.sub("", text)

def extract_ansi_info(text: str) -> Dict:
    """Extract ANSI color and formatting information from text"""
    ansi_info = {
        "has_color": False,
        "colors": [],
        "formatting": [],
        "clean_text": text,
    }

    ansi_pattern = re.compile(r"\x1b\[([0-9;]*)([mGKHfJABCD])")
    matches = ansi_pattern.findall(text)

    if matches:
        ansi_info["has_color"] = True
        for codes, command in matches:
            if command == "m":
                code_list = [int(c) for c in codes.split(";") if c.isdigit()]
                for code in code_list:
                    if code == 0:
                        ansi_info["formatting"].append("reset")
                    elif code == 1:
                        ansi_info["formatting"].append("bold")
                    elif code == 22:
                        ansi_info["formatting"].append("normal_intensity")
                    elif 30 <= code <= 37:
                        ansi_info["colors"].append(f"fg_{code - 30}")
                    elif code == 39:
                        ansi_info["colors"].append("fg_default")
                    elif 40 <= code <= 47:
                        ansi_info["colors"].append(f"bg_{code - 40}")
                    elif code == 49:
                        ansi_info["colors"].append("bg_default")
        ansi_info["clean_text"] = strip_ansi_codes(text)

    return ansi_info

def extract_component(message: str) -> str:
    """Extract component name from log message"""
    if not message:
        return "unknown"

    component_patterns = [
        r"^([a-zA-Z0-9_-]+)\s+",
        r"^([a-zA-Z0-9_-]+):",
        r"^([a-zA-Z0-9_-]+)\.",
    ]

    for pattern in component_patterns:
        match = re.match(pattern, message.strip())
        if match:
            return match.group(1).lower()

    words = message.strip().split()
    if words and len(words[0]) > 2:
        first_word = words[0].lower()
        if re.match(r"^[a-zA-Z0-9_-]+$", first_word):
            return first_word

    return "unknown"

async def run_command(command: str) -> Tuple[bool, str]:
    """Execute shell command asynchronously"""
    try:
        logger.debug(f"Executing command: {command}")
        process = await asyncio.create_subprocess_exec(
            *shlex.split(command),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        stdout_decoded = stdout.decode(errors='replace').strip()
        stderr_decoded = stderr.decode(errors='replace').strip()
        
        full_output = stdout_decoded
        if stderr_decoded:
            full_output = f"{full_output}\n{stderr_decoded}" if full_output else stderr_decoded
        return process.returncode == 0, full_output
    except Exception as e:
        logger.error(f"❌ Command execution failed: {e}")
        return False, str(e)

def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def check_authorization(user_id: int) -> bool:
    """Check if user is authorized"""
    from config.settings import AUTHORIZED_USERS
    return user_id in AUTHORIZED_USERS
