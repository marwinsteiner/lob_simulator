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

    def get_queue_sizes(self, side: OrderSide, level: int) -> int:
        """Get the queue size at a specific level."""
        return self.queue_sizes.get((side, level), 0)

    def update_reference_price(self, new_price: float):
        """Update reference price and shift queues if necessary."""
        price_change = round((new_price - self.reference_price) / self.tick_size)
        if price_change != 0:
            self._shift_queues(price_change)  # TODO: implement this helper
            self.reference_price = new_price

    def get_best_bid(self):
        pass

    def get_best_ask(self):
        pass

    def get_mid_price(self):
        pass

    def get_spread(self):
        pass

    def get_order_book(self):
        pass
