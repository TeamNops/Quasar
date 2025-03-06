from functions.youtube_education import generate_skill_playlist,respond_to_normal_query
from fastapi import APIRouter,Query
router = APIRouter(
    prefix="/api/yotube_videos",
    tags=["quiz"],
    responses={404: {"description": "Not found"}},
)
from fastapi import APIRouter, HTTPException
from functions.youtube_education import generate_skill_playlist

router = APIRouter(
    prefix="/api/yotube_videos",
    tags=["quiz"],
    responses={404: {"description": "Not found"}},
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
