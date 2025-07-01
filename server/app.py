from dotenv import load_dotenv # type: ignore
import os
import json
from supabase import create_client # type: ignore
from datetime import datetime
from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
import requests # type: ignore
import re
import random
import string

# Load environment variables
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)  

app = Flask(__name__)
CORS(app)

def create_api_key():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=32))

# GitHub helper functions
def get_github_username(social_links):
    github_url = social_links.get("Github")
    if not github_url:
        return None
    match = re.match(r"(?:https?://github\.com/)?([A-Za-z0-9-]+)", github_url)
    if match:
        return match.group(1)
    return None

def fetch_github_info(username):
    url = f"https://api.github.com/users/{username}"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        return resp.json()
    return None

def fetch_github_contributions(username):
    try:
        url = f"https://api.github.com/users/{username}/events/public"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return {}
        
        events = resp.json()
        contributions = {}
        
        for event in events:
            if event.get('type') in ['PushEvent', 'CreateEvent', 'PullRequestEvent', 'IssuesEvent']:
                date = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00')).date()
                contributions[date.isoformat()] = contributions.get(date.isoformat(), 0) + 1
        
        return contributions
    except Exception:
        return {}

def get_total_stars(username):
    try:
        stars = 0
        page = 1
        while True:
            url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}"
            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                break
            repos = resp.json()
            if not repos:
                break
            stars += sum(repo.get("stargazers_count", 0) for repo in repos)
            if len(repos) < 100:
                break
            page += 1
        return stars
    except Exception:
        return "?"

# Validation functions
def is_valid_username(username):
    return re.match(r"^[a-zA-Z0-9_]{3,20}$", username) is not None

def is_unique_username(username):
    response = supabase.table("Users").select("username").eq("username", username).execute()
    return len(response.data) == 0

def is_valid_password(password):
    return len(password) >= 8

# API Routes
@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    response = supabase.table("Users").select("*").eq("username", username).eq("password", password).execute()
    if len(response.data) == 0:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    return jsonify({"success": True, "user": response.data[0]})

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    bio = data.get('bio', '')
    social_links = data.get('social_links', {})
    
    # Validate input
    if not is_valid_username(username):
        return jsonify({"success": False, "message": "Username must be 3-20 characters, only letters, numbers, and underscores."}), 400
    
    if not is_unique_username(username):
        return jsonify({"success": False, "message": "Username already taken."}), 400
    
    if not is_valid_password(password):
        return jsonify({"success": False, "message": "Password must be at least 8 characters long."}), 400
    
    try:
        supabase.table("Users").insert({
            "username": username,
            "password": password,
            "social": social_links,
            "bio": bio
        }).execute()
        
        return jsonify({"success": True, "message": "Account created successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/user/<username>', methods=['GET'])
def get_user(username):
    response = supabase.table("Users").select("*").eq("username", username).execute()
    if not response.data:
        return jsonify({"success": False, "message": "User not found"}), 404

    user = response.data[0].copy()
    user.pop("password", None)  # Remove password from response

    # Get GitHub data if available
    github_data = None
    social_links = user.get("social", {})
    github_username = get_github_username(social_links)

    if github_username:
        gh_info = fetch_github_info(github_username)
        if gh_info:
            contributions = fetch_github_contributions(github_username)
            total_stars = get_total_stars(github_username)
            github_data = {
                "info": gh_info,
                "contributions": contributions,
                "total_stars": total_stars
            }

    return jsonify({
        "success": True,
        "user": user,
        "github_data": github_data
    })

@app.route('/api/user/<username>/update', methods=['PUT'])
def update_user(username):
    data = request.json
    bio = data.get('bio')
    social_links = data.get('social_links')
    password = data.get('password')

    if not password:
        return jsonify({"success": False, "message": "Password is required."}), 400
    
    response = supabase.table("Users").select("*").eq("username", username).eq("password", password).execute()
    if len(response.data) == 0:
        return jsonify({"success": False, "message": "Invalid password."}), 401

    try:
        supabase.table("Users").update({
            "bio": bio,
            "social": social_links
        }).eq("username", username).execute()
        
        return jsonify({"success": True, "message": "Profile updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    header = data.get('header')
    content = data.get('content')
    
    if not password:
        return jsonify({"success": False, "message": "Password is required."}), 400

    if not header.strip() or not content.strip():
        return jsonify({"success": False, "message": "Header and content cannot be empty"}), 400
    
    response = supabase.table("Users").select("*").eq("username", username).eq("password", password).execute()
    if len(response.data) == 0:
        return jsonify({"success": False, "message": "Invalid username or password."}), 401

    try:
        supabase.table("Posts").insert({
            "username": username,
            "header": header,
            "content": content
        }).execute()
        
        return jsonify({"success": True, "message": "Post created successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/posts/<username>', methods=['GET'])
def get_user_posts(username):
    try:
        response = supabase.table("Posts").select("*").eq("username", username).order("created_at", desc=True).execute()
        return jsonify({"success": True, "posts": response.data})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/posts/random', methods=['GET'])
def get_random_posts():
    try:
        response = supabase.table("Posts").select("*").execute()
        posts = response.data or []
        random_posts = random.sample(posts, min(3, len(posts)))
        return jsonify({"success": True, "posts": random_posts})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4982)