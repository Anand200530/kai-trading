#!/usr/bin/env python3
"""
KAI - Daily Indian Market Scanner + Paper Trading
Automated daily analysis with alerts
"""

import yfinance as yf
import numpy as np
import json
import os
from datetime import datetime
from pathlib import Path

# Config
WALLET_FILE = "/home/anand/.openclaw/workspace/trading/india_wallet.json"
LOG_FILE = "/home/anand/.openclaw/workspace/trading/india_log.txt"
PAPER_CAPITAL = 100000  # ₹1 lakh

STOCKS = {
    "NIFTY_50": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "TITAN.NS", "HCLTECH.NS",
        "KOTAKBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS",
        "SUNPHARMA.NS", "TATASTEEL.NS", "WIPRO.NS", "HINDUNILVR.NS", "NTPC.NS",
        "POWERGRID.NS", "ONGC.NS", "COALINDIA.NS", "BPCL.NS", "ULTRACEMCO.NS"],
    "NIFTY_BANK": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "INDUSINDBK.NS", "BANDHANBNK.NS", "AUBANK.NS"],
    "NIFTY_IT": ["INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "LTIM.NS", "TECHM.NS"],
    "NIFTY_AUTO": ["MARUTI.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "EICHERMOT.NS"],
    "NIFTY_PHARMA": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "MIDCAP": ["POLYCAB.NS", "HAVELLS.NS", "MARICO.NS", "DABUR.NS", "PIDILITIND.NS"]
}

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def load_wallet():
    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE) as f:
            return json.load(f)
    return {"capital": PAPER_CAPITAL, "balance": PAPER_CAPITAL, "positions": [], "trades": []}

def save_wallet(w):
    with open(WALLET_FILE, "w") as f:
        json.dump(w, f, indent=2)

def get_data(symbol):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="1y", interval="1d")
        info = t.info
        return df, info
    except:
        return None, None

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
    gains = sum([closes[i] - closes[i-1] for i in range(1, period+1) if closes[i] > closes[i-1]])
    losses = sum([closes[i-1] - closes[i] for i in range(1, period+1) if closes[i] < closes[i-1]])
    rs = gains / losses if losses > 0 else 100
    return 100 - (100 / (1 + rs))

def analyze(symbol, category):
    df, info = get_data(symbol)
    if df is None or len(df) < 50:
        return None
    
    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values
    
    current = close[-1]
    rsi = calc_rsi(close)
    ema9 = calc_ema(close, 9)
    ema21 = calc_ema(close, 21)
    ema50 = calc_ema(close, 50)
    ema200 = calc_ema(close, 200)
    
    sup = low[-20:].min()
    res = high[-20:].max()
    
    try:
        pe = info.get('trailingPE', 0) or 0
    except:
        pe = 0
    
    ret_1m = ((close[-1] / close[-20]) - 1) * 100 if len(close) >= 20 else 0
    
    score = 0
    signals = []
    
    if rsi < 35:
        score += 3
        signals.append(f"RSI {rsi:.0f}")
    elif rsi > 70:
        score -= 2
    
    if ema9 and ema21 and ema9 > ema21:
        score += 2
        signals.append("Golden Cross")
    
    if ema200 and current > ema200:
        score += 2
    
    if 0 < pe < 25:
        score += 1
    
    if ret_1m > 5:
        score += 1
    
    name = symbol.replace('.NS', '')
    
    return {
        "name": name, "symbol": symbol, "category": category,
        "price": current, "rsi": rsi, "pe": pe,
        "ema9": ema9, "ema21": ema21, "ema200": ema200,
        "support": sup, "resistance": res,
        "ret_1m": ret_1m, "score": score, "signals": signals
    }

def scan_market():
    log("Scanning Indian market...")
    results = []
    
    for category, symbols in STOCKS.items():
        for sym in symbols:
            r = analyze(sym, category)
            if r:
                results.append(r)
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def open_position(symbol, entry_price, qty, wallet):
    cost = entry_price * qty
    
    if cost > wallet['balance']:
        log(f"❌ Insufficient balance for {symbol}")
        return wallet
    
    position = {
        "id": len(wallet['trades']) + 1,
        "symbol": symbol,
        "entry_price": entry_price,
        "qty": qty,
        "cost": cost,
        "entry_time": datetime.now().isoformat(),
        "stop_loss": round(entry_price * 0.97, 2),
        "target": round(entry_price * 1.10, 2),
        "status": "OPEN"
    }
    
    wallet['positions'].append(position)
    wallet['balance'] -= cost
    save_wallet(wallet)
    
    log(f"✅ BUY {symbol} | Qty: {qty} | Entry: ₹{entry_price} | Target: ₹{position['target']} | SL: ₹{position['stop_loss']}")
    return wallet

def check_positions(wallet):
    if not wallet['positions']:
        return wallet
    
    for pos in list(wallet['positions']):
        try:
            df, _ = get_data(pos['symbol'] + ".NS")
            if df is None:
                continue
            current = df['Close'].values[-1]
            
            # Check exit
            if current <= pos['stop_loss']:
                pnl = (pos['stop_loss'] - pos['entry_price']) * pos['qty']
                wallet['balance'] += pos['cost'] + pnl
                pos['exit_price'] = current
                pos['exit_time'] = datetime.now().isoformat()
                pos['pnl'] = pnl
                pos['status'] = 'SL'
                wallet['trades'].append(pos)
                wallet['positions'].remove(pos)
                log(f"🛑 SL EXIT: {pos['symbol']} | P&L: ₹{pnl:.0f}")
                
            elif current >= pos['target']:
                pnl = (pos['target'] - pos['entry_price']) * pos['qty']
                wallet['balance'] += pos['cost'] + pnl
                pos['exit_price'] = current
                pos['exit_time'] = datetime.now().isoformat()
                pos['pnl'] = pnl
                pos['status'] = 'TARGET'
                wallet['trades'].append(pos)
                wallet['positions'].remove(pos)
                log(f"🎯 TARGET HIT: {pos['symbol']} | P&L: ₹{pnl:.0f}")
        except Exception as e:
            log(f"Error checking {pos['symbol']}: {e}")
    
    save_wallet(wallet)
    return wallet

def daily_report():
    log("="*50)
    log("KAI DAILY REPORT")
    log("="*50)
    
    wallet = load_wallet()
    wallet = check_positions(wallet)
    
    results = scan_market()
    
    # Portfolio
    invested = PAPER_CAPITAL - wallet['balance']
    open_pnl = 0
    for pos in wallet['positions']:
        try:
            df, _ = get_data(pos['symbol'] + ".NS")
            if df:
                current = df['Close'].values[-1]
                open_pnl += (current - pos['entry_price']) * pos['qty']
        except:
            pass
    
    total_value = wallet['balance'] + invested + open_pnl
    total_pnl = total_value - PAPER_CAPITAL
    
    log(f"💰 Portfolio: ₹{total_value:,.0f} | P&L: ₹{total_pnl:,.0f}")
    log(f"   Cash: ₹{wallet['balance']:,.0f} | Invested: ₹{invested:,.0f} | Open P&L: ₹{open_pnl:,.0f}")
    
    # Top setups
    buys = [r for r in results if r['score'] >= 5]
    log(f"\n🎯 Top {len(buys)} BUY Signals:")
    for r in buys[:5]:
        log(f"   {r['name']} | ₹{r['price']:.0f} | RSI: {r['rsi']:.0f} | Score: {r['score']}")
    
    save_wallet(wallet)
    return results

if __name__ == "__main__":
    daily_report()
