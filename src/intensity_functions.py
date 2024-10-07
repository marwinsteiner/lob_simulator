import numpy as np
from abc import ABC, abstractmethod
from typing import Callable


class IntensityFunction(ABC):
    @abstractmethod
    def __call__(self, queue_size: int) -> float:
        pass


class ConstantIntensity(IntensityFunction):
    def __init__(self, constant: float):
        self.constant = constant

    def _call(self, queue_size: int) -> float:
        return self.constant


class LinearIntensity(IntensityFunction):
    def __init__(self, slope: float, intercept: float):
        self.slope = slope
        self.intercept = intercept

    def __call__(self, queue_size: int) -> float:
        return max(0, self.slope * queue_size + self.intercept)


class ExponentialIntensity(IntensityFunction):
    def __init__(self, scale: float, rate: float):
        self.scale = scale
        self.rate = rate

    def __call__(self, queue_size: int) -> float:
        return self.scale * np.exp(-self.rate * queue_size)


class CustomIntensity(IntensityFunction):
    def __init__(self, func: Callable[[int], float]):
        self.func = func

    def __call__(self, queue_size: int) -> float:
        return self.func(queue_size)


class LimitOrderIntensity(IntensityFunction):
    def __init__(self, base_intensity: float, alpha: float):
        self.base_intensity = base_intensity
        self.alpha = alpha

    def __call__(self, queue_size: int) -> float:
        return self.base_intensity * (queue_size + 1) ** (-self.alpha)


class CancellationIntensity(IntensityFunction):
    def __init__(self, mu: float):
        self.mu = mu

    def __call__(self, queue_size: int) -> float:
        return self.mu * queue_size


class MarketOrderIntensity(IntensityFunction):
    def __init__(self, theta: float):
        self.theta = theta

    def __call__(self, queue_size: int) -> float:
        return self.theta


def create_intensity_function(function_type: str, **kwargs) -> IntensityFunction:
    if function_type == 'constant':
        return ConstantIntensity(**kwargs)
    elif function_type == 'linear':
        return LinearIntensity(**kwargs)
    elif function_type == 'exponential':
        return ExponentialIntensity(**kwargs)
    elif function_type == 'limit_order':
        return LimitOrderIntensity(**kwargs)
    elif function_type == 'cancellation':
        return CancellationIntensity(**kwargs)
    elif function_type == 'market_order':
        return MarketOrderIntensity(**kwargs)
    elif function_type == 'custom':
        return CustomIntensity(**kwargs)
    else:
        raise ValueError(f"Unknown intensity function type: {function_type}")
