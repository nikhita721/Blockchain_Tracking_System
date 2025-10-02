"""
Main application for the Blockchain Tracking System
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Set

from database import DatabaseManager
from websocket_client import BlockchainWebSocketClient
from models import Transaction, Block
from config import MONITORED_ADDRESSES, LOG_LEVEL, LOG_FILE, BLOCKCHAIN_WS_URL, DATABASE_PATH

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BlockchainTracker:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.ws_client = BlockchainWebSocketClient(self.db_manager)
        self.is_running = False
        self.stats = {
            'transactions_processed': 0,
            'blocks_processed': 0,
            'start_time': None,
            'high_value_transactions': [],
            'recent_blocks': []
        }
        
        # Setup callbacks
        self.ws_client.add_transaction_callback(self.on_transaction)
        self.ws_client.add_block_callback(self.on_block)
    
    async def on_transaction(self, transaction: Transaction):
        """Handle new transaction events"""
        self.stats['transactions_processed'] += 1
        
        # Log high-value transactions (>1 BTC)
        if transaction.total_output_value > 100_000_000:  # 1 BTC = 100,000,000 satoshis
            high_value_tx = {
                'hash': transaction.hash,
                'value': transaction.total_output_value / 100_000_000,  # Convert to BTC
                'time': transaction.time,
                'fee': transaction.fee
            }
            self.stats['high_value_transactions'].append(high_value_tx)
            
            # Keep only last 10 high-value transactions
            if len(self.stats['high_value_transactions']) > 10:
                self.stats['high_value_transactions'].pop(0)
            
            logger.info(f"High-value transaction detected: "
                       f"{high_value_tx['value']:.2f} BTC - {transaction.hash[:16]}...")
        
        # Check if transaction involves monitored addresses
        for output in transaction.out:
            if output.addr in MONITORED_ADDRESSES:
                logger.warning(f"Transaction to monitored address {output.addr}: "
                              f"{output.value / 100_000_000:.8f} BTC")
        
        for inp in transaction.inputs:
            if inp.prev_out.get('addr') in MONITORED_ADDRESSES:
                logger.warning(f"Transaction from monitored address {inp.prev_out.get('addr')}: "
                              f"{inp.prev_out.get('value', 0) / 100_000_000:.8f} BTC")
        
        # Log stats every 100 transactions
        if self.stats['transactions_processed'] % 100 == 0:
            await self.log_statistics()
    
    async def on_block(self, block: Block):
        """Handle new block events"""
        self.stats['blocks_processed'] += 1
        
        block_info = {
            'height': block.height,
            'hash': block.hash,
            'time': block.time,
            'tx_count': block.nTx,
            'size': block.size
        }
        self.stats['recent_blocks'].append(block_info)
        
        # Keep only last 5 blocks
        if len(self.stats['recent_blocks']) > 5:
            self.stats['recent_blocks'].pop(0)
        
        logger.info(f"New block #{block.height}: {block.nTx} transactions, "
                   f"{block.size} bytes")
    
    async def log_statistics(self):
        """Log current statistics"""
        if not self.stats['start_time']:
            return
        
        runtime = datetime.now() - self.stats['start_time']
        tx_rate = self.stats['transactions_processed'] / runtime.total_seconds() * 60  # per minute
        
        logger.info(f"Statistics - Runtime: {runtime}, "
                   f"Transactions: {self.stats['transactions_processed']}, "
                   f"Blocks: {self.stats['blocks_processed']}, "
                   f"TX Rate: {tx_rate:.1f}/min")
        
        # Get database statistics
        db_stats = self.db_manager.get_network_statistics()
        logger.info(f"Database - Total TX: {db_stats['transaction_count']}, "
                   f"Total Blocks: {db_stats['block_count']}, "
                   f"Latest Height: {db_stats['latest_height']}")
    
    async def monitor_addresses(self, addresses: list[str]):
        """Monitor specific Bitcoin addresses"""
        for address in addresses:
            success = await self.ws_client.subscribe_to_address(address)
            if success:
                logger.info(f"Now monitoring address: {address}")
    
    async def start(self):
        """Start the blockchain tracker"""
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        logger.info("Starting Blockchain Tracking System...")
        logger.info(f"Monitoring {len(MONITORED_ADDRESSES)} addresses: {MONITORED_ADDRESSES}")
        
        try:
            # Start WebSocket client with reconnection
            ws_task = asyncio.create_task(self.ws_client.run_with_reconnect())
            
            # Wait a bit for connection to establish
            await asyncio.sleep(2)
            
            # Subscribe to monitored addresses
            if MONITORED_ADDRESSES:
                await self.monitor_addresses(MONITORED_ADDRESSES)
            
            # Log statistics periodically
            stats_task = asyncio.create_task(self.periodic_stats())
            
            # Wait for tasks
            await asyncio.gather(ws_task, stats_task)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            await self.stop()
    
    async def periodic_stats(self):
        """Log statistics periodically"""
        while self.is_running:
            await asyncio.sleep(300)  # Every 5 minutes
            await self.log_statistics()
    
    async def stop(self):
        """Stop the blockchain tracker"""
        self.is_running = False
        logger.info("Stopping Blockchain Tracking System...")
        
        await self.ws_client.disconnect()
        
        # Log final statistics
        await self.log_statistics()
        
        logger.info("Blockchain Tracking System stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point"""
    tracker = BlockchainTracker()
    tracker.setup_signal_handlers()
    
    try:
        await tracker.start()
    except KeyboardInterrupt:
        logger.info("Application interrupted")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Example of adding addresses to monitor via environment or direct modification
    # You can modify this list or set MONITORED_ADDRESSES environment variable
    example_addresses = [
        # "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block address
        # "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",  # Example high-activity address
    ]
    
    print("Blockchain Tracking System")
    print("=" * 50)
    print(f"WebSocket URL: {BLOCKCHAIN_WS_URL}")
    print(f"Database: {DATABASE_PATH}")
    print(f"Monitored addresses: {len(MONITORED_ADDRESSES)}")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print()
    
    asyncio.run(main())
