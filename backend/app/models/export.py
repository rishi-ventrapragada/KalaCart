from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class CurrencyItem(BaseModel):
    code: str
    name: str
    symbol: str
    exchange_rate_to_inr: float
    is_active: bool = True

class ConvertCurrencyRequest(BaseModel):
    amount_inr: float = Field(..., ge=0)
    target_currency: str = "USD"

class ConvertCurrencyResponse(BaseModel):
    amount_inr: float
    target_currency: str
    converted_amount: float
    symbol: str
    formatted: str
    exchange_rate: float

class HSNCodeResponse(BaseModel):
    hsn_code: str
    craft_category: str
    description: str
    gst_rate_percent: float
    export_incentive_rodtep_percent: float
    restricted_countries: List[str] = Field(default_factory=list)
    compliance_notes: Optional[str] = None

class ExportProductCreate(BaseModel):
    product_id: str
    hsn_code: str
    export_ready: bool = True
    customs_declaration_desc: str
    weight_grams: int = Field(..., gt=0)
    length_cm: float = Field(..., gt=0)
    width_cm: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    lead_time_days: int = Field(default=7, gt=0)
    origin_state: str = "Odisha"
    country_restrictions: Optional[List[str]] = Field(default_factory=list)

class MultiCurrencyPrice(BaseModel):
    currency: str
    symbol: str
    price: float
    formatted: str

class ExportProductResponse(BaseModel):
    id: str
    product_id: str
    hsn_code: str
    export_ready: bool
    customs_declaration_desc: str
    weight_grams: int
    length_cm: float
    width_cm: float
    height_cm: float
    volumetric_weight_grams: int
    lead_time_days: int
    origin_state: str
    country_restrictions: List[str] = Field(default_factory=list)
    multi_currency_prices: List[MultiCurrencyPrice] = Field(default_factory=list)
    compliance_passed: bool = True

class InternationalShippingEstimateRequest(BaseModel):
    destination_country: str = "USA"
    destination_postal_code: str = "10001"
    weight_grams: int = Field(..., gt=0)
    length_cm: float = Field(..., gt=0)
    width_cm: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    product_value_inr: float = Field(..., gt=0)

class InternationalCourierOption(BaseModel):
    carrier_name: str
    service_type: str
    shipping_cost_inr: float
    shipping_cost_usd: float
    estimated_delivery_days: int
    tracking_supported: bool = True
    customs_clearance_included: bool = True

class InternationalShippingEstimateResponse(BaseModel):
    destination_country: str
    billable_weight_grams: int
    courier_options: List[InternationalCourierOption]
    estimated_import_duty_usd: float

class ExportDocumentsResponse(BaseModel):
    export_invoice_number: str
    order_id: str
    destination_country: str
    commercial_invoice: Dict[str, Any]
    packing_list: Dict[str, Any]
    certificate_of_origin: Dict[str, Any]
    ready_for_dispatch: bool = True
