# KalaCart — product requirements and build status

Written 2026-09-11 against commit `dbe5beb` ("add seller flow device test script") plus the
uncommitted unified-agent files. Status labels in §5 come from running code paths, not from
documents. For engineering rules see `CLAUDE.md`; for decisions see `memory/decisions.md`.

## 1. Vision

KalaCart lets rural Indian artisans photograph a handicraft, describe it in their own language,
and get a sellable listing — enhanced photo, bilingual description, fair price — which is reviewed
by a ministry moderator and then sold to retail and B2B buyers. The pitch and problem statement
are in `KalaCart/README.md` (§Project Vision), `KalaCart/docs/SYSTEM_ARCHITECTURE.md` §1–2 and
`KalaCart/docs/SIH_DEMO_SCRIPT.md`; they are not repeated here. Target competition: SIH 2026.

The three product promises, in priority order:

1. **Zero-barrier listing** — voice/typed description in any of 12 Indian languages plus one photo
   produces a complete listing. The artisan edits, does not author.
2. **Fair, transparent pricing** — a suggested INR price with a material/labour/skill breakdown the
   artisan can read.
3. **Trusted marketplace** — every listing is moderated before buyers see it; sellers are verified.

## 2. Users and roles

| Role | Where they act | Identity in the data |
|---|---|---|
| **Seller / artisan** | Android app (`KalaCart/android-app/`) | `profiles.role = 'seller'` + a `sellers` row; products carry `sellers.id` |
| **Buyer** | Android app (Discover tab); later web | `profiles.role = 'buyer'` + a `buyers` row |
| **Ministry admin / moderator** | Intended: the website. **No UI exists.** | Sets `products.status` to `approved`/`rejected`; owns `profiles.is_verified`, `verification_level` |

## 3. TOP-PRIORITY GAP — the AI path is broken end to end

This is the most urgent item in the product and is listed on its own so it is not lost in §7.

**The FastAPI backend cannot authenticate any request from the app.** The app signs in with Supabase
GoTrue and sends the Supabase access token as `Authorization: Bearer` (`RetrofitClient.java`).
The backend's `get_current_user` (`backend/app/core/security.py`) verifies a **Firebase** ID token
and then loads the user from `artisans.firebase_uid` — a table the app never writes. Outside
`DEBUG=true` (where the backend falls back to decoding the token without verification) every
authenticated backend call returns 401 or 404. That includes the entire unified agent
(`POST /api/v1/agent/process`, `/agent/catalog`), and the legacy `/catalog/generate`,
`/pricing/*` and `/image/enhance` endpoints.

**On top of that, the AI button the artisan can actually press is a placeholder.** "Continue with
AI →" in `AddProductActivity` calls `AiProductServiceImpl.generateListing`, which picks one of a few
hard-coded listings by keyword-matching the typed description ("terracotta", "jute", "wood"…) after
an 800 ms delay. No photo is analysed, no model is called, no price is computed. The artisan is then
shown that placeholder in `AiProductReviewActivity` as if it were AI output.

The real AI pipeline (`backend/app/agent/`, 42 unit tests, live smoke-tested per
`docs/UNIFIED_ARTISAN_AGENT.md`) exists and works when called with a valid token — but the app has
no client path that reaches it, and `ArtisanAgentRepository.java` is not invoked by any screen.

Consequence: promise #1 and promise #2 in §1 are **not delivered** today, even though both the
listing flow and the AI service are individually "done". Closing this gap requires a decision on
backend auth (accept Supabase JWTs by verifying against the project's JWT secret / JWKS, and resolve
users via `profiles.auth_user_id` instead of `artisans.firebase_uid`), then wiring
`ArtisanAgentRepository` into the add-product step with per-stage progress. Neither has been
decided or started; see `memory/decisions.md` open items.

## 4. Flows that work today (verified route)

From `docs/DEVICE_TEST_SELLER_FLOW.md` and the 2026-09-11 code. "Works" means the Supabase rows
land with the right columns and the screen reflects them.

**Sign-in and identity** — `LoginActivity` → GoTrue password sign-in → `SessionIdentityResolver`
walks `auth.uid()` → `profiles` (created if missing, `role = 'seller'`) → `sellers`. Outcomes route
to Home (`SELLER_READY`), `SellerRegistrationActivity` (`SELLER_REGISTRATION_REQUIRED`) or the
account-type chooser (`NOT_A_SELLER`). `profiles.id` and `sellers.id` are cached in `SessionManager`.

**Seller registration** — multi-step wizard writes a `profiles` row (upsert by `auth_user_id`) then a
`sellers` row with `profile_id`. Server-owned columns are excluded from the write.

**Categories** — Discover tab and the review screen load the live `categories` table (`id`, `name`,
`icon`, `image_url`). Choosing one supplies a real `products.category_id`.

**Add product (the only reachable publishing route)** — Sell tab → *Artisan Management Hub* → `+ Add`
→ `AddProductActivity` (gallery pick or camera via FileProvider) → typed or spoken description →
"Continue with AI →" (placeholder, §3) → `AiProductReviewActivity` (edit name/description/material/
category/dimensions/price) → **Publish** → `ProductInsert` with exactly `seller_id, category_id, title,
description, category, material, price, stock, image_urls, city, state, status='pending'`. "Save as
Draft" is hidden (no draft store). Publishing is blocked with a message if there is no `sellers` row or
no category chosen.

**Image upload** — `ImageRepository` uploads to Storage bucket `product_images` and returns the public
URL; `CreateProductFragment` inserts `product_images` rows (`product_id, image_url, image_order`) once
the product id exists.

**My Products** — lists `products` where `seller_id = sellers.id`, with a real status badge
(`Pending` amber / `Approved` / `Rejected`). No sample data is shown on empty or error.

**Buyer Discover** — lists `products` where `status = 'approved' AND is_active = true` (`is_active` is
trigger-maintained from `status`). Pending products never appear.

## 5. Feature inventory

Status vocabulary:
- **Working** — on the verified route in §4.
- **Wired, unreachable** — client code exists and targets a real endpoint, but nothing in the UI calls it, or the call cannot authenticate (§3).
- **Placeholder** — a stand-in that returns fabricated data by design.
- **Backend only** — endpoint + unit tests exist; never exercised against the live app or live Supabase.
- **Unbuilt** — no real implementation anywhere.
- **Doc only** — exists only in `docs/archive/known-fabricated/`.

| Area | Feature | Status | Where |
|---|---|---|---|
| Auth | Email/password sign-in, sign-up, reset, refresh | Working | `SupabaseAuthManager`, `LoginActivity`, `RegisterActivity` |
| Auth | Identity resolution → profile/seller ids | Working | `SessionIdentityResolver` |
| Onboarding | Seller registration wizard | Working | `SellerRegistrationActivity` |
| Onboarding | Buyer registration | Working (not on device test) | `BuyerRegistrationActivity` |
| Catalogue | Add product with photo (gallery/camera) | Working | `AddProductActivity` |
| Catalogue | AI listing generation (photo + voice → listing) | **Placeholder** in app; **Wired, unreachable** on backend | `AiProductServiceImpl` / `agent/` |
| Catalogue | AI price suggestion with breakdown | **Placeholder** in app; **Wired, unreachable** on backend | same |
| Catalogue | AI photo enhancement (background removal, white canvas) | **Wired, unreachable** | `backend/app/vision/`, `api/image.py`, `api/agent.py` |
| Catalogue | Review/edit listing, submit as pending | Working | `AiProductReviewActivity` |
| Catalogue | My Products with moderation status | Working | `MyProductsFragment` |
| Catalogue | Six-step Capture→Voice→Price→Preview→Publish wizard | Unreachable from navigation | `ui/sell/*` |
| Catalogue | Voice input (SpeechRecognizer, 10+ languages) | Present in `AddProductActivity` ("Speak"/"Type instead"); not verified on device test | `speech/` |
| Catalogue | Offline drafts + WorkManager sync | Backend-era code; `SyncWorker` still targets FastAPI endpoints → unreachable | `data/local/` |
| Moderation | Admin approves/rejects products, verifies sellers | **Unbuilt** — greenfield. `web/` has mock auth and no API integration; no admin screens exist. | — |
| Buyer | Discover approved products by category | Working | `DiscoverFragment`, `DiscoveryRepository` |
| Buyer | Product detail, enquiry to seller | Partially direct-to-Supabase (`enquiries` table); unverified | `ProductDetailsFragment`, `SendEnquiryBottomSheet` |
| Buyer | Wishlist, follow seller, search history, product views | Direct-to-Supabase tables; unverified | `WishlistRepository`, `FollowRepository`, … |
| B2B | RFQ create / quote / compare | Direct-to-Supabase `rfqs`; unverified | `ui/rfq/*` |
| Commerce | Orders, escrow, payments (Razorpay helper), shipping, invoices | Mixed: some direct-to-Supabase, some via FastAPI → unreachable; unverified | `OrderRepository`, `PaymentRepository`, `api/orders.py`… |
| Trust | Seller trust score, verification requests, documents | Direct-to-Supabase; unverified | `trust/`, `TrustVerificationRepository` |
| Messaging | Buyer–seller chat, realtime | Direct-to-Supabase `conversations`/`messages` + `SupabaseRealtimeManager`; unverified | `MessagingRepository` |
| Storefront | Mini storefront pages, deep links | Direct-to-Supabase `storefronts`; unverified | `ui/storefront/*`, `ui/seller/storefront/*` |
| Web | Buyer-facing marketplace site | Prototype with canned fallback data | `web/src/pages/*` |
| Backend | Health, request-id, security headers, rate limiting | Backend only | `main.py`, `core/middleware.py`, `core/rate_limit.py` |
| Backend | Clusters, passports, festival, quality, sustainability, growth, negotiation, forecasting, academy, export, ONDC, live commerce, ERP, AR, digital twin, personalization, heritage, IoT, museum, governance, monitoring, DR, legal, cloud infra… | Backend only (stubs) | `api/*.py` |
| Everything in `docs/archive/known-fabricated/` | PQC crypto, blockchain provenance, multi-region failover, ERP sync, robotics… | Doc only | — |

## 6. The intended AI product (built, not integrated)

Per `docs/UNIFIED_ARTISAN_AGENT.md`, the target experience is **one call** that runs three stages
and degrades per stage:

1. **Image enhancement** — a free vision model assesses the photo and picks parameters; deterministic
   OpenCV executes them (background removal, CLAHE, white balance, unsharp, compose on white, crop to
   1:1 or 4:5, resize). The model never touches pixels.
2. **Multilingual cataloguing** — transcript in any of 12 languages → English title/description/
   category/materials/tags/care + a real Devanagari Hindi description. Every field except
   `description_hi` is English, enforced by validation.
3. **Pricing** — suggested INR price, min/max range, breakdown (material, labour, skill premium,
   platform fee, packaging), justification, confidence.

Contract the UI must honour: `stages[]` reports each stage's success independently; a `200` does
not mean all three worked; show per-stage progress (good runs take ~42–48 s, worst case 240 s per
stage on free models). The OpenRouter key stays on the server.

This is the spec the add-product step should be wired to once §3 is resolved.

## 7. Open items and known gaps

Ordered by how much they block §1.

1. **Backend auth mismatch + placeholder AI button** — §3. Blocks promises #1 and #2.
2. **No admin/moderation UI.** Products are stuck at `pending` unless someone edits rows in the
   Supabase dashboard. The website is greenfield: real auth, role gating, product/seller approval
   queues, and the trigger/RLS on the admin side all need designing. Blocks promise #3.
3. **Live schema is unrecorded.** `database/` does not describe the tables the app writes; migration
   numbers collide. Needs a `pg_dump --schema-only` (or equivalent) committed and the 65 migrations
   either reconciled or archived.
4. **Backend-era Android code still targets FastAPI** (`SyncWorker`, `CatalogRepository`,
   `PricingRepository`, `MarketplaceRepository`, `OrderRepository`, `PaymentRepository`,
   `ShippingRepository`, `AnalyticsRepository`, `FCMService`…). Each is either dead or will fail with
   401 once called. Needs a per-repository decision: port to direct Supabase, keep behind the fixed
   backend auth, or delete.
5. **Uncommitted agent work** — `backend/app/agent/`, `api/agent.py`, `tests/test_agent.py`,
   `scripts/agent_smoke_test.py`, `android-app/…/agent/AgentResult.java`,
   `ArtisanAgentRepository.java`, plus edits to `main.py`, `.env.example`, `ApiService.java`, and
   `docs/UNIFIED_ARTISAN_AGENT.md`. Should be reviewed and committed as one unit.
6. **Voice input on the reachable route is unverified** — the device test uses "Type instead".
7. **Test suites are stale.** Android unit tests predate the Supabase switch; backend tests cover
   stubs as much as real paths; neither runs anywhere. Re-baseline before treating a failure as a
   regression.
8. **Repository hygiene** — no git remote; CI targets branches that do not exist; stub backend
   modules and their migrations remain in the tree; `README.md` still describes Firebase OTP.
9. **`kalacartflutter/` direction** — parked by assumption; confirmation from its owner outstanding.

## 8. Non-goals for now

Nothing in the "Backend only (stubs)" or "Doc only" rows of §5 is in scope until the three product
promises are delivered on the verified route. Specifically out of scope: ONDC, ERP integrations,
multi-region, blockchain/PQC, IoT, live commerce, AR, digital twin, white-label tenancy, and the
public developer API.

## 9. Build status snapshot (2026-09-11)

- `KalaCart/` at `dbe5beb` on `master`; 13 commits since the baseline import earlier the same day, all
  reconciling the Android app with the live Supabase schema. Working tree: 19 docs moved to
  `docs/archive/known-fabricated/` (staged), agent files uncommitted (item 5).
- Debug APK builds with the repaired Gradle wrapper. Device test `A–E` in
  `docs/DEVICE_TEST_SELLER_FLOW.md` is the acceptance run; its results have not been recorded in the
  repo yet.
- Backend: importable; agent smoke test documented as passing live; no test run on this machine.
- Web: `web/dist` last built 2026-09-07; not deployed anywhere known.
