from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
import os
from dotenv import load_dotenv
import uuid

from functions.rag_function import YouTubeLangChainRAG, extract_video_id, get_transcript

# Ensure environment variables are loaded
load_dotenv()

router = APIRouter(
    prefix="/api/youtube-qa",
    tags=["youtube-qa"],
    responses={404: {"description": "Not found"}},
)

# Cache for storing RAG system (in a production app, use a proper cache like Redis)
rag_cache = {}


class YouTubeQARequest(BaseModel):
    """Request model for asking a question about a YouTube video"""
    video_url: HttpUrl
    question: str
    languages: List[str] = ["en"]
    top_k: int = 3


class YouTubeProcessRequest(BaseModel):
    """Request model for processing a YouTube video"""
    video_url: HttpUrl
    languages: List[str] = ["en"]
    force_refresh: bool = False


def get_rag_system():
    """Dependency to get the RAG system"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY not found in .env file. Please add GOOGLE_API_KEY=your_api_key to your .env file."
        )

    # Check if RAG system already exists in cache
    if "rag_system" not in rag_cache:
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        rag_cache["rag_system"] = YouTubeLangChainRAG(api_key, model_name)

    return rag_cache["rag_system"]


@router.post("/process", response_model=Dict[str, Any])
async def process_youtube_video(
        params: YouTubeProcessRequest,
        rag_system=Depends(get_rag_system)
):
    """
    Process a YouTube video transcript and create a vector store for RAG
    """
    try:
        # Extract video_id first as a quick validation
        video_id = extract_video_id(str(params.video_url))
        if not video_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL"
            )

        # Process video
        video_data = rag_system.process_video(
            video_url=str(params.video_url),
            languages=params.languages,
            force_refresh=params.force_refresh
        )

        # Return success response
        return {
            "success": True,
            "video_id": video_id,
            "video_url": str(params.video_url),
            "documents_count": len(video_data["documents"]),
            "transcript_length": len(video_data["transcriptions"]),
            "message": "Video processed successfully and ready for questions"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process video: {str(e)}"
        )


@router.post("/ask", response_model=Dict[str, Any])
async def ask_question(
        params: YouTubeQARequest,
        rag_system=Depends(get_rag_system)
):
    """
    Ask a question about a YouTube video using LangChain RAG
    """
    try:
        # Extract video_id first as a quick validation
        video_id = extract_video_id(str(params.video_url))
        if not video_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL"
            )

        # Validate question
        if not params.question or len(params.question.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a valid question"
            )

        # Answer question
        result = rag_system.answer_question(
            video_url=str(params.video_url),
            question=params.question,
            languages=params.languages,
            top_k=params.top_k
        )

        # Return answer with metadata
        return {
            "success": True,
            "video_id": video_id,
            "video_url": str(params.video_url),
            "question": params.question,
            "answer": result.get("answer", ""),
            "sources": result.get("sources", [])
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.get("/transcript/{video_id}", response_model=Dict[str, Any])
async def get_video_transcript(
        video_id: str,
        languages: List[str] = ["en"]
):
    """
    Get the transcript for a YouTube video
    """
    try:
        # Validate video ID
        if not video_id or len(video_id) != 11:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube video ID"
            )

        # Get transcript
        transcriptions = get_transcript(video_id, languages)

        # Return transcript
        return {
            "success": True,
            "video_id": video_id,
            "transcriptions": transcriptions
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transcript: {str(e)}"
        )


def register_youtube_qa_routes(app):
    """
    Register all YouTube Q&A routes with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.include_router(router)