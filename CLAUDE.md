# KalaCart — engineering constitution

Written 2026-09-11 from the code, not from the older docs. Every claim below points at a file.
If the code and this file disagree, the code wins and this file gets fixed in the same change.

## 1. What is in this workspace

| Path | What it is | Status |
|---|---|---|
| `KalaCart/` | The product. Git repo (`master`, no remote). Android app + FastAPI backend + React web + SQL. | Active |
| `KalaCart/android-app/` | Java 17 Android app. This is the thing users run. | Active — all Sep 11 work is here |
| `KalaCart/backend/` | FastAPI service. Holds the AI pipeline. Not reachable from the app today (see §4). | Built, not integrated |
| `KalaCart/web/` | React 18 + Vite site. Mock auth, canned data. Meant to become the ministry admin/approval site. | Prototype |
| `KalaCart/database/` | `schema.sql` + 65 migrations. **Not the live schema** (see §5). | Stale |
| `KalaCart/docs/` | Mixed. See §2 before trusting any of it. | — |
| `kalacartflutter/` | Flutter rewrite started 2026-09-10 (~20k lines, Riverpod + go_router + supabase_flutter, same Supabase project, mostly mock repositories, debug APK built once, not a git repo, untouched since). Treated as **parked**; not a first-class stack in this doc. | Parked pending owner confirmation |
| `memory/` | `decisions.md` (§D log) and future memory files. | Active |
| `PRD.md` | Product scope and honest build status. | Active |

## 2. Which documents to believe

Order of authority, highest first:

1. **The code**, especially anything touched by the 2026-09-11 commits (`git log` — 13 commits, "baseline before schema reconciliation" onward).
2. `KalaCart/docs/DEVICE_TEST_SELLER_FLOW.md` and `KalaCart/docs/UNIFIED_ARTISAN_AGENT.md` (2026-09-11). Match the code.
3. `KalaCart/docs/CODEBASE_GUIDE.md`, `MAINTAINER_GUIDE.md`, `SECURITY_AUDIT.md`, `TEST_REPORT.md`, `PERFORMANCE_REPORT.md`, `Android_Code_Quality_PhaseB_Report.md` (2026-09-02). Honest about method, but describe an **earlier system**: Firebase phone OTP, an `artisans` table, seven migrations, Android talking only to FastAPI. Read them as history. Their branching model (`main`/`develop`/`release/*`), test counts (471/111) and CI gates were never in force in this repo.
4. `KalaCart/README.md`, `docs/SYSTEM_ARCHITECTURE.md`, `docs/JUDGING_POINTS.md`, `docs/SIH_DEMO_SCRIPT.md` — vision and pitch. `README.md` §"Tech Stack"/"Database Schema" is partly stale (it still says Firebase OTP and `profiles.firebase_uid`).
5. `docs/ARCHITECTURE.md`, `DEPLOYMENT_GUIDE.md`, `ER_DIAGRAM.md`, `API_DOCUMENTATION.md`, `DATABASE_ERD.md` — unverified; each has at least one false claim (Kotlin, Gemini, Redis, migration index). Use only with the code open.
6. `docs/archive/known-fabricated/` — **never cite.** 19 documents with false test counts, fake PQC/blockchain, imaginary regions. See the README there.

## 3. Actual stack (from build files)

**Android** — `KalaCart/android-app/app/build.gradle`
- Java 17 (`sourceCompatibility VERSION_17`), no Kotlin. `compileSdk 34`, `minSdk 24`, `targetSdk 34`, `applicationId com.kalacart.app`, `versionCode 1 / versionName "1.0.0"`.
- Gradle 8.13 wrapper (repaired 2026-09-11; `./gradlew` and `gradlew.bat` both work), AGP 8.13.2, JDK 17 target (JDK 21 on the dev machine works via toolchain).
- XML layouts (166) + **ViewBinding**; Material Components 1.11.0; Navigation Component 2.7.7 with one `nav_graph.xml` under `MainActivity`; many standalone Activities (see manifest).
- Retrofit 2.9 + OkHttp 4.12 + Gson 2.10; Glide 4.16; Room 2.6.1 + WorkManager 2.9 (offline layer, partially wired); CameraX 1.3.3; Firebase BoM 34 for **Crashlytics/Analytics/FCM only** — Firebase Auth is not used.
- Tests: JUnit 4, Mockito 5, Robolectric 4.11, MockWebServer — 23 files, 164 `@Test`, under `app/src/test`. Not run in CI (no remote). Some tests predate the Supabase switch; expect failures until re-baselined.
- Build variants: `debug` (`BASE_URL=http://10.0.2.2:8000/`), `staging`, `release` (minify on; signing only from `KALACART_KEYSTORE_*` env or gradle properties — no defaults).

**Backend** — `KalaCart/backend/requirements.txt`, `Dockerfile`
- Python 3.11 in Docker (3.13 on the dev machine; `pytest` is **not installed** there — `pip install pytest pytest-cov httpx` first).
- FastAPI 0.110, Pydantic 2.6 + pydantic-settings, Uvicorn/Gunicorn, `supabase-py 2.7.1` (**synchronous** client — every `.execute()` blocks the event loop), httpx 0.27, OpenCV 4.9, Pillow, firebase-admin 6.4.
- 60+ routers mounted in `app/main.py`. The ones that matter: `agent`, `catalog`, `pricing`, `image`, `auth`, `products`, `marketplace`. The rest are feature stubs with unit tests that exercise the stubs.
- Tests: 87 files, 753 `def test_`, all mock Supabase/LLM via `conftest.py` env defaults (`DEBUG=true`, placeholder Supabase URL/keys).

**Web** — `KalaCart/web/package.json`: React 18.3, Vite 6, TypeScript 5.7, Tailwind 3.4, react-router 6, `@supabase/supabase-js` 2.49 (client created but `AuthContext.tsx` is a hard-coded mock user; `lib/api.ts` returns canned data on any fetch failure).

**Data** — Supabase project `imprsuvtgqxepwzimqmc` (PostgreSQL + GoTrue + PostgREST + Storage). The anon key is compiled into the app (`res/values/strings.xml`, `SupabaseConfig.java`) — that is normal for Supabase anon keys; RLS is the boundary. The **service-role key and OpenRouter key live only in `backend/.env`** (gitignored).

**AI** — OpenRouter. The unified agent (`backend/app/agent/`) uses only `:free` model slugs walked in a fallback chain. Legacy `catalog.py`/`pricing.py` use `qwen/qwen3-32b` and `deepseek/deepseek-chat` from settings.

## 4. How data actually flows

```
Android app ──GoTrue (email+password)──▶ Supabase Auth      SupabaseAuthManager.java
Android app ──PostgREST (anon key + user JWT)──▶ Supabase DB  SupabaseClient.java → SupabaseService.java
Android app ──Storage REST──▶ bucket `product_images`        ImageRepository.java

Android app ──Retrofit (Supabase JWT as Bearer)──▶ FastAPI   RetrofitClient.java → ApiService.java
                                                    │
                                                    ▼  core/security.py verifies a **Firebase** token
                                                       and looks up artisans.firebase_uid  → 401/404
```

- **The app talks to Supabase directly.** 40 classes use `SupabaseService`; 19 still reference `ApiService`, and none of those paths are on the tested seller flow.
- **The backend cannot authenticate the app today.** `get_current_user` expects a Firebase ID token and an `artisans` row keyed by `firebase_uid`; the app has neither. In `DEBUG=true` the backend falls back to unverified "mock decode", which is why local demos may appear to work. This is the top open item in `PRD.md`.
- The reachable **"Continue with AI →"** step (`ui/seller/addproduct/AddProductActivity.java`) calls `ai/AiProductServiceImpl.java`, a keyword-matching placeholder with an 800 ms delay. `ArtisanAgentRepository.java` (uncommitted) targets `POST /api/v1/agent/process` but no screen invokes it.
- Identity chain, and the single most common bug class in this codebase:
  `auth.uid()` == `profiles.auth_user_id` → `profiles.id` == `sellers.profile_id` → `sellers.id` → `products.seller_id`.
  `profiles.id` is written explicitly and kept equal to the auth uid on first insert (`SessionIdentityResolver.createProfile`). `products.seller_id` is **`sellers.id`, never the auth uid and never `profiles.id`**. `SessionManager.getSellerId()` returning null means "cannot publish", not "fall back".

## 5. Schema rule

`database/schema.sql` and `database/migrations/*.sql` describe a schema the app does not use. The live tables the app writes have `profiles.auth_user_id`, `products.status / is_active / category_id / seller_id / stock / material`, a `categories` table, `product_images.image_order`, and a bucket named `product_images` (underscore). None of these appear in any migration. Migration numbers 016, 018–029 and 052 are each used twice.

Therefore:
- Before writing to or filtering on any column, confirm it against the Supabase dashboard **or** the `@SerializedName` fields in the Sep 11 model classes (`Profile.java`, `Seller.java`, `Product.java`, `ProductInsert.java`, `ProductImage.java`, `Category.java`). A PostgREST 400 mentioning a column is the schema telling you it is wrong.
- Never edit a shipped migration. New migrations start at `066_`.
- Recording the live schema in the repo (a `pg_dump --schema-only` or a hand-written `database/LIVE_SCHEMA.md`) is an open item; until it exists, the code comments are the record.

## 6. Android conventions actually in use

- **Write only real columns.** Request bodies are either an explicit insert type (`ProductInsert` with a builder that refuses a null seller id or title) or a model whose database-owned fields carry `@ServerOwned` and are dropped by `SupabaseGson` on serialisation only. Add `@ServerOwned` to any field a trigger or the admin owns (`products.is_active`, `profiles.is_verified`, `profiles.verification_level`, `sellers.location`, generated `id`s).
- **PostgREST filters are literal strings**: callers pass `"eq." + id`, `"eq.approved"`, `"created_at.desc"`. Keep that shape; do not invent a query builder.
- **Errors carry the PostgREST message.** Repositories return `Result<T>` via `SupabaseProfileService.parseError(response, fallback)` or an `Exception` whose message is the server's. Surface it to the user (Toast/Snackbar); do not swallow it into an empty list. Log tags: `KALACART_DB` for data, `KALACART_FATAL` for crashes, `SUPABASE_AUTH` for auth.
- **No mock fallbacks in data screens.** An empty catalogue and a broken query must look different (`MyProductsFragment.loadProducts`). `AiProductServiceImpl` is the one deliberate placeholder and is labelled as such.
- **Callbacks arrive on the main thread** (`Handler(Looper.getMainLooper())` in managers, Retrofit's default executor in repositories). Guard with `if (!isAdded() || binding == null) return;` in fragments; null `binding` in `onDestroy*`.
- **Session state lives in `SessionManager`** (plain `SharedPreferences`, file `kalacart_prefs`). Distinct keys: auth uid (`getUid`/`getAuthUserId`), `getProfileId()`, `getSellerId()`, Supabase access/refresh tokens, role, `isProfileCompleted`. `AuthManager` is a thin façade over `SupabaseAuthManager`.
- **Architecture as practised:** Activities/Fragments construct repositories directly and use callbacks. `viewmodel/*ViewModel.java` and LiveData exist (20 of them) but are not the dominant path on the seller flow. Follow the file you are editing; do not refactor a screen to MVVM as a side effect.
- **Buyer-visible catalogue = `status = 'approved' AND is_active = true`.** Every new product is `status = 'pending'`. The app never sets `approved`.
- Singletons use double-checked locking with `KalaCartApplication.getInstance()` as the context source. `BuildConfig.DEBUG` gates HTTP body logging.
- Strings: multilingual `values-hi/kn/ta/te` exist; new user-visible strings go in `strings.xml`, not code (the Sep 11 screens have some inline strings — do not add more).

## 7. Backend conventions actually in use

- Routers are plain `APIRouter()`; **`app/main.py` owns the prefix** (`/api/v1/<domain>`). `analytics` keeps an internal prefix as a documented exception.
- Config only via `get_settings()` (`core/config.py`, `@lru_cache`, reads `backend/.env`). Never `os.getenv` in new code.
- Auth via `Depends(get_current_user)` / `get_optional_current_user` from `core/security.py`. Tests override with `app.dependency_overrides`.
- Rate limiting via `core/rate_limit.check_rate_limit(store, key, max, window)` with a per-router store. In-memory; not safe across workers.
- Upload validation lives in `api/image.py` and is duplicated in `api/agent.py`: 10 MB cap, MIME allowlist, blocked executable suffixes, 100–6000 px.
- The agent: `agent/models.py` (free-model catalogue + `complete()` fallback walker), `agent/tools.py` (three capabilities with output validation), `agent/orchestrator.py` (stage sequencing, per-stage degradation, 240 s per stage), `api/agent.py` (multipart endpoint, 10 runs/min). Read `docs/UNIFIED_ARTISAN_AGENT.md` before touching it — the free-tier quirks (reasoning-token budgets, `content` empty with `reasoning_content` filled, models that 400 on `response_format`) were all found live and are not visible in mocked tests.
- Tests mock the network: patch `httpx.AsyncClient` for LLM calls and `get_supabase_client` for DB. `backend/scripts/agent_smoke_test.py` is the only live check.

## 8. Working agreements

- **Plan before scope.** Any new scope — including follow-on work right after finishing something — starts with a plan and waits for a go-ahead. Report what was done, what was verified, and what was skipped, separately.
- **Verification means running it.** For seller-flow changes the acceptance gate is `docs/DEVICE_TEST_SELLER_FLOW.md` on a real device with a seller account. For backend changes, `python -m pytest backend/tests -q` from `KalaCart/`. "Verified" in a report means one of those happened.
- **Commands that work on this machine** (Windows, Git Bash or PowerShell):
  - `cd KalaCart/android-app && ./gradlew :app:assembleDebug` → `app/build/outputs/apk/debug/app-debug.apk`
  - `./gradlew testDebugUnitTest --continue`
  - `cd KalaCart && python -m pytest backend/tests -q` (after installing pytest)
  - `cd KalaCart/backend && uvicorn app.main:app --reload` (needs `backend/.env`; a real `OPENROUTER_API_KEY` for the agent)
- **Git:** single `master`, no remote. Commit messages are one lowercase imperative sentence, no prefix ("fix camera capture in AddProductActivity"). Do not introduce Conventional Commits or a `develop` branch without a decision. `.github/workflows/ci.yml` targets `main`/`develop` and has never run.
- **Secrets:** `backend/.env`, `android-app/app/google-services.json`, `local.properties`, keystores are gitignored — keep it that way. Release signing has no defaults by design.
- **Decisions:** anything that changes an architectural or product rule gets a `D-n` entry in `memory/decisions.md` in the same change. Reopening an existing entry is done explicitly, not by overwriting it.
- **Docs-as-code:** if you change behaviour that a document in §2 tiers 1–2 describes, update that document in the same change. Do not touch tier 6.

## 9. Things not to assume

- No file-size or line-count caps. No DI framework (no Hilt/Dagger). No Kotlin, no Compose. No coroutines.
- No Redis, no Celery, no second region, no Kong, no Next.js — regardless of what `docker-compose.prod.yml` or archived docs suggest.
- No Firebase Auth. No phone OTP. No `artisans.firebase_uid` for app users.
- No admin/approval UI exists anywhere in the repo.
- No CI has ever run; test counts in any doc are historical or fictional.
- The six-step "Capture → Voice → Price → Preview → Publish" wizard under `ui/sell/` is **not reachable** from the app's navigation; the only publishing route is Sell tab → `+ Add` → `AddProductActivity` → `AiProductReviewActivity`.
