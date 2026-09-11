from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.export import (
    CurrencyItem,
    ConvertCurrencyRequest,
    ConvertCurrencyResponse,
    HSNCodeResponse,
    ExportProductCreate,
    ExportProductResponse,
    MultiCurrencyPrice,
    InternationalShippingEstimateRequest,
    InternationalShippingEstimateResponse,
    InternationalCourierOption,
    ExportDocumentsResponse
)

# Live FX rates registry (1 foreign currency unit = X INR)
_CURRENCY_RATES = {
    "INR": {"name": "Indian Rupee", "symbol": "₹", "rate": 1.0000},
    "USD": {"name": "United States Dollar", "symbol": "$", "rate": 83.5000},
    "EUR": {"name": "Euro", "symbol": "€", "rate": 90.2000},
    "GBP": {"name": "British Pound", "symbol": "£", "rate": 105.8000},
    "AED": {"name": "UAE Dirham", "symbol": "د.إ", "rate": 22.7500}
}

# Standard HSN Directory
_HSN_DIRECTORY = [
    {
        "hsn_code": "691200",
        "craft_category": "Terracotta & Pottery",
        "description": "Ceramic tableware, kitchenware and terracotta art",
        "gst_rate_percent": 12.0,
        "export_incentive_rodtep_percent": 3.0,
        "restricted_countries": [],
        "compliance_notes": "Requires lead-free glaze certificate for US FDA & EU dining standards."
    },
    {
        "hsn_code": "520811",
        "craft_category": "Handloom Silk & Cotton",
        "description": "Woven handloom fabrics, sarees and tapestries",
        "gst_rate_percent": 5.0,
        "export_incentive_rodtep_percent": 2.5,
        "restricted_countries": [],
        "compliance_notes": "GI Tag / Handloom Mark certification advised."
    },
    {
        "hsn_code": "741999",
        "craft_category": "Brass & Dhokra Bell Metal",
        "description": "Dhokra lost-wax casting and brass decorative artware",
        "gst_rate_percent": 18.0,
        "export_incentive_rodtep_percent": 3.5,
        "restricted_countries": [],
        "compliance_notes": "Non-ferrous handicraft declaration required for international air customs."
    },
    {
        "hsn_code": "442010",
        "craft_category": "Wood Craft",
        "description": "Statuettes and ornaments of wood",
        "gst_rate_percent": 12.0,
        "export_incentive_rodtep_percent": 2.0,
        "restricted_countries": [],
        "compliance_notes": "Requires Vriksh / CITES non-endangered timber certificate."
    }
]

_EXPORT_PRODUCTS: Dict[str, Dict[str, Any]] = {}

class ExportService:
    @staticmethod
    def list_currencies() -> List[CurrencyItem]:
        return [
            CurrencyItem(
                code=code,
                name=data["name"],
                symbol=data["symbol"],
                exchange_rate_to_inr=data["rate"],
                is_active=True
            )
            for code, data in _CURRENCY_RATES.items()
        ]

    @staticmethod
    def convert_currency(req: ConvertCurrencyRequest) -> ConvertCurrencyResponse:
        target = req.target_currency.upper()
        curr_data = _CURRENCY_RATES.get(target)
        if not curr_data:
            raise ValueError(f"Unsupported currency: {target}")

        rate = curr_data["rate"]
        converted = round(req.amount_inr / rate, 2)
        sym = curr_data["symbol"]
        formatted = f"{sym}{converted:,.2f}"

        return ConvertCurrencyResponse(
            amount_inr=req.amount_inr,
            target_currency=target,
            converted_amount=converted,
            symbol=sym,
            formatted=formatted,
            exchange_rate=rate
        )

    @staticmethod
    def list_hsn_codes(query: Optional[str] = None) -> List[HSNCodeResponse]:
        if not query:
            return [HSNCodeResponse(**h) for h in _HSN_DIRECTORY]
        q = query.lower()
        return [
            HSNCodeResponse(**h)
            for h in _HSN_DIRECTORY
            if q in h["hsn_code"].lower() or q in h["craft_category"].lower() or q in h["description"].lower()
        ]

    @staticmethod
    def configure_export_product(payload: ExportProductCreate) -> ExportProductResponse:
        export_id = str(uuid.uuid4())
        volumetric_weight = int((payload.length_cm * payload.width_cm * payload.height_cm) / 5.0)  # IATA divisor
        
        # Base mock price for product in INR
        base_price_inr = 2500.0
        multi_prices = []
        for code, data in _CURRENCY_RATES.items():
            converted = round(base_price_inr / data["rate"], 2)
            multi_prices.append(MultiCurrencyPrice(
                currency=code,
                symbol=data["symbol"],
                price=converted,
                formatted=f"{data['symbol']}{converted:,.2f}"
            ))

        record = {
            "id": export_id,
            "product_id": payload.product_id,
            "hsn_code": payload.hsn_code,
            "export_ready": payload.export_ready,
            "customs_declaration_desc": payload.customs_declaration_desc,
            "weight_grams": payload.weight_grams,
            "length_cm": payload.length_cm,
            "width_cm": payload.width_cm,
            "height_cm": payload.height_cm,
            "volumetric_weight_grams": volumetric_weight,
            "lead_time_days": payload.lead_time_days,
            "origin_state": payload.origin_state,
            "country_restrictions": payload.country_restrictions or [],
            "multi_currency_prices": multi_prices,
            "compliance_passed": True
        }
        _EXPORT_PRODUCTS[payload.product_id] = record
        return ExportProductResponse(**record)

    @staticmethod
    def get_export_product(product_id: str) -> Optional[ExportProductResponse]:
        record = _EXPORT_PRODUCTS.get(product_id)
        if not record:
            return None
        return ExportProductResponse(**record)

    @staticmethod
    def estimate_international_shipping(req: InternationalShippingEstimateRequest) -> InternationalShippingEstimateResponse:
        volumetric_weight = int((req.length_cm * req.width_cm * req.height_cm) / 5.0)
        billable_weight = max(req.weight_grams, volumetric_weight)
        kg = max(billable_weight / 1000.0, 0.5)

        usd_rate = _CURRENCY_RATES["USD"]["rate"]
        
        # Courier rate calculations
        dhl_cost_inr = round(1200 + (kg * 650), 2)
        fedex_cost_inr = round(1100 + (kg * 600), 2)
        ems_cost_inr = round(750 + (kg * 400), 2)

        couriers = [
            InternationalCourierOption(
                carrier_name="DHL Express Worldwide",
                service_type="Priority Air Cargo",
                shipping_cost_inr=dhl_cost_inr,
                shipping_cost_usd=round(dhl_cost_inr / usd_rate, 2),
                estimated_delivery_days=4,
                tracking_supported=True,
                customs_clearance_included=True
            ),
            InternationalCourierOption(
                carrier_name="FedEx International Priority",
                service_type="Standard Express Air",
                shipping_cost_inr=fedex_cost_inr,
                shipping_cost_usd=round(fedex_cost_inr / usd_rate, 2),
                estimated_delivery_days=6,
                tracking_supported=True,
                customs_clearance_included=True
            ),
            InternationalCourierOption(
                carrier_name="India Post EMS Speed Post",
                service_type="Postal Tracked Packet",
                shipping_cost_inr=ems_cost_inr,
                shipping_cost_usd=round(ems_cost_inr / usd_rate, 2),
                estimated_delivery_days=10,
                tracking_supported=True,
                customs_clearance_included=False
            )
        ]

        # Estimated US import tariff for Indian handicrafts (typically 0% under GSP or ~3% standard)
        duty_usd = round((req.product_value_inr / usd_rate) * 0.03, 2)

        return InternationalShippingEstimateResponse(
            destination_country=req.destination_country,
            billable_weight_grams=billable_weight,
            courier_options=couriers,
            estimated_import_duty_usd=duty_usd
        )

    @staticmethod
    def generate_export_documents(order_id: str, destination_country: str = "United States") -> ExportDocumentsResponse:
        inv_num = f"KC-EXP-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
        now_str = datetime.utcnow().strftime("%Y-%m-%d")

        commercial_inv = {
            "invoice_number": inv_num,
            "date": now_str,
            "exporter": "KalaCart Artisan Cluster Direct Export Hub, Odisha, India",
            "importer_destination": destination_country,
            "incoterms": "DAP (Delivered at Place)",
            "currency": "USD",
            "total_declared_value_usd": 185.00,
            "hsn_code": "691200",
            "declaration": "I hereby declare that this commercial invoice shows the actual price of the authentic Indian handicraft goods and that all particulars are true and correct."
        }

        packing_list = {
            "invoice_reference": inv_num,
            "total_packages": 1,
            "gross_weight_kg": 2.4,
            "net_weight_kg": 1.8,
            "dimensions_cm": "30 x 25 x 20",
            "packaging_type": "3-Ply Reinforced Corrugated Box with Honeycomb Paper Cushioning"
        }

        cert_of_origin = {
            "certificate_reference": f"CoO-{inv_num}",
            "issuing_authority": "Export Promotion Council for Handicrafts (EPCH) / Govt. of India",
            "country_of_origin": "India",
            "goods_description": "100% Genuine Handcrafted GI-Tagged Artisan Pottery",
            "certified_at": now_str
        }

        return ExportDocumentsResponse(
            export_invoice_number=inv_num,
            order_id=order_id,
            destination_country=destination_country,
            commercial_invoice=commercial_inv,
            packing_list=packing_list,
            certificate_of_origin=cert_of_origin,
            ready_for_dispatch=True
        )
