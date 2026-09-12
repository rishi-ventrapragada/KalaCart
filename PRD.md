# KalaCart — product requirements and build status

Rewritten 2026-09-12 against the code in this repository at commit `5a6349c`. Status labels come
from running code paths, not from documents. For engineering rules see `CLAUDE.md`; for decisions
see `memory/decisions.md`.

This replaces the 2026-09-11 version, which described the Java/Android client that the consolidation
dropped. Sections touching the backend wiring were **verified by running the code on 2026-09-12**
(`flutter analyze`, `flutter test`, both APK builds, and live calls to the deployed backend); the
rest is still read from source. See §7 for exactly which is which.

## 1. Vision

KalaCart lets rural Indian artisans photograph a handicraft, describe it in their own language, and
get a sellable listing — enhanced photo, bilingual description, fair price — which is then sold to
retail and B2B buyers. Target competition: SIH 2026.

The three product promises, in priority order:

1. **Zero-barrier listing** — a spoken or typed description in an Indian language plus one photo
   produces a complete listing. The artisan edits, does not author.
2. **Fair, transparent pricing** — a suggested INR price with a material/labour/skill breakdown the
   artisan can read.
3. **Trusted marketplace** — sellers are verified and listings are trustworthy.

Promise 3 is where the current architecture is internally inconsistent; see §3.

## 2. Users and roles

| Role | Where they act | Identity in the data |
|---|---|---|
| **Seller / artisan** | Flutter app | `profiles.role = 'seller'` + a `sellers` row; products carry `sellers.id` |
| **Buyer** | Flutter app | `profiles.role = 'buyer'`; onboarded once the profile has a name and city |
| **Ministry admin / moderator** | **Nowhere. No surface exists in this repository.** | — |

The admin role has no UI, no API client, and no code path in this tree. The React admin site
described by older documents lives only in the archived repository; there is no `web/` directory
here (`git ls-files` tracks `app/`, `backend/`, `memory/` and the two governance files). Building it
is unstarted greenfield work, not a prototype to finish.

## 3. Where the product actually stands

**The backend auth gap is closed.** `backend/app/core/supabase_auth.py` verifies Supabase access
tokens against the project JWKS with signature, expiry, audience and issuer pinning (`:71-79`) and
resolves users via `profiles.auth_user_id` (`:96-111`). The old top-priority item — a backend that
could only understand Firebase tokens — is resolved.

**Two gaps replaced it. The first is now closed; the second still stands.**

**(a) The client now calls the backend — closed 2026-09-12.** All three AI features run against the
deployed FastAPI instance from `AiStudioScreen`, reached at `/ai-studio` from both the buyer and
seller shells. `dio` carries the calls and the caller's Supabase access token
(`app/lib/core/network/api_client.dart`), and `BackendAiRepository` covers `/image/enhance`,
`/pricing/analyze` and `/catalog/generate`. Verified 2026-09-12: `flutter analyze` clean,
`flutter test` passing, debug and release APKs built, `/health` 200 in 0.75 s. Promises 1 and 2 in
§1 are delivered through this screen.

Two caveats, both properties of the free tier rather than of the code. The first call of a session
pays a Render cold start measured at **43.9 s**, which the client absorbs with a 120 s timeout and
a "Waking the server" banner. And four catalog calls issued ~2 s apart made the 512 MB single-worker
instance return Render's own HTML 502 for ~60 s before recovering unprompted; at 20 s spacing it is
clean (D-17).

**(b) The AI the artisan can actually touch is entirely mocked — and it writes real rows.** All
seven providers in `app/lib/features/ai/data/ai_providers.dart:5-35` return `Mock*` implementations;
there is no non-mock implementation in the client. The Catalog Studio — the flagship
photo-to-listing flow — is `MockCatalogStudioRepository`
(`features/catalog_studio/data/catalog_studio_repository.dart:16`), seeded with three fake images
pointing at `assets/mock/pottery_*.jpg` (`:24-41`) and a list of hard-coded presets (`:45`). Its
publish button calls the real repository: `createProduct(...)` at
`features/catalog_studio/presentation/catalog_studio_screen.dart:1088`. **Fabricated AI output lands
in the live Supabase catalogue as a genuine product row.** Nothing in the Dart code marks any of
this as temporary — a grep for `TODO`/`FIXME`/`HACK` across `app/lib` returns zero hits.

Consequence: promises 1 and 2 in §1 **are** delivered, but only through `AiStudioScreen` (§3a). The
older Catalog Studio beside it is still the mock described above and still writes real rows, so the
two flows now disagree about what "AI" means in this app. Reconciling them — pointing Catalog Studio
at `BackendAiRepository`, or retiring it — is the obvious next piece of work and is item 10.

### The moderation conflict — unresolved, needs a decision

**The client has no ministry-approval gate.** `ProductStatus` is `{published, draft, archived}`
(`app/lib/shared/models/product.dart:16-27`); `ProductInput` defaults `status` to **`published`**
(`:199`); sellers self-publish directly from both the wizard and the Catalog Studio; and the app
writes `is_active` itself (`:214`, `supabase_products_repository.dart:87`) rather than leaving it to
a database trigger. Buyer-visible means `is_active = true AND status = 'published'`
(`supabase_products_repository.dart:20-24`) — a filter the seller alone controls.

**This contradicts the website's entire model.** The admin-verification flow, the moderation queue,
and the provenance code issued on approval all presuppose a `pending` → `approved` transition owned
by a ministry moderator, which no longer exists on the client side. The app already derives a
passport code locally and unconditionally from the product id
(`Product.passportCode`, `product.dart:103`) — so a provenance code is minted for every listing at
creation, with no verification behind it.

It also contradicts the decision log: **D-10** ("every listing inserts as `status = 'pending'`; only
the ministry admin moves it on") and **D-12** ("buyer-visible is `status = 'approved' AND is_active =
true`; `is_active` is trigger-owned") describe the archived Android behaviour.

This is a **cross-component product conflict, not a documentation detail.** It cannot be settled by
editing a doc, because the app, the website and the decision log currently encode three different
answers to "who decides a listing is fit for buyers". It needs an explicit decision on whether
KalaCart is a moderated marketplace or a self-publish one, and then a `D-n` entry superseding D-10
and D-12 in whichever direction is chosen. Tracked as §8 item 3. **Do not resolve it by rewriting
D-10, D-12, this document, or the client.**

## 4. Target platform

**Flutter cross-platform, Android + iOS, one shared FastAPI backend and one Supabase project.**
That is the target. Current reality:

- **Android** — builds and runs; debug and release APKs both built 2026-09-12 (release 58.3 MB).
  `applicationId com.kalacart.kalacart`, Java/Kotlin 17 (`app/android/app/build.gradle.kts:19`,
  `:13-14`). The missing INTERNET permission is **fixed** — the main manifest now declares INTERNET,
  CAMERA and RECORD_AUDIO, confirmed present in the merged *release* manifest. One blocker remains
  before any real distribution: release builds are still **signed with the debug keystore** (`:36`).
  `compileSdk`/`minSdk`/`targetSdk` are unpinned and inherit Flutter SDK defaults (`:9`, `:22-23`).
- **iOS** — the target is template-configured but has **never been built**. Bundle id
  `com.kalacart.kalacart` and `IPHONEOS_DEPLOYMENT_TARGET = 15.0` are set
  (`app/ios/Runner.xcodeproj/project.pbxproj:386`, `:363`), but there is **no `Podfile` or
  `Podfile.lock`** — `supabase_flutter` pulls in plugins with iOS platform code, so CocoaPods has
  never run. "Cross-platform" is currently an aspiration backed by one built platform.
- No `web/`, `windows/`, `macos/` or `linux/` runners exist.

## 5. The three required features

| Feature | Backend | Client | What wiring it needs |
|---|---|---|---|
| **Voice → catalogue listing** | **Text path real; audio path dormant by design.** `POST /api/v1/catalog/generate` (`catalog.py:442-487`) takes a transcript and produces the listing via OpenRouter. `POST /api/v1/catalog/voice` (`:490-560`) additionally transcribes audio via Sarvam (`app/ai/speech.py:49-116`) and **raises HTTP 500 while `SARVAM_API_KEY` is unset** (`speech.py:72-78`); the key is unset, and as of 2026-09-12 that is deliberate — speech-to-text is to run **on-device in Flutter**, with the app sending a transcript to `/catalog/generate` (`backend/.env.example`, Sarvam block). | **Live.** On-device `speech_to_text` dictates the transcript, which `BackendAiRepository.generateCatalog` posts to `/catalog/generate`. Language coverage is whatever the device engine offers — a per-device variable, not a product guarantee. | **Done.** The Sarvam audio path stays mounted and re-enables with a key, no code change. |
| **Fair pricing** | **Real and the best-built path.** `POST /api/v1/pricing/analyze` (`pricing.py:921-1039`) extracts attributes with a vision model, then **computes** the price deterministically in `app/services/pricing_engine.py::compute_price` and returns every factor. Skips the AI call entirely when the seller supplies category+size+quality+complexity (`pricing.py:983-995`). | **Live.** `BackendAiRepository.analyzePricing` renders the full factor breakdown. The client always sends category+size+quality+complexity, so the vision call is skipped and the path is immune to upstream model rate limits. | **Done.** |
| **Photo enhancement** | **Real, no LLM.** `POST /api/v1/image/enhance` (`image.py:335-648`) runs OpenCV + PIL — GrabCut background removal, CLAHE, compose on white, crop, resize — with three-tier degradation (`app/vision/background.py:11-19`). Uploads under the caller's own token so storage RLS applies (`image.py:292-332`). | **Live.** `image_picker` captures, the client downscales to 2000 px to stay inside the backend's size and dimension checks, and the result renders whether storage accepted it or it came back inline. | **Done** for the AI Studio path. The product-creation wizard still takes pasted URLs (`product_creation_wizard_screen.dart:543-547`) and is not yet on this path. |

Also note `POST /api/v1/pricing/predict` (`pricing.py:856-878`) — a pure-LLM alternative to
`/analyze`, taking optional auth. It previously ran on a paid model; since 2026-09-12 all three model
settings are pinned to `google/gemma-4-31b-it:free` (`core/config.py:69`, `:75`, `:77`).

## 6. Feature inventory

Status vocabulary:

- **Working** — real Supabase reads/writes on a reachable screen.
- **Mock** — runs in the app and returns fabricated data; no real implementation exists.
- **Backend only** — endpoint exists and is mounted; no client has ever called it.
- **Unbuilt** — no implementation anywhere.
- **Dead** — code exists, nothing reaches it.

| Area | Feature | Status | Where |
|---|---|---|---|
| Auth | Email/password sign-in, sign-up, reset, session restore | Working | `features/auth/data/supabase_auth_repository.dart` |
| Auth | Identity resolution → `profiles` / `sellers` ids | Working | same, `:96-134`, `:309-313` |
| Auth | Route guard, onboarding redirect | Working | `core/routing/app_router.dart:141-167` |
| Onboarding | Buyer and artisan onboarding | Working | `features/onboarding/presentation/` |
| Catalogue | Create/edit product (manual, typed) | Working | `product_creation_wizard_screen.dart`; `supabase_products_repository.dart:69-80` |
| Catalogue | Seller catalogue, status/stock changes, duplicate, delete | Working | `supabase_products_repository.dart:82-118` |
| Catalogue | **AI photo-to-listing studio** | **Mock that writes real rows** | `catalog_studio_repository.dart:16`; publishes at `catalog_studio_screen.dart:1088` |
| Catalogue | Image upload | **Working in AI Studio** (`image_picker` → `/image/enhance`, falls back to inline data if storage RLS rejects); **still unbuilt in the wizard**, which takes pasted URLs | `ai_studio_screen.dart`; `product_creation_wizard_screen.dart:543-547` |
| Discovery | Browse/search published products, categories | Working | `supabase_products_repository.dart:20-32`; `discovery_screen.dart` |
| Discovery | Product detail | Working | `features/products/presentation/product_details_screen.dart` |
| Storefront | Artisan storefront, featured sellers | Working | `features/seller/data/sellers_repository.dart:100-112` |
| Commerce | Cart → checkout → orders (buyer and seller views) | Working; **payment is a demo step — no money moves**, orders record `payment_status = paid` | `cart_provider.dart`, `orders_repository.dart:133-152` |
| B2B | RFQ create, quote, enquiry lists | Working | `features/rfq/data/supabase_rfq_repository.dart:79-100` |
| Messaging | Buyer–seller chat, realtime | Working | `supabase_chat_repository.dart:71-75`, `:181` |
| Passport | Craft passport / provenance view | Working, but **derived locally from product + seller data with no verification** | `product.dart:103`; `craft_passport_screen.dart` |
| AI | **The three live features — photo enhance, fair price, voice → listing** | **Working against the deployed backend** | `features/ai/presentation/ai_studio_screen.dart`, `data/backend_ai_repository.dart` |
| AI | Vision, translation, STT, TTS, pricing, recommendations, assistant | **Mock** (all 7) — superseded by the row above for the three that matter, still live for the rest | `features/ai/data/ai_providers.dart:5-35` |
| Live | Live commerce streams | **Mock** — no video transport | `features/live/data/live_repository.dart:5-16` |
| Offline | Queue + sync + connectivity | **Mock** — `_processAction` is a 600 ms delay that discards the action; `queueAction` is never called | `core/sync/sync_manager.dart:71`, `:112-117` |
| Seller | Dashboard analytics | **Mock** — 461 lines of hard-coded data | `features/seller/data/seller_repository.dart` |
| Moderation | Admin approval, seller verification | **Unbuilt** — no surface anywhere (§2, §3) | — |
| i18n | Multilingual UI | **Unbuilt** — no `flutter_localizations`, no `.arb` files | §8 item 8 |
| Backend | The three AI endpoints | Backend only | §5 |
| Backend | Health, request-id, security headers, rate limiting | Backend only | `main.py`, `core/middleware.py`, `core/rate_limit.py` |
| Backend | ~50 further routers (ONDC, blockchain, IoT, quantum, robotics, digital twin, museum, white-label, …) | Backend only, and **in-memory demoware** — state is per-process Python lists and `uuid4()` | `core/blockchain_provenance.py:121,182`, `services/iot_service.py:172,198`, `services/ondc/ondc_service.py:23` |
| Client | 11 dead files, incl. all of `core/errors/`, a duplicate cart, mock passport/RFQ/home data | Dead | `CLAUDE.md` §6, §9 |
| Client | 5 empty feature folders (`craft_passport`, `notifications`, `quotes`, `settings`, `storefront`) | Dead | README stub only |

## 7. Build state (2026-09-12)

- Fresh repository, **`master`, pushed to `origin`
  (`github.com/rishi-ventrapragada/KalaCart.git`).**
- **Client: builds, verified 2026-09-12.** `flutter analyze` reports **no issues** across the tree
  including the ~1,140 new lines of backend wiring; `flutter test` passes; `flutter build apk
  --debug` and `--release` both succeed (release 58.3 MB). The merged release manifest was inspected
  and carries INTERNET, CAMERA and RECORD_AUDIO.
- **The Flutter SDK is at `C:\src\flutter` and is not on PATH** on this machine — prepend
  `C:\src\flutter\bin` before the commands in CLAUDE.md §8, or they fail with "command not found".
- **Build warning:** `speech_to_text` applies the legacy Kotlin Gradle Plugin. Harmless today; future
  Flutter releases will refuse to build it.
- **Client tests: one test.** `app/test/widget_test.dart` pumps the app with `MockAuthRepository` and
  asserts three strings. No unit tests, no golden tests, no `integration_test/`. Nothing covers any
  repository, any `fromRow`, the router guard, or cart pricing.
- **Backend:** 81 test files, 819 `def test_` (59 async). **Not run this session, and their result
  is not trustworthy until the harness is fixed** — there is no `pytest.ini`/`pyproject.toml`
  anywhere, so `pytest-asyncio` has no `asyncio_mode` and the async tests likely never execute, a
  hazard `requirements.txt:42-44` documents. `backend/tests/README.md` describes a different,
  five-file suite.
- **The backend is deployed and live** at `https://kalacart-api.onrender.com` (Render free tier,
  512 MB, one gunicorn worker, auto-deploying from `origin/master`). Measured 2026-09-12: `/health`
  200 in **0.75 s** warm; `/api/v1/pricing/predict` returned a correct 422 with per-field detail in
  0.22 s. Cold start after ~15 min idle is **43.9 s**. Still no CI (`.github/workflows/` does not
  exist).
- **`backend/` was being edited concurrently while this document was written.** Uncommitted at the
  time of writing: the D-13 model fix, `opencv-python-headless`, the `$PORT`/single-worker
  Dockerfile, `fly.toml` and `.dockerignore`. Backend line citations here were checked against the
  working tree on 2026-09-12 and may drift; re-check before relying on one.
- **What was verified by running code (2026-09-12):** the client build, analyze and test results
  above; the release manifest contents; and the two live backend probes. Everything else in this
  document — backend internals, the router inventory, the dead-code counts — is still read from
  source and carries the same caveats it always did.

## 8. Open items

Ordered by severity and by how much each blocks §1.

1. **Authentication can be bypassed by default (security).** `_is_debug_mock_allowed()`
   (`backend/app/core/security.py:145-155`) enables unverified token decoding whenever `DEBUG` is
   true **or** `APP_ENV != "production"` — and `APP_ENV` defaults to `"development"`
   (`core/config.py:25`). `_decode_jwt_without_verify` (`:158-178`) base64-decodes the payload with
   no signature check; an opaque token gets a fabricated one (`:260-283`). Anyone can mint
   `{"uid": "<victim>"}` and be that user. The condition **fails open** — a `get_settings()` failure
   re-reads raw env with the same permissive default — and startup only logs CRITICAL on
   production+DEBUG, with a comment confirming it takes no action (`main.py:97-100`). Fix direction:
   gate the mock path on an explicit positive opt-in that cannot be reached by omission, and make
   production startup `raise` rather than log. The Supabase verification path is correct and not
   implicated.
2. **Flutter ↔ backend wiring — CLOSED 2026-09-12.** All three endpoints are called from
   `AiStudioScreen` over `dio` with the caller's Supabase token (§3a). Promises 1 and 2 are
   delivered. What remains is not wiring but reconciliation: the Catalog Studio and the
   product-creation wizard still run on mocks and pasted URLs beside it — item 10.
3. **Moderation model conflict — app vs website vs decision log.** §3. Needs a product decision on
   whether KalaCart is moderated or self-publish, then a `D-n` superseding **D-10** and **D-12**.
   Also determines whether `passportCode` may keep being minted unconditionally at creation. Blocks
   promise 3.
4. **The free-tier STT gap.** `DEEPSEEK_MODEL` previously defaulted to the paid
   `deepseek/deepseek-chat`, contradicting D-13 in the same file that cites it; **fixed 2026-09-12**
   — all three model settings now point at `google/gemma-4-31b-it:free` (`core/config.py:69`, `:75`,
   `:77`). Speech remains unresolved. Sarvam is paid, `speech.py:72-78` hard-fails with 500 without a
   key, and it covers **five** languages (hi, te, ta, kn, en — `speech.py:20-27`), not the twelve the
   pitch claims. The current answer is to move STT **on-device in Flutter** and post a transcript to
   `/catalog/generate` (`backend/.env.example`, Sarvam block) — that choice is recorded in a comment,
   not yet in a `D-n`, and no on-device implementation exists in the client. It also inherits
   whatever language coverage the device engine offers, which is a per-device variable, not a
   product guarantee. D-13 is explicit that none of this may be resolved by quietly restoring paid
   text models.
5. **Android release networking — CLOSED 2026-09-12.** The main manifest now declares INTERNET,
   alongside CAMERA and RECORD_AUDIO for the new capture surfaces. Verified by inspecting the merged
   *release* manifest of a built APK, not just the source. Release signing is still the debug
   keystore and remains open — tracked at §4 rather than here.
6. **The live schema is recorded nowhere.** No `database/` directory, no migrations, no DDL, no
   seeds, no `alembic.ini` despite `alembic` being pinned. The backend references ~60 table names.
   The system is not reproducible from source. Needs a `pg_dump --schema-only` or a hand-maintained
   `LIVE_SCHEMA.md` committed.
7. **iOS has never been built.** No `Podfile`/`Podfile.lock` (§4). Until CocoaPods runs and the app
   launches on a device or simulator, "cross-platform" is unproven.
8. **No i18n, against a multilingual product promise.** No `flutter_localizations`, no `l10n.yaml`,
   no `.arb` files; every user-facing string is an inline English literal. `intl` is used only for
   currency and date formatting. The only multilingual artifacts in the client are hard-coded strings
   inside mock data (`features/seller/data/seller_repository.dart:23-28`).
9. **Backend is not deployed yet; deployment is in progress.** As of 2026-09-12 a Fly.io config
   exists (`backend/fly.toml`, app `kalacart-api`, region `bom`, one always-on 512 MB
   `shared-cpu-1x`) and the Dockerfile now honours `$PORT` and runs **one** gunicorn worker. Nothing
   has been deployed from it in this tree. The older `backend/nginx/nginx.conf` is now vestigial and
   contradicts it: it proxies to Docker-Compose services `backend` and `web` that exist in **no
   compose file anywhere in the repository**, so it cannot start as committed. Domains are also split
   — nginx serves `kalacart.shop` while the code sends `HTTP-Referer: https://kalacart.in`. Decide
   whether nginx is deleted or reconciled before it misleads someone.
10. **Mock AI writes real catalogue rows.** §3b. Either gate the Catalog Studio behind a demo flag,
    label its output in the data, or wire it to the real endpoints. Today a buyer cannot tell a
    fabricated listing from a real one.
11. **A masked `NameError` in the pricing path.** `pricing.py:305` and `:330` call
    `get_supabase_client()`, imported only function-locally at `:904`; bare `except Exception`
    handlers (`:309-310`, `:341-342`) swallow it, so the advertised live demand index has never
    executed and every response carries a hard-coded 9-entry default (`:311-321`).
12. **~50 of 71 routers are in-memory demoware** whose state is per-worker under `gunicorn -w 4` and
    does not survive a restart. Decide per module: delete, unmount, or keep and label. An OpenAPI
    document advertising them as capabilities overstates the system.
13. **Test suites are not trustworthy.** Client: one test. Backend: no pytest config, so 59 async
    tests likely do not run; 76 files each wire their own dependency overrides because there is no
    shared fixture, which has shaped production code (`security.py:334-379`). Re-baseline before
    treating any failure as a regression.
14. **Rate limiting does not survive scaling.** Counters are in-memory and per-process
    (`core/rate_limit.py:16-19`). The Dockerfile's move to a single gunicorn worker (2026-09-12)
    makes the limit correct for one instance, but any second worker or second Fly machine multiplies
    it; a shared store is needed before scaling. Separately, `request.client.host` is checked before
    `X-Forwarded-For` (`:121-132`), so behind any proxy all anonymous traffic collapses into one
    bucket.
15. **Every Supabase call blocks the event loop.** The sync client is used throughout async handlers,
    including `/health` (`database/connection.py:14-17`, `:220-237`).
16. **Repository hygiene.** No git remote. 11 dead client files including all of `core/errors/`; five
    empty feature folders; a duplicate cart implementation. `app/lib/core/redis.py`-style
    `os.getenv` bypasses of `get_settings()` in the backend.

## 9. Non-goals for now

Nothing in the "Backend only … demoware" row of §6 is in scope until the three promises in §1 are
delivered in the client. Specifically out of scope: ONDC, ERP integrations, multi-region,
blockchain/PQC, IoT, live commerce, AR, digital twin, white-label tenancy, robotics, knowledge graph,
and the public developer API.

Also out of scope until §8 items 1–3 are settled: new feature work in the app, and any change that
assumes a moderation model before the decision in §8 item 3 is made.
