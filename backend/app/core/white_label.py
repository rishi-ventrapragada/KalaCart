"""
White-Label Multi-Tenant Core Engine (Phase 9)
Enables governments (ODOP UP, TRIFED), state craft federations, and NGOs to operate
isolated branded marketplaces from a single shared codebase with custom domains,
themes, languages, policies, categories, payment gateways, and tenant admins.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PROVISIONING = "provisioning"
    ARCHIVED = "archived"


class OrganizationType(str, Enum):
    GOVERNMENT = "government"
    NGO = "ngo"
    COOPERATIVE_FEDERATION = "cooperative_federation"
    PRIVATE_ENTERPRISE = "private_enterprise"


class TenantBranding(BaseModel):
    brand_name: str
    logo_url: str
    favicon_url: str = "https://kalacart.in/favicon.ico"
    primary_color: str = "#D97706"
    secondary_color: str = "#451A03"
    accent_color: str = "#F59E0B"
    font_family: str = "Inter, sans-serif"


class TenantPolicies(BaseModel):
    terms_of_service_url: str = ""
    privacy_policy_url: str = ""
    return_policy_days: int = 7
    commission_fee_pct: float = 2.5
    gi_mandatory: bool = False


class TenantPaymentSettings(BaseModel):
    primary_gateway: str = "razorpay"  # razorpay, stripe, payu, billdesk, custom_treasury
    upi_enabled: bool = True
    escrow_enabled: bool = True
    custom_submerchant_id: Optional[str] = None


class TenantDomain(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain_name: str
    is_primary: bool = True
    ssl_status: str = "active"
    dns_verification_token: str = Field(default_factory=lambda: f"kc-verify-{uuid.uuid4().hex[:12]}")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TenantAdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    email: str
    full_name: str
    role: str = "tenant_admin"  # tenant_superadmin, tenant_admin, tenant_auditor
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TenantRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_slug: str
    organization_name: str
    organization_type: OrganizationType = OrganizationType.GOVERNMENT
    status: TenantStatus = TenantStatus.ACTIVE
    primary_contact_email: str
    tier: str = "enterprise"
    branding: TenantBranding
    supported_languages: List[str] = Field(default_factory=lambda: ["en", "hi"])
    supported_districts: List[str] = Field(default_factory=list)
    allowed_categories: List[str] = Field(default_factory=list)
    policies: TenantPolicies = Field(default_factory=TenantPolicies)
    payment_settings: TenantPaymentSettings = Field(default_factory=TenantPaymentSettings)
    domains: List[TenantDomain] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "organization_name": self.organization_name,
            "organization_type": self.organization_type.value,
            "status": self.status.value,
            "primary_contact_email": self.primary_contact_email,
            "tier": self.tier,
            "branding": self.branding.model_dump(),
            "supported_languages": self.supported_languages,
            "supported_districts": self.supported_districts,
            "allowed_categories": self.allowed_categories,
            "policies": self.policies.model_dump(),
            "payment_settings": self.payment_settings.model_dump(),
            "domains": [d.model_dump() for d in self.domains],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class WhiteLabelPlatformEngine:
    """
    Multi-tenant isolation & customization manager.
    Resolves incoming requests by domain name or tenant slug, and isolates analytics,
    catalogs, and admins per tenant.
    """

    def __init__(self):
        self.tenants: Dict[str, TenantRecord] = {}  # tenant_id -> TenantRecord
        self.domain_lookup: Dict[str, str] = {}  # domain_name -> tenant_id
        self.slug_lookup: Dict[str, str] = {}  # tenant_slug -> tenant_id
        self.tenant_admins: Dict[str, List[TenantAdminUser]] = {}  # tenant_id -> list of admins
        self.tenant_orders: Dict[str, List[Dict[str, Any]]] = {}  # tenant_id -> list of orders
        self._seed_default_tenants()

    def _seed_default_tenants(self):
        # 1. UP ODOP (One District One Product - Govt of Uttar Pradesh)
        up_tenant = TenantRecord(
            tenant_slug="up-odop",
            organization_name="Uttar Pradesh ODOP Craft Mart",
            organization_type=OrganizationType.GOVERNMENT,
            primary_contact_email="director.odop@up.gov.in",
            tier="government_sovereign",
            branding=TenantBranding(
                brand_name="UP ODOP Bazaar",
                logo_url="https://odop.up.gov.in/static/img/odop-logo.png",
                primary_color="#1E3A8A",  # Royal Blue
                secondary_color="#1E293B",
                accent_color="#F59E0B",
            ),
            supported_languages=["hi", "en", "ur"],
            supported_districts=["Varanasi", "Moradabad", "Bhadohi", "Lucknow", "Saharanpur", "Firozabad"],
            allowed_categories=["Banarasi Silk", "Brass Metalware", "Handmade Carpets", "Chikankari", "Wood Carving", "Glassware"],
            policies=TenantPolicies(
                terms_of_service_url="https://odop.up.gov.in/terms",
                privacy_policy_url="https://odop.up.gov.in/privacy",
                return_policy_days=10,
                commission_fee_pct=1.0,
                gi_mandatory=True,
            ),
            payment_settings=TenantPaymentSettings(
                primary_gateway="billdesk",
                upi_enabled=True,
                escrow_enabled=True,
                custom_submerchant_id="UP_ODOP_TREASURY_01",
            ),
            domains=[
                TenantDomain(domain_name="odop.up.gov.in", is_primary=True, ssl_status="active"),
                TenantDomain(domain_name="crafts.up.gov.in", is_primary=False, ssl_status="active"),
            ],
        )

        # 2. TRIFED (Tribes India - Ministry of Tribal Affairs)
        trifed_tenant = TenantRecord(
            tenant_slug="trifed-tribal",
            organization_name="Tribes India Artisan Federation",
            organization_type=OrganizationType.GOVERNMENT,
            primary_contact_email="admin@tribesindia.com",
            tier="government_sovereign",
            branding=TenantBranding(
                brand_name="Tribes India",
                logo_url="https://tribesindia.com/assets/img/logo-trifed.png",
                primary_color="#065F46",  # Forest Green
                secondary_color="#064E3B",
                accent_color="#D97706",
            ),
            supported_languages=["en", "hi", "or", "te", "bn"],
            supported_districts=["Bastar", "Mayurbhanj", "Araku Valley", "Dindori", "Wayanad"],
            allowed_categories=["Dokra Metal", "Tribal Paintings", "Forest Honey & Organic", "Terracotta", "Bamboo Crafts"],
            policies=TenantPolicies(
                terms_of_service_url="https://tribesindia.com/terms",
                privacy_policy_url="https://tribesindia.com/privacy",
                return_policy_days=14,
                commission_fee_pct=0.0,  # 0% commission for tribal artisans
                gi_mandatory=False,
            ),
            payment_settings=TenantPaymentSettings(
                primary_gateway="razorpay",
                upi_enabled=True,
                escrow_enabled=True,
                custom_submerchant_id="TRIFED_CENTRAL_PAY_09",
            ),
            domains=[
                TenantDomain(domain_name="tribesindia.com", is_primary=True, ssl_status="active"),
                TenantDomain(domain_name="tribalcrafts.gov.in", is_primary=False, ssl_status="active"),
            ],
        )

        self._store_tenant(up_tenant)
        self._store_tenant(trifed_tenant)

        # Seed Admins
        self.tenant_admins[up_tenant.id] = [
            TenantAdminUser(
                tenant_id=up_tenant.id,
                email="admin@odop.up.gov.in",
                full_name="Rajesh Pathak (Nodal Officer)",
                role="tenant_superadmin",
            )
        ]
        self.tenant_admins[trifed_tenant.id] = [
            TenantAdminUser(
                tenant_id=trifed_tenant.id,
                email="admin@tribesindia.com",
                full_name="Sunita Soren (Tribal Outreach Director)",
                role="tenant_superadmin",
            )
        ]

        # Seed initial orders for separate analytics verification
        self.tenant_orders[up_tenant.id] = [
            {"order_id": "ORD-UP-001", "gross_inr": 12500.0, "district": "Varanasi", "category": "Banarasi Silk", "created_at": datetime.now(timezone.utc).isoformat()},
            {"order_id": "ORD-UP-002", "gross_inr": 8400.0, "district": "Moradabad", "category": "Brass Metalware", "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        self.tenant_orders[trifed_tenant.id] = [
            {"order_id": "ORD-TR-001", "gross_inr": 4500.0, "district": "Bastar", "category": "Dokra Metal", "created_at": datetime.now(timezone.utc).isoformat()},
            {"order_id": "ORD-TR-002", "gross_inr": 3200.0, "district": "Araku Valley", "category": "Bamboo Crafts", "created_at": datetime.now(timezone.utc).isoformat()},
            {"order_id": "ORD-TR-003", "gross_inr": 1800.0, "district": "Dindori", "category": "Tribal Paintings", "created_at": datetime.now(timezone.utc).isoformat()},
        ]

    def _store_tenant(self, tenant: TenantRecord):
        self.tenants[tenant.id] = tenant
        self.slug_lookup[tenant.tenant_slug] = tenant.id
        for dom in tenant.domains:
            self.domain_lookup[dom.domain_name.lower()] = tenant.id

    def resolve_tenant(self, identifier: str) -> Optional[TenantRecord]:
        """
        Resolves a tenant by either domain name (e.g. odop.up.gov.in), tenant slug, or UUID.
        """
        clean_id = identifier.strip().lower()
        if clean_id in self.domain_lookup:
            return self.tenants.get(self.domain_lookup[clean_id])
        if clean_id in self.slug_lookup:
            return self.tenants.get(self.slug_lookup[clean_id])
        if identifier in self.tenants:
            return self.tenants.get(identifier)
        return None

    def provision_tenant(
        self,
        tenant_slug: str,
        organization_name: str,
        primary_contact_email: str,
        organization_type: OrganizationType = OrganizationType.NGO,
        primary_domain: str = "",
        branding: Optional[Dict[str, Any]] = None,
        supported_languages: Optional[List[str]] = None,
        supported_districts: Optional[List[str]] = None,
        allowed_categories: Optional[List[str]] = None,
        payment_gateway: str = "razorpay",
    ) -> TenantRecord:
        """Provision a brand new isolated marketplace tenant."""
        if tenant_slug in self.slug_lookup:
            raise ValueError(f"Tenant slug '{tenant_slug}' is already registered.")

        brand_obj = TenantBranding(
            brand_name=branding.get("brand_name", organization_name) if branding else organization_name,
            logo_url=branding.get("logo_url", "https://kalacart.in/static/logo.png") if branding else "https://kalacart.in/static/logo.png",
            primary_color=branding.get("primary_color", "#D97706") if branding else "#D97706",
            secondary_color=branding.get("secondary_color", "#451A03") if branding else "#451A03",
        )

        domains_list: List[TenantDomain] = []
        if primary_domain:
            domains_list.append(TenantDomain(domain_name=primary_domain.lower(), is_primary=True, ssl_status="active"))

        tenant = TenantRecord(
            tenant_slug=tenant_slug,
            organization_name=organization_name,
            organization_type=organization_type,
            primary_contact_email=primary_contact_email,
            branding=brand_obj,
            supported_languages=supported_languages or ["en", "hi"],
            supported_districts=supported_districts or [],
            allowed_categories=allowed_categories or [],
            payment_settings=TenantPaymentSettings(primary_gateway=payment_gateway),
            domains=domains_list,
        )

        self._store_tenant(tenant)
        self.tenant_admins[tenant.id] = [
            TenantAdminUser(
                tenant_id=tenant.id,
                email=primary_contact_email,
                full_name=f"Admin ({organization_name})",
                role="tenant_superadmin",
            )
        ]
        self.tenant_orders[tenant.id] = []
        return tenant

    def update_tenant_branding_and_settings(
        self,
        tenant_id: str,
        branding: Optional[Dict[str, Any]] = None,
        supported_languages: Optional[List[str]] = None,
        supported_districts: Optional[List[str]] = None,
        allowed_categories: Optional[List[str]] = None,
        policies: Optional[Dict[str, Any]] = None,
        payment_settings: Optional[Dict[str, Any]] = None,
    ) -> Optional[TenantRecord]:
        """Customizes tenant appearance, localization, catalog filters, or policies."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None

        if branding:
            for k, v in branding.items():
                if hasattr(tenant.branding, k):
                    setattr(tenant.branding, k, v)
        if supported_languages is not None:
            tenant.supported_languages = supported_languages
        if supported_districts is not None:
            tenant.supported_districts = supported_districts
        if allowed_categories is not None:
            tenant.allowed_categories = allowed_categories
        if policies:
            for k, v in policies.items():
                if hasattr(tenant.policies, k):
                    setattr(tenant.policies, k, v)
        if payment_settings:
            for k, v in payment_settings.items():
                if hasattr(tenant.payment_settings, k):
                    setattr(tenant.payment_settings, k, v)

        tenant.updated_at = datetime.now(timezone.utc).isoformat()
        return tenant

    def add_tenant_domain(self, tenant_id: str, domain_name: str, is_primary: bool = False) -> TenantDomain:
        """Attaches a custom domain to a tenant."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant '{tenant_id}' not found.")

        dom_clean = domain_name.strip().lower()
        if dom_clean in self.domain_lookup:
            raise ValueError(f"Domain '{dom_clean}' is already assigned to another tenant.")

        domain_obj = TenantDomain(domain_name=dom_clean, is_primary=is_primary, ssl_status="active")
        tenant.domains.append(domain_obj)
        self.domain_lookup[dom_clean] = tenant.id
        return domain_obj

    def get_isolated_analytics(self, tenant_id: str) -> Dict[str, Any]:
        """Returns completely isolated analytics and revenue metrics for a specific tenant."""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant '{tenant_id}' not found.")

        orders = self.tenant_orders.get(tenant_id, [])
        total_orders = len(orders)
        gross_gmv = sum(o.get("gross_inr", 0.0) for o in orders)
        commission_earned = round(gross_gmv * (tenant.policies.commission_fee_pct / 100.0), 2)
        net_artisan_disbursed = round(gross_gmv - commission_earned, 2)

        # Group by district
        district_counts: Dict[str, int] = {}
        for o in orders:
            d = o.get("district", "Other")
            district_counts[d] = district_counts.get(d, 0) + 1

        return {
            "tenant_id": tenant.id,
            "tenant_slug": tenant.tenant_slug,
            "organization_name": tenant.organization_name,
            "total_orders": total_orders,
            "gross_gmv_inr": gross_gmv,
            "commission_earned_inr": commission_earned,
            "net_artisan_disbursed_inr": net_artisan_disbursed,
            "district_breakdown": district_counts,
            "registered_admins_count": len(self.tenant_admins.get(tenant.id, [])),
            "custom_domains": [d.domain_name for d in tenant.domains],
        }


# Global Singleton Instance
white_label_engine = WhiteLabelPlatformEngine()
