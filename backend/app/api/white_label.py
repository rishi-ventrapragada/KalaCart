"""
White-Label Multi-Tenant API Router (Phase 9)
Provides multi-tenant resolution, branding customizer, isolated analytics,
domain management, and admin user provisioning.
"""

from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.core.white_label import (
    white_label_engine,
    TenantStatus,
    OrganizationType,
)

router = APIRouter(prefix="/api/v1/tenants", tags=["White-Label Multi-Tenant Platform"])


class ProvisionTenantRequest(BaseModel):
    tenant_slug: str
    organization_name: str
    primary_contact_email: str
    organization_type: str = "government"
    primary_domain: str = ""
    branding: Optional[Dict[str, Any]] = None
    supported_languages: Optional[List[str]] = None
    supported_districts: Optional[List[str]] = None
    allowed_categories: Optional[List[str]] = None
    payment_gateway: str = "razorpay"


class UpdateTenantSettingsRequest(BaseModel):
    tenant_id: str
    branding: Optional[Dict[str, Any]] = None
    supported_languages: Optional[List[str]] = None
    supported_districts: Optional[List[str]] = None
    allowed_categories: Optional[List[str]] = None
    policies: Optional[Dict[str, Any]] = None
    payment_settings: Optional[Dict[str, Any]] = None


class AddDomainRequest(BaseModel):
    tenant_id: str
    domain_name: str
    is_primary: bool = False


@router.get("/resolve")
async def resolve_tenant_by_host(
    domain: Optional[str] = Query(None, description="Domain name or tenant slug"),
    x_tenant_domain: Optional[str] = Header(None, alias="X-Tenant-Domain"),
):
    """Resolve tenant branding, policies, and localized configs by custom domain or header."""
    target_identifier = domain or x_tenant_domain
    if not target_identifier:
        raise HTTPException(status_code=400, detail="Domain or X-Tenant-Domain header is required.")

    tenant = white_label_engine.resolve_tenant(target_identifier)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"No tenant mapped to '{target_identifier}'.")
    return {
        "status": "success",
        "resolved_by": target_identifier,
        "tenant": tenant.to_dict(),
    }


@router.get("/list")
async def list_tenants():
    """List all registered white-label marketplace tenants."""
    tenants = [t.to_dict() for t in white_label_engine.tenants.values()]
    return {
        "count": len(tenants),
        "tenants": tenants,
    }


@router.get("/{tenant_id}")
async def get_tenant_details(tenant_id: str):
    """Retrieve full tenant configuration including domains, branding, and admins."""
    tenant = white_label_engine.resolve_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found.")
    return tenant.to_dict()


@router.post("/provision")
async def provision_tenant(req: ProvisionTenantRequest):
    """Provision a new white-label tenant marketplace."""
    try:
        try:
            org_type = OrganizationType(req.organization_type)
        except ValueError:
            org_type = OrganizationType.GOVERNMENT

        tenant = white_label_engine.provision_tenant(
            tenant_slug=req.tenant_slug,
            organization_name=req.organization_name,
            primary_contact_email=req.primary_contact_email,
            organization_type=org_type,
            primary_domain=req.primary_domain,
            branding=req.branding,
            supported_languages=req.supported_languages,
            supported_districts=req.supported_districts,
            allowed_categories=req.allowed_categories,
            payment_gateway=req.payment_gateway,
        )
        return {
            "status": "success",
            "message": f"Tenant '{tenant.organization_name}' provisioned successfully.",
            "tenant": tenant.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/settings")
async def update_tenant_settings(req: UpdateTenantSettingsRequest):
    """Update tenant branding, policies, or payment settings."""
    tenant = white_label_engine.update_tenant_branding_and_settings(
        tenant_id=req.tenant_id,
        branding=req.branding,
        supported_languages=req.supported_languages,
        supported_districts=req.supported_districts,
        allowed_categories=req.allowed_categories,
        policies=req.policies,
        payment_settings=req.payment_settings,
    )
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant '{req.tenant_id}' not found.")
    return {
        "status": "success",
        "message": "Tenant settings updated successfully.",
        "tenant": tenant.to_dict(),
    }


@router.post("/domains/add")
async def add_tenant_domain(req: AddDomainRequest):
    """Attach a custom CNAME/A-record domain to a tenant."""
    try:
        domain = white_label_engine.add_tenant_domain(
            tenant_id=req.tenant_id,
            domain_name=req.domain_name,
            is_primary=req.is_primary,
        )
        return {
            "status": "success",
            "domain": domain.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{tenant_id}/analytics")
async def get_tenant_analytics(tenant_id: str):
    """Retrieve isolated sales and performance analytics for a specific tenant."""
    try:
        analytics = white_label_engine.get_isolated_analytics(tenant_id)
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
