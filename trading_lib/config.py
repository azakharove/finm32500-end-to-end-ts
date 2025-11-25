"""Configuration management for the trading system."""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from dotenv import load_dotenv
import os

load_dotenv()


class Mode(str, Enum):
    SIMULATION = "simulation"
    LIVE = "live"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

@dataclass
class AlpacaConfig:
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class GatewayConfig:
    """Gateway configuration."""
    mode: Mode
    
    # Simulation mode settings
    csv_path: Optional[str] = None
    data_dir: Optional[str] = "data"
    
    # Live mode settings
    alpaca: Optional[AlpacaConfig] = None
    symbols: Optional[list] = None


@dataclass
class TradingConfig:
    """Trading system configuration."""
    gateway: GatewayConfig
    strategy: Optional[dict] = None  # Strategy configuration dict
    initial_capital: float = 100000.0
    max_orders_per_minute: int = 60
    max_position_size: Optional[float] = None
    max_order_value: Optional[float] = None


def load_config(config_path: str) -> TradingConfig:
    """Load configuration from JSON file.
    
    Args:
        config_path: Path to JSON config file
    
    Returns:
        TradingConfig object
    
    Example config.json:
        {
            "gateway": {
                "mode": "simulation",
                "csv_path": "AAPL_5d_1m.csv",
                "data_dir": "data"
            }
        }
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        data = json.load(f)
    
    alpaca_key = os.getenv('ALPACA_API_KEY')
    alpaca_secret = os.getenv('ALPACA_API_SECRET')
    alpaca_base_url = os.getenv('ALPACA_BASE_URL')
    
    gateway_data = data.get('gateway', {})
    gateway_config = GatewayConfig(
        mode=gateway_data['mode'],
        csv_path=gateway_data.get('csv_path'),
        data_dir=gateway_data.get('data_dir', 'data'),
        alpaca=AlpacaConfig(
            api_key=alpaca_key,
            api_secret=alpaca_secret,
            base_url=alpaca_base_url
        ),
        symbols=gateway_data.get('symbols', [])
    )
    
    return TradingConfig(
        gateway=gateway_config,
        strategy=data.get('strategy'),
        initial_capital=data.get('initial_capital', 100000.0),
        max_orders_per_minute=data.get('max_orders_per_minute', 60),
        max_position_size=data.get('max_position_size'),
        max_order_value=data.get('max_order_value')
    )

