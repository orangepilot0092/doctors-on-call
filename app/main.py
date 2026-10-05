from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.api.router import router as pilot_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀 Starting {settings.app_name}...")
    yield
    # Shutdown
    print(f"👋 Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    description="Concierge MVP for B2B doctor staffing in MMR",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(pilot_router)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
