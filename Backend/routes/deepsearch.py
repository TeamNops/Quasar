from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json

# Import your function
from functions.search_doc import generate_skill_resources

router = APIRouter(
    prefix="/api/deepresearch",
    tags=["docs recommendation"]
)

class SkillAssessmentInput(BaseModel):
    data: Dict[str, Any]

@router.post("/recommendations")
async def get_recommendations(input_data: SkillAssessmentInput):
    try:
        # Generate recommendations
        results = generate_skill_resources(input_data.data)
        return {"status": "success", "recommendations": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
