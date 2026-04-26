# src/main.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from agent_logic import analyze_report_image, check_duplicate_report
from mock_db import tickets, save_ticket, get_recent_tickets, AGENCIES

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "bantay-daan-2026")

# Mock User DB for fallback
MOCK_USERS = {
    "citizen@bantay.ph": "password123"
}

@app.route("/")
def index():
    user = session.get("user")
    if not user:
        return redirect(url_for("login_page"))
    return render_template("dashboard.html", user=user, tickets=reversed(tickets))

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Basic Auth Logic
        if email in MOCK_USERS and MOCK_USERS[email] == password:
            session["user"] = {"name": email.split('@')[0], "email": email}
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials. Use citizen@bantay.ph / password123")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        MOCK_USERS[email] = password
        session["user"] = {"name": email.split('@')[0], "email": email}
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("login_page"))

@app.route("/report", methods=["POST"])
def report():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    file = request.files.get("image")
    location = request.form.get("location", "Manila")
    gps_coords = request.form.get("gps_coords") # Expecting "lat,lon"
    
    if file:
        os.makedirs("src/static/uploads", exist_ok=True)
        temp_path = os.path.join("src/static/uploads", file.filename)
        file.save(temp_path)
        
        try:
            # Step 1: Vision Analysis
            analysis = analyze_report_image(temp_path, location, gps_coords)
            if "error" in analysis:
                return jsonify(analysis), 500
            
            # Step 2: Triage (Deduplication)
            recent = get_recent_tickets(10)
            triage_result = check_duplicate_report({"issue": analysis['issue'], "location": location}, recent)
            
            return jsonify({
                "analysis": analysis,
                "triage": triage_result,
                "image_url": f"/static/uploads/{file.filename}",
                "image_path": temp_path,
                "agencies": list(AGENCIES.keys())
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "No file"}), 400

@app.route("/submit_final", methods=["POST"])
def submit_final():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    try:
        ticket = save_ticket(
            data['agency'],
            data['issue'],
            data['severity'],
            data['coordinates'],
            data['location']
        )
        return jsonify({"success": True, "ticket_id": ticket['id']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    os.makedirs("src/static/uploads", exist_ok=True)
    app.run(debug=True, port=5000)
