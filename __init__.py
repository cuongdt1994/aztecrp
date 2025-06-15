"""
Aztec Node Monitor Bot
A comprehensive monitoring solution for Aztec validator nodes
"""

__version__ = "0.0.5"
__author__ = "Aztec Monitor Team"
__description__ = "Telegram bot for monitoring Aztec validator nodes"

from .core.monitor import AztecMonitor
from .config.settings import Config

__all__ = ["AztecMonitor", "Config"]
