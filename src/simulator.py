import random
from typing import List, Tuple
from loguru import logger
from src.queue_reactive_model import QueueReactiveModel
from src.order_book import OrderBook
from src.orders import OrderSide


class Simulator:
    def __init__(self, K: int, delta: float, theta: float, theta_reinit: float):
        self.model = QueueReactiveModel(K, delta, theta, theta_reinit)
        self.order_book = OrderBook(K, delta)
        self.time = 0.0

    def run_simulation(self, num_steps: int) -> List[dict]:
        logger.info(f'Starting simulation for {num_steps} steps...')
        results = []

        for step in range(num_steps):
            event = self._generate_next_event()
            self._process_event(event)
            self._update_order_book()

            state = self._get_current_state()
            results.append(state)

            self.time += 1.0

            if (step + 1) % 1000 == 0:
                logger.info(f'Step {step + 1} / {num_steps}: {self.time}')
        logger.info('Simulation completed.')
        return results

    def _generate_next_event(self) -> Tuple[str, OrderSide, int, int]:
        event_type = random.choices(['limit', 'market', 'cancel'], weights=[0.6, 0.2, 0.2])[0]
        side = random.choice([OrderSide.BUY, OrderSide.SELL])  # proxy: stoch proc to model?
        level = random.randint(0, self.model.K - 1)
        volume = random.randint(1,10)  # proxy: essentially too basic, maybe look at a stoch proc to model this?
        return event_type, side, level, volume

    def _process_event(self, event: Tuple[str, OrderSide, int, int]):
        event_type, side, level, volume = event
        if event_type == 'limit':
            self.model.handle_limit_order(str(side), level, volume)
        elif event_type == 'market':
            self.model.handle_market_order(str(side), level)
        elif event_type == 'cancel':
            self.model.handle_cancellation(str(side), level, volume)

    def _update_order_book(self):
        # update reference price
        new_reference_price = self.model.get_reference_price()
        self.order_book.update_reference_price(new_reference_price)

        # update queue sizes
        for side in [OrderSide.BUY, OrderSide.SELL]:
            for level in range(self.model.K):
                queue_size = self.model.get_queue_size(str(side), level)
                self.order_book.update_queue_size(side, level, queue_size - self.order_book.get_queue_size(side, level))

    def _get_current_state(self) -> dict:
        return {
            'time': self.time,
            'reference_price': self.order_book.reference_price,
            'mid_price': self.order_book.get_mid_price(),
            'spread': self.order_book.get_spread(),
            'order_book_state': self.order_book.get_order_book_state()
        }