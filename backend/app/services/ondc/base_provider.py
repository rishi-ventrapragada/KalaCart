from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.models.ondc import (
    ONDCPublishProductRequest,
    BecknItem,
    BecknDescriptor,
    ONDCIncomingOrderRequest,
    ONDCOrderResponse,
    ONDCCancellationRequest,
    ONDCReturnRequest
)

class IONDCProvider(ABC):
    """
    Abstract Provider Interface for ONDC / Beckn BPP (Seller-side) Network Adapters.
    Allows plugging in Beckn Gateway v1.2, Custom BPP Node, or Sandbox Adapters.
    """

    @abstractmethod
    def build_beckn_item(self, req: ONDCPublishProductRequest) -> BecknItem:
        """Transforms KalaCart product into standard Beckn Item format."""
        pass

    @abstractmethod
    def handle_search(self, category_id: Optional[str] = None) -> List[BecknItem]:
        """Responds to ONDC network /search calls with catalog."""
        pass

    @abstractmethod
    def handle_order_init_and_confirm(self, req: ONDCIncomingOrderRequest) -> Dict[str, Any]:
        """Processes network incoming /init and /confirm calls into a validated order."""
        pass

    @abstractmethod
    def handle_cancellation(self, order_id: str, req: ONDCCancellationRequest) -> Dict[str, Any]:
        """Executes Beckn /cancel flow with standardized reason codes."""
        pass

    @abstractmethod
    def handle_return(self, order_id: str, req: ONDCReturnRequest) -> Dict[str, Any]:
        """Executes Beckn /update return flow."""
        pass
