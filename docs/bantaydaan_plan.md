# BantayDaan Implementation Plan

## Tech Stack
- **Frontend/UI:** Streamlit (Python)
- **AI Model:** Gemini 1.5 Flash (via `google-generativeai`)
- **Spatial Feature:** Bounding box detection for infrastructure issues.

## Project Structure
- `app.py`: Main Streamlit application.
- `agent_logic.py`: Gemini configuration and tool definitions.
- `mock_db.py`: Local data for agencies and simulated ticket database.

## 60-Minute Countdown
1. **[0-10m] Setup:** Initialize environment and mock data.
2. **[10-25m] AI Integration:** Implement the spatial prompting to get coordinates.
3. **[25-45m] Agentic Workflow:** Implement tool calling (Agency lookup).
4. **[45-60m] Polishing:** Streamlit UI layout and "Aesthetics" check.
