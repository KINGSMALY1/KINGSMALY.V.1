# Deploying Kingsmaly to Render (Free)

## 1. Push this project to GitHub

Render deploys from a GitHub repo, not a zip upload.

```
cd kingsmaly
git init
git add .
git commit -m "Initial deploy"
```

Create a new **empty** repo on github.com (don't add a README there),
then:

```
git remote add origin https://github.com/YOUR_USERNAME/kingsmaly.git
git branch -M main
git push -u origin main
```

Since `.env` is in `.gitignore`, it will NOT be pushed - good, that's
intentional. Your real secrets never touch GitHub.

## 2. Create a Render account

Go to render.com, sign up (GitHub login is easiest - it also makes step 3
faster since Render can see your repos directly).

## 3. Deploy using the Blueprint (render.yaml)

- In the Render dashboard: **New +** -> **Blueprint**
- Connect the `kingsmaly` GitHub repo
- Render reads `render.yaml` automatically and shows you a plan:
  one web service + one free PostgreSQL database
- Click **Apply**

This provisions everything, but the app will fail to start yet -
that's expected, because the real secrets (Paystack, GWN) are marked
`sync: false` and need to be entered manually next.

## 4. Add your real secrets in the Render dashboard

Go to your new **kingsmaly** web service -> **Environment** tab, and fill in:

| Key | Value |
|---|---|
| `PAYSTACK_SECRET_KEY` | Your Paystack secret key (start with the test key `sk_test_...`) |
| `GWN_APP_ID` | `667977` (or your current App ID) |
| `GWN_SECRET_KEY` | Your current GWN Secret Key (reset it once more before using here) |
| `GWN_NETWORK_ID` | `281663` (confirmed earlier) |
| `APP_BASE_URL` | Your live Render URL, e.g. `https://kingsmaly.onrender.com` (Render shows you this after first deploy - come back and set this once you know it) |

Save changes - Render will automatically redeploy with these in place.

## 5. Database tables + default admin are created automatically

Render's free tier doesn't include Shell access, so the app creates
its own tables and a default admin the moment it boots up - no manual
step needed here.

Go to your web service's **Logs** tab and look for a boot-up message
like:

```
CREATED DEFAULT ADMIN -> username: admin / password: xxxxxxxxxxxx
SAVE THIS PASSWORD NOW - it will not be shown again in logs.
```

**Copy that password immediately** - it only prints once, the first
time the tables are created. (If you'd rather choose your own
password instead of a random one, set `ADMIN_PASSWORD` as an
environment variable *before* first boot, and it'll use that instead.)

## 6. Point Paystack at your live app

Back in Paystack's dashboard (API Keys & Webhooks page):

- **Test Webhook URL**: `https://kingsmaly.onrender.com/api/webhook/paystack`
- **Test Callback URL**: `https://kingsmaly.onrender.com/payment/success`

(Replace with your actual Render URL if different.)

## 7. Test the full flow for real

- Visit `https://kingsmaly.onrender.com`
- Buy a plan with the test card (`4084 0840 8408 4081`, any future
  expiry, CVV `408`)
- Confirm: payment completes -> webhook fires -> a real voucher
  appears in GWN.Cloud -> the success page shows the code

## Notes / limitations to know about

- **Free tier sleeps after inactivity.** First request after idle time
  takes a few extra seconds to wake up - normal, not a bug.
- **Celery/Redis (scheduled sync + expiry tasks) are NOT included in
  this deploy.** Render's free tier doesn't include a free Redis
  instance or a background worker process. The web app and voucher
  creation work fully without it - only the automatic hourly sync and
  expiry tasks are affected. This can be added later on a paid tier,
  or you can trigger "Sync with GWN" manually from the admin panel for now.
- **Going live for real money**: switch `PAYSTACK_SECRET_KEY` to your
  **live** key (`sk_live_...`) only once you've fully tested with the
  test key, and update the webhook/callback URLs in Paystack's **Live
  Mode** settings too (they're configured separately from Test Mode).
