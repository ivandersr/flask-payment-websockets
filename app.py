from flask import Flask, request, jsonify, send_file, render_template
from database import db
from dotenv import load_dotenv
from flask_socketio import SocketIO
from datetime import datetime, timedelta
from payments.pix import Pix
from models.payment import Payment

load_dotenv()

app = Flask(__name__)
app.config.from_object('configs.Config')
db.init_app(app)

socketio = SocketIO(app)

@app.route("/payments/pix", methods=["POST"])
def create_pix_payment():
    data = request.get_json()

    value = data.get("value")

    if not value:
        return jsonify({"message": "Invalid value"}), 400

    expiration_date = datetime.now() + timedelta(minutes=30)

    new_payment = Payment(value=value, expiration_date=expiration_date)

    pix_obj = Pix()
    pix_payment_data = pix_obj.create_payment()

    new_payment.qr_code = pix_payment_data.get("qr_code_path")
    new_payment.bank_payment_id = pix_payment_data.get("bank_payment_id")
    db.session.add(new_payment)
    db.session.commit()

    return jsonify({
        "message": "The payment has been created",
        "payment": new_payment.as_dict()
    })

@app.route("/payments/pix/qr_code/<file_name>", methods=["GET"])
def get_image(file_name):
    return send_file(f"static/img/{file_name}.png", mimetype="image/png")

@app.route("/payments/pix/confirmation", methods=["POST"])
def confirm_pix_payment():
    data = request.get_json()

    if "bank_payment_id" not in data or "value" not in data:
        return jsonify({"message": "Invalid payment data"}), 400

    payment = Payment.query.filter_by(
        bank_payment_id=data.get("bank_payment_id")
    ).first()
    
    if not payment:
        return jsonify({"message": "Payment not found"}), 404
    
    if data.get("value") != payment.value:
        return jsonify({"message": "Invalid payment data"}), 400
    
    payment.paid = True
    db.session.commit()
    socketio.emit(f"payment-confirmed-{payment.id}")

    return jsonify({"message": "The payment has been confirmed"}) 

@app.route("/payments/pix/<int:payment_id>", methods=["GET"])
def pix_payment_page(payment_id):
    payment = Payment.query.get(payment_id)

    if not payment:
        return render_template("404.html")
    
    if payment.paid:
        return render_template(
            "confirmed_payment.html",
            payment_id=payment.id, 
            value=payment.value,
            host="http://localhost:5000",   
            qr_code_path=payment.qr_code
        )
    
    return render_template(
        "payment.html", 
        payment_id=payment.id, 
        value=payment.value,
        host="http://localhost:5000",   
        qr_code_path=payment.qr_code
    )

# Websockets
@socketio.on("connect")
def handle_connect():
    print("Client has connected to the server")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client has disconnected from the server")

if __name__ == "__main__":
    socketio.run(app, debug=True)