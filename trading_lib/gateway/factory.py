"""Factory for creating trading system components from configuration."""

from trading_lib.config import GatewayConfig, Mode
from trading_lib.gateway import Gateway, SimulationGateway, LiveGateway


def create_gateway(config: GatewayConfig) -> Gateway:
    """Create gateway from configuration.
    
    Args:
        config: Trading system configuration
    
    Returns:
        Gateway instance (either SimulationGateway or LiveGateway)
    """
    match config.mode:
        case Mode.SIMULATION:
            return SimulationGateway(
                csv_path=config.csv_path,
                data_dir=config.data_dir
            )
        case Mode.LIVE:
            return LiveGateway(
                api_key=config.api_key,
                api_secret=config.api_secret,
                base_url=config.base_url,
                symbols=config.symbols
            )
        case _:
            raise ValueError(f"Invalid gateway mode: {config.mode}")

