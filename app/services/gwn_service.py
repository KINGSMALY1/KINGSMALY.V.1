import json
import random
import string
import time
import hashlib
import requests

from flask import current_app


class GWNService:
    """
    Thin client for the Grandstream GWN.Cloud API.
    Only talks to Grandstream - no business logic, no DB writes.
    That lives in VoucherService / SyncService instead.
    """

    def __init__(self):
        self.base_url = current_app.config.get("GWN_CLOUD_BASE_URL") or "https://www.gwn.cloud"
        self.client_id = current_app.config["GWN_APP_ID"]
        self.client_secret = current_app.config["GWN_SECRET_KEY"]
        self.network_id = current_app.config["GWN_NETWORK_ID"]

        self.token = None
        self.token_expires_at = 0  # unix timestamp

    def login(self):
        """
        Authenticate with GWN.Cloud using the OAuth2 client_credentials
        flow. CONFIRMED against the live API on 2026-07-24:

            GET {base_url}/oauth/token
                ?grant_type=client_credentials
                &client_id={APP_ID}
                &client_secret={SECRET_KEY}
        """

        params = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.get(
            f"{self.base_url}/oauth/token",
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        self.token = data["access_token"]
        self.token_expires_at = time.time() + data.get("expires_in", 3599) - 60

        return self.token

    def _ensure_token(self):
        if self.token is None or time.time() >= self.token_expires_at:
            self.login()

    def _build_signature(self, timestamp, body_dict=None):
        """
        Signature scheme for GWN.Cloud's signed data endpoints (voucher,
        network, etc - everything under /oapi/v1.0.0/... other than the
        oauth/token endpoint itself, which doesn't need this).

        Verified against Grandstream's own documented worked example:
        the body-hash step reproduces their published result exactly.
        The full concatenation order (access_token, appID, secretKey,
        timestamp, then body hash) is taken directly from their
        "Step 5: Getting the Signature" documentation.
        """

        body_str = json.dumps(body_dict or {}, separators=(",", ":"))
        body_hash = hashlib.sha256(body_str.encode()).hexdigest()

        params_str = (
            f"access_token={self.token}"
            f"&appID={self.client_id}"
            f"&secretKey={self.client_secret}"
            f"&timestamp={timestamp}"
        )

        signature = hashlib.sha256(
            f"&{params_str}&{body_hash}&".encode()
        ).hexdigest()

        return signature, body_str

    def _signed_post(self, path, body_dict):
        """
        POST to a signed GWN.Cloud data endpoint, e.g. /voucher/save.
        """

        self._ensure_token()

        timestamp = int(time.time() * 1000)
        signature, body_str = self._build_signature(timestamp, body_dict)

        url = (
            f"{self.base_url}{path}"
            f"?access_token={self.token}"
            f"&appID={self.client_id}"
            f"&timestamp={timestamp}"
            f"&signature={signature}"
        )

        response = requests.post(
            url,
            data=body_str,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    def _signed_get(self, path, body_dict=None):
        """
        GET to a signed GWN.Cloud data endpoint, e.g. /voucher/list.
        Some GWN list endpoints still take a JSON body on a GET request
        (confirmed pattern from their network/list example) - requests
        supports this via the `data=` kwarg on a GET call.
        """

        self._ensure_token()

        timestamp = int(time.time() * 1000)
        signature, body_str = self._build_signature(timestamp, body_dict)

        url = (
            f"{self.base_url}{path}"
            f"?access_token={self.token}"
            f"&appID={self.client_id}"
            f"&timestamp={timestamp}"
            f"&signature={signature}"
        )

        response = requests.get(
            url,
            data=body_str,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    @staticmethod
    def generate_code():
        """
        Generates a human-friendly voucher code like KSM-4X7P-9Q2M.

        Excludes ambiguous characters (0/O, 1/I) so codes are easy to
        read and type over the phone or WhatsApp.
        """

        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0, O, 1, I

        def group(n):
            return "".join(random.choice(chars) for _ in range(n))

        return f"KSM-{group(4)}-{group(4)}"

    @staticmethod
    def _duration_breakdown(duration_minutes):
        """Splits total minutes into GWN's required {d, h, m} shape."""
        days, remainder = divmod(int(duration_minutes), 1440)
        hours, minutes = divmod(remainder, 60)
        return {"d": str(days), "h": str(hours), "m": str(minutes)}

    def create_voucher(self, payment, redemption_window_days=30):
        """
        Creates exactly ONE voucher (via GWN's "voucher group" endpoint,
        using voucherType=1 to specify our own code as the password,
        with voucherNum=1) tied to the plan's duration.

        redemption_window_days: how long the voucher stays valid for
        first use after purchase (separate from how long it LASTS once
        activated, which comes from the plan's duration_minutes).
        """

        code = self.generate_code()

        body = {
            "networkId": self.network_id,
            "name": payment.reference,
            "vocherNum": 1,          # sic - matches GWN's documented (misspelled) field name
            "deviceNum": payment.plan.duration_minutes and 1 or 1,
            "upRate": 0,
            "downRate": 0,
            "usageQuota": 0,
            "expiration": redemption_window_days,
            "effectDurationMap": self._duration_breakdown(payment.plan.duration_minutes),
            "description": f"Kingsmaly - {payment.plan.name}",
            "usageLimitType": 0,
            "voucherType": 1,        # 1 = customize voucher ID/password ourselves
            "passwords": [code],
        }

        result = self._signed_post("/oapi/v1.0.0/voucher/save", body)

        if result.get("retCode") != 0:
            raise RuntimeError(f"GWN voucher creation failed: {result}")

        return code

    def portal_pass(self, ap_mac, client_mac, ssid_name,
                    start_use_time=None, end_use_time=None):
        """
        "Allow client to connect SSID of AP" -
        POST /oapi/v1.0.0/portal/pass

        Authorizes one client device server-to-server, so we never have
        to submit a form to GWN's own splash page.

            mac             (required) the AP's MAC address
            client_mac      (required) the customer's device MAC
            ssid_name       (required) the WiFi SSID
            start_use_time  (optional) 13-digit ms timestamp
            end_use_time    (optional) 13-digit ms timestamp

        Uses the same HMAC signing as voucher/save.
        """

        body = {
            "networkId": self.network_id,
            "mac": ap_mac,
            "client_mac": client_mac,
            "ssid_name": ssid_name,
        }

        if start_use_time is not None:
            body["start_use_time"] = int(start_use_time)

        if end_use_time is not None:
            body["end_use_time"] = int(end_use_time)

        result = self._signed_post("/oapi/v1.0.0/portal/pass", body)

        if result.get("retCode") != 0:
            raise RuntimeError(f"GWN portal pass failed: {result}")

        return result

    def get_voucher_groups(self, network_id=None):
        """
        Lists voucher GROUPS for the configured network - CONFIRMED
        working against the live API. Note: this returns group-level
        stats (vocherNum, usedVoucherNum, availableVoucherNum), not
        individual voucher codes/status/MAC addresses.

        For per-code status (needed by SyncService), a separate
        "list vouchers within a group" endpoint is needed - not yet
        confirmed. See get_voucher_group_detail() below (unconfirmed).
        """

        body = {
            "networkId": network_id or self.network_id,
            "pageNum": 1,
            "pageSize": 100,
        }

        result = self._signed_post("/oapi/v1.0.0/voucher/list", body)

        if result.get("retCode") != 0:
            raise RuntimeError(f"GWN voucher list failed: {result}")

        return result.get("data", {}).get("result", [])

    def get_voucher_group_detail(self, group_id):
        """
        NOT YET CONFIRMED. Intended to list individual voucher codes
        (with status/MAC address) inside a specific voucher group, so
        SyncService can reconcile per-code status. Path/params below
        are a placeholder until the real endpoint is confirmed the same
        way voucher/save and voucher/list were - test in Colab first.
        """

        body = {
            "networkId": self.network_id,
            "id": group_id,
            "pageNum": 1,
            "pageSize": 1000,
        }

        result = self._signed_post("/oapi/v1.0.0/voucher/password/list", body)

        if result.get("retCode") != 0:
            raise RuntimeError(f"GWN voucher detail list failed: {result}")

        return result.get("data", {}).get("result", [])

    def find_voucher_group_id(self, reference):
        """
        GWN's voucher/save response doesn't return the group's internal
        id, so to delete/disable a voucher later we look it up by name
        (our payment reference) via voucher/list's search param.
        """

        body = {
            "networkId": self.network_id,
            "search": reference,
            "pageNum": 1,
            "pageSize": 5,
        }

        result = self._signed_post("/oapi/v1.0.0/voucher/list", body)

        if result.get("retCode") != 0:
            raise RuntimeError(f"GWN voucher search failed: {result}")

        matches = result.get("data", {}).get("result", [])

        for group in matches:
            if group.get("name") == reference:
                return group["id"]

        return None

    def delete_voucher_group(self, group_id):
        """
        Deletes a voucher group on the Grandstream side - CONFIRMED
        endpoint. Note: GWN blocks deleting a voucher that's currently
        in use (error 16024), so this only cleanly succeeds for unused
        vouchers - there's no separate "disable" endpoint in the API.
        """

        body = {
            "networkId": self.network_id,
            "groupIds": [group_id],
        }

        result = self._signed_post("/oapi/v1.0.0/voucher/delete", body)

        if result.get("retCode") == 16024:
            raise RuntimeError(
                "This voucher is currently in use and can't be removed "
                "from GWN while active."
            )

        if result.get("retCode") != 0:
            raise RuntimeError(f"GWN voucher delete failed: {result}")

        return result

    def disable_voucher(self, reference):
        """
        Kingsmaly's "disable" maps to GWN's delete, since there's no
        separate disable endpoint. Looks the group up by reference/name
        first, since voucher/save never returns the group id directly.
        """

        group_id = self.find_voucher_group_id(reference)

        if group_id is None:
            raise RuntimeError(
                f"No matching GWN voucher group found for '{reference}' - "
                "it may have already been removed, or was never created."
            )

        return self.delete_voucher_group(group_id)
