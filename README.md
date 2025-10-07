# Blockchain Tracking System

A real-time Bitcoin blockchain monitoring system that connects to [Blockchain.com's WebSocket API](https://www.blockchain.com/explorer/api/api_websocket) to track live transactions, blocks, and network activity.

## Features

- **Real-time Transaction Monitoring**: Track all new Bitcoin transactions as they happen
- **Block Tracking**: Monitor new blocks being mined on the Bitcoin network
- **Address Monitoring**: Subscribe to specific Bitcoin addresses for targeted tracking
- **High-Value Transaction Detection**: Automatically detect and log transactions above 1 BTC
- **SQLite Database Storage**: Store transaction and block data locally
- **Web Dashboard**: Beautiful real-time visualization dashboard
- **Network Statistics**: Comprehensive stats about Bitcoin network activity
- **Auto-reconnection**: Robust WebSocket client with automatic reconnection

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the blockchain tracker**:
   ```bash
   python main.py
   ```

4. **Open the dashboard** (in a separate terminal):
   ```bash
   python dashboard.py
   ```
   Then visit `http://localhost:8050` in your web browser.

## Dashboard Features

The web dashboard provides real-time visualization of:

- **Network Statistics**: Total transactions, blocks, latest block height, average fees
- **High-Value Transactions**: Recent transactions over 1 BTC
- **Real-time Activity**: Activity in the last 5 minutes
- **Transaction Volume Chart**: Transactions per minute over the last hour
- **Block Analysis**: Transactions per block for recent blocks
- **Fee Distribution**: Histogram of transaction fees
- **Recent Transactions Table**: Latest transactions with sortable columns

## Configuration

You can customize the system by modifying `config.py` or setting environment variables:

### Monitoring Specific Addresses

To monitor specific Bitcoin addresses, you can:

1. **Set environment variable**:
   ```bash
   export MONITORED_ADDRESSES="address1,address2,address3"
   ```

2. **Or modify the addresses list in `main.py`**:
   ```python
   example_addresses = [
       "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",  # Genesis block address
       "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",  # Example address
   ]
   ```

### Database Configuration

- **Database file**: `blockchain_data.db` (SQLite)
- **Max stored transactions**: 10,000 (configurable in `config.py`)
- **Max stored blocks**: 1,000 (configurable in `config.py`)

### Dashboard Configuration

- **Host**: `127.0.0.1`
- **Port**: `8050`
- **Debug mode**: Enabled by default

## Project Structure

```
Blockchain_Tracking_System/
├── main.py                 # Main application entry point
├── websocket_client.py     # WebSocket client for Blockchain.com API
├── database.py            # Database management and storage
├── dashboard.py           # Web dashboard for visualization
├── models.py              # Data models and schemas
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── run.py                 # Convenience script to run both tracker and dashboard
```

## API Integration

This system uses the [Blockchain.com WebSocket API](https://www.blockchain.com/explorer/api/api_websocket) with the following subscriptions:

- **Unconfirmed Transactions**: `{"op": "unconfirmed_sub"}`
- **New Blocks**: `{"op": "blocks_sub"}`
- **Address Monitoring**: `{"op": "addr_sub", "addr": "bitcoin_address"}`

## Data Models

### Transaction Data
- Hash, index, timestamp, size, version
- Input and output details
- Fee calculation
- Total value transferred

### Block Data
- Hash, height, timestamp, size
- Transaction count
- Merkle root, nonce, difficulty bits
- Previous block reference

### Address Statistics
- Transaction count
- Total received/sent
- Last activity timestamp

## Usage Examples

### Basic Usage
```bash
# Start the tracker
python main.py

# In another terminal, start the dashboard
python dashboard.py
```

### Monitor Specific Addresses
```bash
# Set addresses to monitor
export MONITORED_ADDRESSES="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa,3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
python main.py
```

### View Logs
```bash
# Logs are written to blockchain_tracker.log
tail -f blockchain_tracker.log
```

## Database Schema

The system creates the following SQLite tables:

- `transactions`: Main transaction data
- `transaction_inputs`: Transaction input details
- `transaction_outputs`: Transaction output details
- `blocks`: Block information
- `address_subscriptions`: Monitored address data
- `statistics`: System statistics

## Security & Privacy

- **Local Storage**: All data is stored locally in SQLite database
- **No API Keys**: Uses public Blockchain.com WebSocket API
- **Read-Only**: System only reads blockchain data, never writes to the network
- **Privacy**: No personal data is collected or transmitted

## Troubleshooting

### Connection Issues
- Check internet connection
- Verify WebSocket URL is accessible
- Review logs in `blockchain_tracker.log`

### Dashboard Not Loading
- Ensure port 8050 is not in use
- Check dashboard logs for errors
- Verify database file exists

### High Memory Usage
- Adjust `MAX_STORED_TRANSACTIONS` and `MAX_STORED_BLOCKS` in `config.py`
- Database automatically cleans up old records

## Logging

The system logs to both console and `blockchain_tracker.log`:

- **INFO**: General operation status
- **WARNING**: Monitored address activity
- **ERROR**: Connection and processing errors
- **DEBUG**: Detailed message processing (when debug enabled)

## Contributing

This is a complete, self-contained blockchain tracking system. You can extend it by:

- Adding more cryptocurrencies
- Implementing additional analysis features
- Creating custom alerts and notifications
- Adding export functionality
- Integrating with other APIs

## License

This project is open source and available under the MIT License.

## Features in Detail

### Real-time Monitoring
- Connects to live Bitcoin network data
- Processes transactions as they are broadcast
- Tracks new blocks as they are mined
- Automatic reconnection on connection loss

### Smart Analysis
- Detects high-value transactions (>1 BTC)
- Calculates transaction fees automatically
- Monitors specific addresses for activity
- Tracks network statistics and trends

### Beautiful Dashboard
- Modern, responsive web interface
- Real-time charts and graphs
- Sortable transaction tables
- Color-coded high-value transactions
- Auto-refreshing every 5 seconds

### Robust Storage
- SQLite database for reliability
- Automatic data cleanup
- Indexed for fast queries
- Transaction-safe operations

---

**Ready to track the Bitcoin blockchain in real-time!**

Start with `python main.py` and open `http://localhost:8050` to see live Bitcoin transactions flowing through the network.
