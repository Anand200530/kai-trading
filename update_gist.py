#!/usr/bin/env python3
"""
Update GitHub Gist with trading data
"""

import json
import os
import requests

# Your GitHub token (set as env var GITHUB_TOKEN)
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# Gist ID (will be created if not exists)
GIST_ID = ''  # Will be set after creating gist

WALLET_FILE = "/home/anand/.openclaw/workspace/trading/india_wallet.json"
GIST_FILENAME = "trading_data.json"

def read_wallet():
    with open(WALLET_FILE) as f:
        return json.load(f)

def update_gist():
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN not set")
        return False
    
    data = read_wallet()
    
    # Get existing gist or create new
    if GIST_ID:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Update existing gist
            gist = response.json()
            gist['files'][GIST_FILENAME]['content'] = json.dumps(data, indent=2)
            requests.patch(url, headers=headers, json=gist)
            print(f"Updated gist: {GIST_ID}")
            return True
    
    # Create new gist
    gist_data = {
        "description": "KAI Trading Data",
        "public": False,
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(data, indent=2)
            }
        }
    }
    
    response = requests.post(
        "https://api.github.com/gists",
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json=gist_data
    )
    
    if response.status_code == 201:
        gist_id = response.json()['id']
        print(f"Created new gist: {gist_id}")
        print(f"Add this to update_gist.py: GIST_ID = '{gist_id}'")
        return True
    
    print(f"Error: {response.status_code}")
    print(response.text)
    return False

if __name__ == "__main__":
    update_gist()
