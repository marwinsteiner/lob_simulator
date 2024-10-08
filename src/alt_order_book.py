from typing import List, Dict, Optional
from src.orders import Order, OrderType, OrderSide
from collections import defaultdict


class IndividualOrderBook:
    """
    This implementation of the OrderBook class uses individiual orders and represents an alternative approach to the
    one presented in Rosenbaum's 2015 paper.
    """
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
        state = {'bids': [], 'asks': []}

        bid_prices = sorted(self.bids.keys(), reverse=True)[:levels]
        ask_prices = sorted(self.asks.keys())[:levels]

        for price in bid_prices:
            state['bids'].append({'price': price, 'volume': self.get_volume_at_price(OrderSide.BUY, price)})
            # TODO: Implement the get_volume_at_price method.
        for price in ask_prices:
            state['asks'].append({'price': price, 'volume': self.get_volume_at_price(OrderSide.SELL, price)})
            # TODO: Implement the get_volume_at_price method.
        return state
