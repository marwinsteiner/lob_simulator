from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    LIMIT = 'limit'
    MARKET = 'market'
    CANCEL = 'cancel'


class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'


@dataclass
class Order:
    type: OrderType
    side: OrderSide
    price: float
    volume: int
    queue_position: int = 0  # limit order position in the queue


@dataclass
class LimitOrder(Order):
    def __init__(self, side: OrderSide, price: float, volume: int):
        super().__init__(OrderType.LIMIT, side, price, volume)


@dataclass
class MarketOrder(Order):
    def __init__(self, side: OrderSide, volume: int):  # price isn't super important for market orders
        super().__init__(OrderType.MARKET, side, volume)


@dataclass
class CancelOrder(Order):
    def __init__(self, side: OrderSide, price: float, volume: int):
        super().__init__(OrderType.CANCEL, side, price, volume)