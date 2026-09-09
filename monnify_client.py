"""
monnify_client.py

Monnify payment gateway integration for the Kingsmaly hotspot billing app.
Replaces the previous Paystack integration.

Required environment variables (already set on Render):
    MONNIFY_API_KEY
    MONNIFY_SECRET_KEY
    MONNIFY_CONTRACT_CODE
    MONNIFY_BASE_URL      e.g. https://sandbox.monnify.com (sandbox)
                                https://api.monnify.com     (live)

Usage:
    from monnify_client import init_transaction, verify_transaction, verify_webhook_signature

    result = init_transaction(
        amount=500,
        customer_email="user@example.com",
        customer_name="John Doe",
        payment_reference="KM-20260909-0001",
        payment_description="1 Day Voucher",
    )
    checkout_url = result["responseBody"]["checkoutUrl"]
"""

import base64
import hashlib
import hmac
import os
import time

import requests

MONNIFY_API_KEY = os.environ["MONNIFY_API_KEY"]
MONNIFY_SECRET_KEY = os.environ["MONNIFY_SECRET_KEY"]
MONNIFY_CONTRACT_CODE = os.environ["MONNIFY_CONTRACT_CODE"]
MONNIFY_BASE_URL = os.environ["MONNIFY_BASE_URL"].rstrip("/")

# In-memory token cache. Fine for a single Render web worker;
# if you scale to multiple workers, move this to Redis/DB instead.
_token_cache = {"access_token": None, "expires_at": 0}


class MonnifyError(Exception):
    """Raised when Monnify returns a non-success response."""
    pass


def _get_access_token() -> str:
    """
    Fetch (and cache) a Monnify bearer token.
    Tokens are valid for 1 hour; we refresh 60s early to be safe.
    """
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    credentials = f"{MONNIFY_API_KEY}:{MONNIFY_SECRET_KEY}"
    encoded = base64.b64encode(credentials.encode()).decode()

    resp = requests.post(
        f"{MONNIFY_BASE_URL}/api/v1/auth/login",
        headers={"Authorization": f"Basic {encoded}"},
        timeout=15,
    )
    data = resp.json()

    if not resp.ok or not data.get("requestSuccessful"):
        raise MonnifyError(f"Monnify auth failed: {data}")

    token = data["responseBody"]["accessToken"]
    # expiresIn is in seconds; Monnify usually returns 3600
    expires_in = data["responseBody"].get("expiresIn", 3600)

    _token_cache["access_token"] = token
    _token_cache["expires_at"] = now + expires_in - 60

    return token


def init_transaction(
    amount: float,
    customer_email: str,
    payment_reference: str,
    payment_description: str,
    customer_name: str = "Kingsmaly Customer",
    currency_code: str = "NGN",
    payment_methods: list | None = None,
    redirect_url: str | None = None,
) -> dict:
    """
    Initialize a Monnify transaction. Returns the full parsed JSON response.
    Send the user to result["responseBody"]["checkoutUrl"] to complete payment,
    or embed result["responseBody"]["transactionReference"] into the Monnify
    inline JS SDK if you'd rather show a modal instead of redirecting.
    """
    token = _get_access_token()

    payload = {
        "amount": amount,
        "customerName": customer_name,
        "customerEmail": customer_email,
        "paymentReference": payment_reference,
        "paymentDescription": payment_description,
        "currencyCode": currency_code,
        "contractCode": MONNIFY_CONTRACT_CODE,
        "paymentMethods": payment_methods or ["CARD", "ACCOUNT_TRANSFER", "USSD"],
    }
    if redirect_url:
        payload["redirectUrl"] = redirect_url

    resp = requests.post(
        f"{MONNIFY_BASE_URL}/api/v1/merchant/transactions/init-transaction",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=15,
    )
    data = resp.json()

    if not resp.ok or not data.get("requestSuccessful"):
        raise MonnifyError(f"Monnify init-transaction failed: {data}")

    return data


def verify_transaction(transaction_reference: str) -> dict:
    """
    Verify a transaction's current status directly with Monnify.
    Use this as a backup check even after receiving a webhook.
    """
    token = _get_access_token()

    resp = requests.get(
        f"{MONNIFY_BASE_URL}/api/v2/transactions/{transaction_reference}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )
    data = resp.json()

    if not resp.ok or not data.get("requestSuccessful"):
        raise MonnifyError(f"Monnify verify-transaction failed: {data}")

    return data


def verify_webhook_signature(raw_body: bytes, monnify_signature_header: str) -> bool:
    """
    Verify that a webhook POST genuinely came from Monnify.

    Monnify signs the raw request body with your secret key using SHA512
    HMAC and sends it in the 'monnify-signature' header. Always verify
    this before trusting a webhook payload.

    Usage in your Flask route:
        signature = request.headers.get("monnify-signature", "")
        if not verify_webhook_signature(request.get_data(), signature):
            abort(401)
    """
    computed = hmac.new(
        MONNIFY_SECRET_KEY.encode(),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(computed, monnify_signature_header)
