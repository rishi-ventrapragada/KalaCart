"""Festival demand prediction & recommendation service."""

from datetime import datetime, timezone, date
from typing import Dict, List, Optional
from app.models.festival import (
    FestivalPredictionResponse,
    FestivalPoster,
    ProductFestivalRecommendation,
)

# Festivals calendar for 2026/2027
FESTIVAL_CALENDAR = [
    {
        "key": "dussehra",
        "name": "Dussehra & Navratri",
        "month": 10,
        "day": 20,
        "year": 2026,
        "surge_pct": 175,
        "color_hex": "#D84315",
        "audiences": ["Devotees", "Cultural Collectors", "Festive Decorators", "B2B Gift Buyers"],
        "trending_crafts": ["Clay Idols & Golu Dolls", "Kondapalli Wood Toys", "Chaniya Cholis & Bandhani", "Brass Pooja Bells", "Terracotta Torans"],
        "price_factor": 1.15,
        "default_products": [
            ("Traditional Kondapalli Wooden Toy Set", "woodwork", 12, 45, 1400.0, 1650.0, 17.8, "High pre-Navratri demand for traditional doll arrangements."),
            ("Handcrafted Clay Durga & Pooja Idols", "pottery", 8, 60, 650.0, 750.0, 15.3, "Steep ceremonial demand spikes 2-3 weeks before festival."),
            ("Embroidered Garba Chaniya Choli", "textile", 5, 25, 3200.0, 3600.0, 12.5, "Peak wedding and seasonal festival attire procurement.")
        ],
        "headline": "Celebrate Navratri & Dussehra with Authentic Indian Crafts",
        "tagline": "Handmade with Sacred Tradition & Devotion",
        "offer": "Pre-Festive Artisan Special: Up to 20% Off",
        "hashtags": ["#NavratriCrafts", "#Dussehra2026", "#GoluDolls", "#IndianArtisans", "#KalaCartHandmade"],
        "steps": [
            "Prepare 3x standard weekly raw material inventory 30 days in advance.",
            "Bundle complementary items (e.g. Diya + Puja thali) for higher Average Order Value.",
            "Update product titles with high-intent festival keywords ('Navratri Golu', 'Dussehra Decor')."
        ]
    },
    {
        "key": "diwali",
        "name": "Diwali (Festival of Lights)",
        "month": 11,
        "day": 8,
        "year": 2026,
        "surge_pct": 240,
        "color_hex": "#F57C00",
        "audiences": ["Home Decorators", "Corporate Gifting", "Families", "Global NRI Shoppers"],
        "trending_crafts": ["Terracotta Diya Sets", "Brass Lamps & Kuthu Vilakku", "Banarasi & Handloom Silk Sarees", "Handmade Torans & Hangings", "Carved Wooden Gift Boxes"],
        "price_factor": 1.20,
        "default_products": [
            ("Hand-Painted Terracotta Diya Set (Pack of 12)", "pottery", 20, 150, 450.0, 550.0, 22.2, "Highest selling craft item in India during Q4."),
            ("Pure Brass Kuthu Vilakku Oil Lamp", "metalwork", 4, 30, 2400.0, 2850.0, 18.7, "Symbolic auspicious lighting piece in corporate and home gifting."),
            ("Handwoven Banarasi Silk Brocade Dupatta", "textile", 10, 40, 2100.0, 2450.0, 16.6, "Festive attire gifting surge across all metro buyer segments.")
        ],
        "headline": "Illuminate Your Home with Pure Handmade Radiance",
        "tagline": "Direct from the Master Artisans of India",
        "offer": "Festive Gift Hampers: Flat 15% Off on Bulk Orders",
        "hashtags": ["#Diwali2026", "#FestivalOfLights", "#ArtisanDiyas", "#VocalForLocal", "#KalaCartFestive"],
        "steps": [
            "Stock packing material and break-proof bubble/corrugated cushioning early.",
            "Initiate corporate gifting outreach 45 days ahead of Diwali.",
            "Schedule social media promotions featuring master artisans at work."
        ]
    },
    {
        "key": "christmas",
        "name": "Christmas & New Year",
        "month": 12,
        "day": 25,
        "year": 2026,
        "surge_pct": 140,
        "color_hex": "#C2185B",
        "audiences": ["Holiday Gift Shoppers", "International Export Buyers", "Interior Stylists"],
        "trending_crafts": ["Hand-Carved Wooden Baubles", "Cashmere & Pashmina Shawls", "Artisanal Scented Soy Candles in Terracotta", "Jute Christmas Stockings"],
        "price_factor": 1.12,
        "default_products": [
            ("Hand-Carved Channapatna Wooden Holiday Ornaments", "woodwork", 15, 60, 850.0, 950.0, 11.7, "Eco-friendly natural lac-turned tree decorations."),
            ("Pashmina Wool Handwoven Winter Shawl", "textile", 6, 25, 4500.0, 5100.0, 13.3, "Peak winter gifting item with premium export appeal.")
        ],
        "headline": "Eco-Friendly Christmas Crafts from Heart of India",
        "tagline": "Warmth, Heritage & Sustainable Holiday Cheer",
        "offer": "Holiday Season Special: Free Gift Packaging Included",
        "hashtags": ["#EcoChristmas", "#HandcraftedHolidays", "#WoodenOrnaments", "#SustainableCrafts"],
        "steps": [
            "Emphasize zero-plastic compostable holiday packaging.",
            "Highlight craft heritage stories for international export buyers."
        ]
    },
    {
        "key": "pongal",
        "name": "Pongal",
        "month": 1,
        "day": 14,
        "year": 2027,
        "surge_pct": 160,
        "color_hex": "#388E3C",
        "audiences": ["Traditional Households", "South Indian Diaspora", "Organic Living Communities"],
        "trending_crafts": ["Traditional Terracotta Pongal Cooking Pots", "Handloom Cotton Dhotis & Angavastrams", "Brass Serving Uruli", "Palm Leaf Baskets"],
        "price_factor": 1.15,
        "default_products": [
            ("Traditional Hand-Painted Terracotta Pongal Pot", "pottery", 10, 80, 550.0, 650.0, 18.1, "Harvest festival core utility with sacred hand-drawn kolam motifs."),
            ("Pure Brass Traditional Cooking Uruli", "metalwork", 3, 20, 3200.0, 3600.0, 12.5, "Auspicious harvest cooking vessel in high demand.")
        ],
        "headline": "Harvest the Joy of Authentic Tradition this Pongal",
        "tagline": "Pure Clay, Sacred Brass, and Heritage Weaves",
        "offer": "Harvest Combo: Pot + Ladle Set at 15% Off",
        "hashtags": ["#Pongal2027", "#HarvestFestival", "#TerracottaPot", "#TraditionRenewed"],
        "steps": [
            "Procure fine river clay ahead of winter rains.",
            "Collaborate with nearby village clusters for combined harvest bazaar offers."
        ]
    },
    {
        "key": "sankranti",
        "name": "Makar Sankranti",
        "month": 1,
        "day": 14,
        "year": 2027,
        "surge_pct": 150,
        "color_hex": "#FBC02D",
        "audiences": ["Families", "Kite Festival Enthusiasts", "Ethnic Wear Lovers"],
        "trending_crafts": ["Handmade Paper Kites & Spools", "Black Handloom Cotton Sarees", "Sesame Serving Terracotta Bowls", "Bamboo Baskets"],
        "price_factor": 1.12,
        "default_products": [
            ("Handloom Black Chandrakala Saree with Zari Border", "textile", 4, 30, 2800.0, 3200.0, 14.2, "Cultural tradition of wearing black on Sankranti drives heavy demand.")
        ],
        "headline": "Soar High with Traditional Crafts this Sankranti",
        "tagline": "Bright Hues, Pure Handloom & Auspicious Heritage",
        "offer": "Festive Celebration Pack: Free Shipping on Pre-orders",
        "hashtags": ["#MakarSankranti", "#KiteFestival", "#HandloomPride", "#KalaCart"],
        "steps": [
            "Feature sun and harvest motifs in product descriptions."
        ]
    },
    {
        "key": "eid",
        "name": "Eid-ul-Fitr",
        "month": 3,
        "day": 21,
        "year": 2027,
        "surge_pct": 170,
        "color_hex": "#00796B",
        "audiences": ["Festive Shoppers", "Fashion & Jewelry Lovers", "Home Entertaining Hosts"],
        "trending_crafts": ["Zardozi & Chikankari Kurtas", "Silver Filigree Jewelry", "Ceramic Serving Platters & Bowls", "Handcrafted Attar Glass Bottles"],
        "price_factor": 1.18,
        "default_products": [
            ("Handcrafted Lucknowi Chikankari Kurta", "textile", 8, 45, 2600.0, 3050.0, 17.3, "Major festive wardrobe staple across India and Middle East."),
            ("Cuttack Silver Filigree (Tarakasi) Earrings", "jewelry", 6, 35, 1950.0, 2300.0, 17.9, "Intricate ceremonial gifting favorite during festive season.")
        ],
        "headline": "Cherish the Blessings of Eid with Pure Craftsmanship",
        "tagline": "Finest Chikankari, Silver Filigree & Festive Elegance",
        "offer": "Eid Special: Complimentary Gift Box on Orders above ₹2,000",
        "hashtags": ["#EidMubarak", "#Chikankari", "#SilverFiligree", "#FestiveElegance"],
        "steps": [
            "Stock festive textiles 40 days in advance of Ramadan/Eid.",
            "Offer premium gift packaging options for family gifting."
        ]
    }
]


def get_upcoming_festival(target_key: Optional[str] = None) -> FestivalPredictionResponse:
    now = datetime.now(timezone.utc)
    today = now.date()

    selected_fest = None
    if target_key:
        for f in FESTIVAL_CALENDAR:
            if f["key"].lower() == target_key.lower():
                selected_fest = f
                break

    if not selected_fest:
        # Find nearest upcoming festival
        best_diff = 9999
        for f in FESTIVAL_CALENDAR:
            f_date = date(f["year"], f["month"], f["day"])
            diff = (f_date - today).days
            if 0 <= diff < best_diff:
                best_diff = diff
                selected_fest = f

        if not selected_fest:
            selected_fest = FESTIVAL_CALENDAR[0]

    f_date = date(selected_fest["year"], selected_fest["month"], selected_fest["day"])
    days_rem = max(1, (f_date - today).days)

    # Build recommendations
    recs = []
    for title, cat, cur_stk, rec_stk, cur_p, sug_p, p_adj, reason in selected_fest["default_products"]:
        recs.append(ProductFestivalRecommendation(
            product_id=None,
            product_title=title,
            category=cat,
            current_stock=cur_stk,
            recommended_stock=rec_stk,
            current_price=cur_p,
            suggested_price=sug_p,
            price_adjustment_pct=p_adj,
            reasoning=reason,
            confidence_score=88
        ))

    poster = FestivalPoster(
        headline=selected_fest["headline"],
        tagline=selected_fest["tagline"],
        offer_text=selected_fest["offer"],
        theme_color_hex=selected_fest["color_hex"],
        hashtags=selected_fest["hashtags"],
        suggested_caption=(
            f"{selected_fest['headline']}! 🎉\n\n"
            f"{selected_fest['tagline']}. "
            f"Handmade by master artisans. {selected_fest['offer']}.\n\n"
            f"Shop authentic, support local: {' '.join(selected_fest['hashtags'])}"
        )
    )

    return FestivalPredictionResponse(
        festival_key=selected_fest["key"],
        festival_name=selected_fest["name"],
        festival_date=f_date.strftime("%B %d, %Y"),
        days_remaining=days_rem,
        demand_surge_pct=selected_fest["surge_pct"],
        target_audiences=selected_fest["audiences"],
        trending_crafts=selected_fest["trending_crafts"],
        recommended_products=recs,
        promotional_poster=poster,
        actionable_preparation_steps=selected_fest["steps"]
    )
