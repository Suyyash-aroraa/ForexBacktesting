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

def RSIBuyOrSell(cache,emaBuy, emaLoss, overBought = 70, overSold = 30, window = 14):
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
    elif RSI < 40: return 0.5  # Changed from RSI > 60 to RSI < 40
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
    def __init__(self, fast=12, slow=26, signal=9):
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

position = None
entryPrice = None
logPnL = []
overbought_input = input("Enter RSI overbought (default 70): ")
overbought = int(overbought_input) if overbought_input.strip() else 70
oversold_input = input("Enter RSI oversold (default 30): ")
oversold = int(oversold_input) if oversold_input.strip() else 30
windowInput = input("Enter RSI window  and slow SMA window (default 14): ")
window1 = int(windowInput) if windowInput.strip() else 14

windowInput2 = input("Enter fast SMA window  (default 7): ")
window2 = int(windowInput2) if windowInput2.strip() else 7

cache = Cache(window=max(window1, 26))
emaObj1 = EMACalc(window=window1)
emaObj2 = EMACalc(window=window1)
macd = MACD(fast=max(window2,12), slow=max(window1, 26))
smaCalculator = SMACrossOver(slowWindow=window1, fastWindow=window2)
weights = (.3, .3, .4)  #RSI, SMA, MACD
takeLoss = None
takeProfit = None
buyAfterReversal = [False, None]

while True:
    RSIsignal = RSIBuyOrSell(cache,emaObj1, emaObj2, overBought=overbought, overSold=oversold, window=window1)
    SMAsignal = smaCalculator.calc(cache.cacheArr)
    macdSignal = macd.macd(cacheArr=cache.cacheArr)
    score = (RSIsignal * weights[0]) + (SMAsignal * weights[1]) + (macdSignal * weights[2])
    atr =  calculateATR(cache=cache, period=window1)
    
    if score >= 0.6 and position == None and atr > 0.0002 and atr < 0.0008 and liquidityIndicator(cache.volumeArr) and RSIsignal >= 0.5 and not buyAfterReversal[0]:
        buyAfterReversal = [True, cache.cacheArr[-1]]
    
    if buyAfterReversal[0] and cache.cacheArr[-1] < (buyAfterReversal[1] - 0.0001) and score >= 0.4:  # Changed to require bigger pullback and lower score threshold
        entryPrice = cache.cacheArr[-1] + (cache.cacheArr[-1] * 0.0001)  # Reduced spread to realistic level
        print(f"entered buy position at currentPrice = {entryPrice}")
        print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
        position = "buy"
        takeLoss = entryPrice - (atr * 2)  # Tighter stop loss
        takeProfit = entryPrice + (atr * 3)  # More reasonable take profit
        buyAfterReversal = [False, None]  # Reset after entry
        print(f"TP: {takeProfit:.5f}, SL: {takeLoss:.5f}")
    elif score < 0.4:  # Reset if conditions deteriorate
        buyAfterReversal = [False, None]
        
    if position == "buy":
        current_price = cache.cacheArr[-1]
        if current_price >= takeProfit:
            pnl = current_price - entryPrice #- (current_price * 0.0001)
            logPnL.append(pnl)
            print(f"exited buy position at currentPrice = {current_price} (take profit)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None
        elif current_price <= takeLoss:
            pnl = current_price - entryPrice #- (current_price * 0.0001)
            logPnL.append(pnl)
            print(f"exited buy position at currentPrice = {current_price} (stop loss)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None    
            
    if score <= -0.6 :
        buyAfterReversal = [False, None]
        if position == "buy":
            pnl = cache.cacheArr[-1] - entryPrice #- (cache.cacheArr[-1] * 0.0001)
            logPnL.append(pnl)
            print(f"exited buy position at currentPrice = {cache.cacheArr[-1]} (signal exit)")
            print(f"RSI={RSIsignal}, SMA={SMAsignal}, MACD={macdSignal}, score={score}")
            position = None
            
    if not cache.shiftCacheOne():
        if position == 'buy':
            pnl = cache.cacheArr[-1] - entryPrice
            logPnL.append(pnl)
            print(f"forced exited buy position at currentPrice = {cache.cacheArr[-1]}")
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