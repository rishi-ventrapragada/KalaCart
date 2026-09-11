"""
KalaCart Phase 6 — Hyper-Personalization AI Engine.

Continuously computes preference weight vectors (region, material, category, festival,
language, price sensitivity, RFQ intent, export intent) and dynamically structures
personalized home feed sections with adaptive widget configurations.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict

from app.models.personalization import (
    UserBehaviorTrack,
    RecommendationWeightsResponse,
    DynamicSection,
    PersonalizedLayoutResponse,
)

logger = logging.getLogger(__name__)

# Base weight lookup for interaction signals
ACTION_WEIGHTS: Dict[str, float] = {
    "search": 1.5,
    "click": 1.0,
    "view": 0.8,
    "like": 2.5,
    "filter_region": 2.0,
    "filter_material": 2.0,
    "festival_browse": 2.2,
    "chat": 3.0,
    "rfq": 4.5,
    "order": 6.0,
}

# Rich Craft Knowledge Base for Persona Generation & Section Assembly
DEFAULT_CRAFT_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "prod_tel_bamboo_01",
        "title": "Telangana Artisanal Bamboo Weave Fruit Basket",
        "category": "Bamboo Craft",
        "material": "Bamboo",
        "region": "Telangana",
        "festival": "Everyday / Eco-Living",
        "price": 890.0,
        "artisan_name": "Kiran Varma",
        "artisan_state": "Telangana",
        "is_gi_certified": True,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1590402494682-cd3fb53b1f70?w=500",
        "rating": 4.9,
    },
    {
        "id": "prod_tel_pochampally_02",
        "title": "Pochampally Double Ikat Silk Saree (GI Tagged)",
        "category": "Handloom Silk",
        "material": "Silk",
        "region": "Telangana",
        "festival": "Wedding",
        "price": 7850.0,
        "artisan_name": "Lakshmi Handlooms",
        "artisan_state": "Telangana",
        "is_gi_certified": True,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=500",
        "rating": 5.0,
    },
    {
        "id": "prod_tel_pembarthi_03",
        "title": "Pembarthi Metal Craft Sheet Brass Wall Hanging",
        "category": "Metal Art",
        "material": "Brass",
        "region": "Telangana",
        "festival": "Diwali",
        "price": 2650.0,
        "artisan_name": "Gopal Chari",
        "artisan_state": "Telangana",
        "is_gi_certified": True,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=500",
        "rating": 4.8,
    },
    {
        "id": "prod_bamboo_lamp_04",
        "title": "Assam Eco Cane & Bamboo Pendant Chandelier",
        "category": "Bamboo Craft",
        "material": "Bamboo",
        "region": "Assam",
        "festival": "Diwali / Home Decor",
        "price": 1450.0,
        "artisan_name": "Biren Bora",
        "artisan_state": "Assam",
        "is_gi_certified": False,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=500",
        "rating": 4.7,
    },
    {
        "id": "prod_wedding_banarasi_05",
        "title": "Bridal Royal Red Banarasi Katan Silk Lehenga Saree",
        "category": "Handloom Silk",
        "material": "Silk",
        "region": "Uttar Pradesh",
        "festival": "Wedding",
        "price": 14500.0,
        "artisan_name": "Ansari Silk Heritage",
        "artisan_state": "Uttar Pradesh",
        "is_gi_certified": True,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1617627143750-d86bc21e42bb?w=500",
        "rating": 4.95,
    },
    {
        "id": "prod_wedding_kundan_06",
        "title": "Jaipur Handcrafted Kundan & Meenakari Bridal Choker",
        "category": "Jewelry",
        "material": "Silver / Kundan",
        "region": "Rajasthan",
        "festival": "Wedding",
        "price": 6200.0,
        "artisan_name": "Mahesh Soni",
        "artisan_state": "Rajasthan",
        "is_gi_certified": True,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=500",
        "rating": 4.9,
    },
    {
        "id": "prod_export_dhokra_07",
        "title": "Bastar Lost-Wax Bell Metal Elephant Sculpture (B2B Pack of 20)",
        "category": "Metal Art",
        "material": "Brass",
        "region": "Chhattisgarh",
        "festival": "Export",
        "price": 18000.0,
        "artisan_name": "Sukhram Bastar Guild",
        "artisan_state": "Chhattisgarh",
        "is_gi_certified": True,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1606293926075-69a00dbfde81?w=500",
        "rating": 4.85,
    },
    {
        "id": "prod_jaipur_blue_pottery_08",
        "title": "Jaipur Blue Pottery Persian Azure Floor Urn (18 inch)",
        "category": "Pottery",
        "material": "Quartz Ceramic",
        "region": "Rajasthan",
        "festival": "Home Decor",
        "price": 3200.0,
        "artisan_name": "Rajesh Prajapati",
        "artisan_state": "Rajasthan",
        "is_gi_certified": True,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1578749556568-bc2c40e68b61?w=500",
        "rating": 4.92,
    },
    {
        "id": "prod_channapatna_toys_09",
        "title": "Channapatna Non-Toxic Lacquer Wood Educational Play Set",
        "category": "Woodcraft",
        "material": "Ivory Wood",
        "region": "Karnataka",
        "festival": "Gifting",
        "price": 1150.0,
        "artisan_name": "Syed Channapatna Toys",
        "artisan_state": "Karnataka",
        "is_gi_certified": True,
        "is_export_ready": True,
        "image_url": "https://images.unsplash.com/photo-1596461404969-9ae70f2830c1?w=500",
        "rating": 4.8,
    }
]


class HyperPersonalizationEngine:
    """Core AI engine for learning user weights and compiling dynamic feeds."""

    @staticmethod
    def calculate_weights(events: List[UserBehaviorTrack], user_id: str, user_role: str = "buyer") -> RecommendationWeightsResponse:
        """Computes multidimensional affinity weights from interaction logs."""
        cat_scores: Dict[str, float] = defaultdict(float)
        mat_scores: Dict[str, float] = defaultdict(float)
        reg_scores: Dict[str, float] = defaultdict(float)
        fest_scores: Dict[str, float] = defaultdict(float)
        lang_counts: Dict[str, int] = defaultdict(int)
        
        rfq_signals = 0.0
        export_signals = 0.0
        prices_seen: List[float] = []

        for ev in events:
            w = ACTION_WEIGHTS.get(ev.action_type.lower(), 1.0) * (ev.metadata.get("weight_override", 1.0) if ev.metadata else 1.0)
            
            if ev.category:
                cat_scores[ev.category] += w
            if ev.material:
                mat_scores[ev.material] += w
            if ev.region:
                reg_scores[ev.region] += w
            if ev.festival:
                fest_scores[ev.festival] += w
            if ev.language:
                lang_counts[ev.language] += 1

            if ev.action_type == "rfq":
                rfq_signals += 1.0
            if ev.metadata and (ev.metadata.get("is_export") or ev.metadata.get("currency") not in (None, "INR")):
                export_signals += 1.0
            if ev.metadata and "price" in ev.metadata:
                try:
                    prices_seen.append(float(ev.metadata["price"]))
                except (ValueError, TypeError):
                    pass

        # Normalize weights to scale of 0.0 - 1.0
        def normalize_dict(d: Dict[str, float]) -> Dict[str, float]:
            if not d:
                return {}
            max_val = max(d.values())
            if max_val <= 0:
                return {}
            return {k: round(v / max_val, 3) for k, v in sorted(d.items(), key=lambda x: x[1], reverse=True)}

        norm_cat = normalize_dict(cat_scores)
        norm_mat = normalize_dict(mat_scores)
        norm_reg = normalize_dict(reg_scores)
        norm_fest = normalize_dict(fest_scores)

        top_region = max(reg_scores, key=reg_scores.get) if reg_scores else None
        top_material = max(mat_scores, key=mat_scores.get) if mat_scores else None
        top_category = max(cat_scores, key=cat_scores.get) if cat_scores else None
        top_festival = max(fest_scores, key=fest_scores.get) if fest_scores else None
        top_lang = max(lang_counts, key=lang_counts.get) if lang_counts else "en"

        avg_price = sum(prices_seen) / len(prices_seen) if prices_seen else 2500.0
        min_price = min(prices_seen) if prices_seen else 500.0
        max_price = max(prices_seen) if prices_seen else 10000.0

        return RecommendationWeightsResponse(
            user_id=user_id,
            user_role=user_role,
            category_weights=norm_cat,
            material_weights=norm_mat,
            region_weights=norm_reg,
            festival_weights=norm_fest,
            language_preference=top_lang,
            price_affinity_range={"min": round(min_price, 2), "max": round(max_price, 2), "target_avg": round(avg_price, 2)},
            rfq_intent_score=min(round(rfq_signals / max(len(events) * 0.2, 1.0), 2), 1.0) if events else 0.0,
            export_intent_score=min(round(export_signals / max(len(events) * 0.2, 1.0), 2), 1.0) if events else 0.0,
            top_preferred_region=top_region,
            top_preferred_material=top_material,
            top_preferred_category=top_category,
            top_preferred_festival=top_festival,
            last_learned_at=datetime.now(timezone.utc).isoformat(),
        )

    @classmethod
    def generate_dynamic_layout(
        cls,
        user_id: str,
        weights: RecommendationWeightsResponse,
        catalog_products: Optional[List[Dict[str, Any]]] = None,
        recent_viewed_items: Optional[List[Dict[str, Any]]] = None
    ) -> PersonalizedLayoutResponse:
        """
        Dynamically constructs, sorts, and decorates unique feed sections based on user affinity weights.
        No two personas receive the same order or selection of widgets.
        """
        products = catalog_products or DEFAULT_CRAFT_CATALOG
        sections: List[DynamicSection] = []
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Check if user is a B2B / Export Buyer
        if weights.rfq_intent_score > 0.4 or weights.export_intent_score > 0.4:
            export_items = [p for p in products if p.get("is_export_ready")]
            sections.append(
                DynamicSection(
                    id="export_ready_sellers",
                    title="Global Export & B2B Ready Master Artisans",
                    subtitle="Certified exporters with container packaging and commercial escrow terms",
                    widget_type="rfq_spotlight",
                    badge="Direct B2B Pricing",
                    reason=f"Generated because of your high RFQ & Export intent score ({weights.rfq_intent_score})",
                    items=export_items,
                    view_all_link="/rfq?filter=export_ready",
                    display_order=1,
                )
            )

        # 2. Regional Affinity Section (e.g. Crafts from Telangana)
        target_region = weights.top_preferred_region or "Telangana"
        region_items = [p for p in products if str(p.get("region", "")).lower() == target_region.lower()]
        if not region_items:
            region_items = [p for p in products if "telangana" in str(p.get("region", "")).lower()] or products[:3]

        sections.append(
            DynamicSection(
                id=f"region_spotlight_{target_region.lower().replace(' ', '_')}",
                title=f"Handmade Crafts from {target_region}",
                subtitle=f"Direct from authentic GI heritage clusters in {target_region}",
                widget_type="hero_spotlight" if len(sections) == 0 else "carousel",
                badge=f"{target_region} GI Special",
                reason=f"Recommended due to your strong interest in {target_region} artisan clusters",
                items=region_items,
                view_all_link=f"/explore?region={target_region}",
                display_order=len(sections) + 1,
            )
        )

        # 3. Favorite Material Section (e.g. Bamboo you may like)
        target_material = weights.top_preferred_material or "Bamboo"
        mat_items = [p for p in products if str(p.get("material", "")).lower() == target_material.lower()]
        if not mat_items:
            mat_items = [p for p in products if "bamboo" in str(p.get("material", "")).lower() or "bamboo" in str(p.get("title", "")).lower()]

        if mat_items:
            sections.append(
                DynamicSection(
                    id=f"material_affinity_{target_material.lower()}",
                    title=f"{target_material} Crafts You May Like",
                    subtitle=f"Sustainable hand-crafted {target_material} creations curated for your home",
                    widget_type="multi_grid",
                    badge=f"{target_material} Collection",
                    reason=f"Learned from your searches and clicks on {target_material} crafts",
                    items=mat_items,
                    view_all_link=f"/explore?material={target_material}",
                    display_order=len(sections) + 1,
                )
            )

        # 4. Festival / Occasion Section (e.g. Wedding Collection, Diwali)
        target_festival = weights.top_preferred_festival or "Wedding"
        fest_items = [p for p in products if target_festival.lower() in str(p.get("festival", "")).lower()]
        if not fest_items:
            fest_items = [p for p in products if "wedding" in str(p.get("festival", "")).lower() or "silk" in str(p.get("category", "")).lower()]

        if fest_items:
            sections.append(
                DynamicSection(
                    id=f"occasion_curation_{target_festival.lower()}",
                    title=f"The Royal {target_festival} Heritage Collection",
                    subtitle="Heirloom bridal weaves, silver jewelry, and handcrafted gifts",
                    widget_type="card_banner",
                    badge=f"{target_festival} Special",
                    reason=f"Personalized for your upcoming {target_festival} shopping interests",
                    items=fest_items,
                    view_all_link=f"/explore?occasion={target_festival}",
                    display_order=len(sections) + 1,
                )
            )

        # 5. Recently Viewed Section
        viewed = recent_viewed_items or products[:2]
        sections.append(
            DynamicSection(
                id="recently_viewed",
                title="Recently Viewed & Picked For You",
                subtitle="Pick up right where you left off with certified artisans",
                widget_type="carousel",
                badge="Your History",
                reason="Items and craft categories you interacted with recently",
                items=viewed,
                view_all_link="/profile#history",
                display_order=len(sections) + 1,
            )
        )

        # 6. Master Artisan Showcase (Dynamic per preferred category)
        target_category = weights.top_preferred_category or "Pottery"
        artisan_items = [p for p in products if target_category.lower() in str(p.get("category", "")).lower()]
        if not artisan_items:
            artisan_items = products[3:6] if len(products) >= 6 else products

        sections.append(
            DynamicSection(
                id="master_artisan_showcase",
                title=f"National Awardee Master Artisans ({target_category})",
                subtitle="Meet the generational craftspeople behind India's timeless art",
                widget_type="seller_showcase",
                badge="GI Master Verified",
                reason=f"Highlighted based on your appreciation for master {target_category} craftsmanship",
                items=artisan_items,
                view_all_link="/clusters",
                display_order=len(sections) + 1,
            )
        )

        # Persona summary generation
        summary_parts = []
        if weights.top_preferred_region:
            summary_parts.append(f"{weights.top_preferred_region} admirer")
        if weights.top_preferred_material:
            summary_parts.append(f"{weights.top_preferred_material} craft lover")
        if weights.top_preferred_festival:
            summary_parts.append(f"{weights.top_preferred_festival} shopper")
        if weights.rfq_intent_score > 0.4:
            summary_parts.append("B2B wholesale buyer")

        persona_summary = " • ".join(summary_parts) if summary_parts else "Curated GI Artisan Enthusiast"

        return PersonalizedLayoutResponse(
            user_id=user_id,
            user_role=weights.user_role,
            persona_summary=persona_summary,
            layout_version="v2_dynamic",
            sections=sections,
            generated_at=now_str,
        )
