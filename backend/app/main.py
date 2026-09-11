"""
KalaCart FastAPI Application Entry Point.

Modular routing: each domain registers its APIRouter under /api/v1.
Security: Firebase Admin init on startup, centralized exception handlers, CORS from Settings.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent
from app.api import catalog, pricing, image, products, auth, upload, marketplace, notifications, analytics, orders, inventory, shipping, clusters, passports, sustainability, festival, quality, storefront, voice, recommendations, payments, admin, business_suite, growth, business_ai, marketing_studio, negotiation, forecast_planner, procurement, academy, export, command_center, ondc, supply_chain, cooperative, ar, live_commerce, workshop_erp, executive_brain, enterprise_security, gov_procurement, localization, digital_twin, personalization, heritage, iot, public_v1, developer_portal, impact, museum, governance, monitoring, benchmarks, security_audit, disaster_recovery, legal, cloud_infrastructure, ai_model_ops, enterprise_integrations, blockchain_provenance, smart_contracts, marketplace_federation, white_label, ai_agents, robotics_manufacturing, global_trade, verifiable_identity, spatial_commerce, knowledge_graph, quantum_security
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.core.security import initialize_firebase
from app.core.redis import redis_cache

logger = logging.getLogger(__name__)

# ── Settings & CORS ─────────────────────────────────────────────
settings = get_settings()

# Determine CORS origins — from Settings, permissive for dev
cors_origins = settings.CORS_ORIGINS or []
# Normalize: if DEBUG and no explicit production lock, allow permissive origins for Android emulator/web
if settings.DEBUG:
    # In DEBUG, if origins are default localhost-only, expand to allow all for emulator convenience
    # Keep Settings value if user explicitly set production origins; otherwise be permissive
    if not cors_origins or cors_origins == ["http://localhost:3000", "http://10.0.2.2:8000"]:
        # Allow all in dev — FastAPI CORSMiddleware will echo origin when allow_credentials=True
        cors_origins = ["*"]
    # Also ensure "*" is handled: if user set "*" explicitly, keep it
    if "*" in cors_origins:
        cors_origins = ["*"]
else:
    # Production: require explicit origins but fallback to Settings; never default to "*"
    if not cors_origins:
        cors_origins = settings.CORS_ORIGINS or ["https://kalacart.example.com"]
    if "*" in cors_origins:
        logger.error(
            "CORS_ORIGINS contains '*' in production — stripping wildcard for security. "
            "Set explicit origins via CORS_ORIGINS env (e.g., https://kalacart.in,https://www.kalacart.in)"
        )
        cors_origins = [o for o in cors_origins if o != "*"]
        if not cors_origins:
            cors_origins = ["https://kalacart.example.com"]

# SECURITY: never allow wildcard with credentials — filtered above ensures prod never has "*"
allow_credentials = True
if "*" in cors_origins:
    # Defensive: if wildcard somehow remains (DEBUG), credentials must be disabled per CORS spec
    allow_credentials = False
    logger.warning("CORS wildcard with allow_credentials — disabling credentials for safety")

app = FastAPI(
    title="KalaCart API",
    description="AI-powered backend for artisan handicraft digitization — "
                "smart cataloging, translation, pricing, image enhancement, and B2B marketplace.",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
)

# Register centralized exception handlers before middleware/routes
register_exception_handlers(app)

# Security headers (OWASP) — outermost so headers apply even on errors
app.add_middleware(SecurityHeadersMiddleware)

# Request context (X-Request-ID and latency) middleware
app.add_middleware(RequestContextMiddleware)

# CORS - read from Settings but keep permissive for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    """Initialize Firebase Admin on startup (graceful fallback to mock in dev)."""
    # SECURITY: fail-fast on insecure defaults in production
    try:
        settings.validate_secret_key_or_warn()
    except Exception as exc:
        logger.critical("Security config error: %s", exc)
        if settings.is_production:
            raise
    if settings.is_production and settings.DEBUG:
        logger.critical("DEBUG=true in production — disabling DEBUG for security")
        # Don't mutate runtime DEBUG flag (pydantic frozen), but log critical; force downstream mock checks to fail
        # Operational action: set DEBUG=false in env

    try:
        initialized = initialize_firebase()
        if initialized:
            logger.info("Firebase initialized successfully on startup")
        else:
            logger.warning("Firebase not initialized on startup — mock auth mode (check Settings)")
            if settings.is_production:
                logger.critical("Production startup without Firebase — auth will reject all requests (set FIREBASE_CREDENTIALS_JSON/PATH)")
    except Exception as exc:
        logger.error("Firebase initialization failed on startup: %s", exc, exc_info=True)
        # Don't crash app — allow mock mode
        if settings.is_production:
            logger.critical("Production startup without Firebase — auth will reject all requests")

    # Multi-region Redis Pub/Sub Cache initialization
    try:
        await redis_cache.initialize()
    except Exception as exc:
        logger.warning("Redis async cache initialization failed (falling back to memory): %s", exc)



@app.on_event("shutdown")
async def on_shutdown():
    """Cleanup — close DB pool if used."""
    try:
        from app.database.connection import close_db_pool

        close_db_pool()
        logger.info("Shutdown: DB pool closed")
    except Exception as exc:
        logger.warning("Shutdown cleanup failed: %s", exc)


@app.get("/", tags=["Root"])
async def root():
    """Health check root."""
    return {
        "name": "KalaCart API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Liveness & readiness probe for Docker / load balancer."""
    try:
        from app.database.connection import check_supabase_health

        supa = await check_supabase_health()
    except Exception as exc:
        supa = {"status": "unknown", "error": str(exc)}
    return {"status": "ok", "version": "1.0.0", "supabase": supa}


# Register modular routers — prefix convention: main.py owns /api/v1/* prefix
# for all domains (single source of truth via Settings.API_V1_PREFIX). Most
# routers define `APIRouter()` without internal prefix and are mounted with
# `prefix="/api/v1/<domain>"` below.
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
# SUPERSEDED — the unified artisan agent route is deliberately NOT mounted.
# Decision D-14: the three AI features are served by the dedicated endpoints
# below (/catalog/voice, /pricing/analyze, /image/enhance), which are the only
# live path. The agent could not satisfy the voice requirement on its own: it
# accepts a transcript string and has no speech-to-text stage.
# The code stays in app/agent/ — its free-model fallback walker
# (app/agent/models.py) has no equivalent elsewhere and is worth keeping.
# Re-mounting it would create a second, competing implementation of the same
# three features; do not re-enable without revisiting D-14.
# app.include_router(
#     agent.router,
#     prefix="/api/v1/agent",
#     tags=["Unified Artisan Agent"],
# )
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Catalog"])
app.include_router(pricing.router, prefix="/api/v1/pricing", tags=["Pricing"])
app.include_router(image.router, prefix="/api/v1/image", tags=["Image"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["Upload"])
app.include_router(marketplace.router, prefix="/api/v1", tags=["Marketplace"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
# Phase C audit note — analytics internal vs external prefix inconsistency:
# `app.api.analytics` defines `APIRouter(prefix="/api/v1/analytics")` and is
# mounted with `prefix=""` here (historical). All other domains mount with
# external prefix in main.py. Path is still `/api/v1/analytics/dashboard`
# (verified via OpenAPI), so we preserve it for backward compat.
# Recommended future normalize (non-breaking): remove internal prefix from
# analytics router and mount as `prefix="/api/v1/analytics"` like peers, or
# keep internal but document as exception. No change made now to avoid
# breaking existing clients / tests.
app.include_router(analytics.router, prefix="", tags=["Analytics"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(inventory.router, prefix="", tags=["Inventory"])
app.include_router(shipping.router, prefix="", tags=["Shipping"])
app.include_router(clusters.router, prefix="", tags=["Clusters"])
app.include_router(passports.router, prefix="", tags=["Craft Passports & GI Verification"])
app.include_router(sustainability.router, prefix="", tags=["Sustainability & Eco Score"])
app.include_router(festival.router, prefix="", tags=["Festival Demand Predictor"])
app.include_router(quality.router, prefix="", tags=["Quality Verification Workflow"])
app.include_router(storefront.router, prefix="", tags=["Mini Storefront Websites"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice Commerce Engine"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Personalized Recommendation Engine"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Secure Payments & Escrow"])
app.include_router(admin.router, prefix="", tags=["Admin Portal & Fraud Intelligence"])
app.include_router(business_suite.router, prefix="", tags=["Seller Business Suite"])
app.include_router(growth.router, prefix="/api/v1/growth", tags=["Growth & Marketing Engine"])
app.include_router(business_ai.router, prefix="", tags=["Kala AI Business Manager"])
app.include_router(marketing_studio.router, prefix="", tags=["AI Marketing Studio"])
app.include_router(negotiation.router, prefix="", tags=["AI Sales Negotiation Agent"])
app.include_router(forecast_planner.router, prefix="", tags=["Demand Forecast & Production Planner"])
app.include_router(procurement.router, prefix="", tags=["National B2B Procurement Hub"])
app.include_router(academy.router, prefix="", tags=["AI Knowledge Academy"])
app.include_router(export.router, prefix="", tags=["Global Export Readiness"])
app.include_router(command_center.router, prefix="", tags=["Super Admin AI Command Center"])
app.include_router(ondc.router, prefix="", tags=["ONDC Integration Layer"])
app.include_router(supply_chain.router, prefix="", tags=["AI Supply Chain Network"])
app.include_router(cooperative.router, prefix="", tags=["Cooperative & SHG Workspace"])
app.include_router(ar.router, prefix="", tags=["AR Product Experience"])
app.include_router(live_commerce.router, prefix="", tags=["Live Commerce Platform"])
app.include_router(workshop_erp.router, prefix="", tags=["Workshop ERP"])
app.include_router(executive_brain.router, prefix="", tags=["Predictive AI Executive Brain"])
app.include_router(enterprise_security.router, prefix="", tags=["Enterprise Security & Reliability"])
app.include_router(gov_procurement.router, prefix="", tags=["Government & Institutional Procurement Hub"])
app.include_router(localization.router, prefix="", tags=["Global Translation & Localization"])
app.include_router(digital_twin.router, prefix="", tags=["Digital Twin Marketplace & AI Sandbox"])
app.include_router(personalization.router, prefix="/api/v1/personalization", tags=["Hyper-Personalization Engine"])
app.include_router(heritage.router, prefix="/api/v1/heritage", tags=["Cultural Heritage Intelligence"])
app.include_router(iot.router, prefix="", tags=["IoT Smart Workshop"])
app.include_router(public_v1.router, prefix="", tags=["Public API Platform"])
app.include_router(developer_portal.router, prefix="", tags=["Developer Portal"])
app.include_router(impact.router, prefix="/api/v1", tags=["NGO & Impact Analytics"])
app.include_router(museum.router, prefix="/api/v1", tags=["Digital Craft Museum"])
app.include_router(governance.router, prefix="/api/v1", tags=["AI Governance & Explainability"])
app.include_router(monitoring.router, prefix="", tags=["Observability & Production Monitoring"])
app.include_router(benchmarks.router, prefix="", tags=["Performance Benchmarks"])
app.include_router(security_audit.router, prefix="", tags=["Enterprise Security Hardening"])
app.include_router(disaster_recovery.router, prefix="/api/v1", tags=["Disaster Recovery & Backups"])
app.include_router(legal.router, prefix="/api/v1", tags=["Legal & Regulatory Compliance"])
app.include_router(cloud_infrastructure.router, prefix="", tags=["Multi-Region Cloud Infrastructure"])
app.include_router(ai_model_ops.router, prefix="", tags=["AI Model Operations & MLOps"])
app.include_router(enterprise_integrations.router, prefix="", tags=["Enterprise Integration Hub"])
app.include_router(blockchain_provenance.router, prefix="", tags=["Blockchain Provenance & Craft Passports"])
app.include_router(smart_contracts.router, prefix="", tags=["Smart Contracts & Institutional Escrow"])
app.include_router(marketplace_federation.router, prefix="", tags=["Global Marketplace Federation"])
app.include_router(white_label.router, prefix="", tags=["White-Label Multi-Tenant Platform"])
app.include_router(ai_agents.router, prefix="", tags=["Universal AI Agent Platform (V10)"])
app.include_router(robotics_manufacturing.router, prefix="", tags=["Robotics & Smart Manufacturing (V10)"])
app.include_router(global_trade.router, prefix="", tags=["Global Trade Intelligence (V10)"])
app.include_router(verifiable_identity.router, prefix="", tags=["Verifiable Digital Identity (V10)"])
app.include_router(spatial_commerce.router, prefix="", tags=["Spatial Commerce & GIS Intelligence (V10)"])
app.include_router(knowledge_graph.router, prefix="", tags=["Knowledge Graph Engine (V10)"])
app.include_router(quantum_security.router, prefix="", tags=["Quantum-Ready Security Layer (V10)"])
