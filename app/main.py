from fastapi import FastAPI
from app.core.config import settings
from app.api import abdm, auth, hpr, verification, shifts, facilities, whatsapp, bulk_import, portal, ops_dashboard, onboarding, ops_queue, registry_verification, facility_verification, matching, shift_acceptance, attendance, semantic_matching, negotiation, handoff, payments, payouts, compliance, disputes, attendance, trust, hospital_rostering

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(ops_dashboard.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

ROUTERS_BY_PREFIX = {
    "/api/v1": [
        hospital_rostering,
        abdm,
        auth,
        hpr,
        verification,
        shifts,
        facilities,
        whatsapp,
        bulk_import,
        portal,
        onboarding,
        ops_queue,
        registry_verification,
        facility_verification,
        matching,
        shift_acceptance,
        attendance,
        semantic_matching,
        negotiation,
        handoff,
        payments,
        payouts,
        compliance,
        disputes,
    ],
}

for _prefix, _router_list in ROUTERS_BY_PREFIX.items():
    for _router in _router_list:
        app.include_router(_router.router, prefix=_prefix)

app.include_router(trust.router, prefix="/api/v1")
