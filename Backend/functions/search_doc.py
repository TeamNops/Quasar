
import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_community.tools import TavilySearchResults
from langchain_community.utilities import GoogleSerperAPIWrapper
from duckduckgo_search import DDGS  # Install via `pip install duckduckgo-search`
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException
import json
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

# Initialize the Gemini client (set your API key if needed)
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model_id = "gemini-2.0-flash"

# Configure Google Search as a tool
google_search_tool = Tool(
    google_search=GoogleSearch()
)
def llm_serper(query):
    search = GoogleSerperAPIWrapper(serper_api_key="5abd612e50256b99688f9eded0b9583685c815cf")
    results = search.results(query)
    organic_results = results.get("organic", [])
    links = [result.get("link") for result in organic_results if "link" in result]
    return links

def get_web_links(query):
    # Generate a grounded response for the given query
    response = client.models.generate_content(
        model=model_id,
        contents=query,
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"],
        )
    )
    
    links = []
    grounding_metadata = response.candidates[0].grounding_metadata
    #print('grounding \n', grounding_metadata)

    # Try to get grounding chunks with either attribute name
    chunks = None
    if hasattr(grounding_metadata, 'groundingChunks'):
        chunks = grounding_metadata.groundingChunks
    elif hasattr(grounding_metadata, 'grounding_chunks'):
        chunks = grounding_metadata.grounding_chunks

    if chunks:
        for chunk in chunks:
            # Ensure the chunk has a web attribute and it's not None
            if hasattr(chunk, 'web') and chunk.web is not None:
                links.append({
                    "uri": chunk.web.uri,
                    "title": chunk.web.title
                })
    return links

    
def tavily_search(query):
    """
    Perform a Tavily search and return relevant documents.
    """
    tavily_tool = TavilySearchResults()
    results = tavily_tool.run(query)
    return results
import time
# def duckduckgo_search(query, max_results=5, retries=3, delay=2):
#     for attempt in range(retries):
#         try:
#             with DDGS() as ddgs:
#                 results = list(ddgs.text(query, max_results=max_results))
#                 return [
#                     {
#                         "title": result.get("title", "No Title"),
#                         "link": result.get("href", "No Link")
#                     }
#                     for result in results
#                 ]
#         except DuckDuckGoSearchException as e:
#             print(f"Attempt {attempt+1} failed with error: {e}")
#             if attempt < retries - 1:
#                 print(f"Retrying in {delay} seconds...")
#                 time.sleep(delay)
#                 delay *= 2  # Exponential backoff
#             else:
#                 raise e

def generate_skill_resources(input_json):
    """
    Takes JSON data (string or dict) as input, extracts skills from the 'skill_gaps' areas,
    generates a learning workflow for each skill via a generative model, retrieves Tavily documents,
    and DuckDuckGo links, and returns a list of skills with their respective resources.

    Returns:
        A list of dictionaries in the format:
        [
            {
                "skill": "Skill Name",
                "documents": [
                    {"title": "Doc Title 1", "content": "Doc Content 1", "link": "Doc Link 1"},
                    ...
                ],
                "links": [
                    {"title": "Link Title 1", "link": "Link URL 1"},
                    ...
                ]
            },
            ...
        ]
    """
    # Load environment variables
    load_dotenv()

    # Parse input JSON if it is a string
    if isinstance(input_json, str):
        data = json.loads(input_json)
    else:
        data = input_json

    # Extract skills from the JSON data
    improvement_areas = data.get("skill_gaps", {}).get("areas", [])
    skills = [area["skill"] for area in improvement_areas if "skill" in area]
    import google.generativeai as genai
    # Configure the generative AI model
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    generation_config = {
        "temperature": 0.2,       # More deterministic output
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 3000 # Allows longer responses
    }
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config=generation_config
    )

    # Helper function: clean the generative model's JSON response
    def clean_json_response(response_text):
        cleaned_text = re.sub(r"```json|```", "", response_text).strip()
        return cleaned_text

    # Helper function: generate a workflow (list of concepts) for a given skill
    def generate_workflow(skill):
        prompt = f"""Generate a structured JSON response for learning {skill}, listing essential concepts in a logical order. The response should follow this format:  
{{
  "skill": "{skill}",
  "concepts": [
    "keyword1",
    "keyword2",
    "keyword3"
    // up to a maximum of 10 keywords
  ]
}}
"""
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        print(f"\nRaw response for {skill}:\n{raw_text}")
        return clean_json_response(raw_text)

    # For each skill, generate the workflow, Tavily documents, and DuckDuckGo links
    result = []
    for skill in skills:
        print(f"\nGenerating workflow for: {skill}")
        workflow_json = generate_workflow(skill)

        try:
            workflow_data = json.loads(workflow_json)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {skill}: {e}\nResponse: {workflow_json}")
            continue

        # Get list of concepts from the workflow
        concepts = workflow_data.get("concepts", [])

        # Generate Tavily documents
        tavily_query = f"{skill} learning blogs"
        tavily_docs = tavily_search(tavily_query)

        # Generate DuckDuckGo links
        duckduckgo_query = f"find me blogs on topic {skill}"
        #duckduckgo_links = duckduckgo_search(duckduckgo_query, max_results=5)
        links=llm_serper(duckduckgo_query)
        vertexta_ai_search=get_web_links(duckduckgo_query)

        # Append results for the current skill
        result.append({
            "skill": skill,
            "documents": tavily_docs,
            "blogs":links
        })

    return result

# # Example usage
# if __name__ == "__main__":
#     sample_json = """
#     {
#       "score": {
#         "correct": 5,
#         "total": 10,
#         "percentage": 50
#       },
#       "assessed_level": "intermediate",
#       "question_feedback": [
#         {
#           "question_index": 0,
#           "is_correct": true,
#           "correct_answer": 1,
#           "explanation": "NumPy is the fundamental package for scientific computing in Python, providing support for large, multi-dimensional arrays and matrices."
#         }
#       ],
#       "skill_gaps": {
#         "overall": "Based on your assessment, we've identified areas for improvement",
#         "areas": [
#           {
#             "skill": "Data Analysis",
#             "level": "satisfactory"
#           },
#           {
#             "skill": "Programming",
#             "level": "needs improvement"
#           }
#         ]
#       },
#       "recommendations": [
#         {
#           "title": "Machine Learning Algorithms",
#           "type": "course"
#         }
#       ]
#     }
#     """
#     playlists = generate_skill_resources(sample_json)
#     print(json.dumps(playlists, indent=4))

# response=llm_serper("Data Science")
# print(response)