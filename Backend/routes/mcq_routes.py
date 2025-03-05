from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from functions.mcq_functions import create_quiz_generator, generate_quiz, score_quiz

# Ensure environment variables are loaded
load_dotenv()

router = APIRouter(
    prefix="/api/quiz",
    tags=["quiz"],
    responses={404: {"description": "Not found"}},
)

# Cache for storing generated quizzes (in a production app, use a proper cache like Redis)
quiz_cache = {}


class UserParameters(BaseModel):
    """User parameters for generating a quiz"""
    primary_goal: str
    selected_skills: List[str]
    time_commitment: str
    career_path: str
    experience_level: str = "intermediate"
    num_questions: int = 10


class QuizSubmission(BaseModel):
    """User's quiz submission with answers"""
    quiz_id: str
    user_answers: List[int]


class SkillGapResponse(BaseModel):
    """Response model for skill gap analysis"""
    overall_level: str
    skill_gaps: Dict[str, Any]
    recommendations: List[Dict[str, Any]]


def get_quiz_generator():
    """Dependency to get the quiz generator"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY not found in .env file. Please add GEMINI_API_KEY=your_api_key to your .env file."
        )
    return create_quiz_generator(api_key)


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


@router.post("/submit", response_model=Dict[str, Any])
async def submit_quiz(submission: QuizSubmission):
    """
    Submit answers for a generated quiz and get results with skill gap analysis
    """
    # Retrieve the quiz from cache
    if submission.quiz_id not in quiz_cache:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found. It may have expired."
        )

    quiz_content = quiz_cache[submission.quiz_id]

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
                {"skill": "Programming", "level": "satisfactory" if skill_level == "advanced" else "needs improvement"}
            ]
        },
        "recommendations": recommendations
    }

    # In a production app, you'd probably want to clean up the cache eventually
    # background_tasks.add_task(lambda: quiz_cache.pop(submission.quiz_id, None))

    return response


@router.get("/sample/{skill_area}")
async def get_sample_questions(skill_area: str):
    """
    Get sample questions for a specific skill area (for testing purposes)
    """
    # This endpoint could provide some sample questions without requiring the full generation
    # Useful for testing the UI without hitting the LLM API

    sample_questions = {
        "programming": [
            {
                "question": "What does the following Python code output? \n\nx = [1, 2, 3]\ny = x\ny.append(4)\nprint(x)",
                "options": ["[1, 2, 3]", "[1, 2, 3, 4]", "[1, 2, 3], [1, 2, 3, 4]", "Error"],
                "difficulty": "intermediate"
            }
        ],
        "data_science": [
            {
                "question": "Which of the following is NOT a common evaluation metric for classification problems?",
                "options": ["Precision", "Recall", "Mean Squared Error", "F1 Score"],
                "difficulty": "intermediate"
            }
        ],
        "leadership": [
            {
                "question": "Which leadership style involves making decisions based on input from team members?",
                "options": ["Autocratic", "Laissez-faire", "Democratic", "Transformational"],
                "difficulty": "intermediate"
            }
        ]
    }

    if skill_area.lower() not in sample_questions:
        return {"questions": []}

    return {"questions": sample_questions[skill_area.lower()]}


@router.get("/debug")
async def debug_endpoint():
    """
    Debug endpoint to check if the quiz generation is working properly
    """
    try:
        # Test with hard-coded values
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "GEMINI_API_KEY not found in environment"}

        return {
            "status": "API key found",
            "message": "Use POST /api/quiz/generate with proper JSON body to generate quiz"
        }
    except Exception as e:
        return {"error": str(e)}