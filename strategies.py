import numpy as np
import pandas as pd

def cross_over(data, fast, slow):
    fast = fast.reindex(data.index)
    slow = slow.reindex(data.index)

    position = pd.Series(0, index=data.index)
    position[fast > slow] = 1
    position[fast < slow] = -1

    signal = position.diff().fillna(0)
    signal = signal.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    return signal


def threshold(data, series, lower= None, upper = None):
    """
    Threshold-based signals.
    Buy (+1) if series < lower.
    Sell (-1) if series > upper.
    """

    signal = pd.Series(0, index = data.index)

    if lower is not None:
        signal[series < lower] = 1

    if upper is not None:
        signal[series > upper] = -1

    return signal

def breakout(data, lookback = 20, col = 'close'):
    """
    Breakout strategy using lookback highs/lows.
    Buy (+1) if close > N-day high.
    Sell (-1) if close < N-day low.
    Comparisons with NaN always return False, so no assignment happens.
    That means those rows in signals remain 0, not NaN.w

    shift(1) to avoid lookahead bias, when we are testing for today, we don't know today's close.
    """
    highs = data[col].rolling(lookback).max()
    lows = data[col].rolling(lookback).min()
    
    signal = pd.Series(0, index=data.index)
    signal[data[col] > highs.shift(1)] = 1   # Breakout above
    signal[data[col] < lows.shift(1)] = -1  # Breakdown below
    
    return signal

def band(data, kind = "bolligner", window = 20, std = 2):
    """
    Band-based trading strategies.
    
    kind = "bollinger" → Bollinger Bands
    kind = "donchian"  → Donchian Channels
    """

    signal = pd.Series(0, index = data.index)

    if kind == "bollinger":
        ma = data['close'].rolling(window).mean()
        std = data['close'].rolling(window).std()
        upper = ma + std * std
        lower = ma - std * std
        
        signal[data['close'] < lower] = 1   # Buy near lower band
        signal[data['close'] > upper] = -1  # Sell near upper band

    elif kind == "donchian":
        highs = data['close'].rolling(window).max()
        lows = data['close'].rolling(window).min()
        
        signal[data['close'] > highs.shift(1)] = 1
        signal[data['close'] < lows.shift(1)] = -1
    
    return signal

def vol(data, lookback=20):
    """
    Volume confirmation strategy.
    Buy: volume > avg_volume.
    Sell: volume > avg_volume.
    """
    avg_vol = data['volume'].rolling(lookback).mean()
    
    signals = pd.Series(0, index=data.index)
    signals[data['volume'] > avg_vol] = 1
    signals[data['volume'] > avg_vol] = -1
    
    return signals