"""
WebSocket client for connecting to Blockchain.com live data stream
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from typing import Set, Optional, Callable
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from config import BLOCKCHAIN_WS_URL, DATABASE_PATH
from models import Transaction, Block, WebSocketMessage, AddressSubscription
from database import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BlockchainWebSocketClient:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.websocket = None
        self.is_connected = False
        self.subscribed_addresses: Set[str] = set()
        self.transaction_callbacks: list[Callable] = []
        self.block_callbacks: list[Callable] = []
        self.reconnect_delay = 5  # seconds
        
    async def connect(self) -> bool:
        """Connect to the Blockchain.com WebSocket API"""
        try:
            logger.info(f"Connecting to {BLOCKCHAIN_WS_URL}")
            self.websocket = await websockets.connect(
                BLOCKCHAIN_WS_URL,
                ping_interval=30,
                ping_timeout=10
            )
            self.is_connected = True
            logger.info("Successfully connected to Blockchain.com WebSocket")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("Disconnected from WebSocket")
    
    async def send_message(self, message: dict):
        """Send a message to the WebSocket"""
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            logger.debug(f"Sent message: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def ping(self):
        """Send a ping message"""
        return await self.send_message({"op": "ping"})
    
    async def subscribe_unconfirmed_transactions(self):
        """Subscribe to all new unconfirmed transactions"""
        message = {"op": "unconfirmed_sub"}
        success = await self.send_message(message)
        if success:
            logger.info("Subscribed to unconfirmed transactions")
        return success
    
    async def unsubscribe_unconfirmed_transactions(self):
        """Unsubscribe from unconfirmed transactions"""
        message = {"op": "unconfirmed_unsub"}
        success = await self.send_message(message)
        if success:
            logger.info("Unsubscribed from unconfirmed transactions")
        return success
    
    async def subscribe_to_address(self, address: str):
        """Subscribe to transactions for a specific Bitcoin address"""
        message = {"op": "addr_sub", "addr": address}
        success = await self.send_message(message)
        if success:
            self.subscribed_addresses.add(address)
            # Store subscription in database
            subscription = AddressSubscription(
                address=address,
                subscribed_at=datetime.now()
            )
            await self.db_manager.store_address_subscription(subscription)
            logger.info(f"Subscribed to address: {address}")
        return success
    
    async def unsubscribe_from_address(self, address: str):
        """Unsubscribe from a Bitcoin address"""
        message = {"op": "addr_unsub", "addr": address}
        success = await self.send_message(message)
        if success:
            self.subscribed_addresses.discard(address)
            logger.info(f"Unsubscribed from address: {address}")
        return success
    
    async def subscribe_to_blocks(self):
        """Subscribe to new block notifications"""
        message = {"op": "blocks_sub"}
        success = await self.send_message(message)
        if success:
            logger.info("Subscribed to new blocks")
        return success
    
    async def unsubscribe_from_blocks(self):
        """Unsubscribe from block notifications"""
        message = {"op": "blocks_unsub"}
        success = await self.send_message(message)
        if success:
            logger.info("Unsubscribed from blocks")
        return success
    
    def add_transaction_callback(self, callback: Callable):
        """Add a callback function for new transactions"""
        self.transaction_callbacks.append(callback)
    
    def add_block_callback(self, callback: Callable):
        """Add a callback function for new blocks"""
        self.block_callbacks.append(callback)
    
    async def handle_message(self, message_data: dict):
        """Handle incoming WebSocket messages"""
        try:
            message = WebSocketMessage(**message_data)
            
            if message.op == "utx" and message.x:
                # New unconfirmed transaction
                transaction = Transaction(**message.x)
                logger.info(f"New transaction: {transaction.hash[:16]}... "
                           f"(Value: {transaction.total_output_value} satoshis)")
                
                # Store in database
                await self.db_manager.store_transaction(transaction)
                
                # Call registered callbacks
                for callback in self.transaction_callbacks:
                    try:
                        await callback(transaction)
                    except Exception as e:
                        logger.error(f"Transaction callback error: {e}")
            
            elif message.op == "block" and message.x:
                # New block
                block = Block(**message.x)
                logger.info(f"New block: {block.height} "
                           f"(Hash: {block.hash[:16]}..., Transactions: {block.nTx})")
                
                # Store in database
                await self.db_manager.store_block(block)
                
                # Call registered callbacks
                for callback in self.block_callbacks:
                    try:
                        await callback(block)
                    except Exception as e:
                        logger.error(f"Block callback error: {e}")
            
            elif message.op == "ping":
                logger.debug("Received ping")
            
            else:
                logger.debug(f"Received message: {message.op}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def listen(self):
        """Listen for incoming messages"""
        if not self.is_connected or not self.websocket:
            logger.error("WebSocket not connected")
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            self.is_connected = False
    
    async def run_with_reconnect(self):
        """Run the WebSocket client with automatic reconnection"""
        while True:
            try:
                if not self.is_connected:
                    success = await self.connect()
                    if not success:
                        logger.info(f"Retrying connection in {self.reconnect_delay} seconds...")
                        await asyncio.sleep(self.reconnect_delay)
                        continue
                
                # Subscribe to default streams
                await self.subscribe_unconfirmed_transactions()
                await self.subscribe_to_blocks()
                
                # Listen for messages
                await self.listen()
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.is_connected = False
                await asyncio.sleep(self.reconnect_delay)
    
    async def ping_latest_block(self):
        """Request the latest block for debugging"""
        return await self.send_message({"op": "ping_block"})
    
    async def ping_latest_transaction(self):
        """Request the latest transaction for debugging"""
        return await self.send_message({"op": "ping_tx"})
