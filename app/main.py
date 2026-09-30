from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.api.router import router as pilot_router
from app.api.doctor_router import router as doctor_router
from app.api.subscription_router import router as subscription_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.app_name}...")
    yield
    print(f"👋 Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Medical Staffing Platform with Subscription Billing",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Register all routers
app.include_router(pilot_router)
app.include_router(doctor_router)
app.include_router(subscription_router)


@app.get("/", response_class=HTMLResponse)
async def clinic_portal(request: Request):
    return templates.TemplateResponse(request=request, name="clinic_portal.html", context={})


@app.get("/doctors", response_class=HTMLResponse)
async def doctor_portal(request: Request):
    return templates.TemplateResponse(request=request, name="doctor_portal.html", context={})


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    return templates.TemplateResponse(request=request, name="pricing.html", context={})


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}
