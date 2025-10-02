"""
Data models for blockchain tracking system
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class TransactionInput(BaseModel):
    sequence: int
    prev_out: Dict[str, Any]
    script: str

class TransactionOutput(BaseModel):
    spent: bool
    tx_index: int
    type: int
    addr: Optional[str] = None
    value: int
    n: int
    script: str

class Transaction(BaseModel):
    lock_time: int
    ver: int
    size: int
    inputs: List[TransactionInput]
    time: int
    tx_index: int
    vin_sz: int
    hash: str
    vout_sz: int
    relayed_by: str
    out: List[TransactionOutput]
    
    @property
    def total_input_value(self) -> int:
        """Calculate total input value"""
        return sum(inp.prev_out.get('value', 0) for inp in self.inputs if 'value' in inp.prev_out)
    
    @property
    def total_output_value(self) -> int:
        """Calculate total output value"""
        return sum(out.value for out in self.out)
    
    @property
    def fee(self) -> int:
        """Calculate transaction fee"""
        return self.total_input_value - self.total_output_value

class Block(BaseModel):
    txIndexes: List[int]
    nTx: int
    totalBTCSent: int
    estimatedBTCSent: int
    reward: int
    size: int
    blockIndex: int
    prevBlockIndex: int
    height: int
    hash: str
    mrklRoot: str
    version: int
    time: int
    bits: int
    nonce: int

class WebSocketMessage(BaseModel):
    op: str
    x: Optional[Dict[str, Any]] = None
    addr: Optional[str] = None

class AddressSubscription(BaseModel):
    address: str
    subscribed_at: datetime
    transaction_count: int = 0
    total_received: int = 0
    total_sent: int = 0
