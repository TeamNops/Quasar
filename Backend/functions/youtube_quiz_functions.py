import os
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from pydantic import BaseModel, Field
import re

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(youtube_url):
    """
    Extract the video ID from a YouTube URL.
    Supports various YouTube URL formats.
    """
    # Regular expression to match various YouTube URL formats
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )

    youtube_match = re.match(youtube_regex, youtube_url)

    if youtube_match:
        return youtube_match.group(6)

    return None


def get_transcript(video_id, languages=['en']):
    """
    Get the transcript for a YouTube video.
    Will try preferred languages first, but will use any available if those aren't found.

    Args:
        video_id (str): YouTube video ID
        languages (list): List of language codes to try, in order of preference

    Returns:
        list: List of transcript entries with 'timestamp' and 'text' keys
    """
    try:
        # Get all available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try to get transcript in preferred languages first
        transcript = None

        # Try each preferred language
        for lang in languages:
            try:
                # Try manual transcript first
                transcript = transcript_list.find_transcript([lang])
                if not transcript.is_generated:
                    print(f"Using manually created transcript in {lang}")
                    break
            except:
                pass

            try:
                # Try generated transcript
                transcript = transcript_list.find_transcript([lang])
                if transcript.is_generated:
                    print(f"Using auto-generated transcript in {lang}")
                    break
            except:
                pass

        # If preferred languages not found, use first available transcript
        if not transcript:
            print("Preferred languages not available. Using any available transcript...")

            # Get list of available transcripts
            available_langs = []
            for t in transcript_list:
                available_langs.append(t.language_code)

            if available_langs:
                # Use the first available language
                first_lang = available_langs[0]
                transcript = transcript_list.find_transcript([first_lang])
                print(f"Using transcript in {first_lang}")
            else:
                raise Exception("No transcripts available for this video.")

        # Get the transcript data
        transcript_data = transcript.fetch()

        # Format the transcript data into a list of entries
        transcriptions = []
        for entry in transcript_data:
            start_time = entry['start']
            # Convert seconds to HH:MM:SS format
            hours, remainder = divmod(start_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            timestamp = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

            transcriptions.append({
                "timestamp": timestamp,
                "description": entry['text']
            })

        return transcriptions

    except Exception as e:
        raise Exception(f"Error retrieving transcript: {str(e)}")


class YouTubeQuizGenerator:
    """Class to generate quizzes based on YouTube video content"""

    def __init__(self, api_key):
        """Initialize the quiz generator with API key"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        # Use a powerful model for generation
        self.generation_config = {
            "temperature": 0.2,  # Lower temperature for more deterministic output
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,  # Allow for long responses with multiple questions
        }
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",  # Use appropriate model based on API access
            generation_config=self.generation_config
        )

    def extract_video_metadata(self, video_id):
        """
        Extract metadata for a YouTube video using transcript.
        In a production system, you might want to use the YouTube Data API for this.

        Returns:
            dict: Video metadata including title and description
        """
        try:
            # For now, we'll use a simpler approach since we're focused on the transcript
            # You could extend this to use the YouTube Data API
            return {
                "video_id": video_id,
                "extracted_from_transcript": True
            }
        except Exception as e:
            raise Exception(f"Error extracting video metadata: {str(e)}")

    def prepare_transcript_for_quiz(self, transcriptions):
        """
        Prepare transcript for quiz generation by concatenating text.

        Args:
            transcriptions (list): List of transcript entries

        Returns:
            str: Concatenated transcript text
        """
        # Concatenate all transcript entries
        full_text = " ".join([entry["description"] for entry in transcriptions])

        # If text is very long, we might need to truncate or summarize it
        # For now, we'll use the full text if it's reasonable in length
        # This is where you might add chunking logic for very long videos
        return full_text

    def generate_quiz_from_transcript(self, transcript_text, num_questions=5, difficulty="intermediate"):
        """
        Generate a quiz based on transcript text.

        Args:
            transcript_text (str): Video transcript text
            num_questions (int): Number of questions to generate
            difficulty (str): Difficulty level (beginner, intermediate, advanced)

        Returns:
            dict: Generated quiz with questions and answers
        """
        # Create the prompt
        prompt = f"""
        You are an expert in creating educational assessments. Generate a quiz based on the following video transcript:

        {transcript_text[:8000]}  # Limited to 8000 chars to avoid token limits

        Create {num_questions} multiple-choice questions (with 4 options each) to test understanding of the key concepts in this video. 
        The questions should be at {difficulty} level.

        For each question:
        1. Make sure it tests understanding, not just recall
        2. Include one clear correct answer and three plausible but incorrect options
        3. Provide a brief explanation for why the correct answer is right

        Return the result as a JSON object with the following structure:
        {{
          "questions": [
            {{
              "question": "Question text goes here?",
              "options": ["Option A", "Option B", "Option C", "Option D"],
              "correct_answer": 0,  // Index of the correct answer (0-based)
              "explanation": "Explanation for the correct answer",
              "difficulty": "{difficulty}"
            }}
            // ... more questions
          ]
        }}

        IMPORTANT: Format your response ONLY as a valid JSON object. DO NOT include any additional text, markdown formatting, or code blocks.
        """

        # Generate the response
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text

            # Extract JSON content
            if "```json" in response_text:
                json_content = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_content = response_text.split("```")[1].strip()
            else:
                json_content = response_text

            # Parse the JSON response
            try:
                parsed_json = json.loads(json_content)
                return parsed_json
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {str(e)}")
                # Return a fallback with error info
                return self._create_fallback_quiz(num_questions, difficulty, "JSON parsing error")
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            return self._create_fallback_quiz(num_questions, difficulty, str(e))

    def _create_fallback_quiz(self, num_questions, difficulty, error_info):
        """Create a fallback quiz if generation fails"""
        questions = []
        for i in range(min(3, num_questions)):
            questions.append({
                "question": f"Question {i + 1} about the video content (Generation Error: {error_info})",
                "options": [
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D"
                ],
                "correct_answer": 0,
                "explanation": "Please try again later. There was an error generating this quiz.",
                "difficulty": difficulty
            })

        return {"questions": questions}

    def generate_quiz_from_video_url(self, video_url, num_questions=5, difficulty="intermediate", languages=['en']):
        """
        Generate a quiz from a YouTube video URL.

        Args:
            video_url (str): YouTube video URL
            num_questions (int): Number of questions to generate
            difficulty (str): Difficulty level (beginner, intermediate, advanced)
            languages (list): List of language codes to try for transcript

        Returns:
            dict: Generated quiz with video metadata and questions
        """
        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Get video transcript
        transcriptions = get_transcript(video_id, languages)

        # Extract video metadata
        metadata = self.extract_video_metadata(video_id)

        # Prepare transcript for quiz generation
        transcript_text = self.prepare_transcript_for_quiz(transcriptions)

        # Generate quiz
        quiz = self.generate_quiz_from_transcript(transcript_text, num_questions, difficulty)

        # Combine everything
        result = {
            "video_id": video_id,
            "video_url": video_url,
            "metadata": metadata,
            "questions": quiz["questions"]
        }

        return result