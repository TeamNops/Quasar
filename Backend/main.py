import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from routes.mcq_routes import router as mcq_router
from routes.auth_routes import router as auth_router
from routes.onboarding_routes import router as onboarding_router
from routes.youtube_education import router as youtube_router

# Load environment variables from .env file
load_dotenv()

# Check for required API keys
if not os.getenv("GOOGLE_API_KEY"):
    print("Warning: GEMINI_API_KEY not found in .env file. Quiz generation will not work.")
    print("Please add GEMINI_API_KEY=your_api_key to your .env file")

# Initialize FastAPI app
app = FastAPI(
    title="SkillMaster Assessment API",
    description="API for generating personalized skill assessments and quizzes using Google Gemini",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(mcq_router)
app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(youtube_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    # Also verify API key is available
    api_key_status = "available" if os.getenv("GOOGLE_API_KEY") else "missing"
    return {
        "status": "healthy",
        "api_key_status": api_key_status
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the SkillMaster Assessment API (Gemini Version)",
        "docs": "/docs",
        "available_endpoints": [
            "/api/quiz/generate",
            "/api/quiz/submit",
            "/api/quiz/sample/{skill_area}",
            "/api/quiz/debug",
            "/api/auth/register",
            "/api/auth/login",
            "/api/onboarding/save",
            "api/onboarding/status",
            "api/onboarding/user-skills",
        ]
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)