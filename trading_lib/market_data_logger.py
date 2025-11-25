"""Market data logger for saving live ticks to CSV files."""

import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

from trading_lib.models import MarketDataPoint


class MarketDataLogger:
    """Logs market data ticks to CSV files organized by date and symbol."""
    
    def __init__(self, data_dir: str = "data/live"):
        """Initialize market data logger.
        
        Args:
            data_dir: Directory to store market data CSVs
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Track open file handles by symbol
        self._files = {}
        self._writers = {}
        self._current_date = {}
        
        # Track last logged tick per symbol to prevent duplicates
        # Key: symbol, Value: (timestamp, price) tuple
        self._last_logged = {}
    
    def log_tick(self, tick: MarketDataPoint):
        """Log a market data tick to appropriate CSV file.
        
        File organization: data/live/{symbol}/{symbol}_{YYYYMMDD}.csv
        
        Args:
            tick: Market data point to log
        """
        symbol = tick.symbol
        date_str = tick.timestamp.strftime('%Y%m%d')
        
        # Check for duplicates: skip if this tick is identical to the last logged one
        tick_key = (tick.timestamp, tick.price)
        if symbol in self._last_logged and self._last_logged[symbol] == tick_key:
            return  # Skip duplicate tick
        
        # Check if we need to rotate to a new file (date changed)
        if symbol in self._current_date and self._current_date[symbol] != date_str:
            self._close_file(symbol)
        
        # Open file if not already open
        if symbol not in self._files:
            self._open_file(symbol, date_str)
        
        # Write the tick
        self._writers[symbol].writerow({
            'Datetime': tick.timestamp.isoformat(),
            'Symbol': tick.symbol,
            'Close': tick.price
        })
        
        # Flush immediately for real-time logging
        self._files[symbol].flush()
        
        # Update last logged tick for this symbol
        self._last_logged[symbol] = tick_key
    
    def _open_file(self, symbol: str, date_str: str):
        """Open CSV file for symbol and date."""
        # Create symbol directory
        symbol_dir = self.data_dir / symbol
        symbol_dir.mkdir(exist_ok=True)
        
        # Create filename: AAPL_20231125.csv
        filename = f"{symbol}_{date_str}.csv"
        filepath = symbol_dir / filename
        
        # Check if file exists to determine if we need to write header
        file_exists = filepath.exists()
        
        # Open file in append mode
        file_handle = open(filepath, 'a', newline='')
        writer = csv.DictWriter(file_handle, fieldnames=['Datetime', 'Symbol', 'Close'])
        
        # Write header if new file
        if not file_exists:
            writer.writeheader()
        
        self._files[symbol] = file_handle
        self._writers[symbol] = writer
        self._current_date[symbol] = date_str
    
    def _close_file(self, symbol: str):
        """Close file handle for symbol."""
        if symbol in self._files:
            self._files[symbol].close()
            del self._files[symbol]
            del self._writers[symbol]
            del self._current_date[symbol]
            # Note: Keep _last_logged to prevent duplicates across file rotations
    
    def close_all(self):
        """Close all open file handles."""
        for symbol in list(self._files.keys()):
            self._close_file(symbol)
    
    def get_filepath(self, symbol: str, date: Optional[datetime] = None) -> Path:
        """Get filepath for a symbol and date.
        
        Args:
            symbol: Symbol name
            date: Date (default: today)
        
        Returns:
            Path to CSV file
        """
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime('%Y%m%d')
        return self.data_dir / symbol / f"{symbol}_{date_str}.csv"
    
    def __del__(self):
        """Ensure files are closed on cleanup."""
        self.close_all()

