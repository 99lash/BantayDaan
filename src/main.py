# src/main.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from agent_logic import run_bantay_daan_agent
from mock_db import tickets

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
    
    if file:
        temp_path = os.path.join("src/assets", file.filename)
        file.save(temp_path)
        
        try:
            summary, _ = run_bantay_daan_agent(temp_path, location)
            return jsonify({"summary": summary})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "No file"}), 400

if __name__ == "__main__":
    os.makedirs("src/assets", exist_ok=True)
    app.run(debug=True, port=5000)
