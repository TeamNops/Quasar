import json
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_community.tools import YouTubeSearchTool
tool=YouTubeSearchTool()
def respond_to_normal_query(query):
    links=tool.run(f"{query},20")
    return links
def generate_skill_playlist(input_json):
    """
    Takes JSON data (string or dict) as input, extracts skills from the 'skill_gaps' areas,
    generates a learning workflow for each skill via a generative model, retrieves YouTube links
    for each concept, and returns a list of skills with their respective playlists.

    Returns:
        A list of dictionaries in the format:
        [
            {
                "skill": "Skill Name",
                "playlist": [
                    {"concept": "keyword1", "youtube_link": "Link1"},
                    {"concept": "keyword2", "youtube_link": "Link2"},
                    ...
                ]
            },
            ...
        ]
    """
    # Load environment variables
    load_dotenv()

    # Initialize YouTube search tool
    tool = YouTubeSearchTool()

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
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
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
        # Debug: Print raw response (optional)
        print(f"\nRaw response for {skill}:\n{raw_text}")
        return clean_json_response(raw_text)

    # Helper function: generate YouTube playlist for a list of concepts
    def generate_playlist(skill, concepts):
        playlist = []
        for concept in concepts:
            try:
                # Search for a full video related to the concept (top result)
                link = tool.run(f"{skill} {concept} course,1")
                playlist.append({"concept": concept, "youtube_link": link})
            except Exception as e:
                print(f"Error fetching YouTube link for {concept}: {e}")
        return playlist


    # For each skill, generate the workflow and YouTube playlist
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
        playlist = generate_playlist(skill,concepts)
        result.append({"skill": skill, "playlist": playlist})

    return result

# Example usage:
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
#     playlists = generate_skill_playlist(sample_json)
#     print(playlists)
#     print("\n--- Generated Playlists ---")
#     for item in playlists:
#         print(f"\nSkill: {item['skill']}")
#         for concept in item["playlist"]:
#             print(f"  - {concept['concept']}: {concept['youtube_link']}")
