# src/agent_logic.py
import os
import PIL.Image
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from mock_db import AGENCIES, save_ticket

load_dotenv(override=True)

API_KEY = os.environ.get("GEMINI_API_KEY")
VISION_MODEL = "gemma-4-26b-a4b-it"
TRIAGE_MODEL = "gemma-3-4b-it"

client = genai.Client(api_key=API_KEY)

def get_responsible_agency(issue_type: str):
    """Determines which government agency handles a specific issue type.
    
    Args:
        issue_type: The type of infrastructure issue (e.g., 'pothole', 'broken street light').
    """
    issue_type = issue_type.lower()
    for agency_id, info in AGENCIES.items():
        for scope in info["scope"]:
            if scope in issue_type:
                return agency_id
    return "Local Barangay"

def analyze_report_image(image_path, user_location="Unknown Location", gps_coords=None):
    """Initial analysis of the image without saving to database."""
    img = PIL.Image.open(image_path)
    
    gps_info = f" (GPS: {gps_coords})" if gps_coords else ""
    prompt = f"""
    You are the BantayDaan Vision Agent. 
    1. Identify the infrastructure issue in this photo at {user_location}{gps_info}.
    2. Determine the responsible agency.
    3. Extract the bounding box coordinates [ymin, xmin, ymax, xmax].
    4. Provide a technical and concise description of the issue in Taglish for the government agency (e.g., Meralco, DPWH) to use for their field report or repair order.
    
    Use the tools provided.
    """

    config = types.GenerateContentConfig(
        tools=[get_responsible_agency],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(),
        system_instruction="You are a professional government logistics assistant in the Philippines. Provide clear, technical descriptions of infrastructure damage in Taglish for official reports."
    )

    try:
        response = client.models.generate_content(
            model=VISION_MODEL,
            contents=[prompt, img],
            config=config
        )
        
        summary = response.text
        agency = "Local Barangay"
        coords = [0, 0, 0, 0]
        issue = "Unknown Issue"
        
        # Extract details from thought process or tool calls
        for content in getattr(response, 'automatic_function_calling_history', []):
            for part in content.parts:
                if part.function_call and part.function_call.name == "get_responsible_agency":
                    issue = part.function_call.args.get("issue_type", "Unknown Issue")
                    # We can't get the result here easily from history without more parsing, 
                    # but we know it called it. Let's re-run it locally for the return.
                    agency = get_responsible_agency(issue)
                
                # Bounding box is often in the thought or final text if not a tool, 
                # but our previous run showed it likes to put it in tool args if we provide a tool.
                # However, we removed the filing tool. Let's look at the response parts.

        # If gemma doesn't put coords in a tool call (since we removed the filing tool), 
        # it might put it in text. Let's refine the prompt to ensure it's easy to find.
        # Actually, let's look at the candidates.
        
        # Let's try to find coords in ANY part of the response
        for cand in response.candidates:
            for part in cand.content.parts:
                if part.text and "[" in part.text and "]" in part.text:
                    import re
                    match = re.search(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]', part.text)
                    if match:
                        coords = [int(x) for x in match.groups()]

        return {
            "issue": issue,
            "agency": agency,
            "summary": summary,
            "coordinates": coords
        }
        
    except Exception as e:
        print(f"Vision Error: {e}")
        return {"error": str(e)}

def check_duplicate_report(new_report, recent_tickets):
    """Checks if the new report is a duplicate of recent ones."""
    if not recent_tickets:
        return None

    tickets_str = json.dumps([
        {"id": t['id'], "issue": t['issue'], "location": t['location']} 
        for t in recent_tickets
    ])
    
    prompt = f"""
    New Report: {new_report['issue']} at {new_report['location']}
    Recent Tickets: {tickets_str}
    
    Task: Does the new report describe the same issue as any of the recent tickets? 
    Consider the issue type and proximity of location.
    
    Return ONLY a raw JSON object like this: {{"is_duplicate": true, "duplicate_ticket_id": "BD-1001"}}
    """

    try:
        response = client.models.generate_content(
            model=TRIAGE_MODEL,
            contents=[prompt]
        )
        
        # Manually extract JSON from response text
        text = response.text.strip()
        # Remove markdown code blocks if any
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        print(f"Triage Error: {e}")
        return {"is_duplicate": False, "duplicate_ticket_id": None}
