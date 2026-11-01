import os
import pyotp
from flask import Flask, request, jsonify
from SmartApi import SmartConnect

app = Flask(__name__)

# --- CONFIGURATION (HARDCODED FOR MOBILE SIMPLICITY) ---
API_KEY = "OLHsReQX"
CLIENT_CODE = "V188801"
PASSWORD = "YOUR_ANGEL_ONE_PASSWORD"    # 👈 Put your real Angel One password here
TOTP_SECRET = "YOUR_TOTP_SECRET_KEY"  # 👈 Put your real 2FA text token key here

def place_angel_order(symbol, action, token, exchange, quantity):
    try:
        # Initialize SmartAPI Connection
        obj = SmartConnect(api_key=API_KEY)
        
        # Generate the dynamic 6-digit TOTP pin automatically
        totp_pin = pyotp.TOTP(TOTP_SECRET).now()
        
        # Login and generate active session tokens
        token_data = obj.generateSession(CLIENT_CODE, PASSWORD, totp_pin)
        
        if not token_data.get('status'):
            return {"status": "failed", "reason": "Angel One Login Failed", "details": token_data}

        # Dynamic product routine based on segment
        product_type = "CARRYFORWARD" if exchange.upper() == "NFO" else "INTRADAY"

        # Build order execution structure
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol.upper(),
            "symboltoken": str(token),  
            "transactiontype": action.upper(),  
            "exchange": exchange.upper(),  
            "ordertype": "MARKET",
            "producttype": product_type,  
            "duration": "DAY",
            "quantity": str(quantity)
        }
        
        # Dispatch trade directly to Angel One exchange terminal
        order_id = obj.placeOrder(order_params)
        return {"status": "success", "order_id": order_id}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/webhook', methods=['POST'])
def webhook():
    # Process incoming alerts sent by TradingView
    data = request.json
    if not data:
        return jsonify({"status": "ignored", "reason": "Empty payload received"}), 400
        
    symbol = data.get("symbol")
    action = data.get("action")     
    token = data.get("token")       
    exchange = data.get("exchange", "NSE")  
    quantity = data.get("quantity", 1)
    
    # Strict validation check to filter invalid pings
    if not symbol or not token or not action:
        return jsonify({"status": "ignored", "reason": "Missing mandatory trading fields"}), 400
        
    # Execute order transaction loop
    response = place_angel_order(symbol, action, token, exchange, quantity)
    return jsonify(response)

if __name__ == '__main__':
    # Automatically binds to Render's dynamic web port assignment
    port_number = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port_number)
