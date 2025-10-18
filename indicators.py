
import numpy as np
import pandas as pd

## -- Momentum
def RSI(data, period = 14, col ='close'):
    delta = data[col].diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))
    return rsi

## -- Oscillators

## -- Overlap

## -- Pattern Detector

## -- Statistical

## -- Trend

def SMA(data, period = 50, col = 'close'):
    # signal = pd.Series(0, index = data.index())
    signal = data[col].rolling(window = period).mean()
    return signal

def EMA(data, period = 50, col = 'close'):
    signal = data[col].ewm(span = period, adjust = False).mean()

    #alpha = 2/(span+1)
    # adjust=True: Each value is a properly normalized weighted average of all past values.
    # adjust=False: Uses recursive updating, so earlier values fade away faster.
    return signal

def MACD(data, short =12, long = 26, signal_period = 9, col = 'close'):
    ema_short = data[col].ewm(span = short, adjust = False).mean()
    ema_long = data[col].ewm(span=long, adjust=False).mean()
    macd = ema_short - ema_long
    macd_signal = macd.ewm(span = signal_period, adjust_period = False).mean()
    macd_hist = macd - macd_signal
    
    return macd, macd_signal, macd_hist

## -- Volume
