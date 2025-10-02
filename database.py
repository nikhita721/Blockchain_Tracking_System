"""
Database management for blockchain tracking system
"""

import sqlite3
import json
import asyncio
from datetime import datetime
from typing import List, Optional
import logging

from models import Transaction, Block, AddressSubscription
from config import DATABASE_PATH, MAX_STORED_TRANSACTIONS, MAX_STORED_BLOCKS

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the database with required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE NOT NULL,
                    tx_index INTEGER,
                    time INTEGER,
                    size INTEGER,
                    version INTEGER,
                    lock_time INTEGER,
                    vin_sz INTEGER,
                    vout_sz INTEGER,
                    relayed_by TEXT,
                    total_input_value INTEGER,
                    total_output_value INTEGER,
                    fee INTEGER,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Transaction inputs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transaction_inputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_hash TEXT,
                    sequence INTEGER,
                    prev_tx_index INTEGER,
                    prev_addr TEXT,
                    prev_value INTEGER,
                    script TEXT,
                    FOREIGN KEY (transaction_hash) REFERENCES transactions (hash)
                )
            """)
            
            # Transaction outputs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transaction_outputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_hash TEXT,
                    addr TEXT,
                    value INTEGER,
                    n INTEGER,
                    spent BOOLEAN,
                    tx_index INTEGER,
                    type INTEGER,
                    script TEXT,
                    FOREIGN KEY (transaction_hash) REFERENCES transactions (hash)
                )
            """)
            
            # Blocks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE NOT NULL,
                    height INTEGER,
                    block_index INTEGER,
                    prev_block_index INTEGER,
                    time INTEGER,
                    size INTEGER,
                    version INTEGER,
                    merkle_root TEXT,
                    nonce INTEGER,
                    bits INTEGER,
                    n_tx INTEGER,
                    total_btc_sent INTEGER,
                    estimated_btc_sent INTEGER,
                    reward INTEGER,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Address subscriptions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS address_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE NOT NULL,
                    subscribed_at TIMESTAMP,
                    transaction_count INTEGER DEFAULT 0,
                    total_received INTEGER DEFAULT 0,
                    total_sent INTEGER DEFAULT 0,
                    last_activity TIMESTAMP
                )
            """)
            
            # Statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_name TEXT UNIQUE NOT NULL,
                    stat_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_hash ON transactions (hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions (time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks (hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_blocks_height ON blocks (height)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_outputs_addr ON transaction_outputs (addr)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_inputs_addr ON transaction_inputs (prev_addr)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    async def store_transaction(self, transaction: Transaction):
        """Store a transaction in the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert main transaction record
                cursor.execute("""
                    INSERT OR IGNORE INTO transactions 
                    (hash, tx_index, time, size, version, lock_time, vin_sz, vout_sz, 
                     relayed_by, total_input_value, total_output_value, fee, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction.hash,
                    transaction.tx_index,
                    transaction.time,
                    transaction.size,
                    transaction.ver,
                    transaction.lock_time,
                    transaction.vin_sz,
                    transaction.vout_sz,
                    transaction.relayed_by,
                    transaction.total_input_value,
                    transaction.total_output_value,
                    transaction.fee,
                    json.dumps(transaction.model_dump())
                ))
                
                # Insert transaction inputs
                for inp in transaction.inputs:
                    cursor.execute("""
                        INSERT INTO transaction_inputs 
                        (transaction_hash, sequence, prev_tx_index, prev_addr, prev_value, script)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        transaction.hash,
                        inp.sequence,
                        inp.prev_out.get('tx_index'),
                        inp.prev_out.get('addr'),
                        inp.prev_out.get('value'),
                        inp.script
                    ))
                
                # Insert transaction outputs
                for out in transaction.out:
                    cursor.execute("""
                        INSERT INTO transaction_outputs 
                        (transaction_hash, addr, value, n, spent, tx_index, type, script)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        transaction.hash,
                        out.addr,
                        out.value,
                        out.n,
                        out.spent,
                        out.tx_index,
                        out.type,
                        out.script
                    ))
                
                conn.commit()
                
                # Update address statistics if we're monitoring any addresses
                await self._update_address_statistics(transaction)
                
                # Clean up old transactions if we exceed the limit
                await self._cleanup_old_transactions()
                
        except Exception as e:
            logger.error(f"Error storing transaction {transaction.hash}: {e}")
    
    async def store_block(self, block: Block):
        """Store a block in the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO blocks 
                    (hash, height, block_index, prev_block_index, time, size, version,
                     merkle_root, nonce, bits, n_tx, total_btc_sent, estimated_btc_sent, 
                     reward, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    block.hash,
                    block.height,
                    block.blockIndex,
                    block.prevBlockIndex,
                    block.time,
                    block.size,
                    block.version,
                    block.mrklRoot,
                    block.nonce,
                    block.bits,
                    block.nTx,
                    block.totalBTCSent,
                    block.estimatedBTCSent,
                    block.reward,
                    json.dumps(block.model_dump())
                ))
                
                conn.commit()
                
                # Clean up old blocks if we exceed the limit
                await self._cleanup_old_blocks()
                
        except Exception as e:
            logger.error(f"Error storing block {block.hash}: {e}")
    
    async def store_address_subscription(self, subscription: AddressSubscription):
        """Store an address subscription"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO address_subscriptions 
                    (address, subscribed_at, transaction_count, total_received, total_sent)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    subscription.address,
                    subscription.subscribed_at,
                    subscription.transaction_count,
                    subscription.total_received,
                    subscription.total_sent
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing address subscription {subscription.address}: {e}")
    
    async def _update_address_statistics(self, transaction: Transaction):
        """Update statistics for monitored addresses"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if any outputs go to monitored addresses
                for out in transaction.out:
                    if out.addr:
                        cursor.execute("""
                            UPDATE address_subscriptions 
                            SET transaction_count = transaction_count + 1,
                                total_received = total_received + ?,
                                last_activity = CURRENT_TIMESTAMP
                            WHERE address = ?
                        """, (out.value, out.addr))
                
                # Check if any inputs come from monitored addresses
                for inp in transaction.inputs:
                    if inp.prev_out.get('addr'):
                        cursor.execute("""
                            UPDATE address_subscriptions 
                            SET total_sent = total_sent + ?,
                                last_activity = CURRENT_TIMESTAMP
                            WHERE address = ?
                        """, (inp.prev_out.get('value', 0), inp.prev_out.get('addr')))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating address statistics: {e}")
    
    async def _cleanup_old_transactions(self):
        """Remove old transactions to keep database size manageable"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM transactions")
                count = cursor.fetchone()[0]
                
                if count > MAX_STORED_TRANSACTIONS:
                    # Delete oldest transactions
                    to_delete = count - MAX_STORED_TRANSACTIONS
                    cursor.execute("""
                        DELETE FROM transactions 
                        WHERE id IN (
                            SELECT id FROM transactions 
                            ORDER BY created_at ASC 
                            LIMIT ?
                        )
                    """, (to_delete,))
                    
                    conn.commit()
                    logger.info(f"Cleaned up {to_delete} old transactions")
                    
        except Exception as e:
            logger.error(f"Error cleaning up transactions: {e}")
    
    async def _cleanup_old_blocks(self):
        """Remove old blocks to keep database size manageable"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM blocks")
                count = cursor.fetchone()[0]
                
                if count > MAX_STORED_BLOCKS:
                    # Delete oldest blocks
                    to_delete = count - MAX_STORED_BLOCKS
                    cursor.execute("""
                        DELETE FROM blocks 
                        WHERE id IN (
                            SELECT id FROM blocks 
                            ORDER BY created_at ASC 
                            LIMIT ?
                        )
                    """, (to_delete,))
                    
                    conn.commit()
                    logger.info(f"Cleaned up {to_delete} old blocks")
                    
        except Exception as e:
            logger.error(f"Error cleaning up blocks: {e}")
    
    def get_recent_transactions(self, limit: int = 100) -> List[dict]:
        """Get recent transactions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT hash, time, total_output_value, fee 
                FROM transactions 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_recent_blocks(self, limit: int = 50) -> List[dict]:
        """Get recent blocks"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT hash, height, time, n_tx, size 
                FROM blocks 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_address_statistics(self, address: str) -> Optional[dict]:
        """Get statistics for a specific address"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM address_subscriptions 
                WHERE address = ?
            """, (address,))
            
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def get_network_statistics(self) -> dict:
        """Get overall network statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Transaction stats
            cursor.execute("SELECT COUNT(*), AVG(fee), SUM(total_output_value) FROM transactions")
            tx_count, avg_fee, total_volume = cursor.fetchone()
            stats['transaction_count'] = tx_count or 0
            stats['average_fee'] = avg_fee or 0
            stats['total_volume'] = total_volume or 0
            
            # Block stats
            cursor.execute("SELECT COUNT(*), MAX(height) FROM blocks")
            block_count, latest_height = cursor.fetchone()
            stats['block_count'] = block_count or 0
            stats['latest_height'] = latest_height or 0
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM transactions 
                WHERE created_at > datetime('now', '-1 hour')
            """)
            stats['transactions_last_hour'] = cursor.fetchone()[0] or 0
            
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE created_at > datetime('now', '-1 hour')
            """)
            stats['blocks_last_hour'] = cursor.fetchone()[0] or 0
            
            return stats
