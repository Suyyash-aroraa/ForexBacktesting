#  <backtest.py>
#  Copyright (C) 2025 Suyyash Raj Arora

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https:www.gnu.org/licenses/>.

# CSV SCHEMA = Date Time, Open, High, Low, Close, Volume
import numpy as np
import csv
import datetime as dt
import os

# Default Configuration Values
DEFAULT_RSI_OVERBOUGHT = 72
DEFAULT_RSI_OVERSOLD = 30
DEFAULT_WINDOW = 14  # Default for RSI and slow SMA
DEFAULT_FAST_WINDOW = 7  # Default for fast SMA
DEFAULT_MACD_FAST = 12
DEFAULT_MACD_SLOW = 26
DEFAULT_MACD_SIGNAL = 10
DEFAULT_BOLLINGER_PERIOD = 20
DEFAULT_BOLLINGER_STD = 2
DEFAULT_STOCHASTIC_D_PERIOD = 3
DEFAULT_ATR_PERIOD = 14
DEFAULT_SAR_ACCELERATION = 0.02
DEFAULT_SAR_MAXIMUM = 0.2
DEFAULT_SCORE_THRESHOLD = 0.2
DEFAULT_MIN_ATR = 0.0003
DEFAULT_MAX_ATR = 0.002
DEFAULT_PRICE_REVERSAL = 0.0001
DEFAULT_ENTRY_ADJUSTMENT = 0.00008
DEFAULT_TP_ATR_MULTIPLIER = 4
DEFAULT_SL_ATR_MULTIPLIER = 2
DEFAULT_VWAP_PERIOD = 20
DEFAULT_CMF_PERIOD = 20


class Cache:
    
    def __init__ (self, start = 0, csvFile = "./EURUSD_M15.csv", window = 14):
        self.cacheArr = []  # Close prices
        self.highArr = []   # High prices
        self.lowArr = []    # Low prices
        self.volumeArr = [] # Volume data
        self.start = start
        self.csvFile_handle = open(csvFile, "r")
        self.csvReader = csv.reader(self.csvFile_handle)
        for i in range (self.start):
            try: 
                next(self.csvReader)
            except StopIteration:
                print(f"Warning: File has fewer than {window} lines. Skipping all available lines.")
        try:
            for line in self.csvReader:
                self.cacheArr.append(float(line[4]))  # Close
                self.highArr.append(float(line[2]))   # High
                self.lowArr.append(float(line[3]))    # Low
                self.volumeArr.append(float(line[5])) # Volume
                window -=1
                if window <= 0:
                    break
            self.cacheArr = np.array(self.cacheArr)
            self.highArr = np.array(self.highArr)
            self.lowArr = np.array(self.lowArr)
            self.volumeArr = np.array(self.volumeArr)
        except Exception as e:
            print(f"Error {e}")
            
    def shiftCacheOne(self):
        try:
            line = next(self.csvReader)
            new_close = float(line[4])
            new_high = float(line[2])
            new_low = float(line[3])
            new_volume = float(line[5])
            
            # Shift arrays
            self.cacheArr[:-1] = self.cacheArr[1:] 
            self.cacheArr[-1] = new_close
            
            self.highArr[:-1] = self.highArr[1:]
            self.highArr[-1] = new_high
            
            self.lowArr[:-1] = self.lowArr[1:]
            self.lowArr[-1] = new_low
            
            self.volumeArr[:-1] = self.volumeArr[1:]
            self.volumeArr[-1] = new_volume
            
            self.start += 1
            return True
        except StopIteration:
            print("End of file reached — can't shift further.")
            return False
        except Exception as e:
            print(f"Error shifting cache: {e}")
            return False
            
    def __del__(self):
        # Cleanup when object is destroyed
        if hasattr(self, 'csvFile_handle'):
            self.csvFile_handle.close()

def calculateATR(cache, period=14):
    if len(cache.cacheArr) < 2:
        return 0
    high_low = cache.highArr[-period:] - cache.lowArr[-period:]
    if len(cache.cacheArr) >= period + 1:
        high_close = np.abs(cache.highArr[-period:] - cache.cacheArr[-(period+1):-1])
        low_close = np.abs(cache.lowArr[-period:] - cache.cacheArr[-(period+1):-1])
    else:
        high_close = np.abs(cache.highArr[-period:] - np.roll(cache.cacheArr[-period:], 1))
        low_close = np.abs(cache.lowArr[-period:] - np.roll(cache.cacheArr[-period:], 1))
        high_close[0] = high_low[0] 
        low_close[0] = high_low[0]
    true_ranges = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = np.mean(true_ranges)
    return atr

class EMACalc:
    def __init__(self, window):
        self.alpha = 1/(window-1)
        self.prevEMA = None
        self.window = window-1
    def ema(self, current_value):
        if self.prevEMA == None:
            self.prevEMA = current_value 
        ema = (current_value + ((self.window - 1) * self.prevEMA)) / self.window
        self.prevEMA = ema
        return ema

def RSIBuyOrSell(cache,emaBuy, emaLoss, overBought = 72, overSold = 30, window = 14):
    if len(cache.cacheArr) < 2:  
        return 0
        
    deltaT = np.array(np.diff(cache.cacheArr[-window:]))
    gains = np.array(np.where(deltaT>0, deltaT, 0))
    losses = np.array(np.where(deltaT<=0, -deltaT, 0))
    current_gain = gains[-1] if len(gains) > 0 else 0
    current_loss = losses[-1] if len(losses) > 0 else 0
    avgGain = emaBuy.ema(current_gain)
    avgLoss = emaLoss.ema(current_loss)
    
    if avgGain is None or avgLoss is None:
        return 0  

    if avgLoss == 0:
        RSI = 100 
    else:
        RS = avgGain / avgLoss
        RSI = 100 - (100 / (1 + RS))
    if RSI > overBought: return -1
    elif RSI < overSold: return 1
    elif RSI < 40: return 0.2  
    elif RSI > 60: return -0.2 
    else: return 0

class SMACrossOver:
    def __init__(self, fastWindow = 7, slowWindow = 14):
        self.fastWindow = fastWindow
        self.slowWindow = slowWindow
        self.prevSMASlow = None
        self.prevSMAFast = None
    def calc(self, cacheArr):
        smaSlow = np.mean(cacheArr[(-self.slowWindow):])
        smaFast = np.mean(cacheArr[(-self.fastWindow):])

        if self.prevSMAFast == None:
            self.prevSMAFast = smaFast
            self.prevSMASlow = smaSlow
            return 0
        else:
            if smaSlow < smaFast and self.prevSMASlow >= self.prevSMAFast:
                crossover = 1
                self.prevSMAFast = smaFast
                self.prevSMASlow = smaSlow
            elif smaSlow > smaFast and self.prevSMASlow <= self.prevSMAFast:
                crossover = -1
                self.prevSMAFast = smaFast
                self.prevSMASlow = smaSlow
            else: 
                crossover = 0
                self.prevSMAFast = smaFast
                self.prevSMASlow = smaSlow

            return crossover

def smaCheck(cacheArr):
    mean = np.mean(cacheArr)
    current = cacheArr[-1]
    if current > mean:
        return 1
    elif current < mean:
        return -1
    else: return 0

def EMACheck(cacheArr, prevEma, period=14):
    alpha = 2/(period+1)  
    currentPrice = cacheArr[-1]
    if prevEma[0] is None:  
        prevEma[0] = np.mean(cacheArr[-period:])
    ema = alpha * currentPrice + (1-alpha) * prevEma[0]
    prevEma[0] = ema
    
    if currentPrice > ema:
        return [ema, 1]
    elif currentPrice < ema:
        return [ema, -1]
    else:
        return [ema, 0]
    
class MACD:
    def __init__(self, fast=DEFAULT_MACD_FAST, slow=DEFAULT_MACD_SLOW, signal=DEFAULT_MACD_SIGNAL):
        self.fastPeriod = fast
        self.slowPeriod = slow
        self.signalPeriod = signal
        self.prevFast = [None]
        self.prevSlow = [None]
        self.prevSignal = None 
        
    def macd(self, cacheArr):
        emaFast = EMACheck(cacheArr=cacheArr, prevEma=self.prevFast, period=self.fastPeriod)
        self.prevFast[0] = emaFast[0]
        emaSlow = EMACheck(cacheArr=cacheArr, prevEma=self.prevSlow, period=self.slowPeriod)
        self.prevSlow[0] = emaSlow[0]

        macdLine = emaFast[0] - emaSlow[0]

        alpha = 2 / (self.signalPeriod + 1)
        if self.prevSignal is None:
            self.prevSignal = macdLine
        signalLine = alpha * macdLine + (1 - alpha) * self.prevSignal
        self.prevSignal = signalLine

        histogram = macdLine - signalLine

        if histogram > 0:
            return 1
        elif histogram < 0:
            return -1
        else:
            return 0
        
def liquidityIndicator(arr):
    if arr[-1] > (1.3 * np.mean(arr[:-1])):
        return True
    else: return False

def williamR(cachArr, highArr, LowArr, period):
    highestHigh = np.max(highArr[-period:])
    lowestLow = np.min(LowArr[-period:])
    close = cachArr[-1]
    william = ((highestHigh-close)/(highestHigh-lowestLow)) *-100
    if william > -20 and william <= -0:
        return -1
    elif william <= -80 and william >= -100:
        return 1
    elif william <-70 :
        return 0.2
    elif william > -30:  
        return -0.2
    else:
        return 0

def calculateADX(high_arr, low_arr, close_arr, period=14):
    if len(high_arr) < period + 1:
        return 0
    highs = high_arr[-(period+1):]
    lows = low_arr[-(period+1):]
    closes = close_arr[-(period+1):]
    
    tr_values = []
    plus_dm_values = []
    minus_dm_values = []
    
    for i in range(1, len(highs)):
        high_low = highs[i] - lows[i]
        high_close = abs(highs[i] - closes[i-1])
        low_close = abs(lows[i] - closes[i-1])
        tr = max(high_low, high_close, low_close)
        tr_values.append(tr)

        up_move = highs[i] - highs[i-1]
        down_move = lows[i-1] - lows[i]
        
        plus_dm = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0
        
        plus_dm_values.append(plus_dm)
        minus_dm_values.append(minus_dm)
    
    smoothed_tr = np.mean(tr_values)
    smoothed_plus_dm = np.mean(plus_dm_values)
    smoothed_minus_dm = np.mean(minus_dm_values)
    
    if smoothed_tr == 0:
        return 0
    
    plus_di = (smoothed_plus_dm / smoothed_tr) * 100
    minus_di = (smoothed_minus_dm / smoothed_tr) * 100
    
    if plus_di + minus_di == 0:
        return 0
    
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx  
    if adx < 20:
        return 0  # No trend
    elif adx >= 30:
        return 1 if plus_di > minus_di else -1  # Strong trend
    else:
        return 0.2 if plus_di > minus_di else -0.2  # Moderate trend\
    
class OBV:
    def __init__(self):
        self.obvArr = np.array([0])
    def calc(self, closeArr, volArr):
        if closeArr[-1] > closeArr[-2]:
            newObv = self.obvArr[-1] + volArr[-1]
        elif closeArr[-1] < closeArr[-2]:
            newObv = self.obvArr[-1] - volArr[-1]
        else:
            newObv = self.obvArr[-1]
        self.obvArr = np.append(self.obvArr, newObv)
        if len(self.obvArr) > 20:
            self.obvArr = self.obvArr[-10:]
        if len(self.obvArr) < 5:
            return 0
        else:
            smaObv = np.mean(self.obvArr[-6:-1])
            if newObv > smaObv:
                return 1
            elif newObv < smaObv:
                return -1
            else: 
                return 0
            
class CMF:
    def __init__(self):
        self.mfv = []
        self.vol = []

    def calc(self, closeArr, highArr, lowArr, volArr):
        high = highArr[-1]
        low = lowArr[-1]
        close = closeArr[-1]
        volume = volArr[-1]

        if high == low:  # Avoid division by zero
            mfm = 0
        else:
            mfm = ((2 * close) - high - low) / (high - low)

        mfvCurrent = mfm * volume

        self.mfv.append(mfvCurrent)
        self.vol.append(volume)

        if len(self.mfv) > 20:
            self.mfv = self.mfv[-20:]
            self.vol = self.vol[-20:]

        if len(self.mfv) < 20:
            return 0

        cmf = np.sum(self.mfv) / np.sum(self.vol)

        if cmf >= 0.2:
            return 1
        elif cmf >= 0.25:
            return 0.2
        elif cmf <= -0.2:
            return -1
        elif cmf <= -0.25:
            return -0.2
        else:
            return 0
        
class VWAP:
    def __init__(self):
        self.typical_price_volume = []
        self.volume = []

    def calc(self, highArr, closeArr, lowArr, volArr):
        high = highArr[-1]
        low = lowArr[-1]
        close = closeArr[-1]
        volume = volArr[-1]

        typical_price = (high + low + close) / 3
        self.typical_price_volume.append(typical_price * volume)
        self.volume.append(volume)

        # Keep only the latest 20
        if len(self.volume) > 20:
            self.typical_price_volume = self.typical_price_volume[-20:]
            self.volume = self.volume[-20:]

        if len(self.volume) < 20:
            return 0

        vwap = np.sum(self.typical_price_volume) / np.sum(self.volume)
        price_ratio = close / vwap

        if price_ratio >= 1.01:
            return 1
        elif price_ratio >= 1.002:
            return 0.2
        elif price_ratio <= 0.99:
            return -1
        elif price_ratio <= 0.998:
            return -0.2
        else:
            return 0

class ParabolicSAR:
    def __init__(self, af_step=DEFAULT_SAR_ACCELERATION, af_max=DEFAULT_SAR_MAXIMUM):
        self.af = af_step         # Acceleration factor
        self.af_step = af_step
        self.af_max = af_max
        self.ep = None            # Extreme point
        self.sar = None           # SAR value
        self.trend = None         # 'up' or 'down'

    def calc(self, highArr, lowArr):
        if len(highArr) < 2:
            return 0  # Not enough data

        high = highArr[-1]
        low = lowArr[-1]

        if self.trend is None:
            # Initialize trend based on last two candles
            if highArr[-1] > highArr[-2]:
                self.trend = 'up'
                self.ep = highArr[-1]
                self.sar = lowArr[-2]
            else:
                self.trend = 'down'
                self.ep = lowArr[-1]
                self.sar = highArr[-2]
            return 0

        # Calculate SAR
        self.sar = self.sar + self.af * (self.ep - self.sar)

        if self.trend == 'up':
            # Ensure SAR is not above last two lows
            self.sar = min(self.sar, lowArr[-2], lowArr[-1])
            if low < self.sar:
                # Trend reversal
                self.trend = 'down'
                self.sar = self.ep
                self.ep = low
                self.af = self.af_step
                return -1  # Sell signal
            else:
                if high > self.ep:
                    self.ep = high
                    self.af = min(self.af + self.af_step, self.af_max)
                return 1  # Buy signal

        elif self.trend == 'down':
            # Ensure SAR is not below last two highs
            self.sar = max(self.sar, highArr[-2], highArr[-1])
            if high > self.sar:
                # Trend reversal
                self.trend = 'up'
                self.sar = self.ep
                self.ep = high
                self.af = self.af_step
                return 1  # Buy signal
            else:
                if low < self.ep:
                    self.ep = low
                    self.af = min(self.af + self.af_step, self.af_max)
                return -1  # Sell signal

        return 0  # Neutral


position = None
entryPrice = None
logPnL = []
overbought_input = input(f"Enter RSI overbought (default {DEFAULT_RSI_OVERBOUGHT}): ")
overbought = int(overbought_input) if overbought_input.strip() else DEFAULT_RSI_OVERBOUGHT
oversold_input = input(f"Enter RSI oversold (default {DEFAULT_RSI_OVERSOLD}): ")
oversold = int(oversold_input) if oversold_input.strip() else DEFAULT_RSI_OVERSOLD
windowInput = input(f"Enter RSI window and slow SMA window (default {DEFAULT_WINDOW}): ")
window1 = int(windowInput) if windowInput.strip() else DEFAULT_WINDOW

windowInput2 = input(f"Enter fast SMA window (default {DEFAULT_FAST_WINDOW}): ")
window2 = int(windowInput2) if windowInput2.strip() else DEFAULT_FAST_WINDOW

cache = Cache(window=max(window1, DEFAULT_MACD_SLOW))
emaObj1 = EMACalc(window=window1)
emaObj2 = EMACalc(window=window1)
macd = MACD(fast=max(window2, DEFAULT_MACD_FAST), slow=max(window1, DEFAULT_MACD_SLOW))
smaCalculator = SMACrossOver(slowWindow=window1, fastWindow=window2)

obvObj = OBV()
takeLoss = None
takeProfit = None
buyAfterReversal = [False, None]
sellAfterReversal = [False, None] 
vwapObj= VWAP()
cmfObj = CMF()
sar = ParabolicSAR()

while True:
    atr = calculateATR(cache)
    RSIsignal = RSIBuyOrSell(cache,emaObj1, emaObj2, overBought=overbought, overSold=oversold, window=window1)
    SMAsignal = smaCalculator.calc(cache.cacheArr)
    macdSignal = macd.macd(cacheArr=cache.cacheArr)
    williamRSignal = williamR(cachArr=cache.cacheArr, LowArr=cache.lowArr, highArr=cache.highArr, period=window1)
    adxSignal = calculateADX(high_arr=cache.highArr, low_arr=cache.lowArr, period=window1, close_arr=cache.cacheArr)
    obvSignal = obvObj.calc(closeArr=cache.cacheArr, volArr=cache.volumeArr)
    cmfSignal = cmfObj.calc(closeArr=cache.cacheArr, highArr=cache.highArr, lowArr=cache.lowArr, volArr=cache.volumeArr)
    vwapSignal = vwapObj.calc(cache.highArr, cache.cacheArr, cache.lowArr, cache.volumeArr)
    sarSignal = sar.calc(cache.highArr, cache.lowArr)
    trendScore = ((SMAsignal) + (adxSignal) + sarSignal)
    momentumScore = (RSIsignal + macdSignal + williamRSignal)
    volumeScore = (vwapSignal+cmfSignal+ obvSignal)
    
    score = (volumeScore + momentumScore + trendScore)/9
    # print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, Williams R={williamRSignal}, ADX={adxSignal}, OBV={obvSignal} score={score}")
        
    
    if score >= DEFAULT_SCORE_THRESHOLD and position == None and atr > DEFAULT_MIN_ATR and atr < DEFAULT_MAX_ATR and liquidityIndicator(cache.volumeArr) and (RSIsignal >= DEFAULT_SCORE_THRESHOLD or williamRSignal >= DEFAULT_SCORE_THRESHOLD) and not buyAfterReversal[0]:
        buyAfterReversal = [True, cache.cacheArr[-1]]
    
    if buyAfterReversal[0] and cache.cacheArr[-1] < (buyAfterReversal[1] - DEFAULT_PRICE_REVERSAL) and score >= DEFAULT_SCORE_THRESHOLD:
        entryPrice = cache.cacheArr[-1] + DEFAULT_ENTRY_ADJUSTMENT
        print(f"entered buy position at currentPrice = {entryPrice}")
        print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, Williams R={williamRSignal}, ADX={adxSignal}, OBV={obvSignal} score={score}")
        position = "buy"
        takeLoss = entryPrice - (atr * DEFAULT_SL_ATR_MULTIPLIER)
        takeProfit = entryPrice + (atr * DEFAULT_TP_ATR_MULTIPLIER)
        buyAfterReversal = [False, None]
        print(f"TP: {takeProfit:.5f}, SL: {takeLoss:.5f}")
    elif score < 0.2:
        buyAfterReversal = [False, None]
    if score <= -0.2 and position == None and atr > 0.0003 and atr < 0.002 and liquidityIndicator(cache.volumeArr) and (RSIsignal <= -0.2 or williamRSignal <= -0.2) and not sellAfterReversal[0]:
        sellAfterReversal = [True, cache.cacheArr[-1]]
    if sellAfterReversal[0] and cache.cacheArr[-1] > (sellAfterReversal[1] + 0.0001) and score <= -0.2:
        entryPrice = cache.cacheArr[-1] - 0.00008
        print(f"entered sell position at currentPrice = {entryPrice}")
        print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, Williams R={williamRSignal}, ADX={adxSignal}, OBV={obvSignal} score={score}")
        
        position = "sell"
        takeProfit = entryPrice - (atr * 4)  # Profit target below entry for shorts
        takeLoss = entryPrice + (atr * 2)    # Stop loss above entry for shorts
        sellAfterReversal = [False, None]
        print(f"TP: {takeProfit:.5f}, SL: {takeLoss:.5f}")
    elif score > -0.2:
        sellAfterReversal = [False, None]
    if position == "buy":
        current_price = cache.cacheArr[-1]
        if current_price >= takeProfit:
            pnl = current_price - entryPrice -  0.00008
            logPnL.append(pnl)
            print(f"exited buy position at currentPrice = {current_price} (take profit)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None
        elif current_price <= takeLoss:
            pnl = current_price - entryPrice - 0.00008
            logPnL.append(pnl)
            print(f"exited buy position at currentPrice = {current_price} (stop loss)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None
    if position == "sell":
        current_price = cache.cacheArr[-1]
        if current_price <= takeProfit:  # Price going down is profit for shorts
            pnl = entryPrice - current_price - 0.00008
            logPnL.append(pnl)
            print(f"exited sell position at currentPrice = {current_price} (take profit)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None
        elif current_price >= takeLoss:  # Price going up is loss for shorts
            pnl = entryPrice - current_price -  0.00008
            logPnL.append(pnl)
            print(f"exited sell position at currentPrice = {current_price} (stop loss)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None
    if score <= -0.2:
        buyAfterReversal = [False, None]
        if position == "buy":
            pnl = cache.cacheArr[-1] - entryPrice -  0.00008
            logPnL.append(pnl)
            print(f"exited buy position at currentPrice = {cache.cacheArr[-1]} (signal exit)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None
    
    if score >= 0.2:
        sellAfterReversal = [False, None]
        if position == "sell":
            pnl = entryPrice - cache.cacheArr[-1] - 0.00008
            logPnL.append(pnl)
            print(f"exited sell position at currentPrice = {cache.cacheArr[-1]} (signal exit)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None
            
    if not cache.shiftCacheOne():
        if position == 'buy':
            pnl = cache.cacheArr[-1] - entryPrice
            logPnL.append(pnl)
            print(f"forced exited buy position at currentPrice = {cache.cacheArr[-1]}")
            position = None
        elif position == 'sell':
            pnl = entryPrice - cache.cacheArr[-1]
            logPnL.append(pnl)
            print(f"forced exited sell position at currentPrice = {cache.cacheArr[-1]}")
            position = None
        cache.csvFile_handle.close()
        break
        
totalTrades = len(logPnL)
if totalTrades == 0:
    print("No trades made.")
else:
    logPnL = np.array(logPnL)
    losses = np.where(logPnL<=0, -logPnL, 0)
    profits = np.where(logPnL>0, logPnL, 0)
    winningTrades = np.count_nonzero(profits)
    losingTrades = np.count_nonzero(losses)
    avgWin = np.mean(profits[profits > 0]) if winningTrades > 0 else 0
    avgLoss = np.mean(losses[losses > 0]) if losingTrades > 0 else 0
    winrate = float(float(winningTrades)/totalTrades * 100)

    print("\n=== BACKTEST SUMMARY ===")
    print(f"Total Trades: {totalTrades}")
    print(f"Winning Trades: {winningTrades}")
    print(f"Losing Trades: {losingTrades}")
    print(f"Average Win: {avgWin:.5f}")
    print(f"Average Loss: {avgLoss:.5f}")
    print(f"Winrate: {winrate:.2f}%")
    print(f"Net PnL assuming trading 100000units or 1lots: {(np.sum(logPnL) * 100000):.2f}")