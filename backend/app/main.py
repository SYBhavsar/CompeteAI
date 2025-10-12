from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.competitors import router as competitors_router
from app.api.data_sources import router as data_sources_router
from app.api.scraping import router as scraping_router

app = FastAPI(
    title="AI Competitive Intelligence Platform",
    description="Automated competitive intelligence with AI-powered insights",
    version="1.0.0"
)

app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(competitors_router, prefix="/competitors", tags=["competitors"])
app.include_router(data_sources_router, prefix="/competitors", tags=["data_sources"])
app.include_router(scraping_router, prefix="/scraping", tags=["scraping"])

@app.get("/")
async def root():
    return {"message": "AI Competitive Intelligence Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}