import random
import string
import time
import requests

API_BASE_URL = "https://glyph.pizzalover125.hackclub.app/api"

def random_username():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=12))

def random_bio():
    bios = [
        "Just another coder.",
        "Exploring the terminal world.",
        "Coffee-powered keyboard warrior.",
        "Trying to make sense of bits and bytes.",
        "A lover of minimal UIs."
    ]
    return random.choice(bios)

def random_post_header():
    headers = [
        "My thoughts on coding...",
        "Terminal hacks you should know",
        "Building my CLI dream",
        "Today's devlog entry",
        "Some command line magic"
    ]
    return random.choice(headers)

def random_post_content():
    sentences = [
        "Today I learned about subprocess in Python.",
        "Loving the simplicity of the terminal interface.",
        "Trying out new CLI tools is addictive.",
        "Glyph is turning out to be a really cool platform.",
        "I spent the whole night fixing one bug..."
    ]
    return "\n".join(random.sample(sentences, k=3))

def api_request(method, endpoint, data=None):
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "GET":
            response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error contacting API: {e}")
        return None

users = []

# Create 100 accounts
for i in range(100):
    username = random_username()
    password = random_password()
    bio = random_bio()
    social_links = {
        "Github": f"https://github.com/{username}"
    }
    user_data = {
        "username": username,
        "password": password,
        "bio": bio,
        "social_links": social_links
    }
    response = api_request("POST", "signup", user_data)
    if response and response.get("success"):
        print(f"[{i+1}/100] Created account: {username}")
        users.append({"username": username, "password": password})
    else:
        print(f"[{i+1}/100] Failed to create: {username}")

# Create 200 posts (randomly assigned to users)
for i in range(200):
    user = random.choice(users)
    post_data = {
        "username": user["username"],
        "password": user["password"],
        "header": random_post_header(),
        "content": random_post_content()
    }
    response = api_request("POST", "posts", post_data)
    if response and response.get("success"):
        print(f"[{i+1}/200] Created post by: {user['username']}")
    else:
        print(f"[{i+1}/200] Failed to post for: {user['username']}")

print("✅ Finished generating test accounts and posts.")
