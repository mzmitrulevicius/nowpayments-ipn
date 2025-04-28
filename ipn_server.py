from flask import Flask, request
import hmac
import hashlib
import sqlite3
import json
import os

app = Flask(__name__)
DB = "users.db"
IPN_SECRET = b"T03tUSJRcSSCKZBmH5Cv4wou9Fh+4XB1"

def verify_ipn(req):
    payload = req.get_data()
    received_hmac = req.headers.get("x-nowpayments-sig")
    if not received_hmac:
        return False
    calculated_hmac = hmac.new(IPN_SECRET, payload, hashlib.sha512).hexdigest()
    return hmac.compare_digest(calculated_hmac, received_hmac)

def credit_user(order_id, amount):
    if not order_id or "-" not in order_id:
        print("⚠️ Invalid order_id format:", order_id)
        return
    try:
        user_id = int(order_id.split("-")[1])
    except ValueError:
        print("⚠️ Cannot extract user_id from order_id:", order_id)
        return

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()
    print(f"✅ Credited {amount} USDT to user ID {user_id}")

@app.route("/ipn", methods=["POST"])
def ipn_handler():
    if not verify_ipn(request):
        return "Invalid HMAC signature", 403

    data = request.json
    print("✅ IPN received:", json.dumps(data, indent=2))

    if data.get("payment_status") == "finished":
        order_id = data.get("order_id")
        amount = float(data.get("price_amount", 0))
        credit_user(order_id, amount)

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # naudoti PORT iš aplinkos
    app.run(host="0.0.0.0", port=port)
