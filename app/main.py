from fastapi import FastAPI
from app.core.config import settings
from app.api import abdm, auth

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include Routers
app.include_router(abdm.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
