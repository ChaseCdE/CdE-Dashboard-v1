# Sharing the CdE Dashboard Externally

## Quick Start

```bash
# 1. Set credentials in .env (copy from .env.example if needed)
cp .env.example .env   # then edit .env with your credentials

# 2. Install dependencies (one-time)
pip install uvicorn

# 3. Start the authenticated dashboard
python serve.py

# 4. In a second terminal, start a tunnel (pick one):
ngrok http 8000                                    # Option A
cloudflared tunnel --url http://localhost:8000      # Option B
```

Share the public URL from the tunnel output with your team. They'll be prompted for the username/password you set in `.env`.

---

## Tunnel Options Compared

| Feature | ngrok (free) | ngrok (paid, $8/mo) | Cloudflare Tunnel (free) |
|---------|-------------|---------------------|--------------------------|
| Stable URL | No (changes on restart) | Yes (static domain) | No* |
| Auth built-in | No | Yes | Via Cloudflare Access |
| Setup complexity | Minimal | Minimal | Slightly more |
| Connection limit | 40/min | Higher | None |
| Best for | Quick demos | Ongoing small-team use | Ongoing use with own domain |

*Cloudflare quick tunnels (`cloudflared tunnel --url`) generate random URLs. For a stable subdomain, set up a named tunnel with a Cloudflare account and your own domain.

---

## Option A: ngrok

### Install
- **macOS**: `brew install ngrok`
- **Windows**: `choco install ngrok` or download from https://ngrok.com/download
- Sign up at https://ngrok.com and run `ngrok config add-authtoken <YOUR_TOKEN>`

### Run
```bash
ngrok http 8000
```

The terminal will show a public URL like `https://abc123.ngrok-free.app`. Share that URL.

### For a stable URL (paid plan)
```bash
ngrok http 8000 --domain=your-reserved-domain.ngrok-free.app
```

---

## Option B: Cloudflare Tunnel (recommended for ongoing use)

### Install
- **macOS**: `brew install cloudflared`
- **Windows**: download from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

### Quick tunnel (random URL, no account needed)
```bash
cloudflared tunnel --url http://localhost:8000
```

### Named tunnel (stable URL, requires free Cloudflare account + domain)
```bash
# One-time setup
cloudflared tunnel login
cloudflared tunnel create cde-dashboard
cloudflared tunnel route dns cde-dashboard dashboard.yourdomain.com

# Run
cloudflared tunnel run --url http://localhost:8000 cde-dashboard
```

---

## Authentication

The dashboard uses HTTP Basic Auth, configured via environment variables:

| Variable | Description |
|----------|-------------|
| `DASHBOARD_USER` | Username for login |
| `DASHBOARD_PASS` | Password for login |

Set these in the `.env` file at the project root (never commit this file).

To disable auth for local development:
```bash
python serve.py --no-auth
```

---

## Recommendations by Use Case

**"I just need to show this to 3 colleagues this week"**
→ ngrok free tier + app-level basic auth. Done in 2 minutes.

**"The team needs regular access over the coming months"**
→ Cloudflare named tunnel (free) or ngrok paid ($8/mo) for a stable URL. Both work well with 2-5 users.

**"We want this always available without my laptop running"**
→ Deploy to a small VPS (Hetzner €4/mo, DigitalOcean $6/mo). Run `serve.py` behind a reverse proxy (Caddy or nginx) with a real domain and TLS.
