import os
import json
import re
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
import numpy as np
from datetime import timedelta

# Langchain imports
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

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


def format_timestamp(seconds):
    """
    Format seconds into HH:MM:SS timestamp.

    Args:
        seconds (float): Time in seconds

    Returns:
        str: Formatted timestamp
    """
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


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
            formatted_timestamp = format_timestamp(start_time)

            transcriptions.append({
                "timestamp": formatted_timestamp,
                "start_seconds": start_time,
                "duration": entry.get('duration', 0),
                "end_seconds": start_time + entry.get('duration', 0),
                "text": entry['text']
            })

        return transcriptions

    except Exception as e:
        raise Exception(f"Error retrieving transcript: {str(e)}")


def create_langchain_documents(transcriptions, chunk_size=5, chunk_overlap=1):
    """
    Convert transcript entries to LangChain Document objects with metadata.

    Args:
        transcriptions (list): List of transcript entries
        chunk_size (int): Number of transcript entries per chunk
        chunk_overlap (int): Number of overlapping entries between chunks

    Returns:
        list: List of LangChain Document objects
    """
    documents = []

    # Process transcript in chunks
    for i in range(0, len(transcriptions), chunk_size - chunk_overlap):
        # Get chunk entries
        chunk_entries = transcriptions[i:i + chunk_size]

        if not chunk_entries:
            continue

        # Combine text content from chunk
        chunk_text = " ".join([entry["text"] for entry in chunk_entries])

        # Get start and end times for chunk
        start_time = chunk_entries[0]["timestamp"]
        start_seconds = chunk_entries[0]["start_seconds"]
        end_time = chunk_entries[-1]["timestamp"]
        end_seconds = chunk_entries[-1]["end_seconds"]

        # Create Document with metadata
        doc = Document(
            page_content=chunk_text,
            metadata={
                "source": "youtube_transcript",
                "start_time": start_time,
                "end_time": end_time,
                "start_seconds": start_seconds,
                "end_seconds": end_seconds
            }
        )

        documents.append(doc)

    return documents


class YouTubeLangChainRAG:
    """Class for LangChain RAG-based Q&A on YouTube video transcripts"""

    def __init__(self, api_key, model_name="gemini-1.5-flash"):
        """Initialize the RAG Q&A with API key"""
        self.api_key = api_key
        self.model_name = model_name

        # Configure Google API
        genai.configure(api_key=api_key)

        # Initialize embedding model
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.2,
            top_p=0.95,
            top_k=64,
            convert_system_message_to_human=True
        )

        # Set up RAG prompt
        self.rag_prompt = PromptTemplate.from_template(
            """
            You are an expert at answering questions based on video transcripts.

            The following are relevant sections from a YouTube video transcript:

            {context}

            Using ONLY the information provided in these transcript sections, answer the following question:

            Question: {question}

            In your answer:
            1. Be direct and to the point.
            2. Provide specific information from the transcript.
            3. Mention the specific timestamps where the information appears (these are included in the context).
            4. If the information isn't in the transcript, clearly state that.
            5. Structure your answer to clearly address the question.

            Format your answer with a clear main response first, followed by "TIMELINE REFERENCES:" that lists the specific parts of the video where the information was found.

            Answer:
            """
        )

        # Store video data
        self.video_data = {}

    def process_video(self, video_url, languages=['en'], force_refresh=False):
        """
        Process a video transcript and create a vector store.

        Args:
            video_url (str): YouTube video URL
            languages (list): List of language codes to try
            force_refresh (bool): Force refresh of existing data

        Returns:
            dict: Processed video data
        """
        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Check if video already processed
        if video_id in self.video_data and not force_refresh:
            return self.video_data[video_id]

        # Get video transcript
        transcriptions = get_transcript(video_id, languages)

        # Convert to LangChain documents
        documents = create_langchain_documents(transcriptions)

        # Create vector store
        vector_store = FAISS.from_documents(
            documents,
            self.embedding_model
        )

        # Store processed data
        self.video_data[video_id] = {
            "video_id": video_id,
            "video_url": video_url,
            "transcriptions": transcriptions,
            "documents": documents,
            "vector_store": vector_store
        }

        return self.video_data[video_id]

    def answer_question(self, video_url, question, languages=['en'], top_k=3):
        """
        Answer a question about a YouTube video using RAG.

        Args:
            video_url (str): YouTube video URL
            question (str): Question about the video
            languages (list): List of language codes to try
            top_k (int): Number of top chunks to retrieve

        Returns:
            dict: Answer with source timestamps
        """
        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Process video if not already processed
        if video_id not in self.video_data:
            self.process_video(video_url, languages)

        # Get video data
        video_data = self.video_data[video_id]

        # Get vector store
        vector_store = video_data["vector_store"]

        # Create retriever with top_k
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": top_k}
        )

        # Get relevant documents
        relevant_docs = retriever.get_relevant_documents(question)

        # Format context from relevant documents
        context = ""
        for i, doc in enumerate(relevant_docs):
            context += f"\n--- Chunk {i + 1} (Timestamp {doc.metadata['start_time']} - {doc.metadata['end_time']}) ---\n"
            context += doc.page_content + "\n"

        # Use the prompt template to format the prompt
        prompt = self.rag_prompt.format(
            context=context,
            question=question
        )

        # Get answer from LLM
        answer = self.llm.invoke(prompt).content

        # Extract source information from relevant documents
        sources = []
        for doc in relevant_docs:
            sources.append({
                "start_time": doc.metadata["start_time"],
                "end_time": doc.metadata["end_time"],
                "start_seconds": doc.metadata["start_seconds"],
                "end_seconds": doc.metadata["end_seconds"]
            })

        # Return answer with metadata
        return {
            "video_id": video_id,
            "video_url": video_url,
            "question": question,
            "answer": answer,
            "sources": sources
        }