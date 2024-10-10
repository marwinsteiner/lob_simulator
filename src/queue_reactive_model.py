import numpy as np
import random
from loguru import logger
from typing import List, Tuple, Dict, Optional, Union
from src.intensity_functions import create_intensity_function
from src.orders import Order, OrderType, OrderSide
from collections import defaultdict


class QueueReactiveModel:
    def __init__(self, K: int, delta: float, theta: float, theta_reinit: float):
        if not all(isinstance(x, (int, float)) for x in [K, delta, theta, theta_reinit]):
            raise ValueError("All parameters must be numeric")
        if K <= 0 or delta <= 0 or not 0 <= theta <= 1 or not 0 <= theta_reinit <= 1:
            raise ValueError("Invalid parameter values")

        self.K = K  # Number of price levels on each side
        self.delta = delta  # Tick size
        self.theta = theta  # Probability of reference price change
        self.theta_reinit = theta_reinit  # Probability of LOB state reinitialization
        self.reference_price = 0.0
        self.order_book_state: Union[np.ndarray, int] = np.zeros(2*K, dtype=int)


        self.limit_order_intensity = create_intensity_function('limit_order', base_intensity=1.0, alpha=0.5)
        self.cancellation_intensity = create_intensity_function('cancellation', mu=0.1)
        self.market_order_intensity = create_intensity_function('market_order', theta=0.05)

        logger.info(
            f"Initialized QueueReactiveModel with K={K}, delta={delta}, theta={theta}, theta_reinit={theta_reinit}")

    def initialize_order_book(self):
        self.order_book_state = np.random.randint(0, 10, size=2 * self.K)
        logger.debug(f"Initialized order book state: {self.order_book_state}")

    def update_reference_price(self):
        if random.random() < self.theta:
            if self.order_book_state[self.K - 1] == 0:  # If the best ask is empty
                self.reference_price += self.delta
                self._shift_order_book('right')
            elif self.order_book_state[self.K] == 0:  # If the best bid is empty
                self.reference_price -= self.delta
                self._shift_order_book('left')
        logger.debug(f"Updated reference price to {self.reference_price}")

    def _shift_order_book(self, direction: str):
        if direction == 'right':
            self.order_book_state[1:] = self.order_book_state[:-1]
            self.order_book_state[0] = np.random.randint(0, 10)
        elif direction == 'left':
            self.order_book_state[:-1] = self.order_book_state[1:]
            self.order_book_state[-1] = np.random.randint(0, 10)
        logger.debug(f"Shifted order book {direction}")

    def handle_limit_order(self, side: str, level: int, volume: int):
        if side not in ['bid', 'ask'] or level < 0 or level >= self.K or volume <= 0:
            raise ValueError("Invalid limit order parameters")
        index = self.K + level if side == 'bid' else self.K - 1 - level
        self.order_book_state[index] += volume
        logger.info(f"Added limit order: side={side}, level={level}, volume={volume}")

    def handle_market_order(self, side: str, volume: int):
        if side not in ['bid', 'ask'] or volume <= 0:
            raise ValueError("Invalid market order parameters")
        index = self.K if side == 'ask' else self.K - 1
        self.order_book_state[index] = max(0, self.order_book_state[index] - volume)
        logger.info(f"Executed market order: side={side}, volume={volume}")

    def handle_cancellation(self, side: str, level: int, volume: int):
        if side not in ['bid', 'ask'] or level < 0 or level >= self.K or volume <= 0:
            raise ValueError("Invalid cancellation parameters")
        index = self.K + level if side == 'bid' else self.K - 1 - level
        self.order_book_state[index] = max(0, self.order_book_state[index] - volume)
        logger.info(f"Cancelled order: side={side}, level={level}, volume={volume}")

    def get_intensity(self, event_type: str, side: str, level: int) -> float:
        queue_size = self.get_queue_size(side, level)
        if event_type == 'limit':
            return self.limit_order_intensity(queue_size)
        elif event_type == 'cancel':
            return self.cancellation_intensity(queue_size)
        elif event_type == 'market':
            return self.market_order_intensity(queue_size)
        else:
            raise ValueError(f"Unknown event type: {event_type}")

    def get_queue_size(self, side: str, level: int) -> int:
        index = self.K + level if side == 'bid' else self.K - 1 - level
        return self.order_book_state[index]

    def simulate_next_event(self) -> Tuple[str, str, int, int]:
        event_type = random.choice(['limit', 'market', 'cancel'])
        side = random.choice(['bid', 'ask'])
        level = random.randint(0, self.K - 1)
        volume = random.randint(1, 10)
        return event_type, side, level, volume

    def run_simulation(self, num_steps: int):
        for _ in range(num_steps):
            event_type, side, level, volume = self.simulate_next_event()
            if event_type == 'limit':
                self.handle_limit_order(side, level, volume)
            elif event_type == 'market':
                self.handle_market_order(side, volume)
            else:
                self.handle_cancellation(side, level, volume)
            self.update_reference_price()
        logger.info(f"Completed simulation of {num_steps} steps")

    def get_order_book_state(self) -> List[int]:
        return self.order_book_state.tolist()

    def get_reference_price(self) -> float:
        return self.reference_price
