"""Simple data loader for downloading and preparing market data."""

import pandas as pd
import yfinance as yf
from pathlib import Path
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
        """Convert DataFrame to MarketDataPoint objects for the engine."""
        points = []
        for _, row in data.iterrows():
            points.append(MarketDataPoint(
                timestamp=row['Datetime'],
                symbol=row['Symbol'],
                price=row['Close']
            ))
        return points


if __name__ == "__main__":
    # Example usage
    loader = DataLoader()
    
    # Download and clean data
    data = loader.download_data("AAPL", period="5d", interval="1m")
    data = loader.clean_data(data)
    
    # Save to CSV
    loader.save_csv(data, "AAPL_5d_1m.csv")
    
    # Load from CSV
    loaded_data = loader.load_csv("AAPL_5d_1m.csv")
    print(f"\nLoaded data shape: {loaded_data.shape}")
    print(f"Date range: {loaded_data['Datetime'].min()} to {loaded_data['Datetime'].max()}")
    
    # Convert to MarketDataPoint objects
    market_points = loader.to_market_data_points(loaded_data)
    print(f"\nCreated {len(market_points)} MarketDataPoint objects")
    print(f"First point: {market_points[0]}")
    print(f"Last point: {market_points[-1]}")

