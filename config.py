"""
Configuration settings for the Blockchain Tracking System
"""

import os
from dotenv import load_dotenv

load_dotenv()

# WebSocket configuration
BLOCKCHAIN_WS_URL = "wss://ws.blockchain.info/inv"

# Database configuration
DATABASE_PATH = "blockchain_data.db"

# Dashboard configuration
DASH_HOST = "127.0.0.1"
DASH_PORT = 8050
DASH_DEBUG = True

# Monitoring configuration
MAX_STORED_TRANSACTIONS = 10000
MAX_STORED_BLOCKS = 1000

# Specific addresses to monitor (can be configured via environment variables)
MONITORED_ADDRESSES = os.getenv("MONITORED_ADDRESSES", "").split(",") if os.getenv("MONITORED_ADDRESSES") else []

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "blockchain_tracker.log"
