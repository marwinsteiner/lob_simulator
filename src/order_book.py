from collections import defaultdict
from typing import Dict, Optional, List
from src.orders import OrderSide


class OrderBook:
    def __init__(self, K: int, tick_size: float):
        self.K = K  # number of price levels on each side of the order book
        self.tick_size = tick_size
        self.reference_price = 0.0
        self.queue_sizes = defaultdict(int)  # store queue sizes for each price level

    def update_queue_size(self):
        """Update the queue siz at a specific price level."""
        pass

    def get_queue_sizes(self):
        pass

    def update_reference_price(self):
        pass

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

