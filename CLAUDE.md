# KalaCart — engineering constitution

Rewritten 2026-09-12 from the code in this repository, not from the older docs. Every claim below
points at a file. If the code and this file disagree, the code wins and this file gets fixed in the
same change.

This replaces the 2026-09-11 version, which described the Java/Android stack that the consolidation
dropped. The client is now Flutter.

## 1. What is in this workspace

Fresh git repository, **branch `master`, tracking `origin`
(`github.com/rishi-ventrapragada/KalaCart.git`)**. The old KalaCart repository is archived; the
website is a separate line of work in its own repository (`KalaCart-Website`) against the **same
live Supabase project** — see §4.

| Path | What it is | Status |
|---|---|---|
| `app/` | **The product.** Flutter client (Dart), targeting Android + iOS. 113 Dart files under `app/lib`. | Active — canonical |
| `backend/` | FastAPI service. Holds the three AI features and ~70 mounted routers. | Active, **deployed** at `kalacart-api.onrender.com`, called by the client for the three AI features (§4) |
| `memory/decisions.md` | The `D-n` decision log. | Active |
| `CLAUDE.md`, `PRD.md` | This file and the product/status doc. | Active |

**There is no `web/` directory in this repository.** `git ls-files` tracks exactly `app/`,
`backend/`, `memory/`, `CLAUDE.md`, `PRD.md`, `.gitignore` (582 files). The React admin site
described by older documents exists only in the archived repository. There is no admin or
moderation UI anywhere in this tree — see PRD §8.

`app/build/` and `backend/.env` are gitignored and present locally only.

## 2. Which documents to believe

Order of authority, highest first:

1. **The code.**
2. `app/README.md` — written against the Flutter tree and accurate on layout, tables, providers and
   the real-vs-simulated split. Its claim that `android/app/src/main/AndroidManifest.xml` declares
   `INTERNET` was wrong when written but is **now true** (fixed 2026-09-12). Treat its
   "everything AI is simulated" framing as outdated: the three live features are not.
   The root `README.md` is the outward-facing overview and is not authoritative for engineering
   detail — prefer this file.
3. `memory/decisions.md` — `D-1` … `D-14`. Several have been outrun by the code; where that is true
   this file says so and PRD §8 lists the supersede entry that is needed. **Entries are appended,
   never rewritten** — do not edit an existing `D-n` to match current behaviour.
4. This file and `PRD.md`.

Not documentation, despite appearances: the `README.md` files under `app/lib/features/*/` are
identical five-line boilerplate stubs restating the layer convention
(`app/lib/features/craft_passport/README.md:1-6` is representative). They describe no feature.
`backend/tests/README.md` is stale — it describes an image-only, five-file suite and asserts "No
voice/catalog/marketplace logic is tested" while `test_catalog_api.py`, `test_catalog_voice.py`,
`test_marketplace_api.py`, `test_voice_api.py` and `test_pricing_api.py` sit beside it.

## 3. Actual stack (from build files)

**Client** — `app/pubspec.yaml`

- Dart SDK `>=3.3.0 <4.0.0`. The **entire** dependency list is `flutter`, `flutter_riverpod ^2.5.1`,
  `go_router ^14.2.0`, `intl ^0.19.0`, `cupertino_icons`, `supabase_flutter ^2.8.3`, and — added
  2026-09-12 for the backend wiring — `dio ^5.7.0`, `http_parser ^4.0.2`, `image_picker ^1.1.2`,
  `speech_to_text ^7.0.0`; dev: `flutter_test`, `flutter_lints ^4.0.0`.
- Consequences that still constrain everything: **no `freezed`, no `json_serializable`, no
  `build_runner`, no `riverpod_generator`, no `connectivity_plus`, no `flutter_localizations`, no
  mocking library.** There is no `lib/generated`, no `*.g.dart`, no `*.freezed.dart`.
- `dio` is for the FastAPI backend only (§4). Supabase traffic goes through `supabase_flutter`;
  do not route it through Dio, and do not add a second HTTP package.
- Lints: `flutter_lints` plus five explicit rules — `prefer_const_constructors`,
  `prefer_const_literals_to_create_immutables`, `prefer_const_declarations`,
  `avoid_unnecessary_containers`, `use_key_in_widget_constructors` (`app/analysis_options.yaml`).
- **Android** — `app/android/app/build.gradle.kts`: `namespace` and `applicationId`
  `com.kalacart.kalacart` (`:8`, `:19`), Java/Kotlin 17 (`:13-14`, `:43`). `compileSdk`, `minSdk`,
  `targetSdk` and `ndkVersion` are **not pinned** — each inherits the Flutter SDK default
  (`:9-10`, `:22-23`). Release builds are **signed with the debug keystore** (`:36`, template TODO
  at `:34`) and are not shippable.
- **Android permissions** — the main manifest declares `INTERNET`, `CAMERA` and `RECORD_AUDIO`,
  plus a `<queries>` entry for `android.speech.RecognitionService` that `speech_to_text` needs on
  Android 11+. INTERNET was missing until 2026-09-12, which silently broke release builds; verified
  present in the merged release manifest of a built APK.
- **iOS** — the target is template-configured but has never been built:
  `PRODUCT_BUNDLE_IDENTIFIER = com.kalacart.kalacart`
  (`app/ios/Runner.xcodeproj/project.pbxproj:386`, `:567`, `:589`),
  `IPHONEOS_DEPLOYMENT_TARGET = 15.0` (`:363`, `:490`, `:542`). **There is no `Podfile` or
  `Podfile.lock`** — `supabase_flutter` pulls in plugins with iOS platform code, so CocoaPods has
  never been run.
- Only `android/` and `ios/` runners exist. `analysis_options.yaml` pre-emptively excludes `web/`,
  `windows/`, `macos/`, `linux/`, but those runners are not present.

**Backend** — `backend/requirements.txt`, `backend/Dockerfile`

- Python 3.11 in Docker. FastAPI 0.110, Pydantic 2.6 + pydantic-settings, Uvicorn/Gunicorn,
  `supabase 2.7.1` (**synchronous** client), httpx 0.27, Pillow 10.3,
  `opencv-python-headless 4.9.0.80`,
  `firebase-admin 6.4.0`, `PyJWT[crypto] 2.10.1`, `python-jose 3.3.0`, pytest 9.1.1 +
  pytest-asyncio 1.3.0 + pytest-cov 7.0.0.
- `requirements.txt` has been repaired since the last rewrite: PyJWT and the pytest trio are now
  declared, each with a comment explaining why (`requirements.txt:16-20`, `:42-44`). The older claim
  that "pytest is not installed" is obsolete.
- Unused or risky pins worth knowing: `rembg` is **not** a dependency and not used (background
  removal is OpenCV GrabCut); `numpy` is used directly by first-party code but arrives only
  transitively via `opencv-python-headless` and is **unpinned**; `openai`, `sqlalchemy`, `alembic` and
  `psycopg2-binary` are pinned but the ORM is unused and there is no `alembic.ini`; `redis` is
  imported at `backend/app/core/redis.py:25` but is **not in `requirements.txt`**, so the in-memory
  fallback is the only path that has ever run.
- 71 routers in `backend/app/api/`; `app/main.py` mounts all but `agent`. Only 21 touch Supabase —
  see §7.

**Data** — Supabase project `imprsuvtgqxepwzimqmc` (PostgreSQL + GoTrue + PostgREST + Realtime +
Storage). The URL and anon key are compiled into the client
(`app/lib/core/config/supabase_config.dart:2-3`); that is normal for an anon key and RLS is the
boundary. Demo account credentials are also committed
(`app/lib/core/config/demo_accounts.dart:8-10`) and surfaced as tap-to-fill buttons on the login
screen. The **service-role key, OpenRouter key and any Sarvam key live only in `backend/.env`**
(gitignored).

**AI** — OpenRouter for text and vision, on `:free` slugs only (D-13). `QWEN_MODEL`, which serves
catalog generation, is `nex-agi/nex-n2.5-pro:free` per D-17; `DEEPSEEK_MODEL` and `VISION_MODEL`
remain `google/gemma-4-31b-it:free`, whose upstream shared pool is exhausted — harmless only because
the client always sends the four attributes that skip that call. Sarvam AI is wired for
speech-to-text but is paid and deliberately outside D-13; as deployed it is dormant, and the client
transcribes on-device instead (§7).

## 4. How data actually flows

```
Flutter app ──GoTrue (email+password)──▶ Supabase Auth    supabase_auth_repository.dart
Flutter app ──PostgREST (anon key + user JWT)──▶ Supabase DB   every features/*/data/*_repository.dart
Flutter app ──Realtime (.stream on messages)──▶ Supabase       supabase_chat_repository.dart:71-75

Flutter app ──dio + user JWT──▶ FastAPI       core/network/api_client.dart (three AI endpoints)

FastAPI ──service-role──▶ Supabase            backend/app/database/connection.py
FastAPI ──httpx──▶ OpenRouter                 catalog.py, pricing.py, app/ai/vision.py
FastAPI ──httpx──▶ Sarvam AI                  app/ai/speech.py
```

**The client calls the backend for the three AI features, and for nothing else.** All other data
still moves over PostgREST directly. The one configured Dio instance is `apiClientProvider`
(`core/network/api_client.dart`); an interceptor attaches the live Supabase access token, which the
backend verifies against the project JWKS. `BackendAiRepository`
(`features/ai/data/backend_ai_repository.dart`) is the only caller, covering `/api/v1/image/enhance`,
`/api/v1/pricing/analyze` and `/api/v1/catalog/generate`; `AiStudioScreen` is the only consumer.
Base URL is the deployed instance, `https://kalacart-api.onrender.com` (`api_client.dart:10`).

Two things in that file are shaped by the free tier rather than by taste, and should not be
"tidied": the 120 s receive timeout and `backendWakingProvider` both exist to absorb a cold start
measured at 43.9 s. Route new backend error text through `apiErrorMessage`, which is to the API
layer what `authErrorMessage` is to auth.

Note `core/network/connectivity_service.dart` is **not** part of this path — it performs no network
I/O and its own comment calls it a simulation (`:24`).

**Backend auth is solved.** `backend/app/core/supabase_auth.py` verifies Supabase access tokens
against the project JWKS with signature, expiry, audience (`authenticated`) and issuer pinning,
`algorithms=["ES256","RS256"]` (`:71-79`), and resolves the user via `profiles.auth_user_id`
(`:96-111`). `get_current_user` tries Supabase first and falls through to the legacy Firebase branch
(`core/security.py:466-472`; same shape at `:400-404`). This closes the old PRD §3 gap. **But the
Firebase fallback contains an authentication bypass that is on by default** — see §7 and PRD §8
item 1.

**The identity chain is unchanged and is still the most common bug class:**

`auth.uid()` == `profiles.auth_user_id` → `profiles.id` == `sellers.profile_id` → `sellers.id` ==
`products.seller_id`.

Written at `supabase_auth_repository.dart:96-134` (profile ensured/created by `auth_user_id`),
`:309-313` (seller row keyed by `profile_id`), and consumed as
`ProductInput.toRow({required String sellerId})` where `sellerId` is **`sellers.id`, never the auth
uid and never `profiles.id`** (`shared/models/product.dart:205-206`). A missing seller id means
"cannot publish" — it is never substituted.

Tables the client touches: `profiles`, `sellers`, `products`, `wholesale_pricing`, `enquiries`,
`messages`, `orders`. The backend references ~60 distinct table names, most of which belong to
unmounted or stub features.

## 5. Schema rule

**The live schema is recorded nowhere in this repository.** There is no `database/` directory, no
migrations, no DDL, no seed SQL, and no `alembic.ini` despite `alembic` being pinned. The system
cannot be stood up from a clean Supabase project using anything in this tree. PRD §8 item 6.

Until that exists, confirm every column against, in order:

1. The `fromRow` / `toRow` mappings in `app/lib/shared/models/` — `product.dart:105-137` and
   `:205-218`, `order_models.dart:111`, `enquiry_models.dart:152`. These are the closest thing to a
   schema of record for what the client reads and writes.
2. The table summary in `app/README.md`.
3. The Supabase dashboard.

A PostgREST 400 naming a column is the schema telling you the code is wrong. Never invent a column
to make a query compile.

## 6. Flutter / Dart conventions actually in use

Only rules the code actually and consistently shows. Follow the file you are editing.

**Layering.** `features/<name>/{data,domain,presentation}`, with `core/` for app-wide
infrastructure and the design system, and `shared/` for cross-feature models and widgets. Adherence
is partial and that is the status quo: only `ai`, `auth`, `catalog_studio` and `live` have a
`domain/`; seven features put their models in `shared/models/` instead; `discovery`, `onboarding`,
`profile` and `home` are presentation-only. Five folders — `craft_passport`, `notifications`,
`quotes`, `settings`, `storefront` — contain **nothing but a boilerplate README**. `auth` is the
reference implementation.

**Repositories.** A plain class per feature taking `SupabaseClient` by constructor injection
(`supabase_products_repository.dart:10-13`). `Supabase.instance.client` is referenced in exactly one
place — `supabaseClientProvider` at `supabase_auth_repository.dart:374-376` — and everything else
watches that. Only 6 files import `package:supabase_flutter`. **No screen touches Supabase
directly.** Auth is the one feature with an interface: `abstract class AuthRepository`
(`auth_repository.dart:12-47`) with a Supabase implementation and a `MockAuthRepository` used to
override `authRepositoryProvider` in tests (`test/widget_test.dart:13`).

**Riverpod — plain and manual.** No code generation anywhere: zero `@riverpod`,
`riverpod_annotation` or `part '*.g.dart'`. Roughly 34 `Provider`, 13 `FutureProvider`, 12
`StateNotifierProvider`, 10 `StateProvider`, 3 `StreamProvider`. **`AsyncNotifierProvider` /
`NotifierProvider` are not used at all** — mutation is uniformly the legacy `StateNotifier`. Do not
introduce the `Notifier` API or codegen into a file that does not already use it.

- Providers are **colocated at the bottom of the repository file** under a `// Providers` banner
  (`auth_repository.dart:178-180`). There is no `providers.dart` per feature. Exceptions:
  `features/ai/data/ai_providers.dart`, and a few private providers declared inline in screens
  (`conversation_list_screen.dart:32`).
- `.family` for parameterised reads (`supabase_products_repository.dart:152,158,171`);
  `.autoDispose` on screen-scoped `FutureProvider`/`StreamProvider` (11 sites). Where autoDispose is
  deliberately omitted, say why — `live_repository.dart:8-11` is the model.
- Async server data rides in `AsyncValue` and is rendered with `.when(...)`. Mutable local state is
  `StateNotifier<T>` where `T` is usually a plain `List<T>` (`cart_provider.dart:25`).
- **Refresh is `ref.invalidate(...)`** — 51 call sites. Do not hand-roll a refresh flag.
- A `.family` argument type must implement `==` and `hashCode` so provider caching works —
  `CatalogQuery` (`supabase_products_repository.dart:144-149`) is the only such type and the
  precedent.

**Routing.** One file, `core/routing/app_router.dart` (385 lines), exposed as
`routerProvider` (`:169`) and consumed in `main.dart:36-45`.

- **Paths only — there are zero named routes**, and correspondingly no `goNamed`/`pushNamed`.
- One `ShellRoute` (`:233-264`) wraps the six bottom-nav destinations; everything else is a root
  route carrying `parentNavigatorKey: _rootNavigatorKey` so it covers the shell full-screen.
- One auth guard: `_redirect(Ref, GoRouterState)` (`:141-167`), wired at `:178`, driven by
  `refreshListenable` — a manual `ValueNotifier<int>` bumped from `ref.listen` on `authStateProvider`
  (`:170-172`). Loading → `/splash`; signed-out + non-public → `/welcome`; signed-in + not onboarded
  → `onboardingPathFor(user)`; signed-in on a public path → `/`. New screens go in `_publicPaths`
  (`:122-131`) or they are gated.
- `context.push` for detail pages (78 calls), `context.go` for tab and auth-flow transitions (35).

**PostgREST query shape.** Fluent builder, with the `select` projection hoisted to a file-level
const — `productSelect` (`supabase_products_repository.dart:8`), `_orderSelect`, `_enquirySelect`,
`_select`. Reads chain `.eq()/.or()/.order()/.limit()`, single rows use `.maybeSingle()` then a null
check or `.single()` after an insert. There is no query-builder abstraction; do not invent one.

**Models — hand-written, with a deliberate naming split.**

- **`fromRow(Map<String, dynamic> row)`** to read a Supabase row — *not* `fromJson`
  (`product.dart:105`, `enquiry_models.dart:152`, `order_models.dart:111`).
- **`toRow({required String sellerId})`** to write — *not* `toJson` (`product.dart:205-218`).
- **Insert-specific models are the convention**, and they are how server-owned fields are excluded:
  `ProductInput` (`product.dart:178-219`) carries only client-supplied fields and its `toRow` emits
  no `id`, no `created_at`, and none of the joined `sellers`/`wholesale_pricing` blocks. This is the
  Flutter equivalent of the old `@ServerOwned` rule — express it by leaving the field out of the
  input model, not by annotating the domain model. `updateProduct` additionally does
  `..remove('seller_id')` so an update never rewrites the owner
  (`supabase_products_repository.dart:77-79`).
- `copyWith` deliberately does **not** accept `id`, `sellerId`, `createdAt` or joined seller fields
  (`product.dart:139-174`). Keep it that way.
- Nullable columns are included conditionally: `if (city != null) 'city': city` (`:216-217`).
- Enum ↔ DB via enhanced enums with `String get dbValue => name;` and a static `fromDb(String?)`
  using `firstWhere(..., orElse: <default>)` — `ProductStatus` (`product.dart:16-27`),
  `EnquiryStatus`, `OrderStatus`.
- Every `fromRow` parses defensively — `(row['price'] as num?)?.toDouble() ?? 0`,
  `DateTime.tryParse(...) ?? DateTime.now()`, list fields guarded by `is List`. Nothing throws on a
  malformed row (`product.dart:107-137`).
- Derived values are getters on the model, not logic in the UI: `artisanName`, `primaryImageUrl`,
  `inStock`, `sortedTiers`, `unitPriceFor(int)`, `passportCode` (`product.dart:75-103`).

**Errors.**

- There is **no `Result`/`Either` type**. Repositories do not catch; they let `AuthException` and
  `PostgrestException` propagate.
- **`core/errors/exceptions.dart` and `core/errors/failures.dart` are dead** — the
  `AppException`/`Failure` hierarchies are defined and imported by nothing. Do not build on them and
  do not treat them as the intended convention.
- Reads surface errors through `AsyncValue`, rendered by `.when(error: ...)` into `AppErrorState`.
- Mutations follow one pattern, ~23 sites, canonically `login_screen.dart:42-64`: a
  `Future<void> _handleX()` on a `ConsumerStatefulWidget` → `setState(_isLoading = true)` → `try` →
  `if (mounted)` before navigating → `catch (e)` → `ScaffoldMessenger...showSnackBar` → `finally`
  with a `mounted` guard. **The `mounted` guard before navigation and SnackBar is not optional.**
- **`authErrorMessage(Object error)`** (`supabase_auth_repository.dart:355-372`) is the app's single
  error formatter despite its name — it maps `AuthException`, then `PostgrestException` →
  `error.message`, then socket/lookup failures → "No internet connection". Non-auth screens call it.
  Route new user-facing error text through it rather than re-deriving a message.
- **An empty result and a failed query must look different.** `AppEmptyState` and `AppErrorState` are
  separate widgets for that reason; never fall back to sample data on error.

**Theme and widgets.**

- `AppTheme.lightTheme` / `darkTheme` (`core/theme/app_theme.dart:12`, `:134`), both wired in
  `main.dart:41-43`. `themeModeProvider` lives in that same file (`:7`).
- `core/constants/` holds static-only classes with private constructors (`AppSpacing._()`).
  `AppSpacing` exposes the scale **and pre-baked `const EdgeInsets` and `const SizedBox` gaps**
  (`paddingAllLg`, `gapV16`, …). Use those rather than literal `EdgeInsets.all(16)`.
- `core/widgets/` is the design system, one widget family per file, all prefixed `App*` — `AppButton`,
  `AppCard`, `AppChip`, `AppSearchBar`, `AppEmptyState`, `AppErrorState`, `AppLoadingState`,
  `AppSkeleton`, `AppImagePlaceholder`, `AppBottomSheet`, `OfflineStatusBar`. **Variants are an enum
  parameter on one class, not subclasses** (`AppButtonVariant`, `app_button.dart:5`).
- `shared/widgets/` holds domain composites without the prefix (`ArtisanCard`, `CraftProductCard`,
  `SocialShareSheet`). The `core/` vs `shared/` widget split is not principled; match the
  neighbouring file.
- `ConsumerWidget` for pure reads; `ConsumerStatefulWidget` once there is a `TextEditingController`
  or an `_isLoading` flag.

**Strings.** All user-facing text is an English literal inline in widget code. There is **no i18n
infrastructure at all** — no `flutter_localizations`, no `l10n.yaml`, no `.arb` files, no
`localizationsDelegates`. `intl` is used only for `NumberFormat.currency` (INR) and `DateFormat`
with hard-coded patterns. Do not add a string to a nonexistent localisation system; see PRD §8
item 8 for the gap this leaves against the product promise.

## 7. Backend conventions actually in use

- Routers are plain `APIRouter()`; **`app/main.py` owns the `/api/v1/<domain>` prefix**. `analytics`
  keeps an internal prefix as a documented exception (`main.py:189-197`).
- Config only via `get_settings()` (`core/config.py`, `@lru_cache`, reads `backend/.env`). Never
  `os.getenv` in new code — `core/redis.py:12` is an existing violation, not a precedent.
- Auth via `Depends(get_current_user)` / `get_optional_current_user` from `core/security.py`.
- Rate limiting via `core/rate_limit.check_rate_limit(store, key, max, window)` with a per-router
  store. **In-memory and per-process** (`rate_limit.py:16-19`). The Dockerfile runs a single
  gunicorn worker, which keeps one quota per instance; any increase in worker count multiplies the
  effective limit and needs a shared store first.
- Redis is optional and degrades to an in-memory dict; it is never required at startup
  (`core/redis.py:23-32`, `main.py:117-120`).

**The three canonical AI features.** These are the only live AI path (D-14).

| Endpoint | Auth | What actually runs |
|---|---|---|
| `POST /api/v1/catalog/generate` | `get_current_user` (`catalog.py:456`) | OpenRouter via `QWEN_MODEL`; one strict-JSON retry then hard 502 (`catalog.py:260-437`) |
| `POST /api/v1/catalog/voice` | `get_current_user` (`catalog.py:506`) | Sarvam STT (`app/ai/speech.py:49-116`) → the same generator. **Hard 500 without `SARVAM_API_KEY`** (`speech.py:72-78`) |
| `POST /api/v1/pricing/predict` (+ deprecated `/suggest`) | `get_optional_current_user` (`pricing.py:870`) | Pure LLM via `DEEPSEEK_MODEL` |
| `POST /api/v1/pricing/analyze` | `get_current_user` (`pricing.py:947`) | Vision extraction (`app/ai/vision.py`) → **deterministic** price from `app/services/pricing_engine.py::compute_price`; skips the AI call entirely when the seller supplies category+size+quality+complexity (`pricing.py:983-995`) |
| `POST /api/v1/image/enhance` | `get_current_user` (`image.py:351`) | **No LLM.** OpenCV + PIL via `app/vision/pipeline.py` — GrabCut background removal, CLAHE, compose on white, crop, resize. Three-tier degradation (`app/vision/background.py:11-19`) |

`/pricing/analyze` and `/image/enhance` are the best-engineered paths in the backend: the price is
computed and every factor returned, and the vision model chooses parameters rather than touching
pixels (D-4 still holds).

**Known defects in these paths — do not "fix" them blind, they are recorded in PRD §8:**

- `pricing.py:305` and `:330` call `get_supabase_client()`, which is **not imported at module
  level** (the only import is function-local at `:904`). Both call sites sit inside bare
  `except Exception` handlers (`:309-310`, `:341-342`), so the `NameError` is swallowed and the code
  always falls through to a hard-coded 9-entry `category_defaults` dict (`:311-321`). The advertised
  live demand index has never executed.
- `DEEPSEEK_MODEL` previously defaulted to the paid slug `deepseek/deepseek-chat`, contradicting
  D-13 in the same file that cites it. **Fixed 2026-09-12** — all three model settings now point at
  `google/gemma-4-31b-it:free` (`core/config.py:69`, `:75`, `:77`, with the rationale in the
  comment at `:70-74`). Keep them on `:free` slugs; the env var still overrides if a paid model is
  ever deliberately chosen.

**The unified agent is unmounted (D-14).** `main.py:165-173` carries the commented-out mount and the
rationale. `app/agent/models.py` is kept because its free-model catalogue (15 `:free` slugs) and
`complete()` fallback walker (`:227-367` — retries on 402/408/409/429/5xx, caches 403/404 as
unavailable, aborts on 401) exist nowhere else and are what make D-13 affordable. Note
`main.py:13` still imports `app.api.agent`, so the package loads at startup even though no route
uses it. Re-mounting reopens D-14.

**The authentication bypass — read this before touching `core/security.py`.**
`_is_debug_mock_allowed()` (`security.py:145-155`) returns true when
`bool(settings.DEBUG) or settings.APP_ENV.lower() != "production"`, and `APP_ENV` **defaults to
`"development"`** (`config.py:25`). When it is true, `_decode_jwt_without_verify`
(`security.py:158-178`) base64-decodes a token's payload with no signature check, and an opaque
token is met by a fabricated payload (`security.py:260-283`). Anyone can mint
`{"uid": "<any-victim-uid>"}` and be that user. The condition fails *open*: if `get_settings()`
throws, the fallback re-reads raw env with the same `!= "production"` default. Startup detects
production+DEBUG and only logs CRITICAL, with a comment confirming it takes no action
(`main.py:97-100`). This is PRD §8 item 1 and is the highest-severity item in the repository. The
Supabase branch by contrast verifies properly and is not implicated.

**Most routers are not backed by data.** 71 routers exist; **21 import Supabase**
(`admin, analytics, auth, business_suite, clusters, growth, image, inventory, marketplace,
notifications, orders, passports, payments, pricing, products, quality, recommendations, shipping,
storefront, sustainability, voice`). The other ~50 delegate to module-level singletons holding
Python lists and `uuid4()` — e.g. `core/blockchain_provenance.py:121,182`,
`services/iot_service.py:172,198`, `services/ondc/ondc_service.py:23`, `core/quantum_security.py:192`.
That state is per-process and does not survive a restart or a second instance. Treat them as demoware; do not
extend one believing it persists.

**Data access.** `get_supabase_client()` (`database/connection.py:92-108`) is `@lru_cache`d and
**synchronous** — every `.execute()` in an async handler blocks the event loop, which the module's
own header states (`:14-17`). `/health` blocks the loop for the same reason (`:220-237`,
`main.py:154`). `get_supabase_anon_client()` **silently falls back to the privileged client** when
`SUPABASE_KEY` is unset (`:140-142`). There is no asyncpg pool; the psycopg2 pool is optional and
unused (`:168-204`).

**Tests.** 81 files, 819 `def test_`, 59 of them `async def`. `conftest.py` mocks by
`os.environ.setdefault` at import time only (`:5-13`) plus synthetic-image fixtures; there is **no
shared client fixture**, so 76 files each wire their own `app.dependency_overrides`. This is why
`get_optional_current_user` carries ~70 lines of reflection to honour those overrides
(`security.py:334-379`) — production code shaped by the harness. **There is no `pytest.ini`,
`pyproject.toml`, `setup.cfg` or `tox.ini` anywhere**, so `pytest-asyncio` has no `asyncio_mode` and
the async tests likely do not execute — a hazard `requirements.txt:42-44` documents explicitly.
Re-baseline before treating any failure as a regression.

## 8. Working agreements

- **Plan before scope.** Any new scope — including follow-on work immediately after finishing
  something — starts with a plan and waits for a go-ahead. Report what was done, what was verified,
  and what was skipped, separately.
- **Verification means running it.**
  - Client: `cd app && flutter analyze` and `flutter test`. Behaviour changes need a run on a real
    device or emulator with a seeded account.
  - Backend: `cd backend && python -m pytest tests -q`. Read §7 on the pytest config gap before
    trusting a green run.
  - "Verified" in a report means one of those happened. Nothing in this session was run.
- **Commands that work on this machine** (Windows, Git Bash or PowerShell):
  - `cd app && flutter pub get && flutter run -d <device>`
  - `cd app && flutter analyze` · `flutter test`
  - `cd backend && uvicorn app.main:app --reload` (needs `backend/.env`)
  - `python app/tool/seed_demo.py` — idempotent demo seeding through the anon key, so it obeys RLS
    exactly like the app.
- **Concurrent sessions.** More than one session may be working in this repository. `app/` and
  `backend/` may be owned by another session at any time; confirm before editing either.
- **Git:** single `master`, pushed to `origin`. Commit messages are one lowercase imperative sentence, no
  prefix ("record the live schema in the repository"). Do not introduce Conventional Commits or a
  `develop` branch without a decision. There is no CI anywhere — no `.github/workflows/`.
- **Secrets:** `backend/.env`, `local.properties`, keystores and `google-services.json` are
  gitignored — keep it that way. Do not add a second copy of a key to `app/`.
- **Decisions:** anything that changes an architectural or product rule gets a `D-n` entry in
  `memory/decisions.md` in the same change. **Entries are appended, never rewritten.** To reverse
  one, add a new entry naming the old one and mark the old `Status: superseded by D-n`. Where the
  code has already outrun a decision, that is an open item in PRD §8, not licence to edit the log.
- **Docs-as-code:** if you change behaviour this file or `PRD.md` describes, update it in the same
  change.

## 9. Things not to assume

**Client**

- No Java, no Kotlin app code, no Android-native UI. No ViewBinding, no XML layouts, no
  `@ServerOwned`/`SupabaseGson`, no PostgREST literal-filter strings like `"eq." + id`, no
  `SessionManager`, no Retrofit/OkHttp/Glide/Room/WorkManager. All of that belonged to the archived
  Android app.
- No Riverpod code generation, no `freezed`, no `json_serializable`, no `build_runner`. No
  `Notifier`/`AsyncNotifier`. No DI framework.
- No `fromJson`/`toJson` on models — it is `fromRow`/`toRow`.
- No named go_router routes.
- No i18n. No `flutter_localizations`, no `.arb` files.
- No image upload **from the client to Supabase Storage directly**. There are still zero
  `.storage.from(...)` calls and the four bucket names in `supabase_config.dart:6-9` are still unused
  by Dart. Images reach storage only via the backend, which uploads under the caller's own token so
  RLS applies, and returns the image inline when storage rejects it. The product-creation wizard
  still takes pasted URLs (`product_creation_wizard_screen.dart:543-547`).
- No real offline support. `core/sync/sync_manager.dart::_processAction` is a
  `Future.delayed(600ms)` that discards the action (`:112-117`), `queueAction` (`:71`) is never
  called, and connectivity is a manually toggled in-memory enum. `OfflineStatusBar` is mounted but
  its pending count is permanently 0.
- The seven providers in `features/ai/data/ai_providers.dart:5-35` are still all `Mock*`, and
  `catalog_studio` and `live` are still mocks. **But "no real AI in the client" is no longer true:**
  the three live features run through `BackendAiRepository` from `AiStudioScreen` (§4). Those are
  two parallel implementations — check which one a screen uses before reasoning about it.
- No `Result`/`Either`, and `core/errors/` is dead code.
- Do not treat `features/{craft_passport,notifications,quotes,settings,storefront}/` as existing
  features — they are empty but for a README.

**Backend**

- No Redis (not installed), no Celery, no second region, no Kong, no message queue.
- No ORM in use, no migrations, no `alembic.ini`, no schema in the repository.
- No deployment. `backend/nginx/nginx.conf` proxies to Docker-Compose services `backend` and `web`,
  and **there is no compose file anywhere in the repository** and no `web` service — nginx cannot
  start as committed. Domains are also split: nginx serves `kalacart.shop` while the code sends
  `HTTP-Referer: https://kalacart.in`.
- No CI has ever run; test counts in any document are historical until someone runs them.
- The unified agent is not live (D-14), and `scripts/agent_smoke_test.py` exercises that unmounted
  code.
- `rembg` is not used; background removal is OpenCV GrabCut.

**Repository and product**

- There is no `web/`, no admin UI, no moderation queue anywhere in this tree.
- **There is no `pending`/`approved` ministry gate in the client.** `ProductStatus` is
  `{published, draft, archived}` (`product.dart:16-27`), `ProductInput` defaults to `published`
  (`:199`), sellers self-publish, and the app writes `is_active` itself (`:214`) rather than leaving
  it to a trigger. D-10 and D-12 describe the archived Android behaviour and are contradicted by the
  code; this is an unresolved cross-component conflict, recorded at PRD §3 and §8 item 3 — do not
  resolve it by editing either document or the decision log.
- No git remote, no CI, no release signing (Android release builds use the debug keystore).
