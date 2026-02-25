#!/usr/bin/env python3
"""
KAI - Advanced Indian Market Analyzer V3
Technical + Fundamental + Multi-timeframe
"""

import yfinance as yf
import numpy as np
from datetime import datetime

STOCKS = {
    "NIFTY_50": [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "TITAN.NS", "HCLTECH.NS",
        "KOTAKBANK.NS", "LTIM.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
        "SUNPHARMA.NS", "TATASTEEL.NS", "WIPRO.NS", "HINDUNILVR.NS", "NTPC.NS",
        "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "BPCL.NS", "ULTRACEMCO.NS",
        "GRASIM.NS", "ADANIPORTS.NS", "JSWSTEEL.NS", "ADANIENT.NS", "HDFCLIFE.NS",
        "SBILIFE.NS", "CIPLA.NS", "DRREDDY.NS", "DIVISLAB.NS", "APOLLOHOSP.NS",
        "AXISBANK.NS", "INDUSINDBK.NS", "TECHM.NS", "M&M.NS", "TATAMOTORS.NS"
    ],
    "NIFTY_BANK": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "INDUSINDBK.NS", "BANDHANBNK.NS", "AUBANK.NS", "IDFCFIRSTB.NS", "YESBANK.NS"
    ],
    "NIFTY_IT": ["INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "LTIM.NS", "TECHM.NS"],
    "NIFTY_AUTO": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
    "NIFTY_PHARMA": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "NIFTY_METAL": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "VEDL.NS", "NMDC.NS"],
    "MIDCAP": ["POLYCAB.NS", "HAVELLS.NS", "MARICO.NS", "DABUR.NS", "PIDILITIND.NS", "COROMANDEL.NS"]
}

def get_data(symbol):
    try:
        t = yf.Ticker(symbol)
        df_d = t.history(period="1y", interval="1d")
        df_w = t.history(period="2y", interval="1wk")
        info = t.info
        return df_d, df_w, info
    except:
        return None, None, None

def calc_ema(closes, period):
    if len(closes) < period:
        return None
    ema = sum(closes[:period]) / period
    mult = 2 / (period + 1)
    for c in closes[period:]:
        ema = (c - ema) * mult + ema
    return ema

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50
    gains = []
    losses = []
    for i in range(1, period + 1):
        diff = closes[-i] - closes[-i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            losses.append(abs(diff))
            gains.append(0)
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_macd(closes):
    if len(closes) < 26:
        return None, None, None
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    if ema12 is None or ema26 is None:
        return None, None, None
    macd_line = ema12 - ema26
    signal = calc_ema([macd_line] * 9, 9) if macd_line else None
    histogram = macd_line - signal if (macd_line and signal) else None
    return macd_line, signal, histogram

def calc_bollinger(closes, period=20):
    if len(closes) < period:
        return None, None, None
    sma = sum(closes[-period:]) / period
    std = np.std(closes[-period:])
    upper = sma + (2 * std)
    lower = sma - (2 * std)
    return upper, sma, lower

def calc_atr(high, low, close, period=14):
    if len(high) < period + 1:
        return None
    tr = []
    for i in range(1, period + 1):
        h = high[-i]
        l = low[-i]
        c = close[-i-1]
        tr.append(max(h-l, abs(h-c), abs(l-c)))
    return sum(tr) / period

def calc_vwap(high, low, close, volume):
    if len(high) < 1:
        return None
    typical_price = (high + low + close) / 3
    return (typical_price * volume).sum() / volume.sum()

def analyze(symbol, category):
    df_d, df_w, info = get_data(symbol)
    if df_d is None or len(df_d) < 50:
        return None
    
    close = df_d['Close'].values
    high = df_d['High'].values
    low = df_d['Low'].values
    volume = df_d['Volume'].values
    
    current = close[-1]
    
    # Technicals
    rsi = calc_rsi(close)
    ema9 = calc_ema(close, 9)
    ema21 = calc_ema(close, 21)
    ema50 = calc_ema(close, 50)
    ema200 = calc_ema(close, 200)
    macd, signal, hist = calc_macd(close)
    bb_upper, bb_mid, bb_lower = calc_bollinger(close)
    atr = calc_atr(high, low, close)
    
    # Weekly trend
    if len(df_w) > 20:
        w_close = df_w['Close'].values
        w_ema21 = calc_ema(w_close, 21)
        weekly_trend = "BULLISH" if w_ema21 and w_close[-1] > w_ema21 else "BEARISH"
    else:
        weekly_trend = "NEUTRAL"
    
    # Support/Resistance
    sup = low[-20:].min()
    res = high[-20:].max()
    
    # Fundamentals
    try:
        pe = info.get('trailingPE', 0) or 0
        pb = info.get('priceToBook', 0) or 0
        mcap = info.get('marketCap', 0)
        roe = info.get('returnOnEquity', 0) or 0
        debt = info.get('totalDebt', 0) or 0
        rev = info.get('revenueGrowth', 0) or 0
    except:
        pe = pb = mcap = roe = debt = rev = 0
    
    # Returns
    ret_1w = ((close[-1] / close[-5]) - 1) * 100 if len(close) >= 5 else 0
    ret_1m = ((close[-1] / close[-20]) - 1) * 100 if len(close) >= 20 else 0
    ret_3m = ((close[-1] / close[-60]) - 1) * 100 if len(close) >= 60 else 0
    
    # Scoring
    score = 0
    signals = []
    
    # RSI
    if rsi < 30:
        score += 3
        signals.append(f"RSI oversold ({rsi:.0f})")
    elif rsi < 40:
        score += 1
        signals.append(f"RSI bullish ({rsi:.0f})")
    elif rsi > 70:
        score -= 2
        signals.append(f"RSI overbought ({rsi:.0f})")
    
    # EMA Trend
    if ema9 and ema21:
        if ema9 > ema21:
            score += 2
            signals.append("Golden Cross (9/21)")
        else:
            score -= 1
            signals.append("Death Cross")
    
    # Above 50 EMA
    if ema50 and current > ema50:
        score += 1
        signals.append("Above 50 EMA")
    
    # Above 200 EMA (supertrend)
    if ema200 and current > ema200:
        score += 2
        signals.append("Above 200 EMA (Strong)")
    elif ema200 and current < ema200:
        score -= 2
        signals.append("Below 200 EMA (Weak)")
    
    # MACD
    if macd and signal and hist:
        if hist > 0:
            score += 1
            signals.append("MACD bullish")
        else:
            score -= 1
    
    # Near support
    dist_sup = (current - sup) / sup * 100
    if dist_sup < 5:
        score += 1
        signals.append(f"Near support ({dist_sup:.1f}%)")
    
    # Near resistance
    dist_res = (res - current) / res * 100
    if dist_res < 2:
        score -= 1
        signals.append(f"Near resistance ({dist_res:.1f}%)")
    
    # Fundamentals
    if 0 < pe < 25:
        score += 1
        signals.append(f"PE {pe:.1f} (reasonable)")
    elif pe > 50:
        score -= 1
        signals.append(f"PE {pe:.1f} (expensive)")
    
    if roe > 15:
        score += 1
        signals.append(f"ROE {roe*100:.0f}% (good)")
    
    # Weekly confirmation
    if weekly_trend == "BULLISH":
        score += 1
        signals.append(f"Weekly {weekly_trend}")
    
    name = symbol.replace('.NS', '')
    
    return {
        "name": name,
        "symbol": symbol,
        "category": category,
        "price": current,
        "rsi": rsi,
        "ema9": ema9,
        "ema21": ema21,
        "ema50": ema50,
        "ema200": ema200,
        "macd": macd,
        "macd_hist": hist,
        "bb_upper": bb_upper,
        "bb_lower": bb_lower,
        "atr": atr,
        "support": sup,
        "resistance": res,
        "weekly_trend": weekly_trend,
        "pe": pe,
        "pb": pb,
        "mcap": mcap,
        "roe": roe,
        "ret_1w": ret_1w,
        "ret_1m": ret_1m,
        "ret_3m": ret_3m,
        "score": score,
        "signals": signals
    }

def run():
    print("\n" + "="*75)
    print("KAI V3 - ADVANCED INDIAN MARKET ANALYSIS")
    print(datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("="*75)
    
    results = []
    
    for category, symbols in STOCKS.items():
        print(f"Analyzing {category}...", end=" ", flush=True)
        count = 0
        for sym in symbols:
            r = analyze(sym, category)
            if r:
                results.append(r)
                count += 1
            print(".", end="", flush=True)
        print(f" {count} stocks")
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # BUY SIGNALS
    print("\n" + "="*75)
    print("🎯 BUY SIGNALS (Technical + Fundamental)")
    print("="*75)
    
    buys = [r for r in results if r['score'] >= 3]
    for r in buys[:8]:
        print(f"\n📈 {r['name']} ({r['category']})")
        print(f"   Price: ₹{r['price']:.2f} | Score: {r['score']}")
        print(f"   RSI: {r['rsi']:.0f} | MACD: {'+' if r['macd_hist'] and r['macd_hist'] > 0 else '-'}")
        print(f"   EMAs: 9>{'Y' if r['ema9'] and r['ema21'] and r['ema9'] > r['ema21'] else 'N'}21>{'Y' if r['ema50'] and r['ema21'] > r['ema50'] else 'N'}50")
        print(f"   1W: {r['ret_1w']:+.1f}% | 1M: {r['ret_1m']:+.1f}% | 3M: {r['ret_3m']:+.1f}%")
        print(f"   Fund: P/E {r['pe']:.1f} | ROE {r['roe']*100:.0f}% | Weekly: {r['weekly_trend']}")
        for s in r['signals'][:4]:
            print(f"   ✓ {s}")
        print(f"   📍 S: ₹{r['support']:.2f} | R: ₹{r['resistance']:.2f}")
    
    # SELL SIGNALS
    print("\n" + "="*75)
    print("⚠️ SELL/WEAK SIGNALS")
    print("="*75)
    
    sells = [r for r in results if r['score'] <= -1]
    for r in sells[:5]:
        print(f"📉 {r['name']} | RSI: {r['rsi']:.0f} | 1M: {r['ret_1m']:+.1f}% | P/E: {r['pe']:.1f}")
    
    # SECTOR SUMMARY
    print("\n" + "="*75)
    print("📊 SECTOR SUMMARY")
    print("="*75)
    
    for cat in STOCKS.keys():
        cat_r = [r for r in results if r['category'] == cat]
        if cat_r:
            avg = sum([x['score'] for x in cat_r]) / len(cat_r)
            buy = len([x for x in cat_r if x['score'] >= 2])
            sell = len([x for x in cat_r if x['score'] <= -1])
            s = "🟢" if avg > 1 else "🔴" if avg < -1 else "🟡"
            print(f"{cat:12} {s} Score: {avg:+.1f} | Buy: {buy} | Sell: {sell}")
    
    # TOP PICKS WITH ENTRY/EXIT
    print("\n" + "="*75)
    print("⭐ TOP TRADING SETUPS")
    print("="*75)
    
    for i, r in enumerate(results[:3], 1):
        target = r['price'] * 1.10
        stop = r['price'] * 0.97
        risk = r['price'] - stop
        reward = target - r['price']
        rr = reward / risk if risk > 0 else 0
        
        print(f"\n#{i} {r['name']} - ₹{r['price']:.2f}")
        print(f"   🎯 Target: ₹{target:.2f} (+10%)")
        print(f"   🛡️  Stop: ₹{stop:.2f} (-3%)")
        print(f"   ⚖️  Risk/Reward: 1:{rr:.1f}")
        print(f"   📊 RSI: {r['rsi']:.0f} | Weekly: {r['weekly_trend']}")

if __name__ == "__main__":
    run()
