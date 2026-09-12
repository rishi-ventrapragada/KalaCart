# KalaCart — decisions log (§D)

One entry per decision that changes an architectural or product rule. Seeded 2026-09-11 **only**
with decisions that already carry an explicit rationale somewhere in the repository (a code
comment, a doc, a commit). Nothing here is inferred from behaviour alone. The log grows from here;
entries are appended, never rewritten. To reverse one, add a new entry that names the old one and
mark the old one `Status: superseded by D-n`.

## Format

```
### D-n · YYYY-MM-DD · one-line statement of the rule
Source: file / doc / commit where the rationale is recorded
Reasoning: why, in the words of the source where possible
Status: active | superseded by D-n
```

---

## Active decisions

### D-1 · 2026-09-01 · The Android app is Java only — no Kotlin
Source: `KalaCart/android-app/docs/architecture.md` §Key Decisions.
Reasoning: "Java only — no Kotlin, to ensure SIH evaluator compatibility."
Status: active. (The archived Sep 7 docs claiming Kotlin/Compose were wrong, not a reversal.)

### D-2 · 2026-09-11 · One agent endpoint runs all three AI features, not three endpoints
Source: `KalaCart/docs/UNIFIED_ARTISAN_AGENT.md` §1; `backend/app/agent/orchestrator.py` docstring.
Reasoning: the stages feed each other — what the vision model sees grounds the catalog text, and
both inform the price; three separate endpoints "would discard that context and cost three round
trips over a rural mobile connection."
Status: active. Not yet wired to any screen (PRD §3).

### D-3 · 2026-09-11 · The agent uses only OpenRouter `:free` models, walked in a fallback chain ordered by measured latency
Source: `UNIFIED_ARTISAN_AGENT.md` §3; `backend/app/agent/models.py` header and chain comments.
Reasoning: zero per-token cost for the platform; free models are rate-limited and uneven, so the
router falls back on 402/408/409/429/5xx, transport errors, empty and truncated replies. Chains are
ordered by measured latency, not benchmark score, because "an artisan on a phone should not wait
88 s when a 12 s model produces an equally valid listing." 403/404 mark a slug unavailable for the
process; 401 aborts the chain.
Status: active.

### D-4 · 2026-09-11 · The vision model never touches pixels; it chooses parameters, OpenCV executes
Source: `UNIFIED_ARTISAN_AGENT.md` §2 ("Design decision").
Reasoning: keeps output reproducible and means "a hallucinating model can never corrupt an
artisan's photo." A failed vision analysis does not block enhancement — the pipeline runs with
defaults.
Status: active.

### D-5 · 2026-09-11 · In agent output, only `description_hi` is Hindi; every other field is English, enforced by validation
Source: `UNIFIED_ARTISAN_AGENT.md` §4 "Field languages"; `agent/tools.py::_validate_catalog`.
Reasoning: without the check "roughly one run in three returned the title and materials in Hindi,
which breaks search." Enforced twice: per-field in the prompt and by rejecting responses whose
`title`/`description_en` are Devanagari or whose `description_hi` is not.
Status: active.

### D-6 · 2026-09-11 · The OpenRouter key lives only on the server, never in the APK
Source: `UNIFIED_ARTISAN_AGENT.md` §6; `ArtisanAgentRepository.java` class comment.
Reasoning: a key shipped in the binary can be extracted.
Status: active.

### D-7 · 2026-09-11 · Release signing credentials come only from environment / gradle properties; there are no defaults
Source: `android-app/app/build.gradle` comment; commit `e881094` "remove hardcoded release keystore passwords".
Reasoning: "an unconfigured machine produces an unsigned release build rather than one signed with
a credential committed to the repo."
Status: active.

### D-8 · 2026-09-11 · The app writes only real live columns: explicit insert bodies, and `@ServerOwned` fields are excluded from every request
Source: `data/model/ServerOwned.java`, `data/supabase/SupabaseGson.java`, `data/model/ProductInsert.java`
javadoc; commits `cd83cab` "stop writing server-owned profile and seller columns" and `8a4371c`
"insert products with real columns and a real category_id".
Reasoning: sending the domain model directly "makes PostgREST reject the whole insert" because it
carries fields with no column; database-owned values (trigger-maintained, or set by the ministry
admin) must be readable but never written by the app. Serialization is asymmetric on purpose.
Status: active.

### D-9 · 2026-09-11 · `products.seller_id` is `sellers.id`; a null seller id blocks publishing rather than falling back to another id
Source: `SessionIdentityResolver.java` and `SessionManager.getSellerId()` javadoc; commit `1a84b6b`
"resolve and cache Supabase row identity after sign-in".
Reasoning: the identity chain is `auth.uid() == profiles.auth_user_id → profiles.id == sellers.profile_id
→ sellers.id → products.seller_id`; "the auth uid is not a valid products.seller_id. Callers must …
treat a null value as 'cannot write products' rather than substituting the auth uid."
Status: active.

### D-10 · 2026-09-11 · Every listing inserts as `status = 'pending'`; only the ministry admin moves it on; "Save as Draft" is hidden
Source: `ProductInsert.java` (`STATUS_PENDING`), `AiProductReviewActivity.setupActionButtons` comment;
commit `855a6f3` "hide Save as Draft on the AI product review screen".
Reasoning: "a seller cannot publish straight to approved"; and "there is no local draft store, so
[Save as Draft] submitted to the ministry approval queue exactly like Publish. A draft button that
silently submits is worse than no draft button."
Status: active. Note: the admin side that moves status onward does not exist yet (PRD §7 item 2).

### D-11 · 2026-09-11 · Data screens show no mock fallback; empty and broken must look different
Source: `MyProductsFragment.loadProducts` comment; `CategoryRepository` javadoc ("an RLS denial
surfaces here, not as an empty list").
Reasoning: "showing sample listings when the query returns nothing, fails, or the seller row is
missing makes an empty catalogue and a broken query look identical." Errors carry the PostgREST
message to the user.
Status: active. `AiProductServiceImpl` is a labelled placeholder, not a fallback, and is outside
this rule until PRD §3 is resolved.

### D-12 · 2026-09-11 · Buyer-visible catalogue is `status = 'approved' AND is_active = true`; `is_active` is trigger-owned
Source: `SupabaseService.getMarketplaceProducts` javadoc; `Product.isActive` javadoc; commit
`a8e6d20` "filter buyer-side products on status and is_active".
Reasoning: "the live products table has no is_published or is_deleted column: visibility is
status='approved' plus is_active, where is_active is kept in sync with status by a database trigger."
Status: active.

### D-13 · 2026-09-11 · Text and vision models stay on OpenRouter `:free` slugs; Sarvam speech-to-text is a separate paid service
Source: `backend/app/core/config.py` (`QWEN_MODEL`, `VISION_MODEL`); `backend/.env.example`;
`backend/app/agent/models.py` free-model catalogue.
Reasoning: the AI-Features handover defaulted the catalog and vision models to
`qwen/qwen3.6-flash` and `qwen/qwen3.7-flash`, both paid. Those defaults were not adopted during
the harvest. Both settings are pinned to `google/gemma-4-31b-it:free`, a free vision-capable slug
that the agent's own fallback walker already ranks first, so the text and vision features cost
nothing per token. Sarvam is deliberately outside this rule: it is a speech service, not an
OpenRouter model slug, and there is no free substitute wired in. `POST /api/v1/catalog/voice`
therefore needs a real `SARVAM_API_KEY`; the other two features run without it. Finding a free
STT alternative is an open item — it must not be resolved by quietly restoring paid text models.
Status: active.

### D-14 · 2026-09-11 · The unified artisan agent is superseded and unmounted; the three dedicated endpoints are the only live AI path
Source: `backend/app/main.py` (router commented out with rationale); `backend/app/agent/__init__.py`
module docstring.
Reasoning: the agent and the AI-Features endpoints are two implementations of the same three
features. Keeping both mounted would leave two live paths that can drift apart. The endpoints win
because the agent cannot satisfy the voice requirement on its own — it takes `transcript` as a
string and has no speech-to-text stage — and its image stage returns JSON advice rather than
editing pixels. The agent's code is kept, not deleted: `app/agent/models.py` holds the `:free`
model catalogue and `complete()` fallback walker, which exists nowhere else and is what makes
D-13 affordable. Re-mounting reopens this decision.
Status: active.

### D-15 · 2026-09-12 · Product status maps onto pending/approved/rejected, and there is no review gate
Source: `app/lib/shared/models/product.dart` (`ProductStatus.dbValue`, `kBuyerVisibleStatus`);
`app/lib/features/products/data/supabase_products_repository.dart`.
Reasoning: every product save failed. `products.status` carries a CHECK constraint accepting only
`pending`, `approved` and `rejected`, and the client wrote `published`/`draft`/`archived`, so each
insert raised 23514. The enum keeps its seller-facing names because the catalogue UI is built on
them; only `dbValue` changes. `archived` is carried by `is_active = false`, since the constraint has
no term for it. Buyer-facing queries filter on `kBuyerVisibleStatus` ('approved') rather than on
what sellers write, so unreviewed listings are not shown.

This resolves the *encoding* half of the D-10/D-12 conflict that PRD §8 records. It does not
resolve the *product* half. Measured against the live project on 2026-09-12:

    INSERT status='pending'  -> stored 'approved'   (rewritten)
    INSERT status='rejected' -> stored 'rejected'
    INSERT status='approved' -> stored 'approved'
    UPDATE ...  ='pending'   -> stored 'pending'

Only `pending` is rewritten, and only on INSERT, so this is server-side behaviour on the table, not
a plain column default. A seller tapping Publish therefore reaches buyers immediately, with no
moderation step — D-10/D-12's ministry-approval gate does not exist in any running form. The web
admin declares `getPendingProducts` / `setProductStatus` in `src/lib/data/types.ts`, but its
provider is still `mockProvider`, so nothing implements them.

Building the gate is a separate, unstarted task: drop the server-side rewrite so `pending` persists,
then implement an approval mechanism and a surface to drive it. Writing the right string is not the
same as having a review step, and this entry should not be read as closing that.
Status: active. The missing approval gate is open work, not a decision.

### D-16 · 2026-09-12 · Email confirmation is off in Supabase Auth — a development unblock, not an intended posture
Source: Supabase dashboard (Authentication → Sign In / Providers → Email → "Confirm email" = off).
Not expressible in this repository; recorded here because nothing in the code shows it.
Reasoning: confirmation emails pointed at the project's default Site URL, `http://localhost:3000`,
which nothing serves, so every new signup dead-ended on ERR_CONNECTION_REFUSED. The app defines no
deep-link scheme and `signUp()` passes no `emailRedirectTo`, so there was no in-app landing place
for the link either. Turning confirmation off unblocked account creation for testing in one step.

The trade-off is real and is accepted only for development: anyone can now register with an email
address they do not control, and `auth.users.email` is no longer evidence of anything. This must be
turned back on before the app is exposed to real users, together with the deep-link work that gives
the confirmation link somewhere to land (a `kalacart://` scheme in the Android manifest, an
`emailRedirectTo` on signup, and the redirect allow-list in Supabase).

Recorded after the fact: this was changed during a debugging exchange rather than through the
plan-first process in CLAUDE.md §8, which is the reason it is written down here rather than left as
a dashboard setting nobody can see from the code.
Status: active, and intended to be reversed.

---

### D-17 · 2026-09-12 · Catalog generation runs on nex-agi/nex-n2.5-pro:free, not the gemma slug
Source: `backend/app/core/config.py` (`QWEN_MODEL`), `backend/app/api/catalog.py` (`max_tokens`).
Reasoning: `/api/v1/catalog/generate` returned 502 for every request against the deployed backend.
The cause was upstream and not the key. `OPENROUTER_API_KEY` is valid and unbilled (`/api/v1/key`
reports `usage: 0`, `is_free_tier: true`), but OpenRouter proxies `google/gemma-4-31b-it:free` to
Google AI Studio's *shared* free pool, which is exhausted; the error carries
`"limit_source": "upstream_provider_shared_pool"` and HTTP 429, which `catalog.py` maps onto a 502
for the caller. The gate is per-model, not per-account, so a different `:free` slug clears it.

D-13 still holds: the replacement is a `:free` slug and measured cost is 0 after all testing. This
entry does not supersede D-13, it is an instance of applying it.

`max_tokens` 1500 -> 3000 because the model reasons before answering and ignores
`"reasoning": {"enabled": false}`. Hidden reasoning (400-1400 tokens, variable per call) counts
against the same budget, and on exhaustion the response returns `finish_reason: "length"` with
`content: null`, which the parser then reports as malformed JSON.

Verified against the live deployment after the Render auto-deploy on 2026-09-12:
3/3 valid seven-field responses for en/hi/te, then 4/4 on a second pass at 20 s spacing,
8-26 s per call, Devanagari present in `description_hi` every time.

`VISION_MODEL` and `DEEPSEEK_MODEL` still point at the gemma slug and were deliberately left alone:
`/pricing/analyze` is their only caller, and the client always sends category+size+quality+
complexity, which skips the model call entirely. They will need the same treatment if anything ever
calls the AI-extraction path.

Operational note, not a decision: the free Render instance (512 MB, one worker) returned Render's own
HTML 502 for ~60 s when four catalog calls were issued back to back with ~2 s spacing, `/health`
included, then recovered unprompted. Spacing the same calls 20 s apart was clean. Treat rapid bursts
against the free tier as a load limit of the deployment, not a fault in this path.
Status: active.

---

## Superseded (recorded so they are not re-adopted by accident)

These were the rules of the 2026-09-01/02 system and are contradicted by the code as of 2026-09-11.
No entry above reverses them explicitly because the reversal happened in code without a written
rationale; they are listed so the older docs in `KalaCart/docs/` are read correctly.

- **Firebase Phone OTP as the auth mechanism** (`android-app/docs/architecture.md`, `README.md`,
  `CODEBASE_GUIDE.md` §3). Superseded in code by Supabase GoTrue email/password
  (`SupabaseAuthManager.java`; migration `008_auth_email_migration.sql` marks the turn).
  The backend still assumes Firebase — that is PRD §3, not a rule.
- **"Android never holds Supabase keys; all data goes through FastAPI"** (`CODEBASE_GUIDE.md` §3.1,
  `SECURITY_AUDIT.md` §9). Superseded in code: the anon key is in `strings.xml`/`SupabaseConfig.java`
  and the app talks PostgREST/Storage directly. RLS is now the security boundary.
- **`artisans` table keyed by `firebase_uid` as the user record** (`schema.sql`, `001`–`007`).
  Superseded in code by `profiles` (keyed by `auth_user_id`) + `sellers` / `buyers`.
- **`is_published` / `is_deleted` as the visibility flags** (`006_marketplace.sql`, backend
  `marketplace.py`). Superseded by D-12.
- **`main` / `develop` / `release/*` branching with Conventional Commits** (`MAINTAINER_GUIDE.md`
  §3). Never adopted; the repo has `master` only and one-sentence lowercase commit messages.

---

## Open items (not decisions — things that need one)

Each of these will become a D-n entry when decided. Ordered as in PRD §7.

1. **Backend auth for app requests.** Options on the table: verify Supabase JWTs in
   `core/security.py` (project JWT secret or JWKS) and resolve users via `profiles.auth_user_id`;
   or move the agent call behind a Supabase Edge Function; or drop the FastAPI tier for app traffic
   entirely. Blocks PRD §3.
2. **Wiring the unified agent into `AddProductActivity`** — replace `AiProductServiceImpl` with
   `ArtisanAgentRepository`, per-stage progress UI, behaviour on partial success. Depends on 1.
3. **Where the admin/moderation UI lives** — `web/` (React) vs. something else; auth model for
   admins; whether approval is a status flip or a review workflow with reasons.
4. **Recording the live schema** — `pg_dump --schema-only` committed vs. hand-maintained
   `database/LIVE_SCHEMA.md`; what to do with the 65 stale migrations and their duplicate numbers.
5. **Fate of backend-era Android repositories** that still target FastAPI (`SyncWorker`,
   `CatalogRepository`, `PricingRepository`, `MarketplaceRepository`, `OrderRepository`,
   `PaymentRepository`, `ShippingRepository`, `AnalyticsRepository`, `FCMService`): port, keep,
   or delete — per repository.
6. **Fate of the stub backend modules** (everything the archived docs describe) and their
   migrations: delete, or keep unmounted.
7. **`kalacartflutter/`** — abandoned or under consideration. Treated as parked until confirmed.
8. **Git hygiene** — add a remote; fix or delete `ci.yml`; commit the agent work as one unit;
   update `README.md` to stop describing Firebase OTP.

---

## Pending rewrite — this file, CLAUDE.md and PRD.md (flagged 2026-09-11, CLOSED 2026-09-12)

These three documents moved into the consolidated repository on 2026-09-11 without being
rewritten. They describe the Java/Android stack that the consolidation drops, so large parts of
them are now wrong. Recorded here so the staleness is deliberate and visible, not forgotten.

Known-wrong, verified at relocation time:

- CLAUDE.md §1 and §8 say the repository has no remote. The old repository has one
  (`KalaCart-Website.git`) carrying both the app line and the website line.
- CLAUDE.md says 13 commits; the old repository holds 64 across its branches.
- CLAUDE.md §4 calls `ArtisanAgentRepository.java` uncommitted; it was committed in `ea57144`.
- CLAUDE.md §1 calls `kalacartflutter/` parked and untouched since 2026-09-10. It was not:
  roughly 3.5 hours of work landed on 2026-09-11, now commits 2 and 3 of this repository.
- CLAUDE.md §3, §6 and §9 are Android/Java conventions — ViewBinding, `@ServerOwned`,
  `SupabaseGson`, PostgREST literal filters, "no Kotlin". Under a Flutter client this is most of
  the document and no longer applies.
- CLAUDE.md §7 describes the agent as live. D-14 unmounted it.
- PRD open item 1 (backend auth for app requests) is resolved by `app/core/supabase_auth.py`.
- PRD open item 2 (wiring the agent into `AddProductActivity`) is void — both the agent route and
  the Android client are gone.
- PRD open item 7 (the fate of `kalacartflutter/`) is decided: it is the client.

The rewrite is a separate task. Until it happens, prefer the code and this log over CLAUDE.md
and PRD.md wherever they disagree.

### Closed 2026-09-12

CLAUDE.md and PRD.md were rewritten for the Flutter + FastAPI architecture on 2026-09-12. Every
item listed above is resolved: both documents now describe `app/` (Flutter client, canonical) and
`backend/` (FastAPI), record the fresh repository with no remote, drop the Android/Java
conventions in favour of the Dart ones the code actually shows, note that the unified agent is
unmounted per D-14, and carry PRD open items 1, 2 and 7 as resolved or void. The block is kept
rather than deleted so the history reads correctly.

This file itself was **not** rewritten and did not need to be — D-1 … D-14 are appended history and
stay as written. Where the code has since outrun a decision, the conflict is recorded as an open
item in PRD §8 rather than by editing the entry: most importantly D-10 and D-12 (the client now
uses `published`/`draft`/`archived` with sellers self-publishing, and no ministry-approval gate
exists), which needs a product decision before any superseding entry is written.

Decisions currently living only in code comments, not yet as `D-n` entries — deliberate for now,
and candidates for future entries: **speech-to-text moving on-device in the Flutter client**
(`backend/.env.example`, Sarvam block) and **the D-13 model pinning fix** that repointed
`DEEPSEEK_MODEL` from a paid slug to `google/gemma-4-31b-it:free` (`backend/app/core/config.py`).