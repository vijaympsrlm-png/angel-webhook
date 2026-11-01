import os
from flask import Flask, request, jsonify
from SmartApi import SmartConnect
import pyotp

app = Flask(__name__)

API_KEY = os.environ.get("ANGEL_API_KEY")
CLIENT_CODE = os.environ.get("ANGEL_CLIENT_CODE")
PASSWORD = os.environ.get("ANGEL_PASSWORD")
TOTP_SECRET = os.environ.get("ANGEL_TOTP_SECRET")

def place_angel_order(symbol, action, token, exchange, quantity):
    try:
        obj = SmartConnect(api_key=API_KEY)
        token_data = obj.generateSession(CLIENT_CODE, PASSWORD, pyotp.TOTP(TOTP_SECRET).now())
        
        if not token_data.get('status'):
            return {"error": "Authentication Failed"}

        # Dynamic product type based on exchange (Options vs Stocks)
        product_type = "CARRYFORWARD" if exchange == "NFO" else "INTRADAY"

        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,  
            "transactiontype": action.upper(),  
            "exchange": exchange,  # Dynamic exchange configuration
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
    
    symbol = data.get("symbol")
    action = data.get("action")     
    token = data.get("token")       
    exchange = data.get("exchange", "NSE")  # Defaults to NSE if not sent
    quantity = data.get("quantity", 1)
    
    # ⚠️ Security Validation Check
    if not symbol or not token:
        return jsonify({"status": "ignored", "reason": "Missing mandatory fields"}), 400
        
    response = place_angel_order(symbol, action, token, exchange, quantity)
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
