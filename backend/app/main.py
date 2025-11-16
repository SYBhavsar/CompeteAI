from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(
    title="AI Competitive Intelligence Platform",
    description="Automated competitive intelligence with AI-powered insights",
    version="1.0.0"
)

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

@app.get("/")
async def root():
    return {"message": "AI Competitive Intelligence Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}