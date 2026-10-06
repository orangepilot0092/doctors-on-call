from fastapi import FastAPI
from app.core.config import settings
from app.api import abdm, auth, hpr, verification, shifts, facilities, whatsapp, bulk_import, portal, ops_dashboard, onboarding, ops_queue, registry_verification, facility_verification, matching, shift_acceptance, attendance, semantic_matching, attendance

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(abdm.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(hpr.router, prefix="/api/v1")
app.include_router(verification.router, prefix="/api/v1")
app.include_router(shifts.router, prefix="/api/v1")
app.include_router(facilities.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")
app.include_router(bulk_import.router, prefix="/api/v1")
app.include_router(portal.router, prefix="/api/v1")
app.include_router(ops_dashboard.router)
app.include_router(onboarding.router, prefix="/api/v1")
app.include_router(ops_queue.router, prefix="/api/v1")
app.include_router(registry_verification.router, prefix="/api/v1")
app.include_router(facility_verification.router, prefix="/api/v1")
app.include_router(matching.router, prefix="/api/v1")
app.include_router(shift_acceptance.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(semantic_matching.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(semantic_matching.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
