from collections import defaultdict
from typing import Dict, Optional, List
from src.orders import OrderSide


class OrderBook:
    def __init__(self, K: int, tick_size: float):
        self.K = K  # number of price levels on each side of the order book
        self.tick_size = tick_size
        self.reference_price = 0.0
        self.queue_sizes = defaultdict(int)  # store queue sizes for each price level

    def update_queue_size(self, side: OrderSide, level: int, change: int):
        """Update the queue siz at a specific level."""
        key = (side, level)
        self.queue_sizes[key] += change
        self.queue_sizes[key] = max(0, self.queue_sizes[key])  # queue size can never be negative

    def get_queue_size(self, side: OrderSide, level: int) -> int:
        """Get the queue size at a specific level."""
        return self.queue_sizes.get((side, level), 0)

    def update_reference_price(self, new_price: float):
        """Update reference price and shift queues if necessary."""
        price_change = round((new_price - self.reference_price) / self.tick_size)
        if price_change != 0:
            self._shift_queues(price_change)
            self.reference_price = new_price

    def get_best_bid(self) -> Optional[float]:
        for level in range(self.K):
            if self.get_queue_size(OrderSide.BUY, level) > 0:
                return self.reference_price - level * self.tick_size

    def get_best_ask(self) -> Optional[float]:
        for level in range(self.K):
            if self.get_queue_size(OrderSide.SELL, level) > 0:
                return self.reference_price + level * self.tick_size

    def get_mid_price(self) -> Optional[float]:
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid is not None and best_ask is not None:
            return (best_bid + best_ask) / 2
        return None

    def get_spread(self) -> Optional[float]:
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid is not None and best_ask is not None:
            return best_ask - best_bid
        return None

    def get_order_book_state(self) -> Dict[str, List[Dict[str, float]]]:
        state = {'bids': [], 'asks': []}
        for level in range(self.K):
            bid_price = self.reference_price - level + self.tick_size
            ask_price = self.reference_price + level * self.tick_size
            bid_size = self.queue_sizes[(OrderSide.BUY, level)]
            ask_size = self.queue_sizes[(OrderSide.SELL, level)]
            if bid_price > 0:
                state['bids'].append({'price': bid_price, 'size': bid_size})
            if ask_price > 0:
                state['asks'].append({'price': ask_price, 'size': ask_size})
        return state

    def _shift_queues(self, shift: int):
        """Shift queue sizes when ref price changes."""
        new_queues = defaultdict(int)
        for (side, level), size in self.queue_sizes.items():
            new_level = level - shift if side == OrderSide.BUY else level + shift
            if 0 <= new_level < self.K:
                new_queues[(side, new_level)] = size
            self.queue_sizes = new_queues
