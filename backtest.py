# CSV SCHEMA = Date Time, Open, High, Low, Close, Volume
import numpy as np
import csv
import datetime as dt
import os

class Cache:
    
    def __init__ (self, start = 0, csvFile = "./EURUSD_M15.csv", window = 14):
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
            # In-place shift (much faster)
            self.cacheArr[:-1] = self.cacheArr[1:]  # Shift left
            self.cacheArr[-1] = new_price           # Add new value
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
    def ema(self, cacheArr):
        if self.prevEMA == None:
            self.prevEMA = np.mean(cacheArr)
        ema = (cacheArr[-1] + ((self.window - 1) * self.prevEMA)) / self.window
        self.prevEMA = ema
        return ema


def RSIBuyOrSell(cache,emaBuy, emaLoss, overBought = 70, overSold = 30, window = 14):
    deltaT = np.array(np.diff(cache.cacheArr))
    gains = np.array(np.where(deltaT>0, deltaT, 0))
    losses = np.array(np.where(deltaT<=0, -deltaT, 0))
    avgGain = emaBuy.ema(gains)
    avgLoss = emaLoss.ema(losses)
    if avgGain is None or avgLoss is None:
        return 0  # No signal until EMAs are initialized

    if avgLoss == 0:
        RSI = 100  # All gains, no losses
    else:
        RS = avgGain / avgLoss
        RSI = 100 - (100 / (1 + RS))
    if RSI > overBought: return -1
    elif RSI < overSold: return 1
    else: return 0


position = None
entryPrice = None
logPnL = []

overbought_input = input("Enter RSI overbought (default 70): ")
overbought = int(overbought_input) if overbought_input.strip() else 70

oversold_input = input("Enter RSI oversold (default 30): ")
oversold = int(oversold_input) if oversold_input.strip() else 30

windowInput = input("Enter RSI window (default 14): ")
window1 = int(windowInput) if windowInput.strip() else 14


cache = Cache(window=window1)
emaObj1 = EMACalc(window=window1)
emaObj2 = EMACalc(window=window1)

while True:
    signal = RSIBuyOrSell(cache,emaObj1, emaObj2, overBought=overbought, overSold=oversold)
    if signal==1 and position == None:
        entryPrice = cache.cacheArr[-1] + (cache.cacheArr[-1] * 0.001)
        print(f"entered buy position at currentPrice = {entryPrice}")
        position = "buy"
    if signal==-1 and position == "buy":
        pnl = cache.cacheArr[-1] - entryPrice - (cache.cacheArr[-1] * 0.001)
        logPnL.append(pnl)
        print(f"exited buy position at currentPrice = {cache.cacheArr[-1]}")
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
    avgWin = np.mean(profits)
    avgLoss = np.mean(losses)
    winrate = float(float(winningTrades)/totalTrades * 100)

    print("\n=== BACKTEST SUMMARY ===")
    print(f"Total Trades: {totalTrades}")
    print(f"Winning Trades: {np.count_nonzero(profits)}")
    print(f"Losing Trades: {np.count_nonzero(losses)}")
    print(f"Average Win: {avgWin:.5f}")
    print(f"Average Loss: {avgLoss:.5f}")
    print(f"Winrate: {winrate:.2f}%")
    print(f"Net PnL assuming trading 100000units or 1lots: {(np.sum(logPnL) * 100000):.2f}")