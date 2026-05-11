"""
SEE Result Monitor – FastAPI Application Entry Point
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import init_db
from app.api import registrations, monitor, logs

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SEE Result Monitor API",
    description=(
        "Automatically monitors SEE result portals and emails students "
        "the moment their result is published."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS – allow the React dev server and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(registrations.router, prefix="/api/v1")
app.include_router(monitor.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup():
    logger.info("⚡ Starting SEE Result Monitor API…")
    await init_db()
    logger.info("✅ Database initialised.")
    logger.info(
        f"📋 Configured Gmail: {settings.GMAIL_USER or '⚠️ NOT SET – set GMAIL_USER and GMAIL_APP_PASSWORD'}"
    )
    logger.info("ℹ️  Use POST /api/v1/monitor/start to begin monitoring.")


@app.on_event("shutdown")
async def on_shutdown():
    from app.services.monitor import stop_monitoring
    stop_monitoring()
    logger.info("🛑 SEE Result Monitor API shut down.")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "app": "SEE Result Monitor API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
