# Kingsmaly Starlink Network

WiFi hotspot captive-portal billing system. Customers pick a plan, pay
with Paystack, and receive a voucher code to log into the network.
Vouchers are provisioned automatically through Grandstream GWN.Cloud.

## Stack
- Python / Flask
- PostgreSQL (Render) / SQLite (local dev)
- Paystack for payments
- GWN.Cloud API for voucher/network integration

## Local development
```
pip install -r requirements.txt
cp .env.example .env   # then fill in real values
python run.py
```

## Deployment (Render)
See `render.yaml` — deploys as a Blueprint with a free Postgres
database attached. Tables and a default admin user are created
automatically on first boot (check the Logs tab for the generated
admin password). Required environment variables are listed in
`.env.example`; the ones marked `sync: false` in `render.yaml` must be
set manually in Render's dashboard (Settings → Environment):

- `APP_BASE_URL` — your live Render URL, e.g. `https://kingsmaly.onrender.com`
  (must NOT be `localhost` — Paystack rejects it as an invalid callback URL)
- `PAYSTACK_SECRET_KEY`
- `GWN_APP_ID`, `GWN_SECRET_KEY`, `GWN_NETWORK_ID`, `GWN_PORTAL_AUTH_URL`

## Admin panel
`/admin` — manage plans, vouchers, and settings.
