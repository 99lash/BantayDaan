# src/agent_logic.py
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from mock_db import AGENCIES, save_ticket

load_dotenv()

# Modern Gemini Client (v2.0+)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_ID = "gemini-robotics-er-1.6-preview"

def get_responsible_agency(issue_type: str) -> str:
    """Determines which government agency handles a specific issue type."""
    issue_type = issue_type.lower()
    for agency_id, info in AGENCIES.items():
        for scope in info["scope"]:
            if scope in issue_type:
                return agency_id
    return "Local Barangay"

def file_infrastructure_report(agency_id: str, issue: str, severity: str, location: str, coordinates: list) -> str:
    """Tool for the agent to 'file' the report to the government system."""
    ticket = save_ticket(agency_id, issue, severity, coordinates, location)
    return f"Success: Ticket {ticket['id']} filed with {agency_id}."

def run_bantay_daan_agent(image_path, user_location="Unknown Location"):
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    prompt = f"""
    You are the BantayDaan Agent at {user_location}.
    1. Identify the infrastructure problem and its severity from this photo.
    2. Use 'get_responsible_agency' to find the right agency.
    3. Use 'file_infrastructure_report' to submit the report.
    4. Provide spatial coordinates [ymin, xmin, ymax, xmax].
    5. Return a friendly summary in Taglish for the citizen.
    """

    # Automatic Function Calling is standard in the new SDK
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt
        ],
        config=types.GenerateContentConfig(
            tools=[get_responsible_agency, file_infrastructure_report],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
        )
    )
    
    return response.text, []
