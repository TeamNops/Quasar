import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_community.tools import TavilySearchResults
from langchain_community.document_loaders import ArxivLoader

def tavily_search(query):
    """
    Perform a Tavily search and return relevant documents.
    """
    tavily_tool = TavilySearchResults()
    results = tavily_tool.run(query)
    return results

def arxiv_search(query, max_results=5):
    """
    Perform an Arxiv search and return research papers.
    """
    loader = ArxivLoader(query=query, load_max_docs=max_results)
    papers = loader.load()
    return [
        {
            "title": paper.metadata.get("Title", "No Title"),
            "summary": paper.page_content,
            "link": paper.metadata.get("Entry ID", "No Link")
        }
        for paper in papers
    ]

def generate_skill_resources(input_json):
    """
    Takes JSON data (string or dict) as input, extracts skills from the 'skill_gaps' areas,
    generates a learning workflow for each skill via a generative model, retrieves Tavily documents,
    and Arxiv papers, and returns a list of skills with their respective resources.

    Returns:
        A list of dictionaries in the format:
        [
            {
                "skill": "Skill Name",
                "documents": [
                    {"title": "Doc Title 1", "content": "Doc Content 1", "link": "Doc Link 1"},
                    ...
                ],
                "papers": [
                    {"title": "Paper Title 1", "summary": "Paper Summary 1", "link": "Paper Link 1"},
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

    # For each skill, generate the workflow, Tavily documents, and Arxiv papers
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
        tavily_query = f"{skill} learning resources"
        tavily_docs = tavily_search(tavily_query)

        # Generate Arxiv papers
        arxiv_query = f"{skill}"
        arxiv_papers = arxiv_search(arxiv_query, max_results=5)

        # Append results for the current skill
        result.append({
            "skill": skill,
            "documents": tavily_docs,
            "papers": arxiv_papers
        })

    return result


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
#     print(playlists)
