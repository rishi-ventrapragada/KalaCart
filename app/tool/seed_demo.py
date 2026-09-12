#!/usr/bin/env python3
"""Seed the KalaCart Supabase project with two demo accounts and demo products.

Uses only the public REST/Auth API with the anon key plus the demo users' own
sessions, so it respects row-level security exactly like the app does.

Requires email confirmation to be either disabled on the project, or the two
accounts to have been confirmed already (e.g. via the Supabase dashboard /
MCP `update auth.users set email_confirmed_at = now()`).

Usage:  python tool/seed_demo.py [--reset-products]
"""
import json
import sys
import urllib.error
import urllib.request

URL = "https://imprsuvtgqxepwzimqmc.supabase.co"
# Publishable key, same one the app ships (lib/core/config/supabase_config.dart).
# Was the legacy anon JWT, which stops working once the legacy JWT-based keys are
# disabled -- and they have to be disabled together with the exposed service_role
# key, since one shared secret signs both.
ANON = "sb_publishable_knkWRgPGlMOSU6XX31Kgbg_MlGxUzon"
PASSWORD = "KalaCart@2026"
BUYER = {"email": "demo.buyer@kalacart.in", "full_name": "Priya Sundaram", "role": "buyer",
         "city": "Bengaluru", "state": "Karnataka", "phone": "+91 98450 11223"}
ARTISAN = {"email": "demo.artisan@kalacart.in", "full_name": "Kripal Kumbh", "role": "seller",
           "city": "Jaipur", "state": "Rajasthan", "phone": "+91 98112 34567"}
SELLER = {"shop_name": "Kripal Kumbh Blue Pottery Studio", "artisan_type": "Pottery & Terracotta",
          "bio": "Third-generation Jaipur Blue Pottery studio shaping quartz-based ceramics with natural cobalt and copper glazes. Every piece is hand-thrown and low-fired in Kot Jewar.",
          "location": "Kot Jewar, Jaipur, Rajasthan", "experience": 22}

PRODUCTS = [
    {"title": "Cobalt Floral Blue Pottery Vase", "category": "Pottery & Terracotta",
     "material": "Quartz powder, fuller's earth, cobalt oxide glaze", "price": 2450, "stock": 18,
     "description": "Hand-thrown Jaipur Blue Pottery amphora vase painted with traditional Mughal floral vines in cobalt and turquoise. Clay-free quartz body, low-fired for a glassy finish. 14 inches tall.",
     "tiers": [(5, 1950), (20, 1650), (100, 1350)]},
    {"title": "Mughal Tile Coasters (Set of 4)", "category": "Pottery & Terracotta",
     "material": "Glazed quartzite, multani mitti", "price": 950, "stock": 42,
     "description": "Four hand-painted 4-inch ceramic tiles with Persian lattice motifs and heat-resistant enamel. Cork-backed. Ideal for corporate gifting.",
     "tiers": [(10, 750), (50, 600)]},
    {"title": "Royal Indigo Decanter & Tumbler Set", "category": "Pottery & Terracotta",
     "material": "Quartz powder, copper oxide, gold leaf trim", "price": 3800, "stock": 5,
     "description": "Limited edition recreation of 18th-century palace dinnerware: one decanter and four tumblers in deep indigo with hand-applied gold leaf rims.",
     "tiers": [(5, 2900)]},
    {"title": "Turquoise Jali Hanging Planter", "category": "Pottery & Terracotta",
     "material": "Natural red clay, turquoise oxide glaze", "price": 1350, "stock": 12,
     "description": "Terracotta planter with hand-cut jali lattice and a turquoise glaze. Comes with a jute hanging rope. 8 inches diameter.",
     "tiers": [(6, 1100)]},
    {"title": "Blue Pottery Door Knobs (Pair)", "category": "Pottery & Terracotta",
     "material": "Quartz ceramic, brass fitting", "price": 640, "stock": 60,
     "description": "Pair of hand-painted ceramic knobs with brass screws. Floral, geometric or peacock motifs. Suitable for cabinets and drawers.",
     "tiers": [(20, 520), (100, 440)]},
    {"title": "Hand-Painted Ceramic Dinner Plate", "category": "Pottery & Terracotta",
     "material": "Food-safe lead-free quartz glaze", "price": 1150, "stock": 30,
     "description": "10-inch dinner plate with a cobalt border and lotus centre. Lead-free food-safe glaze, hand-wash recommended.",
     "tiers": [(12, 950), (48, 820)]},
]


def call(method, path, body=None, token=None, prefer=None):
    req = urllib.request.Request(URL + path, method=method)
    req.add_header("apikey", ANON)
    req.add_header("Authorization", f"Bearer {token or ANON}")
    req.add_header("Content-Type", "application/json")
    if prefer:
        req.add_header("Prefer", prefer)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw.decode(errors="replace")


def sign_in(email):
    code, res = call("POST", "/auth/v1/token?grant_type=password", {"email": email, "password": PASSWORD})
    if code != 200:
        return None, res
    return res["access_token"], res["user"]


def ensure_account(acc):
    token, user = sign_in(acc["email"])
    if token:
        print(f"  signed in {acc['email']}")
        return token, user
    print(f"  sign-in failed ({user}); trying sign-up …")
    code, res = call("POST", "/auth/v1/signup", {
        "email": acc["email"], "password": PASSWORD,
        "data": {"full_name": acc["full_name"], "role": acc["role"]},
    })
    if code not in (200, 201):
        sys.exit(f"  sign-up failed: {code} {res}")
    if not res.get("access_token"):
        sys.exit("  account created but email confirmation is required. Confirm it (dashboard or SQL: "
                 f"update auth.users set email_confirmed_at = now() where email = '{acc['email']}') and re-run.")
    return res["access_token"], res["user"]


def ensure_profile(token, user, acc):
    code, rows = call("GET", f"/rest/v1/profiles?auth_user_id=eq.{user['id']}&select=*", token=token)
    payload = {"email": acc["email"], "full_name": acc["full_name"], "role": acc["role"],
               "city": acc["city"], "state": acc["state"], "phone": acc["phone"]}
    if code == 200 and rows:
        pid = rows[0]["id"]
        call("PATCH", f"/rest/v1/profiles?id=eq.{pid}", payload, token=token)
        print(f"  profile updated {pid}")
        return pid
    payload["auth_user_id"] = user["id"]
    code, res = call("POST", "/rest/v1/profiles", payload, token=token, prefer="return=representation")
    if code not in (200, 201):
        sys.exit(f"  profile insert failed: {code} {res}")
    print(f"  profile created {res[0]['id']}")
    return res[0]["id"]


def ensure_seller(token, profile_id):
    code, rows = call("GET", f"/rest/v1/sellers?profile_id=eq.{profile_id}&select=id", token=token)
    if code == 200 and rows:
        sid = rows[0]["id"]
        call("PATCH", f"/rest/v1/sellers?id=eq.{sid}", SELLER, token=token)
        print(f"  seller updated {sid}")
        return sid
    code, res = call("POST", "/rest/v1/sellers", {"profile_id": profile_id, **SELLER}, token=token,
                     prefer="return=representation")
    if code not in (200, 201):
        sys.exit(f"  seller insert failed: {code} {res}")
    print(f"  seller created {res[0]['id']}")
    return res[0]["id"]


def seed_products(token, seller_id, reset):
    code, existing = call("GET", f"/rest/v1/products?seller_id=eq.{seller_id}&select=id,title", token=token)
    existing = existing if code == 200 else []
    if reset and existing:
        ids = ",".join(p["id"] for p in existing)
        call("DELETE", f"/rest/v1/wholesale_pricing?product_id=in.({ids})", token=token)
        call("DELETE", f"/rest/v1/products?seller_id=eq.{seller_id}", token=token)
        existing = []
        print("  cleared existing products")
    have = {p["title"] for p in existing}
    for p in PRODUCTS:
        if p["title"] in have:
            print(f"  skip existing: {p['title']}")
            continue
        row = {"seller_id": seller_id, "title": p["title"], "description": p["description"],
               "category": p["category"], "material": p["material"], "price": p["price"],
               "stock": p["stock"], "image_urls": [], "is_active": True, "status": "published",
               "city": ARTISAN["city"], "state": ARTISAN["state"]}
        code, res = call("POST", "/rest/v1/products", row, token=token, prefer="return=representation")
        if code not in (200, 201):
            print(f"  product insert failed: {code} {res}")
            continue
        pid = res[0]["id"]
        tiers = [{"product_id": pid, "min_quantity": q, "price": pr} for q, pr in p["tiers"]]
        code, res = call("POST", "/rest/v1/wholesale_pricing", tiers, token=token)
        print(f"  product created: {p['title']} ({pid}) tiers={code}")


def main():
    reset = "--reset-products" in sys.argv
    print("Artisan account")
    a_token, a_user = ensure_account(ARTISAN)
    a_profile = ensure_profile(a_token, a_user, ARTISAN)
    seller_id = ensure_seller(a_token, a_profile)
    print("Products")
    seed_products(a_token, seller_id, reset)
    print("Buyer account")
    b_token, b_user = ensure_account(BUYER)
    ensure_profile(b_token, b_user, BUYER)
    print("Done. Sign in with", BUYER["email"], "or", ARTISAN["email"], "/", PASSWORD)


if __name__ == "__main__":
    main()
