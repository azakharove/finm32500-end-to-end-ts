"""Centralized logging configuration for the trading system."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO, console_output: bool = True) -> None:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Root logger: trading.* → logs/trading.log + console
    root_logger = logging.getLogger('trading')
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    
    general_file = logging.FileHandler(log_path / 'trading.log', mode='w')
    general_file.setLevel(log_level)
    general_file.setFormatter(detailed_formatter)
    root_logger.addHandler(general_file)
    
    if console_output:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(log_level)
        console.setFormatter(simple_formatter)
        root_logger.addHandler(console)
    
    # Order logger: trading.orders → logs/orders.log only
    order_logger = logging.getLogger('trading.orders')
    order_logger.setLevel(logging.INFO)
    order_logger.propagate = False
    order_logger.handlers.clear()
    
    order_file = logging.FileHandler(log_path / 'orders.log', mode='w')
    order_file.setLevel(logging.INFO)
    order_file.setFormatter(detailed_formatter)
    order_logger.addHandler(order_file)
    
    root_logger.info(f"Logging initialized | Level: {logging.getLevelName(log_level)}")
    root_logger.info(f"Log directory: {log_path.absolute()}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    if name:
        return logging.getLogger(f'trading.{name}')
    return logging.getLogger('trading')


def get_order_logger() -> logging.Logger:
    return logging.getLogger('trading.orders')

