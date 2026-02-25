#!/usr/bin/env python3
"""
KAI - Paper Trading Web Dashboard
"""

from flask import Flask, render_template_string, jsonify
import json
import yfinance as yf
from datetime import datetime

app = Flask(__name__)

WALLET_FILE = "/home/anand/.openclaw/workspace/trading/india_wallet.json"

def get_price(symbol):
    try:
        t = yf.Ticker(symbol + ".NS")
        return t.info.get('regularMarketPrice', 0)
    except:
        return 0

def load_data():
    with open(WALLET_FILE) as f:
        return json.load(f)

def get_market_data():
    wallet = load_data()
    data = []
    
    # Update open positions with current prices
    for pos in wallet.get('positions', []):
        current_price = get_price(pos['symbol'])
        if current_price > 0:
            pos['current_price'] = current_price
            pos['current_value'] = current_price * pos['qty']
            pos['pnl'] = (current_price - pos['entry_price']) * pos['qty']
            pos['pnl_pct'] = ((current_price / pos['entry_price']) - 1) * 100
    
    # Update closed trades
    for trade in wallet.get('trades', []):
        trade['pnl_pct'] = ((trade.get('exit_price', 0) / trade['entry_price']) - 1) * 100 if trade.get('exit_price') else 0
    
    return wallet

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>KAI Paper Trading</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f; 
            color: #fff;
            min-height: 100vh;
        }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 20px;
        }
        h1 { font-size: 24px; color: #00ff88; }
        .refresh { 
            background: #333; color: #fff; border: none; 
            padding: 8px 16px; border-radius: 6px; cursor: pointer;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        .stat-label { color: #888; font-size: 12px; margin-bottom: 5px; }
        .stat-value { font-size: 24px; font-weight: bold; }
        .stat-value.green { color: #00ff88; }
        .stat-value.red { color: #ff4444; }
        
        h2 { font-size: 18px; margin-bottom: 15px; color: #ccc; }
        
        .positions { margin-bottom: 30px; }
        .position-card {
            background: #1a1a1a;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .position-info h3 { font-size: 16px; margin-bottom: 5px; }
        .position-info span { color: #888; font-size: 13px; }
        .position-price { text-align: right; }
        .position-price .price { font-size: 18px; font-weight: bold; }
        .position-price .pnl { font-size: 14px; }
        .pnl.positive { color: #00ff88; }
        .pnl.negative { color: #ff4444; }
        
        .target-sl {
            display: flex;
            gap: 20px;
            margin-top: 8px;
            font-size: 12px;
        }
        .target-sl span { color: #666; }
        .target { color: #00ff88; }
        .sl { color: #ff4444; }
        
        .trades { margin-bottom: 30px; }
        .trade-card {
            background: #1a1a1a;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            font-size: 14px;
        }
        
        .empty { text-align: center; color: #666; padding: 40px; }
        
        .BUY { color: #00ff88; }
        .SELL { color: #ff4444; }
        .SL { color: #ff4444; }
        .TARGET { color: #00ff88; }
        
        @media (max-width: 600px) {
            .stats { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>KAI Paper Trading</h1>
            <button class="refresh" onclick="location.reload()">Refresh</button>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Capital</div>
                <div class="stat-value">₹{{ "{:,.0f}".format(data.capital) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Cash</div>
                <div class="stat-value">₹{{ "{:,.0f}".format(data.balance) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Invested</div>
                <div class="stat-value">₹{{ "{:,.0f}".format(invested) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total P&L</div>
                <div class="stat-value {% if total_pnl >= 0 %}green{% else %}red{% endif %}">
                    ₹{{ "{:+,.0f}".format(total_pnl) }}
                </div>
            </div>
        </div>
        
        <div class="positions">
            <h2>Open Positions ({{ data.positions|length }})</h2>
            {% if data.positions %}
                {% for pos in data.positions %}
                <div class="position-card">
                    <div class="position-info">
                        <h3>{{ pos.symbol }}</h3>
                        <span>Bought @ ₹{{ "%.2f"|format(pos.entry_price) }}</span>
                        <div class="target-sl">
                            <span class="target">Target: ₹{{ "%.2f"|format(pos.target) }}</span>
                            <span class="sl">SL: ₹{{ "%.2f"|format(pos.stop_loss) }}</span>
                        </div>
                    </div>
                    <div class="position-price">
                        <div class="price">₹{{ "%.2f"|format(pos.get('current_price', pos.entry_price)) }}</div>
                        <div class="pnl {% if pos.get('pnl', 0) >= 0 %}positive{% else %}negative{% endif %}">
                            {% if pos.get('pnl', 0) >= 0 %}+{% endif %}₹{{ "%.0f"|format(pos.get('pnl', 0)) }} ({{ "%.1f"|format(pos.get('pnl_pct', 0)) }}%)
                        </div>
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty">No open positions</div>
            {% endif %}
        </div>
        
        <div class="trades">
            <h2>Trade History ({{ data.trades|length }})</h2>
            {% if data.trades %}
                {% for trade in data.trades %}
                <div class="trade-card">
                    <div>
                        <span class="{{ trade.side }}">{{ trade.side }}</span>
                        <span>{{ trade.symbol }}</span>
                    </div>
                    <div>₹{{ "%.2f"|format(trade.entry_price) }}</div>
                    <div>₹{{ "%.2f"|format(trade.get('exit_price', 0)) }}</div>
                    <div class="{{ trade.status }}">{{ trade.status }}</div>
                    <div class="{% if trade.get('pnl', 0) >= 0 %}positive{% else %}negative{% endif %}">
                        {% if trade.get('pnl', 0) >= 0 %}+{% endif %}₹{{ "%.0f"|format(trade.get('pnl', 0)) }}
                    </div>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty">No trade history</div>
            {% endif %}
        </div>
        
        <footer style="text-align: center; color: #666; padding: 20px; font-size: 12px;">
            Last updated: {{ last_update }}
        </footer>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    data = get_market_data()
    
    invested = sum([p.get('current_value', p['cost']) for p in data.get('positions', [])])
    total_pnl = sum([p.get('pnl', 0) for p in data.get('positions', [])])
    
    return render_template_string(HTML, 
        data=data, 
        invested=invested, 
        total_pnl=total_pnl,
        last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/api')
def api():
    return jsonify(get_market_data())

if __name__ == '__main__':
    print("="*50)
    print("KAI Paper Trading Dashboard")
    print("Open http://localhost:5000")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)
