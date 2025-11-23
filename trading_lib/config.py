"""Configuration management for the trading system."""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class Mode(str, Enum):
    SIMULATION = "simulation"
    LIVE = "live"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


@dataclass
class GatewayConfig:
    """Gateway configuration."""
    mode: Mode
    
    # Simulation mode settings
    csv_path: Optional[str] = None
    data_dir: Optional[str] = "data"
    
    # Live mode settings
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = "https://paper-api.alpaca.markets"
    symbols: Optional[list] = None


@dataclass
class TradingConfig:
    """Trading system configuration."""
    gateway: GatewayConfig


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
    
    # Parse gateway config
    gateway_data = data.get('gateway', {})
    gateway_config = GatewayConfig(
        mode=gateway_data['mode'],
        csv_path=gateway_data.get('csv_path'),
        data_dir=gateway_data.get('data_dir', 'data'),
        api_key=gateway_data.get('api_key'),
        api_secret=gateway_data.get('api_secret'),
        base_url=gateway_data.get('base_url', 'https://paper-api.alpaca.markets'),
        symbols=gateway_data.get('symbols', [])
    )
    
    return TradingConfig(gateway=gateway_config)

