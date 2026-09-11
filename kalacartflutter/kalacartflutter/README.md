# KalaCart

Direct-to-artisan handicraft commerce for Indian craft clusters. Buyers browse
verified artisan products, raise wholesale enquiries (RFQs), chat with the
maker, and order. Artisans list products, quote on enquiries and fulfil orders.

Flutter 3.47 · Riverpod 2 · go_router 14 · Supabase (Auth + Postgres + Realtime).

## Run it

```bash
# Flutter SDK is expected at C:\src\flutter (see .metadata); add it to PATH first
flutter pub get
flutter run -d chrome        # web
flutter run -d windows       # desktop
flutter run -d <android-id>  # needs Android SDK installed
```

Checks:

```bash
flutter analyze
flutter test
```

## Demo accounts

| Role    | Email                       | Password       |
|---------|-----------------------------|----------------|
| Buyer   | demo.buyer@kalacart.in      | KalaCart@2026  |
| Artisan | demo.artisan@kalacart.in    | KalaCart@2026  |

The login screen has chips that fill these in. Both accounts and the artisan's
sample products are created by `tool/seed_demo.py` (Python 3, no extra
packages):

```bash
python tool/seed_demo.py                  # idempotent
python tool/seed_demo.py --reset-products # recreate the sample catalogue
```

The script uses only the public anon key and the demo users' own sessions, so
it behaves exactly like the app under row-level security. Supabase must either
have "Confirm email" disabled for the email provider, or the two accounts must
be confirmed manually (`update auth.users set email_confirmed_at = now() where
email in (...)`) before the script can sign in.

## Backend

Project: `https://imprsuvtgqxepwzimqmc.supabase.co` (config in
`lib/core/config/supabase_config.dart`). Tables used and how the app maps them:

| Table              | Used for                                                       |
|--------------------|----------------------------------------------------------------|
| `profiles`         | one per auth user: `auth_user_id`, `full_name`, `role` (`buyer`/`seller`), `city`, `state`, `phone` |
| `sellers`          | artisan storefront: `profile_id`, `shop_name`, `artisan_type`, `bio`, `location`, `experience` |
| `products`         | listings: `seller_id → sellers.id`, `title`, `description`, `category`, `material`, `price`, `stock`, `image_urls`, `status` (`published`/`draft`/`archived`), `is_active`, `city`, `state` |
| `wholesale_pricing`| quantity breaks: `product_id`, `min_quantity`, `price`          |
| `enquiries`        | RFQs: `product_id`, `buyer_id` (auth uid), `quantity`, `status`, `message` (structured RFQ text, see `RfqDetails`) |
| `messages`         | chat per enquiry: `enquiry_id`, `sender_id`/`receiver_id` (**profiles.id**), `message`, `is_read`. Quotes and order confirmations are `QUOTE:` / `ORDER:` prefixed messages (see `QuoteDetails`, `OrderMessageDetails`) |
| `orders`           | one product per row: `buyer_id` (auth uid), `seller_id`, `product_id`, `quantity`, `unit_price`, `total_amount`, `order_status`, `payment_status`, `shipping_address` |

Auth flow: Supabase email/password. On first sign-in the app creates the
`profiles` row if it is missing. Role comes from `profiles.role`; artisans are
"onboarded" once a `sellers` row exists, buyers once the profile has a name and
city. The router redirects unauthenticated users to `/welcome` and
un-onboarded users to their onboarding screen.

## Code layout

```
lib/
  core/            theme, design tokens, shared widgets, router, config
  features/<f>/    data/ (repositories + providers), domain/ (models), presentation/
  shared/models/   Product, OrderRecord, Enquiry/Quote models, chat models
  shared/services/ userRoleProvider (derived from the signed-in user)
```

Key providers: `currentUserProvider`, `authControllerProvider`,
`publishedProductsProvider`, `productProvider(id)`, `sellerProductsProvider`,
`cartProvider`, `buyerOrdersProvider`, `sellerOrdersProvider`,
`buyerEnquiriesProvider`, `sellerEnquiriesProvider`,
`enquiryMessagesProvider(id)` (realtime), `sellerStorefrontProvider(id)`.

## What is real and what is simulated

Real (Supabase): authentication, profiles and storefronts, product catalogue
and inventory, cart → orders, RFQs, quotes, chat (realtime), order fulfilment
status, provenance passport (derived from product + seller data).

Simulated, clearly labelled in the UI, kept as extension points behind
interfaces in `features/ai` and `features/live`: the AI catalogue studio
(vision/translation/pricing pipeline), the voice assistant, and live-stream
video/chat. Payment at checkout is a demo step: no money moves; orders are
recorded with `payment_status = paid`.

## Notes

- Product images are stored as URLs in `products.image_urls`; there is no
  in-app image picker yet.
- `android/app/src/main/AndroidManifest.xml` declares `INTERNET`; release
  builds need it to reach Supabase.
