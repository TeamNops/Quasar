from datetime import datetime
from functions.youtube_education import generate_skill_playlist, respond_to_normal_query
from fastapi import APIRouter, Query, Depends, HTTPException, status, Header
from typing import Dict, Any, List
from pydantic import BaseModel
from database import get_db
from bson import ObjectId
import jwt
from jwt_config import settings

router = APIRouter(
    prefix="/api/youtube",
    tags=["youtube"],
    responses={404: {"description": "Not found"}}
)

class AssessmentResults(BaseModel):
    score: Dict[str, Any]
    assessed_level: str
    question_feedback: List[Dict[str, Any]]
    skill_gaps: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

@router.post("/recommendations", response_model=List[Dict[str, Any]])
async def get_youtube_recommendations(
    assessment_results: AssessmentResults = None,
    authorization: str = Header(None)
):
    """
    Generate YouTube video recommendations based on assessment results.
    Uses stored results from the database if no assessment results are provided.
    """
    try:
        # If no assessment results provided, fetch from database
        if not assessment_results and authorization:
            # Get user ID from token
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Not authenticated")
                
            token = authorization.split(" ")[1]
            
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = payload.get("sub")
                if not user_id:
                    raise HTTPException(status_code=401, detail="Invalid token")
            except jwt.PyJWTError:
                raise HTTPException(status_code=401, detail="Invalid token format")
                
            # Get quiz results from database
            db = get_db()
            quiz_result = db.skill_assessment_results.find_one(
                {"user_id": ObjectId(user_id)},
                sort=[("timestamp", -1)]  # Get the most recent result
            )
            
            if not quiz_result:
                raise HTTPException(
                    status_code=404, 
                    detail="No assessment results found for this user"
                )
                
            # Convert ObjectId to string for JSON serialization
            quiz_result["_id"] = str(quiz_result["_id"])
            quiz_result["user_id"] = str(quiz_result["user_id"])
            
            # Use the stored assessment results
            assessment_results = AssessmentResults(
                score=quiz_result["score"],
                assessed_level=quiz_result["assessed_level"],
                question_feedback=quiz_result["question_feedback"],
                skill_gaps=quiz_result["skill_gaps"],
                recommendations=quiz_result["recommendations"]
            )
        
        if not assessment_results:
            raise HTTPException(
                status_code=400,
                detail="Assessment results must be provided"
            )
            
        # Generate playlists using the youtube_education function
        playlists = generate_skill_playlist(assessment_results.dict())
        
        # Optionally store the generated playlists in the database
        if authorization and authorization.startswith("Bearer "):
            try:
                token = authorization.split(" ")[1]
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = payload.get("sub")
                
                if user_id:
                    db = get_db()
                    db.generated_playlists.update_one(
                        {"user_id": ObjectId(user_id)},
                        {
                            "$set": {
                                "playlists": playlists,
                                "updated_at": datetime.utcnow()
                            }
                        },
                        upsert=True
                    )
            except Exception as e:
                # Log the error but don't fail the request
                print(f"Error storing playlists: {str(e)}")
        
        return playlists
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@router.post("/get_videos")
async def get_youtube_videos(payload: dict):
    """
    Accepts JSON input and returns a list of skills with their YouTube video links.
    
    Expected JSON structure example:
    {
      "score": { ... },
      "assessed_level": "intermediate",
      "skill_gaps": {
          "areas": [
              { "skill": "Data Analysis", "level": "satisfactory" },
              { "skill": "Programming", "level": "needs improvement" }
          ]
      },
      "recommendations": [ ... ]
    }
    """
    try:
        result = generate_skill_playlist(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_links(query: str = Query(..., description="The search query to find relevant YouTube videos")):
    """
    Accepts a query parameter and returns a list of YouTube links for the top 10 results.
    
    Example:
      GET /api/yotube_videos/search?query=python+tutorial
    """
    try:
        links = respond_to_normal_query(query)
        return {"links": links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
