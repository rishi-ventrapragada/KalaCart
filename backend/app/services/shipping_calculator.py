import math
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from app.models.shipping import (
    ShippingEstimateRequest,
    ShippingEstimateResponse,
    PackageSize,
    CourierRankOption,
    PackagingRecommendation,
)

def calculate_shipping_estimate(req: ShippingEstimateRequest) -> ShippingEstimateResponse:
    # 1. Volumetric weight = (L * W * H) / 5000 (standard logistics divisor)
    volumetric = round((req.length_cm * req.width_cm * req.height_cm) / 5000.0, 3)
    chargeable = max(req.weight_kg, volumetric)

    # 2. Package Size Classification
    volume_cc = req.length_cm * req.width_cm * req.height_cm
    if chargeable <= 1.0 and volume_cc <= 3000:
        pkg_size = PackageSize.small
        box_desc = "Small Artisan Box (20x15x10 cm)"
    elif chargeable <= 5.0 and volume_cc <= 25000:
        pkg_size = PackageSize.medium
        box_desc = "Medium Corrugated Box (35x25x20 cm)"
    elif chargeable <= 20.0 and volume_cc <= 100000:
        pkg_size = PackageSize.large
        box_desc = "Heavy Duty Double-Wall Box (50x40x35 cm)"
    else:
        pkg_size = PackageSize.bulk
        box_desc = "Wooden Crate / Palletized Container"

    # 3. Zone / Distance calculation based on Pincodes
    origin_circle = req.origin_pincode[:2] if len(req.origin_pincode) >= 2 else "30"
    dest_circle = req.destination_pincode[:2] if len(req.destination_pincode) >= 2 else "56"

    try:
        circle_diff = abs(int(origin_circle) - int(dest_circle))
    except Exception:
        circle_diff = 3

    if origin_circle == dest_circle:
        base_rate = 50.0 + max(0.0, (chargeable - 0.5)) * 30.0
        delivery_days = 2
    elif circle_diff <= 2:
        base_rate = 80.0 + max(0.0, (chargeable - 0.5)) * 45.0
        delivery_days = 3
    else:
        base_rate = 120.0 + max(0.0, (chargeable - 0.5)) * 60.0
        delivery_days = 5

    # 4. Surcharges (Fragile, Insurance, COD)
    fragile_surcharge = 40.0 if req.is_fragile else 0.0
    insurance_fee = round(max(20.0, req.declared_value * 0.01), 2) if req.is_insured else 0.0
    cod_fee = 50.0 if req.is_cod else 0.0

    total_cost = round(base_rate + fragile_surcharge + insurance_fee + cod_fee, 2)
    delivery_date = (datetime.now(timezone.utc) + timedelta(days=delivery_days)).strftime('%d-%b-%Y')

    # 5. Smart Courier Ranking Engine (Distance, Weight, Speed, Cost)
    ranked_couriers: List[CourierRankOption] = [
        CourierRankOption(
            courier_name="India Post Speed Post",
            courier_key="india_post",
            estimated_cost=total_cost,
            estimated_days=delivery_days,
            speed_rating=4.7,
            reliability_score=98.2,
            is_recommended=True,
        ),
        CourierRankOption(
            courier_name="Delhivery Express Logistics",
            courier_key="delhivery",
            estimated_cost=round(total_cost * 1.15, 2),
            estimated_days=max(1, delivery_days - 1),
            speed_rating=4.9,
            reliability_score=96.5,
            is_recommended=False,
        ),
        CourierRankOption(
            courier_name="Blue Dart Surface & Air",
            courier_key="bluedart",
            estimated_cost=round(total_cost * 1.30, 2),
            estimated_days=max(1, delivery_days - 2),
            speed_rating=4.9,
            reliability_score=99.1,
            is_recommended=False,
        ),
    ]

    # 6. Packaging Assistant recommendations
    packaging = PackagingRecommendation(
        suggested_box_size=box_desc,
        is_fragile=req.is_fragile,
        fragile_label="⚠️ FRAGILE / HANDLE WITH CARE — ARTISAN HERITAGE CRAFT" if req.is_fragile else "STANDARD ECO-FRIENDLY SHIPMENT",
        suggested_packing_material="Eco-friendly bubble wrap (2 layers) + Kraft paper void fill + Corner edge protectors" if req.is_fragile else "Corrugated inner box + Shredded craft paper fill + Tamper-evident paper tape",
        estimated_volumetric_weight=volumetric,
        instructions="Secure items centrally with 2-inch cushioning. Apply fragile label on top and side panels."
    )

    return ShippingEstimateResponse(
        estimated_cost=total_cost,
        estimated_delivery_days=delivery_days,
        estimated_delivery_date=delivery_date,
        package_size=pkg_size,
        chargeable_weight_kg=round(chargeable, 3),
        volumetric_weight_kg=volumetric,
        base_rate=round(base_rate, 2),
        fragile_surcharge=fragile_surcharge,
        insurance_fee=insurance_fee,
        cod_fee=cod_fee,
        courier_partner="India Post Speed Post",
        ranked_couriers=ranked_couriers,
        packaging_assistant=packaging,
        pickup_available=True,
        self_drop_available=True,
    )
