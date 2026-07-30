"""
Normalizes the query parameters a GWN AP appends when it bounces a
client's browser to our external splash page.

!!! UNCONFIRMED - VERIFY AGAINST A REAL DEVICE REDIRECT BEFORE GOING LIVE !!!

Grandstream's docs don't pin down the exact param names their captive
portal uses for the external-splash redirect, so we accept several
common spellings for each value. Once you capture a real redirect URL
from an AP, trim these lists down to the names actually used.

Assumed names (lowercased comparison), in priority order:

  client device MAC   -> client_mac, clientmac, client-mac, mac,
                         station_mac, stamac, staMAC, usermac
  AP MAC              -> ap_mac, apmac, ap, nasmac, nas_mac, apid, ap_id
  SSID                -> ssid_name, ssidname, ssid
  original URL        -> url, redirect, originurl, origin_url,
                         redirect_url, target_url, continue

Note the deliberate ordering conflict on "mac": some vendors use `mac`
for the CLIENT, others for the AP. We treat a bare `mac` as the CLIENT
mac only when no client_mac-style param is present, and as the AP mac
only when no ap_mac-style param is present AND a distinct client mac
was found. That ambiguity is exactly what needs confirming.
"""

CLIENT_MAC_KEYS = (
    "client_mac", "clientmac", "client-mac",
    "station_mac", "stamac", "usermac",
)

AP_MAC_KEYS = (
    "ap_mac", "apmac", "ap", "nasmac", "nas_mac", "apid", "ap_id",
)

SSID_KEYS = ("ssid_name", "ssidname", "ssid")

REDIRECT_KEYS = (
    "url", "redirect", "originurl", "origin_url",
    "redirect_url", "target_url", "continue",
)

AMBIGUOUS_MAC_KEYS = ("mac",)

# Everything we bother stashing in the session at first contact.
PORTAL_PARAM_KEYS = (
    CLIENT_MAC_KEYS
    + AP_MAC_KEYS
    + SSID_KEYS
    + REDIRECT_KEYS
    + AMBIGUOUS_MAC_KEYS
    + ("nasid", "vlanid")
)


def _first(params, keys):
    lowered = {k.lower(): v for k, v in params.items() if v}
    for key in keys:
        if lowered.get(key):
            return lowered[key]
    return None


def normalize_mac(value):
    """GWN's portal/pass expects a MAC - normalize to AA:BB:CC:DD:EE:FF."""
    if not value:
        return None

    hex_only = "".join(c for c in value if c.isalnum()).upper()

    if len(hex_only) != 12:
        return value.upper()

    return ":".join(hex_only[i:i + 2] for i in range(0, 12, 2))


def extract_portal_params(params):
    """
    Returns {client_mac, ap_mac, ssid_name, redirect_url} from a mapping
    of raw query params, using the (unconfirmed) name guesses above.
    """

    client_mac = _first(params, CLIENT_MAC_KEYS)
    ap_mac = _first(params, AP_MAC_KEYS)
    bare_mac = _first(params, AMBIGUOUS_MAC_KEYS)

    if bare_mac:
        # See module docstring: `mac` is ambiguous across vendors.
        if not client_mac:
            client_mac = bare_mac
        elif not ap_mac:
            ap_mac = bare_mac

    return {
        "client_mac": normalize_mac(client_mac),
        "ap_mac": normalize_mac(ap_mac),
        "ssid_name": _first(params, SSID_KEYS),
        "redirect_url": _first(params, REDIRECT_KEYS),
    }
