from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional, Any
from app.core.security import get_current_user
from app.models.export import (
    CurrencyItem,
    ConvertCurrencyRequest,
    ConvertCurrencyResponse,
    HSNCodeResponse,
    ExportProductCreate,
    ExportProductResponse,
    InternationalShippingEstimateRequest,
    InternationalShippingEstimateResponse,
    ExportDocumentsResponse
)
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/v1/export", tags=["Global Export Readiness"])

@router.get("/currencies", response_model=List[CurrencyItem])
def list_supported_currencies():
    """
    List all supported global currencies with exchange rates (USD, EUR, GBP, AED, INR).
    """
    return ExportService.list_currencies()

@router.post("/convert", response_model=ConvertCurrencyResponse)
def convert_currency_rate(payload: ConvertCurrencyRequest):
    """
    Convert price in INR to foreign currency (USD, EUR, GBP, AED).
    """
    try:
        return ExportService.convert_currency(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/hsn-codes", response_model=List[HSNCodeResponse])
def search_hsn_codes(query: Optional[str] = Query(None)):
    """
    Lookup Indian handicraft HSN codes, GST rates, and export incentive percentages.
    """
    return ExportService.list_hsn_codes(query=query)

@router.post("/products/{product_id}", response_model=ExportProductResponse, status_code=status.HTTP_201_CREATED)
def configure_export_product(
    product_id: str,
    payload: ExportProductCreate,
    current_user: Any = Depends(get_current_user)
):
    """
    Configure handicraft product for international export with customs metadata & dimensions.
    """
    payload.product_id = product_id
    return ExportService.configure_export_product(payload)

@router.get("/products/{product_id}", response_model=ExportProductResponse)
def get_export_product(product_id: str):
    """
    Retrieve product export readiness status and converted multi-currency pricing.
    """
    res = ExportService.get_export_product(product_id)
    if not res:
        raise HTTPException(status_code=404, detail="Export configuration not found for product")
    return res

@router.post("/shipping-estimate", response_model=InternationalShippingEstimateResponse)
def estimate_international_shipping(payload: InternationalShippingEstimateRequest):
    """
    Calculate cross-border international courier shipping costs (DHL, FedEx, India Post EMS) and customs duties.
    """
    return ExportService.estimate_international_shipping(payload)

@router.post("/documents/{order_id}/generate", response_model=ExportDocumentsResponse)
def generate_export_documents(
    order_id: str,
    destination_country: str = Query("United States"),
    current_user: Any = Depends(get_current_user)
):
    """
    Generate mandatory export compliance documents: Commercial Invoice, Packing List, and Certificate of Origin (CoO).
    """
    return ExportService.generate_export_documents(
        order_id=order_id,
        destination_country=destination_country
    )
