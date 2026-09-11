from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class StockMovementType(str, Enum):
    restock = "restock"
    reservation = "reservation"
    release = "release"
    sale = "sale"
    adjustment = "adjustment"
    damage = "damage"
    return_type = "return"


class ProductInventoryBase(BaseModel):
    product_id: str
    artisan_id: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    available_stock: int = Field(default=0, ge=0)
    reserved_stock: int = Field(default=0, ge=0)
    sold_stock: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=5, ge=0)


class ProductInventoryCreate(BaseModel):
    product_id: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    available_stock: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=5, ge=0)


class ProductInventoryUpdate(BaseModel):
    sku: Optional[str] = None
    barcode: Optional[str] = None
    minimum_stock: Optional[int] = Field(default=None, ge=0)


class StockAdjustmentRequest(BaseModel):
    quantity: int = Field(..., description="Positive to add, negative to reduce")
    movement_type: StockMovementType = Field(default=StockMovementType.restock)
    notes: Optional[str] = None


class StockMovementResponse(BaseModel):
    id: str
    inventory_id: str
    product_id: str
    artisan_id: str
    movement_type: str
    quantity: int
    previous_stock: int
    new_stock: int
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class ProductInventoryResponse(ProductInventoryBase):
    id: str
    product_title: Optional[str] = None
    product_price: Optional[float] = None
    product_image_url: Optional[str] = None
    category: Optional[str] = None
    status_badge: str = "in_stock"  # in_stock, low_stock, out_of_stock
    created_at: datetime
    updated_at: datetime


class RawMaterialBase(BaseModel):
    name: str
    unit: str
    current_stock: float = Field(default=0.0, ge=0)
    minimum_stock: float = Field(default=5.0, ge=0)
    cost_per_unit: float = Field(default=0.0, ge=0)
    supplier_info: Optional[str] = None


class RawMaterialCreate(RawMaterialBase):
    pass


class RawMaterialUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    current_stock: Optional[float] = Field(default=None, ge=0)
    minimum_stock: Optional[float] = Field(default=None, ge=0)
    cost_per_unit: Optional[float] = Field(default=None, ge=0)
    supplier_info: Optional[str] = None


class RawMaterialResponse(RawMaterialBase):
    id: str
    artisan_id: str
    is_low_stock: bool = False
    created_at: datetime
    updated_at: datetime


class InventoryDashboardMetrics(BaseModel):
    total_products: int = 0
    items_in_stock: int = 0
    low_stock_count: int = 0
    out_of_stock_count: int = 0
    total_reserved_stock: int = 0
    total_sold_stock: int = 0


class MonthlyStockMovement(BaseModel):
    month: str
    inflow: int = 0
    outflow: int = 0


class ProductMovementStat(BaseModel):
    product_id: str
    title: str
    total_sold: int
    available_stock: int


class InventoryAnalyticsResponse(BaseModel):
    monthly_stock_movements: List[MonthlyStockMovement] = []
    fast_moving_products: List[ProductMovementStat] = []
    dead_inventory: List[ProductMovementStat] = []
