from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Header
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime
import jwt
import os

from functions.mcq_functions import create_quiz_generator, generate_quiz, score_quiz
from database import get_db
from jwt_config import settings

# Ensure environment variables are loaded
load_dotenv()

router = APIRouter(
    prefix="/api/quiz",
    tags=["quiz"],
    responses={404: {"description": "Not found"}},
)

quiz_cache = {}

# Define a class for quiz submission
class QuizSubmission(BaseModel):
    quiz_id: str
    user_answers: List[int]

class UserParameters(BaseModel):
    """User parameters for generating a quiz"""
    primary_goal: str
    selected_skills: List[str]
    time_commitment: str
    career_path: str
    experience_level: str = "intermediate"
    num_questions: int = 10

def get_quiz_generator():
    """Dependency to get the quiz generator"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not found in .env file. Please add GEMINI_API_KEY=your_api_key to your .env file."
        )
    return create_quiz_generator(api_key)

@router.post("/submit", response_model=Dict[str, Any])
async def submit_quiz(submission: QuizSubmission, authorization: str = Header(None)):
    """
    Submit answers for a generated quiz and get results with skill gap analysis
    """
    # Check authorization
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    # Get database connection
    db = get_db()

    global quiz_cache
    
    # Retrieve the quiz from cache or database
    quiz_content = None
    
    if submission.quiz_id in quiz_cache:
        quiz_content = quiz_cache[submission.quiz_id]
    else:
        # Try to get from database
        stored_quiz = db.quizzes.find_one({"quiz_id": submission.quiz_id})
        if stored_quiz:
            quiz_content = stored_quiz
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found. It may have expired."
            )

    # Validate submission
    if len(submission.user_answers) != len(quiz_content["questions"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of answers doesn't match number of questions"
        )

    # Score the quiz
    result = score_quiz(submission.user_answers, quiz_content)

    # Generate skill gap analysis and learning recommendations
    skill_level = result["assessed_level"]

    # Simple logic for recommendations based on assessed level
    # In production, this would be more sophisticated
    recommendations = []

    if skill_level == "beginner":
        recommendations = [
            {"title": "Fundamentals of Programming", "type": "course"},
            {"title": "Introduction to Data Science", "type": "workshop"},
            {"title": "Basic Statistical Concepts", "type": "tutorial"}
        ]
    elif skill_level == "intermediate":
        recommendations = [
            {"title": "Machine Learning Algorithms", "type": "course"},
            {"title": "SQL for Data Analysis", "type": "workshop"},
            {"title": "Feature Engineering Techniques", "type": "tutorial"}
        ]
    else:  # advanced
        recommendations = [
            {"title": "Advanced Deep Learning", "type": "course"},
            {"title": "Large Scale Data Systems", "type": "workshop"},
            {"title": "Research Methods in ML", "type": "tutorial"}
        ]

    # Construct the response with skill gaps and recommendations
    response = {
        "score": result["score"],
        "assessed_level": skill_level,
        "question_feedback": result["question_feedback"],
        "skill_gaps": {
            "overall": "Based on your assessment, we've identified areas for improvement",
            "areas": [
                {"skill": "Data Analysis", 
                 "level": "needs improvement" if skill_level == "beginner" else "satisfactory"},
                {"skill": "Programming", 
                 "level": "satisfactory" if skill_level == "advanced" else "needs improvement"}
            ]
        },
        "recommendations": recommendations
    }
    
    # Store the quiz results in the database
    try:
        # Create a document for quiz_results collection
        quiz_result_doc = {
            "user_id": ObjectId(user_id),
            "quiz_id": submission.quiz_id,
            "timestamp": datetime.utcnow(),
            "score": result["score"],
            "assessed_level": skill_level,
            "user_answers": submission.user_answers,
            "question_feedback": result["question_feedback"],
            "skill_gaps": response["skill_gaps"],
            "recommendations": recommendations
        }
        
        # Store in quiz_results collection
        db.skill_assessment_results.insert_one(quiz_result_doc)
        
        # Update user's assessment status
        db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"assessment_complete": True}}
        )
        
    except Exception as e:
        print(f"Error storing quiz results: {str(e)}")
        # Don't raise an exception here to allow the API to continue
    
    return response

@router.post("/generate", response_model=Dict[str, Any])
async def generate_assessment(
        params: UserParameters,
        background_tasks: BackgroundTasks,
        quiz_gen=Depends(get_quiz_generator)
):
    """
    Generate a personalized skill assessment quiz based on user parameters
    """
    try:
        # Generate a unique ID for this quiz
        import uuid
        quiz_id = str(uuid.uuid4())

        # Start quiz generation
        quiz_content = generate_quiz(
            model=quiz_gen,
            primary_goal=params.primary_goal,
            selected_skills=params.selected_skills,
            time_commitment=params.time_commitment,
            career_path=params.career_path,
            experience_level=params.experience_level,
            num_questions=params.num_questions
        )

        # Store the quiz with correct answers in cache
        global quiz_cache
        quiz_cache[quiz_id] = quiz_content

        # Create a user-facing version without correct answers
        user_quiz = {
            "quiz_id": quiz_id,
            "questions": [
                {
                    "question": q["question"],
                    "options": q["options"],
                    "difficulty": q.get("difficulty", "intermediate")
                }
                for q in quiz_content["questions"]
            ]
        }

        return user_quiz

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@router.get("/assessment-history")
async def get_assessment_history(authorization: str = Header(None)):
    """
    Get a user's assessment history
    """
    # Check authorization
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token format")

    # Get database connection
    db = get_db()
    
    try:
        # Find all assessment results for this user, sorted by timestamp (newest first)
        results = list(db.skill_assessment_results.find(
            {"user_id": ObjectId(user_id)},
            {"_id": 0}  # Exclude MongoDB _id field
        ).sort("timestamp", -1))
        
        # Convert ObjectId to string and format timestamps
        for result in results:
            if "timestamp" in result:
                result["timestamp"] = result["timestamp"].isoformat()
            if "user_id" in result and isinstance(result["user_id"], ObjectId):
                result["user_id"] = str(result["user_id"])
        
        return {"assessments": results}
    
    except Exception as e:
        print(f"Error retrieving assessment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assessment history: {str(e)}"
        )