# KalaCart — artisan app

**Photograph a handicraft, describe it out loud, get a sellable listing.**

KalaCart is a marketplace that connects rural Indian artisans to retail and B2B buyers. The hard
part for an artisan is not selling — it is *listing*: writing product copy in English, photographing
a craft well enough to compete with studio shots, and guessing a price that is neither self-defeating
nor unsellable.

This repository is the **artisan-facing mobile app** plus the AI backend that serves it. The artisan
points a camera at the craft and speaks a sentence in their own language. The app returns an
enhanced photo, a written listing, and a price with its reasoning shown.

Built for SIH 2026.

---

## What this app does

Three features, all running against a live backend — not mocked.

### Camera-based cataloguing
Capture or pick a photo, and the app downscales and uploads it for processing. Photos go to Supabase
Storage under the artisan's own identity, so storage permissions apply to the upload.

### AI photo enhancement
The backend removes the background with OpenCV GrabCut, applies CLAHE contrast correction, composes
the subject onto white, then crops and resizes to a marketplace-ready ratio. A dim phone photo taken
on a workshop floor comes back looking like catalogue work.

Notably this path uses **no LLM at all** — it is deterministic computer vision, which makes it fast,
free to run, and immune to model rate limits.

### Multilingual voice-to-listing
The artisan speaks a description. Speech-to-text runs **on the device**, and only the resulting text
goes to the server, which turns it into a structured listing — title, description, category, tags,
and a Hindi description alongside the English one.

Supported for generation: Hindi, English, Telugu, Tamil, Kannada.

### AI pricing suggestions
The app returns a suggested INR price with the full breakdown behind it — materials, labour, skill
band, market position — so the artisan can see *why* and argue with it, rather than being handed a
number to accept on faith.

The price itself is **computed deterministically**, not guessed by a language model. When the artisan
supplies category, size, quality and complexity, the AI step is skipped entirely: the result is
instant and reproducible.

---

## How this fits with the website

KalaCart is two repositories sharing **one live Supabase database**.

| Repository | What it is | Who uses it |
|---|---|---|
| **KalaCart-App** (this one) | Flutter mobile app | Artisans listing products; buyers browsing |
| **KalaCart-Website** | React web admin | Ministry administrators reviewing submissions |

They are not independent products with a sync job between them. They read and write the same
PostgreSQL tables in the same Supabase project, so a write from one is immediately visible to the
other.

**The intended flow:**

```
Artisan lists a product in this app
        │
        ▼
  products.status = 'pending'        ← awaiting review
        │
        ▼
Ministry admin opens the website's Verification Queue
        │
        ├── approves ──▶ status = 'approved' ──▶ visible to buyers in this app
        └── rejects  ──▶ status = 'rejected' ──▶ never shown
```

The mechanism that keeps the two sides honest is a **database trigger, `sync_product_status`**, which
lives on the `products` table in Supabase rather than in either codebase. Because it sits in the
database, neither the app nor the website can bypass it by writing a different value — the rule is
enforced in one place for both clients.

The app's buyer-facing queries filter on `status = 'approved'`, so an unreviewed listing does not
reach buyers through this client. See *Known limitations* for where this chain is currently
incomplete.

---

## Tech stack

**Client — Flutter (Dart)**

Riverpod for state, go_router for navigation, `supabase_flutter` for data and auth, `dio` for backend
calls, `image_picker` and `speech_to_text` for capture. No code generation anywhere — no `freezed`,
no `build_runner`, no `.g.dart` files.

**Backend — FastAPI (Python 3.11)**

Deployed at `https://kalacart-api.onrender.com`, in Docker on Render's free tier. OpenCV and Pillow
handle image work; OpenRouter fronts the language models. Requests carry the caller's Supabase access
token, which the backend verifies against the project JWKS (signature, expiry, audience and issuer
all pinned) and resolves to a user.

**Data — Supabase**

PostgreSQL with row-level security, GoTrue auth, PostgREST, Realtime for chat, and Storage for
images. RLS is the security boundary, which is why the client ships a publishable key safely.

### AI models — and why they are all free-tier

**Free-tier was a hard constraint, not a preference.** This is a student project targeting rural
artisans; a per-listing inference cost that scales with adoption would make the product
undeployable for exactly the users it exists to serve. Every model is therefore pinned to a `:free`
slug, and measured spend to date is zero.

| Use | Model |
|---|---|
| Listing generation from voice | `nex-agi/nex-n2.5-pro:free` |
| Pricing and vision extraction | `google/gemma-4-31b-it:free` |
| Photo enhancement | *None* — OpenCV, no LLM |

That constraint shaped the architecture rather than just the config. The pricing engine computes
prices arithmetically instead of asking a model, and enhancement is pure computer vision — so the two
paths that run most often cost nothing and cannot be rate-limited upstream. Only listing generation
actually calls a language model.

It also costs something real: free model pools are shared and occasionally exhausted. The catalog
model was switched to `nex-n2.5-pro` precisely because the previous free slug's upstream pool ran
dry. Speech-to-text moved on-device for the same reason — the hosted option was paid.

---

## Setup

### Prerequisites
- Flutter SDK 3.3+ with the Dart SDK it bundles
- Android Studio or the Android SDK with a device or emulator
- Python 3.11 (only if running the backend locally — the deployed one works out of the box)

### Run the app

```bash
cd app
flutter pub get
flutter run
```

The app points at the deployed backend by default, so no backend setup is needed to run it.

### Build an APK

```bash
cd app
flutter build apk --debug      # development build
flutter build apk --release    # release build, ~58 MB
```

Output lands in `app/build/app/outputs/flutter-apk/`.

### Verify

```bash
cd app
flutter analyze    # expect: No issues found!
flutter test
```

### Configuration

No environment variables are needed for the client. The Supabase URL and publishable key are
compiled into `app/lib/core/config/supabase_config.dart` — the publishable key carries no privileges
of its own and RLS is the boundary, so shipping it is intended.

To change the backend the app talks to, edit `kApiBaseUrl` in
[api_client.dart](app/lib/core/network/api_client.dart).

### Running the backend locally (optional)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # then fill in the values below
uvicorn app.main:app --reload
```

Required in `backend/.env` — all four are secrets and none belongs in git:

| Variable | What it is |
|---|---|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service-role key for privileged reads |
| `SUPABASE_KEY` | Publishable key |
| `OPENROUTER_API_KEY` | OpenRouter key (a free account is sufficient) |

Set `APP_ENV=production` and `DEBUG=false` unless you specifically need the development path — see
the last item under *Known limitations* for why that matters.

---

## Current status

The three headline features work end to end against the deployed backend. Verified 2026-09-12:
`flutter analyze` clean across the tree, tests passing, debug and release APKs both building, and
the live backend answering `/health` in 0.75 s.

Auth, onboarding, the product catalogue, browse and search, cart and checkout, B2B enquiries and
realtime buyer–seller chat are all working against Supabase.

## Known limitations

Stated plainly, because a reviewer will find these anyway:

- **Android only.** iOS is configured in the project but has never been built — CocoaPods has not
  been run — so cross-platform support is unproven rather than shipped.

- **The APK is signed with the debug keystore**, so it installs for testing but is not distributable
  through a store.

- **First request of a session takes ~44 seconds.** Render's free tier sleeps the instance after
  ~15 minutes idle. The app handles this deliberately — a 120-second timeout and a "Waking the
  server…" message rather than a spinner that looks like a hang — but the wait is real. Subsequent
  calls return in under a second. Rapid bursts against the 512 MB instance can also briefly return
  502s; spacing calls ~20 s apart is reliable.

- **The moderation gate is not fully closed.** A product published from the app currently reaches
  buyers without passing admin approval, because a server-side trigger rewrites `pending` to
  `approved` on insert. The client writes the correct status values and buyer queries correctly
  filter on `approved`, but until that database-side behaviour is changed the review step is not
  actually enforced. Known and tracked.

- **The backend contains a development auth-bypass path** that permits unverified token decoding.
  It is disabled in the deployed instance by `APP_ENV=production`, but the code path has not been
  removed. Tracked as the highest-priority open item.

- **Voice language coverage depends on the device.** Speech-to-text runs on-device, so available
  languages vary by handset rather than being guaranteed by the app.

- **Two listing flows coexist.** The AI Studio runs against the live backend; the older Catalog
  Studio beside it still uses mock data, and the product-creation wizard still takes pasted image
  URLs. Reconciling them is the next piece of work.

- **Test coverage is thin.** The client has one widget test; the backend's suite has no pytest
  configuration, so its async tests likely do not execute. Treat the suites as unbaselined.

Engineering conventions are in [CLAUDE.md](CLAUDE.md), current build status and the full open-items
list in [PRD.md](PRD.md), and architectural decisions in
[memory/decisions.md](memory/decisions.md).
