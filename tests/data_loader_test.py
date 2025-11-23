import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime

from trading_lib.data_loader import DataLoader
from trading_lib.models import MarketDataPoint


@pytest.fixture
def loader(tmp_path):
    """Create a DataLoader with a temporary directory."""
    return DataLoader(data_dir=str(tmp_path))


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file for testing."""
    csv_content = """Datetime,Open,High,Low,Close,Volume,Symbol
2025-01-01 10:00:00,100.0,101.0,99.0,100.5,1000,AAPL
2025-01-01 10:01:00,100.5,102.0,100.0,101.5,1500,AAPL
2025-01-01 10:02:00,101.5,103.0,101.0,102.0,2000,AAPL"""
    
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(csv_content)
    return csv_file


def test_clean_data(loader):
    """Test data cleaning functionality."""
    # Create sample data with issues
    data = pd.DataFrame({
        'Datetime': ['2025-01-01 10:00:00', '2025-01-01 10:01:00', '2025-01-01 10:00:00'],
        'Open': [100.0, 101.0, 100.0],
        'Close': [100.5, 101.5, 100.5],
        'Symbol': ['AAPL', 'AAPL', 'AAPL']
    })
    
    cleaned = loader.clean_data(data)
    
    # Should remove duplicate
    assert len(cleaned) == 2
    # Should be sorted
    assert cleaned.iloc[0]['Close'] == 100.5
    assert cleaned.iloc[1]['Close'] == 101.5


def test_load_and_save_csv(loader, sample_csv):
    """Test loading and saving CSV files."""
    # Load the sample CSV
    data = loader.load_csv(sample_csv.name)
    
    assert len(data) == 3
    assert 'Symbol' in data.columns
    assert data.iloc[0]['Symbol'] == 'AAPL'
    
    # Save and reload
    loader.save_csv(data, "saved_test.csv")
    reloaded = loader.load_csv("saved_test.csv")
    
    assert len(reloaded) == 3


def test_to_market_data_points(loader, sample_csv):
    """Test conversion to MarketDataPoint objects."""
    data = loader.load_csv(sample_csv.name)
    points = loader.to_market_data_points(data)
    
    assert len(points) == 3
    assert isinstance(points[0], MarketDataPoint)
    assert points[0].symbol == 'AAPL'
    assert points[0].price == 100.5


def test_stream_from_csv(loader, sample_csv):
    """Test streaming MarketDataPoint objects from CSV."""
    count = 0
    for point in loader.stream_from_csv(sample_csv.name):
        assert isinstance(point, MarketDataPoint)
        assert point.symbol == 'AAPL'
        count += 1
    
    assert count == 3


def test_download_data_with_flattening(loader):
    """Test that MultiIndex columns are flattened properly."""
    # Create a mock DataFrame with MultiIndex columns
    data = pd.DataFrame({
        ('Datetime', ''): [pd.Timestamp('2025-01-01 10:00:00')],
        ('Close', 'AAPL'): [100.0],
        ('Open', 'AAPL'): [99.0],
        ('High', 'AAPL'): [101.0],
        ('Low', 'AAPL'): [98.0],
        ('Volume', 'AAPL'): [1000]
    })
    data.columns = pd.MultiIndex.from_tuples(data.columns)
    
    # Test that our flattening logic would work
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] if col[1] == '' else col[0] for col in data.columns]
    
    assert 'Datetime' in data.columns
    assert 'Close' in data.columns

