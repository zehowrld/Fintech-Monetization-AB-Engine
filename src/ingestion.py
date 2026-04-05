import os
import requests
import pandas as pd 
import numpy as np

from dotenv import load_dotenv
load_dotenv()

def fetch_market_price(symbol="BTC"):
    """Fetches real-time price using Alpha Vantage."""
    
    api_key = os.getenv('ALPHA_VANTAGE_KEY')

    if not api_key:
        print("⚠️ API KEY MISSING: Using fallback market price ($65,000).")
        return 65000.0
    
    url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={symbol}&to_currency=USD&apikey={api_key}"

    try:
        r = requests.get(url).json()
        # Alpha Vantage returns an 'Error Message' key if the key is invalid
        if "Error Message" in r or "Information" in r:
            return 65000.0
        return float(r['Realtime Currency Exchange Rate']['5. Exchange Rate'])       
    except Exception:
        return 65000.0
    
def ingest_monetization_data(n_required):
    """Generates A/B test data influenced by real market price."""
    n = int(n_required)
    price = fetch_market_price()
    np.random.seed(42)

    df = pd.DataFrame({
        'user_id': range(1,n+1),
        'group': np.random.choice(['Control', 'Test'], n),
        'market_price': price
    })

    base_conv = 0.10
    boost = 0.035 if price > 60000 else 0.015

    df['converted'] = df['group'].apply(
        lambda x: np.random.binomial(1, base_conv + boost) if x == 'Test' else np.random.binomial(1, base_conv)
    )

    # REVENUE: Test = $7.99, Control = $10.00
    price_strategy = {
        'Test': 7.99,    # The "Value Tier" challenger
        'Control': 10.00 # The "Premium" baseline
    }
    
    # Initialize revenue at 0.0
    df['revenue'] = 0.0

    # Identify users who actually converted (The 'Success' Mask)
    converted_mask = df['converted'] == 1

    # Map prices only to converted users based on their group
    df.loc[converted_mask, 'revenue'] = df.loc[converted_mask, 'group'].map(price_strategy)

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/raw_ingestion_log.csv", index=False)
    
    return df

if __name__ == "__main__":
    
    if not os.getenv('ALPHA_VANTAGE_KEY'):
        print("❌ SETUP ERROR: .env file not found or ALPHA_VANTAGE_KEY is empty.")
    else:
        test_df = ingest_monetization_data(n_required=10000)
        print("✅ Ingestion Test Successful!")
        print(test_df.head())
        print(f"Total Rows Generated: {len(test_df)}")
        print(f"Columns Ingested: {test_df.columns.to_list()}")