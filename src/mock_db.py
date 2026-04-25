# src/mock_db.py

AGENCIES = {
    "DPWH": {
        "name": "Department of Public Works and Highways",
        "scope": ["pothole", "cracked road", "flooded road"],
        "contact": "hotline@dpwh.gov.ph"
    },
    "Manila Water": {
        "name": "Manila Water Company",
        "scope": ["leaking pipe", "burst pipe", "water service"],
        "contact": "care@manilawater.com"
    },
    "Meralco": {
        "name": "Manila Electric Railroad and Light Company",
        "scope": ["broken street light", "dangling wire", "power outage"],
        "contact": "customercare@meralco.com.ph"
    },
    "MMDA": {
        "name": "Metropolitan Manila Development Authority",
        "scope": ["broken traffic light", "road obstruction"],
        "contact": "mmda_action@gov.ph"
    }
}

# Simulated database for tickets
tickets = []

def save_ticket(agency, issue, severity, coordinates, location):
    ticket_id = f"BD-{len(tickets) + 1000}"
    ticket = {
        "id": ticket_id,
        "agency": agency,
        "issue": issue,
        "severity": severity,
        "coordinates": coordinates,
        "location": location,
        "status": "Submitted to Agency"
    }
    tickets.append(ticket)
    return ticket
