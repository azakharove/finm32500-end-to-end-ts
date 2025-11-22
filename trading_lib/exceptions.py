"""Custom exceptions for the trading system."""

class OrderError(Exception):
    """Exception raised when order validation fails."""

    def __init__(self, order=None, reason="Invalid order"):
        self.order = order
        self.reason = reason
        if order:
            super().__init__(f"Invalid order {order.symbol}: {reason}")
        else:
            super().__init__(reason)

class ExecutionError(Exception):
    """Exception raised when order execution fails."""

    def __init__(self, order=None, reason="Execution failed"):
        self.order = order
        self.reason = reason
        if order:
            super().__init__(f"Failed to execute order {order.symbol}: {reason}")
        else:
            super().__init__(reason)