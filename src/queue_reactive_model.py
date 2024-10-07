import numpy as np
import random
from loguru import logger
from typing import List, Tuple, Dict, Optional
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
        self.order_book_state = np.zeros(2 * K, dtype=int)

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
        self.order_book_state[index] -= min(volume, self.order_book_state[index])
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


# might want to implement the following classes asp:
# class IntensityFunction:
#     def __init__(self, function_type: str):
#         self.function_type = function_type
#
#     def __call__(self, queue_size: int) -> float:
#         # Implement the intensity function based on the queue size
#         pass
#
# class LimitOrderIntensity(IntensityFunction):
#     pass
#
# class CancellationIntensity(IntensityFunction):
#     pass
#
# class MarketOrderIntensity(IntensityFunction):
#     pass

class OrderBook:
    def __init__(self, tick_size: float):
        self.tick_size = tick_size
        self.bids: Dict[float, List[Order]] = defaultdict(list)
        self.asks: Dict[float, List[Order]] = defaultdict(list)
        self.order_id_to_price: Dict[int, float] = {}

    def add_order(self, order: Order) -> None:
        if order.type != OrderType.LIMIT:
            raise ValueError(
                "Only limit orders can be added to the order book")  # market orders are filled instantly,
            # cancelations are removed instantly.

        price = round(order.price / self.tick_size) + self.tick_size
        if order.side == OrderSide.BUY:
            self.bids[price].append(order)  # if it's a buy order add it and its prcie to buy orders
        else:
            self.asks[price].append(
                order)  # if it's not a buy order it must be a sell order and add it and its price to sell orders
        self.order_id_to_price[id(order)] = price

    def cancel_order(self, order_id: int) -> Optional[Order]:
        if order_id not in self.order_id_to_price:  # we need an order ID to cancel!
            return None

        price = self.order_id_to_price[order_id]
        side = self.bids if price in self.bids else self.asks  # will be bids if the price is in bids else it must be
        # in asks

        # if we have identified the order in our list of orders, cancel it
        for i, order in enumerate(side[price]):
            if id(order) == order_id:
                del self.order_id_to_price[order_id]
                return side[price].pop(i)

        return None

    def match_market_order(self, order: Order) -> List[Order]:
        matched_orders = []
        remaining_volume = order.volume

        side = self.asks if order.side == OrderSide.BUY else self.bids
        prices = sorted(side.keys(), reverse=(order.side == OrderSide.BUY))

        for price in prices:
            while side[price] and remaining_volume > 0:
                matched_order = side[price][0]
                matched_volume = min(matched_order.volume, remaining_volume)

                matched_orders.append(Order(
                    type=OrderType.MARKET,
                    side=order.side,
                    price=price,
                    volume=matched_volume
                ))

                remaining_volume -= matched_volume
                matched_order.volume -= matched_volume

                if matched_order.volume == 0:
                    self.cancel_order(id(matched_order))

            if remaining_volume == 0:
                break

        return matched_orders

    def get_best_bid(self) -> Optional[float]:
        return max(self.bids.keys()) if self.bids else None  # if there are no orders there isn't anything to return
        # (None)

    def get_best_ask(self) -> Optional[float]:
        return min(self.asks.keys()) if self.asks else None  # if there are no orders there isn't anything to return
        # (None)

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
            return (best_ask - best_bid)
        return None

    def get_order_book_state(self, levels: int) -> Dict[str, List[Dict[str, float]]]:
        pass