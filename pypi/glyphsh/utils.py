import re
import requests # type: ignore
from rich.console import Console # type: ignore
from rich.panel import Panel # type: ignore
from rich.align import Align # type: ignore

def is_valid_username(username):
    return re.match(r"^[a-zA-Z0-9_]{3,20}$", username) is not None

def is_valid_password(password):
    return len(password) >= 8

API_BASE_URL = "https://glyph-sh.pizzalover125.hackclub.app/api"

def api_request(method, endpoint, data=None):
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        
        return response.json()
    except requests.exceptions.RequestException:
        return {"success": False, "message": "Connection error"}
    
def pad_panel_to_height(panel, height):
    rendered = Console().render_str(str(panel))
    lines = str(panel).splitlines()
    current_height = len(lines)
    missing_lines = height - current_height
    content = Align.center(panel.renderable, vertical="top", height=height)
    return Panel(
        content,
        title=panel.title,
        border_style=panel.border_style,
        box=panel.box,
        padding=panel.padding
    )