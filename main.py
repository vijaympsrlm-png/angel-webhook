import os
from flask import Flask, request, jsonify
from SmartApi import SmartConnect
import pyotp

app = Flask(__name__)

# --- CONFIGURATION (HARDCODED FOR MOBILE SIMPLICITY) ---
API_KEY = "OLHsReQX"
CLIENT_CODE = "V188801"
PASSWORD = "YOUR_ANGEL_ONE_PASSWORD"      # 👈 Replace with your real Angel One password
TOTP_SECRET = "YOUR_TOTP_SECRET_KEY"    # 👈 Replace with your real 2FA text token string

def place_angel_order(symbol, action, token, exchange, quantity):
    try:
        # Initialize SmartAPI Session
        obj = SmartConnect(api_key=API_KEY)
        token_data = obj.generateSession(CLIENT_CODE, PASSWORD, pyotp.TOTP(TOTP_SECRET).now())
        
        if not token_data.get('status'):
            return {"error": "Authentication Failed", "details": token_data}

        # Dynamic product type based on segment (Options vs Stocks)
        product_type = "CARRYFORWARD" if exchange == "NFO" else "INTRADAY"

        # Order Parameters Configuration
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,  
            "transactiontype": action.upper(),  
            "exchange": exchange,  
            "ordertype": "MARKET",
            "producttype": product_type,  
            "duration": "DAY",
            "quantity": str(quantity)
        }
        
        return obj.placeOrder(order_params)
    except Exception as e:
        return {"error": str(e)}

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    # Extract details sent by TradingView
    symbol = data.get("symbol")
    action = data.get("action")     
    token = data.get("token")       
    exchange = data.get("exchange", "NSE")  # Defaults to NSE if not specified
    quantity = data.get("quantity", 1)
    
    # Validation Check
    if not symbol or not token or not action:
        return jsonify({"status": "ignored", "reason": "Missing mandatory trading fields"}), 400
        
    # Execute order
    response = place_angel_order(symbol, action, token, exchange, quantity)
    return jsonify(response)

if __name__ == '__main__':
    # Binds to the dynamic port assigned by Render
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
