from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from app.core.logging_config import setup_logging, set_user_context, clear_user_context
from app.core.database import Base, engine
from app.utils.jwt import decode_token
from app.api.auth import router as auth_router
from app.api.competitors import router as competitors_router
from app.api.data_sources import router as data_sources_router
from app.api.scraping import router as scraping_router
from app.api.schedules import router as schedules_router
from app.api.insights import router as insights_router
from app.api.search import router as search_router
from app.api.analytics import router as analytics_router
from app.api.alerts import router as alerts_router
from app.api.websocket import router as websocket_router
from app.api.historical_intelligence import router as historical_router
from app.api.strategic_intelligence import router as strategic_router
from app.api.predictive_analytics import router as predictive_router
from app.api.swot import router as swot_router

# Initialize logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup"""
    from app import models  # noqa: F401 — registers all models with SQLAlchemy
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")
    yield


app = FastAPI(
    title="AI Competitive Intelligence Platform",
    description="Automated competitive intelligence with AI-powered insights",
    version="1.0.0",
    lifespan=lifespan,
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses with user context"""
    start_time = time.time()

    # Extract user_id from JWT token if present
    user_id = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)
            user_id = payload.get("user_id")
            set_user_context(user_id)
        except:
            pass

    # Log request
    logger.info(f"Request: {request.method} {request.url.path} | Client: {request.client.host}")

    # Process request
    response = await call_next(request)

    # Log response
    duration = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} | "
        f"Status: {response.status_code} | Duration: {duration:.3f}s"
    )

    # Clear user context after request
    clear_user_context()

    return response

# TODO: Lock down CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(competitors_router, prefix="/competitors", tags=["competitors"])
app.include_router(data_sources_router, prefix="/competitors", tags=["data_sources"])
app.include_router(scraping_router, prefix="/scraping", tags=["scraping"])
app.include_router(schedules_router, prefix="/schedules", tags=["schedules"])
app.include_router(insights_router, tags=["insights"])
app.include_router(search_router, tags=["search"])
app.include_router(analytics_router, tags=["analytics"])
app.include_router(alerts_router, tags=["alerts"])
app.include_router(websocket_router, tags=["websocket"])
app.include_router(historical_router, tags=["historical"])
app.include_router(strategic_router, tags=["strategic"])
app.include_router(predictive_router, tags=["predictive"])
app.include_router(swot_router, tags=["swot"])

@app.get("/")
async def root():
    return {"message": "AI Competitive Intelligence Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}