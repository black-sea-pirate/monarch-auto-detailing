# Monarch Auto Interior Detailing

Nuxt 4 / Vue 3 website with a FastAPI quote intake, PostgreSQL persistence,
private temporary uploads, Telegram delivery, Nginx routing, and an optional
Cloudflare Tunnel.

## Local Docker stack

Requirements: Docker Desktop with the Linux container engine enabled.

```powershell
docker compose up -d --build
docker compose ps
```

Open `http://127.0.0.1:3000`. Nginx is the only service published to the host;
FastAPI and PostgreSQL remain on private Docker networks.

Useful commands:

```powershell
docker compose logs -f
docker compose down
docker compose down --volumes  # also removes the local database and temporary uploads
```

Do not use `--volumes` unless losing local test data is intentional.

## Telegram intake

Never commit or paste the bot token into chat. A local root `.env` has already been
created and ignored by Git; put the replacement token directly in that file.

1. Send `/start` to the bot from the Telegram account that should receive requests.
2. Set `TELEGRAM_BOT_TOKEN` in `.env` and restart the API:

   ```powershell
   docker compose up -d --force-recreate api
   docker compose exec api python -m app.telegram_chat_id
   ```

3. Copy the numeric id printed by the command into `TELEGRAM_CHAT_ID` in `.env`.
4. Set a long random `TELEGRAM_WEBHOOK_SECRET` containing only letters, numbers,
   underscores, and hyphens.
5. Once a public HTTPS tunnel exists, set its complete callback address:

   ```dotenv
   TELEGRAM_WEBHOOK_URL=https://monarch-yyc.com/api/v1/telegram/webhook
   ```

6. Recreate the API to register the Telegram webhook:

   ```powershell
   docker compose up -d --force-recreate api
   ```

The bot receives a formatted summary followed by original media. JPEG, PNG, and
WebP images up to Telegram's photo limit are grouped as albums; larger images and
HEIC files are sent as documents without recompression. Pressing `✅ Принял`
deletes the private server files and clears customer details from PostgreSQL.
Unaccepted and abandoned requests are purged after seven days by default.

## Upload design

The browser first creates a protected draft, uploads each original file in a
separate request, and finalizes the draft only after every upload succeeds. Limits:

- 15 photos;
- 2 videos;
- 50 MB per file;
- 500 MB per request in total.

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
python -m app.init_db
uvicorn app.main:app --reload
```
