#!/usr/bin/env python3
"""
Keep trading data synced - updates GitHub Gist
"""

import json
import os
import time
import yfinance as yf
import requests
from datetime import datetime

WALLET_FILE = "/home/anand/.openclaw/workspace/trading/india_wallet.json"
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GIST_ID = ""  # Will be created

def get_price(symbol):
    try:
        t = yf.Ticker(symbol + ".NS")
        return float(t.info.get('regularMarketPrice', 0))
    except:
        return 0

def update_prices(data):
    """Update current prices for all positions"""
    for pos in data.get('positions', []):
        current_price = get_price(pos['symbol'])
        if current_price > 0:
            pos['current_price'] = current_price
            pos['current_value'] = current_price * pos['qty']
            pos['pnl'] = (current_price - pos['entry_price']) * pos['qty']
            pos['pnl_pct'] = ((current_price / pos['entry_price']) - 1) * 100
    return data

def sync_to_gist(data):
    global GIST_ID
    
    # Check if gist exists
    if not GIST_ID:
        # Search for existing gist
        response = requests.get(
            "https://api.github.com/gists",
            headers={"Authorization": f"token {GITHUB_TOKEN}"}
        )
        if response.status_code == 200:
            for gist in response.json():
                if "kai-trading" in gist.get('description', ''):
                    GIST_ID = gist['id']
                    break
    
    data_json = json.dumps(data, indent=2, default=str)
    
    if GIST_ID:
        # Update existing gist
        response = requests.get(
            f"https://api.github.com/gists/{GIST_ID}",
            headers={"Authorization": f"token {GITHUB_TOKEN}"}
        )
        if response.status_code == 200:
            gist = response.json()
            gist['files']['trading_data.json']['content'] = data_json
            requests.patch(
                f"https://api.github.com/gists/{GIST_ID}",
                headers={"Authorization": f"token {GITHUB_TOKEN}"},
                json=gist
            )
            print(f"Updated gist: {GIST_ID}")
            return True
    
    # Create new gist
    gist_data = {
        "description": "kai-trading data",
        "public": False,
        "files": {
            "trading_data.json": {"content": data_json}
        }
    }
    
    response = requests.post(
        "https://api.github.com/gists",
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json=gist_data
    )
    
    if response.status_code == 201:
        GIST_ID = response.json()['id']
        print(f"Created new gist: {GIST_ID}")
        
        # Save gist ID
        with open("/home/anand/.openclaw/workspace/trading/gist_id.txt", "w") as f:
            f.write(GIST_ID)
        return True
    
    print(f"Error: {response.status_code}")
    return False

def main():
    print("="*50)
    print("KAI - Syncing Trading Data")
    print("="*50)
    
    # Load wallet
    with open(WALLET_FILE) as f:
        data = json.load(f)
    
    # Update prices
    data = update_prices(data)
    
    # Save locally
    with open(WALLET_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Sync to gist
    success = sync_to_gist(data)
    
    if success:
        print(f"\n✓ Data synced to Gist")
        print(f"  Gist ID: {GIST_ID}")
        print(f"\nAdd this to your dashboard JavaScript:")
        print(f"const GIST_ID = '{GIST_ID}';")
        print(f"const GITHUB_TOKEN = 'YOUR_TOKEN';")
    
    # Print current status
    invested = sum([p.get('current_value', 0) for p in data.get('positions', [])])
    pnl = sum([p.get('pnl', 0) for p in data.get('positions', [])])
    
    print(f"\n--- Portfolio Status ---")
    print(f"Cash: ₹{data['balance']:,.0f}")
    print(f"Invested: ₹{invested:,.0f}")
    print(f"Open P&L: ₹{pnl:+,.0f}")
    print(f"Total: ₹{data['balance'] + invested + pnl:,.0f}")

if __name__ == "__main__":
    main()
