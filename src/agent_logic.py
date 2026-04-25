# src/agent_logic.py
import os
import requests
import base64
import json
from dotenv import load_dotenv
from mock_db import AGENCIES, save_ticket

load_dotenv(override=True)

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-robotics-er-1.6-preview"

def get_responsible_agency(issue_type: str):
    """Determines which government agency handles a specific issue type."""
    issue_type = issue_type.lower()
    for agency_id, info in AGENCIES.items():
        for scope in info["scope"]:
            if scope in issue_type:
                return agency_id
    return "Local Barangay"

def file_infrastructure_report(agency_id: str, issue: str, severity: str, location: str, coordinates: list):
    """Saves the report to our mock database."""
    ticket = save_ticket(agency_id, issue, severity, coordinates, location)
    return f"Success: Ticket {ticket['id']} filed with {agency_id}."

def run_bantay_daan_agent(image_path, user_location="Unknown Location"):
    # Encode image to base64
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    
    # Prompt for structured JSON output to simulate agentic decision making
    prompt = f"""
    Identify the infrastructure issue in this photo (pothole, broken light, etc.) at {user_location}.
    Return ONLY a JSON object:
    {{
        "issue": "string",
        "severity": "low/medium/high",
        "coordinates": [ymin, xmin, ymax, xmax],
        "summary_taglish": "friendly summary in Taglish"
    }}
    """

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_data}}
            ]
        }],
        "generationConfig": {
            "response_mime_type": "application/json"
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Parse the JSON response from Gemini
        raw_text = result['candidates'][0]['content']['parts'][0]['text']
        content = json.loads(raw_text)
        
        # AGENTIC LOGIC: Execute the "tools" based on AI decision
        issue = content.get('issue', 'Unknown Issue')
        severity = content.get('severity', 'Medium')
        coords = content.get('coordinates', [0,0,0,0])
        summary = content.get('summary_taglish', 'Report processed.')
        
        agency = get_responsible_agency(issue)
        file_infrastructure_report(agency, issue, severity, user_location, coords)
        
        final_output = f"{summary}\n\n**Action:** Report filed with {agency}."
        return final_output, []
        
    except Exception as e:
        return f"Error contacting Gemini API: {str(e)}", []
