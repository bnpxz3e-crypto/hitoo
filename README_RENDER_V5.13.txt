JOYPOP Local V5.13 - Render test build

1) Upload all files/folders in this ZIP to a GitHub repository.
2) In Render create New > Web Service and connect that repository.
3) Render should detect render.yaml. If entering manually:
   Build Command: (leave blank)
   Start Command: python server_v5_13.py
4) After deploy, open the Render URL.
5) Rate Admin: https://YOUR-APP.onrender.com/rate-admin

Notes:
- This is a local/mock frontend. Real JOYPOP login, payment and purchase APIs remain blocked.
- card_rates.json is local runtime state. On Render free/ephemeral storage it can reset after restart/redeploy.
- V5.13 primarily makes V5.12 cloud-deployable; it does not claim to fix every remaining Collection/pool mismatch.
