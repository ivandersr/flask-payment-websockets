import uuid
import qrcode

class Pix:
    def __init__(self):
        pass

    def create_payment(self):     
        bank_payment_id = uuid.uuid4()
        payment_hash = f"payment_hash_{bank_payment_id}"
        img = qrcode.make(payment_hash)
        img.save(f"static/img/qr_code_{bank_payment_id}.png")

        return {
            "bank_payment_id": bank_payment_id,
            "qr_code_path": f"qr_code_{bank_payment_id}.png"
        }

