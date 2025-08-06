# 🧠 Multi-Indicator Forex Trading Strategy
## Algorithmic Psychology Meets Market Reality

> **Project Status: On Pause for Knowledge Foundation Building** 🚧
> 
> *"The most successful trading algorithms don't eliminate human psychology—they systematize the right psychological responses while removing emotional interference."*

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![NumPy](https://img.shields.io/badge/NumPy-Latest-orange.svg)](https://numpy.org)
[![License](https://img.shields.io/badge/License-GPL%20v3.0-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Foundation%20Building-orange.svg)](README.md)

## 🎯 Project Overview

This repository documents my journey in developing a multi-indicator forex trading algorithm that inadvertently mirrors human psychological patterns. What started as a technical analysis project became a fascinating study in algorithmic behavior and the importance of proper quantitative foundations.

### 📊 Latest Results (EUR/USD 15min)
- **42 trades** from 100k+ candle dataset
- **45.24% win rate** (2.25 avg win vs 1.59 avg loss)
- **$623 net profit** on 1-lot position sizing
- **Reality**: Overfitted to single timeframe/pair

## 🧠 The Psychology Discovery

During backtesting, I discovered my algorithm exhibits classic human trading biases:

### Confirmation Bias by Design
```python
# Multi-indicator scoring creates an "echo chamber"
score = (volumeScore + momentumScore + trendScore) / 9
if score >= threshold and multiple_confirmations...
```

The system requires multiple indicators to align, mimicking how traders seek confirming evidence rather than objective market signals.

### Conservative Over-Optimization
- Only 42 trades from 100k candles = 0.042% activity rate
- Too selective, missing profit opportunities
- Classic overfitting to EUR/USD 15-minute data

## 🚫 Why This Project Is On Pause

### Critical Knowledge Gaps Identified
1. **Market Microstructure**: Limited understanding of regime detection
2. **Statistical Foundation**: Need deeper time series analysis skills
3. **Validation Methods**: Proper backtesting and cross-validation techniques
4. **Risk Management**: Portfolio theory and adaptive position sizing
5. **Performance Metrics**: Beyond win rate and P&L analysis

### Overfitting Red Flags
- ✅ Works on EUR/USD 15min
- ❌ Would likely fail on GBP/JPY 1H
- ❌ Parameters hardcoded for specific market conditions
- ❌ No regime detection or market adaptation

## 🛠️ Technical Implementation

### Core Architecture
```python
class Cache:           # Memory-efficient sliding window
class EMACalc:         # Wilder's EMA for RSI
class SMACrossOver:    # Trend direction detection  
class MACD:            # Momentum confirmation
class ParabolicSAR:    # Dynamic support/resistance
```

### Multi-Indicator Scoring System
```python
# Current implementation mirrors confirmation bias
trendScore = (SMAsignal + adxSignal + sarSignal)
momentumScore = (RSIsignal + macdSignal + williamRSignal) 
volumeScore = (vwapSignal + cmfSignal + obvSignal)

finalScore = (volumeScore + momentumScore + trendScore) / 9
```

### Realistic Trading Costs
- Commission: 0.8 pips per round trip
- Slippage adjustment: 0.8 pips
- ATR-based position sizing (in development)

## 📚 Learning Foundation Plan

Rather than continuing with overfitted backtests, focusing on:

### Immediate Learning Goals
- [ ] **Time Series Analysis**: Statistical methods and stationarity testing
- [ ] **C++ Optimization**: Performance improvements for large datasets  
- [ ] **Risk Management Frameworks**: Proper position sizing and drawdown control
- [ ] **Backtesting Methodologies**: Walk-forward analysis and out-of-sample testing
- [ ] **Machine Learning in Finance**: Feature engineering from technical indicators

### Advanced Topics (Future)
- [ ] **Market Regime Detection**: Bull/bear/sideways market adaptation
- [ ] **Portfolio Theory**: Multi-pair correlation and risk distribution
- [ ] **High-Frequency Considerations**: Latency and execution modeling
- [ ] **Alternative Data**: Sentiment and macro-economic integration

## 🔬 Key Insights Learned

### 1. Algorithmic Psychology
Unintentionally coded human biases into "rational" systems:
- **Good**: Risk management and confirmation requirements
- **Bad**: Over-cautiousness and confirmation bias

### 2. Market Reality vs. Theory
- Indicators work differently across timeframes and pairs
- Static parameters fail in dynamic market conditions
- Commission impact can turn profitable strategies unprofitable

### 3. Foundation Importance
- Technical analysis without statistical foundation = curve fitting
- Need to understand WHY indicators work, not just HOW
- Proper validation is more important than impressive backtest results

## 🚀 Version 2.0 Vision

### Planned Improvements
```python
# Adaptive parameter optimization
class AdaptiveStrategy:
    def detect_regime(self, market_data):
        # Trend vs range vs volatile regime detection
        pass
    
    def optimize_parameters(self, regime):
        # Dynamic parameter adjustment
        pass
    
    def validate_performance(self, out_of_sample):
        # Proper statistical validation
        pass
```

### Success Metrics (Version 2.0)
- **Cross-validation**: Performance across multiple pairs/timeframes
- **Statistical significance**: Proper hypothesis testing
- **Risk-adjusted returns**: Sharpe ratio, Sortino ratio, max drawdown
- **Regime adaptability**: Performance in different market conditions

## 📊 Current Strategy Logic

### Entry Conditions
```python
if (score >= threshold and 
    atr_filter and 
    liquidity_check and 
    momentum_confirmation and 
    not position_open):
    enter_position()
```

### Risk Management
- **Take Profit**: 4x ATR multiplier
- **Stop Loss**: 2x ATR multiplier  
- **Position Sizing**: Fixed 1-lot (needs improvement)
- **Signal Exit**: Score threshold reversal

## 🔄 Installation & Usage

### Prerequisites
```bash
pip install numpy pandas matplotlib
```

### Data Format
```csv
Date Time,Open,High,Low,Close,Volume
2024-01-01 00:00:00,1.10450,1.10480,1.10420,1.10465,1500
```

### Run Backtest
```bash
python backtest.py
# Follow interactive prompts for parameter configuration
```

### Sample Output
```
=== BACKTEST SUMMARY ===
Total Trades: 42
Winning Trades: 19  
Losing Trades: 23
Average Win: 0.00225
Average Loss: 0.00159
Winrate: 45.24%
Net PnL: $623.00
```

## 🤝 Contributing

**Current Focus**: Foundation building rather than feature additions

Interested in:
- Statistical validation methods
- Proper backtesting frameworks
- Market regime detection techniques
- Risk management improvements

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🔗 Connect

**LinkedIn**: [Suyyash Arora](https://www.linkedin.com/in/suyyash-arora/)

Interested in connecting with:
- Quantitative developers
- Financial engineers  
- Machine learning practitioners in finance
- Anyone working on proper algorithmic trading validation

---

## ⚠️ Important Disclaimers

1. **Educational Purpose**: This project is for learning and research only
2. **Past Performance**: No guarantee of future results
3. **Overfitting Risk**: Current results are likely overoptimized
4. **Trading Risk**: Substantial risk of loss in real trading
5. **Foundation Phase**: Project paused for proper knowledge building

---

*"I coded rational behavior into an irrational market, while unconsciously embedding both good AND bad human psychological patterns into the logic. Time to build proper foundations."*
