"""Factory for creating trading system components from configuration."""

from trading_lib.config import TradingConfig, Mode
from trading_lib.gateway import Gateway, SimulationGateway, LiveGateway


def create_gateway(config: TradingConfig) -> Gateway:
    """Create gateway from configuration.
    
    Args:
        config: Trading system configuration
    
    Returns:
        Gateway instance (either SimulationGateway or LiveGateway)
    """
    gateway_config = config.gateway
    
    match gateway_config.mode:
        case Mode.SIMULATION:
            return SimulationGateway(
                csv_path=gateway_config.csv_path,
                data_dir=gateway_config.data_dir
            )
        case Mode.LIVE:
            return LiveGateway(
                api_key=gateway_config.api_key,
                api_secret=gateway_config.api_secret,
                base_url=gateway_config.base_url,
                symbols=gateway_config.symbols
            )
        case _:
            raise ValueError(f"Invalid gateway mode: {gateway_config.mode}")

