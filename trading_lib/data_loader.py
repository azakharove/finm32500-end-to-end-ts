"""Simple data loader for downloading and preparing market data."""

import csv
import pandas as pd
import yfinance as yf
from pathlib import Path
from datetime import datetime
from typing import List
from trading_lib.models import MarketDataPoint


class DataLoader:
    """Download, clean, and load market data."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def download_data(self, ticker: str, period: str = "7d", interval: str = "1m") -> pd.DataFrame:
        """Download equity data from yfinance."""
        print(f"Downloading {ticker} data...")
        data = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
        
        # Reset index to get datetime as a column
        data.reset_index(inplace=True)
        
        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] if col[1] == '' else col[0] for col in data.columns]
        
        # Rename the datetime column (could be 'Date' or 'Datetime')
        if 'Date' in data.columns:
            data.rename(columns={'Date': 'Datetime'}, inplace=True)
        
        data['Symbol'] = ticker
        print(f"Downloaded {len(data)} rows")
        return data
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Remove missing values, duplicates, and sort by time."""
        df = data.copy()
        
        # Ensure Datetime column exists and is datetime type
        if 'Datetime' in df.columns:
            df['Datetime'] = pd.to_datetime(df['Datetime'])
        else:
            # If no Datetime column, the index might be the datetime
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'Datetime'}, inplace=True)
            df['Datetime'] = pd.to_datetime(df['Datetime'])
        
        df.dropna(inplace=True)
        df.drop_duplicates(subset=['Datetime'], inplace=True)
        df.sort_values('Datetime', inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    
    def save_csv(self, data: pd.DataFrame, filename: str):
        """Save DataFrame to CSV."""
        filepath = self.data_dir / filename
        data.to_csv(filepath, index=False)
        print(f"Saved to {filepath}")
    
    def load_csv(self, filename: str) -> pd.DataFrame:
        """Load DataFrame from CSV."""
        filepath = self.data_dir / filename
        df = pd.read_csv(filepath)
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        return df
    
    def to_market_data_points(self, data: pd.DataFrame) -> List[MarketDataPoint]:
        """Convert DataFrame to MarketDataPoint objects (loads all into memory)."""
        points = []
        for _, row in data.iterrows():
            points.append(MarketDataPoint(
                timestamp=row['Datetime'],
                symbol=row['Symbol'],
                price=row['Close']
            ))
        return points
    
    def from_csv(self, filename: str) -> List[MarketDataPoint]:
        """Load CSV and convert to MarketDataPoint list (all in memory)."""
        data = self.load_csv(filename)
        return self.to_market_data_points(data)
    
    def stream_from_csv(self, filename: str):
        """Stream MarketDataPoint objects line-by-line from CSV without loading into memory."""
        filepath = self.data_dir / filename
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield MarketDataPoint(
                    timestamp=pd.to_datetime(row['Datetime']),
                    symbol=row['Symbol'],
                    price=float(row['Close'])
                )


if __name__ == "__main__":
    loader = DataLoader()
    
    # Download and clean data
    data = loader.download_data("AAPL", period="5d", interval="1m")
    data = loader.clean_data(data)
    loader.save_csv(data, "AAPL_5d_1m.csv")
    
    print("\n" + "="*60)
    print("Option 1: Load all into memory (from_csv)")
    print("="*60)
    # Loads entire CSV into memory as list of MarketDataPoint objects
    market_points = loader.from_csv("AAPL_5d_1m.csv")
    print(f"Loaded {len(market_points)} points into memory")
    print(f"First: {market_points[0]}")
    print(f"Last: {market_points[-1]}")
    print(f"Loaded {len(market_points)} points into memory")
    
    print("\n" + "="*60)
    print("Option 2: Stream from CSV (stream_from_csv)")
    print("="*60)
    # Streams data points without loading entire file
    count = 0
    for point in loader.stream_from_csv("AAPL_5d_1m.csv"):
        if count < 3:
            print(f"{point}")
        count += 1
    print(f"Streamed {count} total points")

    

