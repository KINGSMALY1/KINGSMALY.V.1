import requests
from flask import current_app


class PaystackService:

    @staticmethod
    def headers():
        return {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def initialize_payment(email, amount, reference, callback_url):
        url = f"{current_app.config['PAYSTACK_BASE_URL']}/transaction/initialize"

        payload = {
            "email": email,
            "amount": int(amount * 100),   # Kobo
            "reference": reference,
            "callback_url": callback_url,
        }

        response = requests.post(
            url,
            json=payload,
            headers=PaystackService.headers(),
            timeout=30,
        )

        # FIX: log Paystack's actual error message before raising, so
        # the real reason (bad key, invalid email, wrong key type,
        # etc.) shows up in Render's logs instead of a bare "400
        # Bad Request" with no explanation.
        if not response.ok:
            print(f"Paystack initialize_payment failed ({response.status_code}): {response.text}", flush=True)

        response.raise_for_status()

        return response.json()

    @staticmethod
    def verify_payment(reference):
        url = f"{current_app.config['PAYSTACK_BASE_URL']}/transaction/verify/{reference}"

        response = requests.get(
            url,
            headers=PaystackService.headers(),
            timeout=30,
        )

        if not response.ok:
            print(f"Paystack verify_payment failed ({response.status_code}): {response.text}", flush=True)

        response.raise_for_status()

        return response.json()
