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
    
    def __init__ (self, start = 0, csvFile = "./EURUSD_M5.csv", window = 14):
        self.cacheArr = []
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
                self.cacheArr.append(float(line[4]))
                window -=1
                if window <= 0:
                    break
            self.cacheArr = np.array(self.cacheArr)
        except Exception as e:
            print(f"Error {e}")
    def shiftCacheOne(self):
        try:
            new_price = float(next(self.csvReader)[4])
            self.cacheArr[:-1] = self.cacheArr[1:] 
            self.cacheArr[-1] = new_price         
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
        
    deltaT = np.array(np.diff(cache.cacheArr))
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
        prevEma[0] = np.mean(cacheArr)
    ema = alpha * currentPrice + (1-alpha) * prevEma[0]
    prevEma[0] = ema
    
    if currentPrice > ema:
        return [ema, 1]
    elif currentPrice < ema:
        return [ema, -1]
    else:
        return [ema, 0]


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



cache = Cache(window=window1)
emaObj1 = EMACalc(window=window1)
emaObj2 = EMACalc(window=window1)
smaCalculator = SMACrossOver(slowWindow=window1, fastWindow=window2)
weights = (.5, 0.5)  
takeLoss = None
takeProfit = None

while True:
    RSIsignal = RSIBuyOrSell(cache,emaObj1, emaObj2, overBought=overbought, overSold=oversold)
    SMAsignal = smaCalculator.calc(cache.cacheArr)
    score = (RSIsignal * weights[0]) + (SMAsignal * weights[1]) 
    
    if score >= 0.6 and position == None:
        entryPrice = cache.cacheArr[-1] + (cache.cacheArr[-1] * 0.001)
        print(f"entered buy position at currentPrice = {entryPrice}")
        position = "buy"
        takeLoss = entryPrice - 0.005   
        takeProfit = entryPrice + 0.010  
        print(f"TP: {takeProfit:.5f}, SL: {takeLoss:.5f}")
    if position == "buy":
        current_price = cache.cacheArr[-1]
        if current_price >= takeProfit:
            pnl = current_price - entryPrice - (current_price * 0.001)
            logPnL.append(pnl)
            print(f"exited buy position at currentPrice = {current_price} (take profit)")
            position = None
        elif current_price <= takeLoss:
            pnl = current_price - entryPrice - (current_price * 0.001)
            logPnL.append(pnl)
            print(f"exited buy position at currentPrice = {current_price} (stop loss)")
            position = None    
    if score <= -0.6 and position == "buy":
        pnl = cache.cacheArr[-1] - entryPrice - (cache.cacheArr[-1] * 0.001)
        logPnL.append(pnl)
        print(f"exited buy position at currentPrice = {cache.cacheArr[-1]} (signal exit)")
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