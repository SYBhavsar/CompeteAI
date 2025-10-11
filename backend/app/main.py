from fastapi import FastAPI

from app.api.auth import router as auth_router

app = FastAPI(
    title="AI Competitive Intelligence Platform",
    description="Automated competitive intelligence with AI-powered insights",
    version="1.0.0"
)

app.include_router(auth_router, prefix="/auth", tags=["authentication"])

@app.get("/")
async def root():
    return {"message": "AI Competitive Intelligence Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}