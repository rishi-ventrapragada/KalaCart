# Deploying the KalaCart backend on Render (free tier)

Written against the code and against Render's docs, 2026-09-12.

## Why Render, and what the free tier actually gives you

Railway's free tier no longer exists. Fly.io requires a card on file even
within its free allowance. Render's free plan is the remaining option that
needs no card.

| | Render free web service |
|---|---|
| Compute | 0.1 CPU, 512 MB RAM |
| Quota | **750 instance-hours per month, per workspace** |
| Idle behaviour | Spins down after **15 minutes** without inbound traffic |
| Cold start | **~1 minute** to spin back up |
| Filesystem | Ephemeral — wiped on every spin-down |
| Port | Render sets `PORT`; its default is `10000` |

## Why there is deliberately no keep-alive pinger

The obvious fix for a 1-minute cold start is to ping `/api/v1/health` every
10 minutes so the service never idles out. **Do not do this here.**

A calendar month is ~730 hours and the free grant is 750 instance-hours per
workspace. A service pinged awake 24/7 burns essentially the entire monthly
grant, and when the grant is exhausted Render suspends **every free service in
the workspace** until the next month. The keep-alive does not defeat the free
tier — it trades "the first request is slow" for "everything is down near
month-end", which is strictly worse.

Render does not prohibit pinging; the quota simply makes it self-defeating.

So: the service is allowed to sleep, and is warmed by hand before a demo.

### Warming it manually before a demo

Roughly **two minutes before** you present, send one request and wait for it:

```bash
curl -sS -o /dev/null -w '%{http_code} in %{time_total}s\n' \
  https://<service>.onrender.com/api/v1/health
```

The first call takes ~60s and that is expected — it is the spin-up. Repeat it;
the second should return `200` in well under a second. The service then stays
warm for 15 minutes after the last request, and each request resets that timer,
so an active demo keeps itself alive.

If you want partial coverage, an external pinger scheduled for working hours
only (~10 hrs/day ≈ 300 hrs/month) stays comfortably inside the 750-hour grant.
A 24/7 pinger does not.

## Configuration that is specific to Render

- `Dockerfile` — `ENV PORT=10000` and the healthcheck both follow Render's
  default port. The `CMD` binds `0.0.0.0:${PORT}`, so Render's injected value
  wins at runtime.
- `-w 1` gunicorn worker. At 0.1 CPU and 512 MB, more workers contend rather
  than parallelise, and `core/rate_limit.py` counts in process memory, so extra
  workers would each enforce a separate, wrong quota.
- `opencv-python-headless`. The GUI build pulls X11 libraries that are useless
  in a container and add hundreds of MB.
- Measured footprint: **~107 MB resident** for the app with OpenCV loaded, one
  worker. Comfortable inside 512 MB.

## Environment variables

`render.yaml` carries the non-sensitive ones and marks the four secrets
`sync: false`, so Render prompts for them and keeps them out of git.

Non-sensitive, already in `render.yaml`:

    APP_ENV=production
    DEBUG=false
    PORT=10000
    API_V1_PREFIX=/api/v1
    CORS_ORIGINS=http://localhost:3000,http://localhost:5173
    SECRET_KEY=<generateValue: true — Render generates it>

Secrets, set in the Render dashboard only:

    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
    SUPABASE_KEY
    OPENROUTER_API_KEY

### `DEBUG` must stay `false`

`core/security.py:_is_debug_mock_allowed()` returns true when `DEBUG=true` **or**
`APP_ENV != production`. In that state the backend decodes bearer tokens
*without verifying signatures* and fabricates user ids. On a public URL that is
an open door. Never set `DEBUG=true` on the deployed service to chase a bug —
reproduce locally instead.

Verified under the deploy env: `_is_debug_mock_allowed()` is `False`.

### Not required

- `SARVAM_API_KEY` — speech-to-text runs on-device in the Flutter app, which
  sends a text transcript. `POST /api/v1/catalog/voice` stays mounted and
  returns a clear error while this is unset. Setting a real key re-enables the
  audio-upload path with no code change.
- Firebase credentials — the app authenticates with Supabase Auth, and
  `get_current_user` tries Supabase first. Firebase init failing only logs.
- `REDIS_URL` — `core/redis.py` falls back to an in-memory cache.

## CORS

CORS is a browser policy. The Flutter app sends no `Origin` header and is
unaffected by `CORS_ORIGINS`; the list matters only for the React web admin.
Note `main.py` strips a wildcard `*` in production by design — do not try to
work around it for the mobile app, which does not need it.

Both formats parse (`app/core/config.py`, `CORS_ORIGINS` property):

    CORS_ORIGINS=https://a.com,https://b.com
    CORS_ORIGINS=["https://a.com","https://b.com"]

The field is held as a `str` and split in a property because pydantic-settings
JSON-decodes `List[str]` env vars *before* field validators run — the previously
documented comma-separated form raised `SettingsError` and crashed startup.

## Verification gates

1. **Health from a phone on mobile data** — not office Wi-Fi, so it proves the
   URL is genuinely public:

       https://<service>.onrender.com/api/v1/health

2. **A real Supabase JWT authenticates against a protected endpoint** — sign in
   from the app, take the access token, and call a `get_current_user` route:

       curl -H "Authorization: Bearer <supabase access token>" \
         https://<service>.onrender.com/api/v1/products/my

   A `200` proves JWKS verification works end to end. A `401` with
   "Invalid access token" means the token or `SUPABASE_URL` is wrong; a `503`
   means the signing keys were unreachable.
