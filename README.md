# Monarch Auto Interior Detailing

Nuxt 4 / Vue 3 website with a FastAPI quote intake, PostgreSQL persistence,
private temporary uploads, a protected admin inbox, minimal Telegram notifications,
Nginx routing, and an optional Cloudflare Tunnel.

## Local Docker stack

Requirements: Docker Desktop with the Linux container engine enabled.

```powershell
docker compose up -d --build
docker compose ps
```

Open `http://127.0.0.1:3000`. Nginx is the only service published to the host;
FastAPI and PostgreSQL remain on private Docker networks.

For the local admin, set the same non-empty test value in `ADMIN_DEV_TOKEN` and
`NUXT_PUBLIC_ADMIN_DEV_TOKEN` inside the ignored root `.env`, rebuild the stack,
then open `http://admin.localhost:3000/admin`. These values must stay blank in
production.

Useful commands:

```powershell
docker compose logs -f
docker compose down
docker compose down --volumes  # also removes the local database and temporary uploads
```

Do not use `--volumes` unless losing local test data is intentional.

## Telegram notifications

Never commit or paste the bot token into chat. A local root `.env` has already been
created and ignored by Git; put the replacement token directly in that file.

1. Send `/start` to the bot from the Telegram account that should receive requests.
2. Set `TELEGRAM_BOT_TOKEN` in `.env` and restart the API:

   ```powershell
   docker compose up -d --force-recreate api
   docker compose exec api python -m app.telegram_chat_id
   ```

3. Copy the numeric id printed by the command into `TELEGRAM_CHAT_ID` in `.env`.
4. Recreate the API:

   ```powershell
   docker compose up -d --force-recreate api
   ```

The bot receives only a request number, vehicle category, broad area, service names,
and a link to the protected admin inbox. Names, contact details, descriptions, photos,
and videos are never sent to Telegram. Notification retries are persisted in PostgreSQL.

## Protected admin inbox

Production admin access uses a dedicated hostname protected by Cloudflare Access.
The API validates the Access JWT as well as the permitted email allowlist; hiding the
page at Nginx alone is not treated as authentication.

Required private environment variables:

```dotenv
ADMIN_BASE_URL=https://admin.example.com
ADMIN_ALLOWED_EMAILS=["owner@example.com"]
CLOUDFLARE_ACCESS_TEAM_DOMAIN=example.cloudflareaccess.com
CLOUDFLARE_ACCESS_AUD=replace-with-the-access-application-audience
```

The inbox has only three workflow states: `new`, `viewed`, and `accepted`. Opening a
request marks it viewed. Accepting it confirms that the conversation has moved to the
customer's chosen contact channel and schedules personal data and media for deletion
after 30 days. Unhandled requests are retained for at most 90 days. Manual deletion is
immediate and leaves only a non-identifying audit tombstone.

The `Website` tab manages public prices and discounts, homepage section visibility,
and portfolio photos. Portfolio media uses its own persistent volume and is not mixed
with temporary customer quote uploads. Uploaded photos are normalized to JPEG, resized,
and stripped of metadata.

## Upload design

The browser first creates a protected draft, uploads each file in a
separate request, and finalizes the draft only after every upload succeeds. Limits:

- 10 photos;
- 2 videos;
- 12 MB per photo;
- 50 MB per video;
- 150 MB per request in total.

Photos are normalized to JPEG, resized to a maximum 2560-pixel dimension, and saved
without EXIF metadata before they become visible in the admin inbox.

Separate uploads keep every HTTP request below Cloudflare's 100 MB Free-plan limit.

## Cloudflare Tunnel

For a temporary public URL that can be opened from a phone, run:

```powershell
docker compose --profile quick-tunnel up -d cloudflared-quick
docker compose logs cloudflared-quick
```

The generated `trycloudflare.com` address is public, intended only for testing,
and changes whenever the quick-tunnel container is recreated. Stop it with:

```powershell
docker compose --profile quick-tunnel stop cloudflared-quick
```

For a stable `monarch-yyc.com` address, the `cloudflared` container uses a named
tunnel. After creating that tunnel in
the Cloudflare dashboard, set `CLOUDFLARE_TUNNEL_TOKEN` in `.env`, configure its
public hostname to use `http://nginx:80`, and start the profile:

```powershell
docker compose --profile tunnel up -d
```

The same profile can be used later on an Ubuntu VPS. HTTPS terminates at Cloudflare;
no public API or database port is required.

## Production deployment

Production runs from `/opt/monarch` on Ubuntu with Docker Compose. The local
`.env` file is copied to that directory separately, remains ignored by Git, and
must have permissions `600`.

Every push to `main` is checked by GitHub Actions. Only after the API tests,
Python lint, frontend type-check, and frontend production build succeed is the
same commit fast-forwarded to the `production` branch. The Lightsail server
checks that branch every five minutes.

Install the poller on the server after the repository and `.env` exist:

```bash
sudo install -m 0755 infra/deploy/monarch-deploy.sh /usr/local/sbin/monarch-deploy
sudo install -m 0644 infra/systemd/monarch-deploy.service /etc/systemd/system/
sudo install -m 0644 infra/systemd/monarch-deploy.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now monarch-deploy.timer
```

Inspect deployment status with:

```bash
systemctl status monarch-deploy.timer
journalctl -u monarch-deploy.service -n 100 --no-pager
```

The deployer builds in place, preserves the PostgreSQL and upload volumes,
checks `/api/v1/ready`, and rebuilds the previous commit if the new version
does not become healthy.

## Direct development without Docker

Frontend:

```powershell
cd web
npm install
Copy-Item .env.example .env
# In web/.env set NUXT_PUBLIC_API_BASE=http://127.0.0.1:8000
npm run dev
```

Backend (requires a reachable PostgreSQL database):

```powershell
cd api
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m app.migrate
uvicorn app.main:app --reload
```
