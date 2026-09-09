import time

import requests
from flask import current_app

# Module-level token cache (per Render worker process).
# Monnify bearer tokens last ~1 hour; we refresh 60s early to be safe.
_token_cache = {"access_token": None, "expires_at": 0}


class MonnifyService:

    @staticmethod
    def _get_access_token():
        import base64

        now = time.time()
        if _token_cache["access_token"] and now < _token_cache["expires_at"]:
            return _token_cache["access_token"]

        api_key = current_app.config["MONNIFY_API_KEY"]
        secret_key = current_app.config["MONNIFY_SECRET_KEY"]
        base_url = current_app.config["MONNIFY_BASE_URL"]

        credentials = f"{api_key}:{secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()

        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            headers={"Authorization": f"Basic {encoded}"},
            timeout=30,
        )

        if not response.ok:
            print(f"Monnify auth failed ({response.status_code}): {response.text}", flush=True)
        response.raise_for_status()

        data = response.json()
        token = data["responseBody"]["accessToken"]
        expires_in = data["responseBody"].get("expiresIn", 3600)

        _token_cache["access_token"] = token
        _token_cache["expires_at"] = now + expires_in - 60

        return token

    @staticmethod
    def initialize_payment(email, amount, reference, callback_url, customer_name="Kingsmaly Customer"):
        """
        Mirrors PaystackService.initialize_payment's signature so call
        sites need minimal changes. Returns Monnify's parsed JSON;
        the checkout link is at result["responseBody"]["checkoutUrl"].
        """
        base_url = current_app.config["MONNIFY_BASE_URL"]
        contract_code = current_app.config["MONNIFY_CONTRACT_CODE"]
        token = MonnifyService._get_access_token()

        payload = {
            "amount": amount,  # Monnify uses Naira directly, NOT kobo
            "customerName": customer_name,
            "customerEmail": email,
            "paymentReference": reference,
            "paymentDescription": "Kingsmaly Voucher Purchase",
            "currencyCode": "NGN",
            "contractCode": contract_code,
            "redirectUrl": callback_url,
            "paymentMethods": ["CARD", "ACCOUNT_TRANSFER", "USSD"],
        }

        response = requests.post(
            f"{base_url}/api/v1/merchant/transactions/init-transaction",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

        if not response.ok:
            print(f"Monnify initialize_payment failed ({response.status_code}): {response.text}", flush=True)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def verify_payment(reference):
        """
        Mirrors PaystackService.verify_payment(reference). Note Monnify
        verifies by transactionReference (returned from init, not the
        paymentReference you sent), so pass whichever reference your
        webhook/callback actually gives you.
        """
        base_url = current_app.config["MONNIFY_BASE_URL"]
        token = MonnifyService._get_access_token()

        response = requests.get(
            f"{base_url}/api/v2/transactions/{reference}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )

        if not response.ok:
            print(f"Monnify verify_payment failed ({response.status_code}): {response.text}", flush=True)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def verify_webhook_signature(raw_body, monnify_signature_header):
        """
        Verify a webhook POST genuinely came from Monnify before trusting
        its payload. Call in your webhook route:

            sig = request.headers.get("monnify-signature", "")
            if not MonnifyService.verify_webhook_signature(request.get_data(), sig):
                abort(401)
        """
        import hashlib
        import hmac

        secret_key = current_app.config["MONNIFY_SECRET_KEY"]
        computed = hmac.new(secret_key.encode(), raw_body, hashlib.sha512).hexdigest()
        return hmac.compare_digest(computed, monnify_signature_header or "")
