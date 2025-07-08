import os
from rich.console import Console # type: ignore
from rich.prompt import Prompt, Confirm # type: ignore
from datetime import datetime, timedelta
from rich.panel import Panel # type: ignore
from rich.table import Table # type: ignore
from rich.columns import Columns # type: ignore
from rich.text import Text # type: ignore
from rich.layout import Layout # type: ignore
from rich.align import Align # type: ignore
from rich.progress import Progress, SpinnerColumn, TextColumn # type: ignore
from rich.box import ROUNDED # type: ignore
from rich.console import Group # type: ignore
import questionary # type: ignore
from utils import is_valid_username, is_valid_password, api_request
import json

def save_user_locally(username, password, bio, social_links):
    home_dir = os.path.expanduser("~")
    glyph_dir = os.path.join(home_dir, "glyph")
    os.makedirs(glyph_dir, exist_ok=True)

    data = {
        "username": username,
        "password": password,
        "bio": bio,
        "social_links": social_links,
        "logged_in": True
    }

    file_path = os.path.join(glyph_dir, "user_data.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_user_locally():
    home_dir = os.path.expanduser("~")
    glyph_dir = os.path.join(home_dir, "glyph")
    file_path = os.path.join(glyph_dir, "user_data.json")
    
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            if data.get("logged_in", False):
                return data
        except Exception:
            pass
    return None

def authenticate_user(username, password):
    response = api_request("POST", "authenticate", {
        "username": username,
        "password": password
    })
    
    if response.get("success"):
        return response["user"]
    return None


def logout_user():
    home_dir = os.path.expanduser("~")
    glyph_dir = os.path.join(home_dir, "glyph")
    file_path = os.path.join(glyph_dir, "user_data.json")
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

def login_user():
    console = Console()
    console.clear()
    header = Panel(
        Align.center(f"[bold white]Login[/bold white]"),
        box=ROUNDED,
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(header)
    
    username = Prompt.ask("[bold green]👤 Username[/bold green]")
    password = Prompt.ask("[bold green]🔒 Password[/bold green]")
    
    user_data = authenticate_user(username, password)
    if not user_data:
        console.print("[red]❌ Invalid username or password![/red]")
        return None
    
    console.print(f"[green]✅ Welcome back, {username}![/green]")
    
    save_user_locally(username, password, user_data.get('bio', ''), user_data.get('social', {}))
    
    return user_data

def sign_up():
    console = Console()
    console.clear()
    user_header = Panel(
        Align.center(f"[bold white]Sign Up:[/bold white]"),
        box=ROUNDED,
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(user_header)

    while True:
        username = Prompt.ask("[bold green]👤 Username[/bold green]")
        if not is_valid_username(username):
            console.print("[red]Username must be 3-20 characters, only letters, numbers, and underscores.[/red]")
            continue
        break

    while True:
        password = Prompt.ask("[bold green]🔒 Password[/bold green]")
        if not is_valid_password(password):
            console.print("[red]Password must be at least 8 characters long.[/red]")
            continue
        break

    selected_platforms = questionary.checkbox(
        "Which links would you like to share? <space> to select, <enter> to confirm, arrow keys to navigate",
        choices=[
            "Github",
            "Linkedin",
            "Personal Website",
            "Email",
            "YouTube"
        ]
    ).ask()

    social_links = {}

    if "Github" in selected_platforms:
        github = Prompt.ask("[bold blue]Github Username[/bold blue]", default=username)
        social_links["Github"] = f"https://github.com/{github}"

    if "Personal Website" in selected_platforms:
        website = Prompt.ask("[bold blue]Personal Website URL[/bold blue]")
        social_links["Website"] = website

    if "Linkedin" in selected_platforms:
        linkedin = Prompt.ask("[bold blue]Linkedin URL[/bold blue]")
        social_links["Linkedin"] = linkedin

    if "Email" in selected_platforms:
        email = Prompt.ask("[bold blue]Email Address[/bold blue]")
        social_links["Email"] = email

    if "YouTube" in selected_platforms:
        youtube = Prompt.ask("[bold blue]YouTube Channel URL[/bold blue]")
        social_links["YouTube"] = youtube

    console.print("\n[bold green]Tell us about yourself (press Enter twice to finish):[/bold green]")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    description = "\n".join(lines)

    console.print("\n[bold magenta]Summary[/bold magenta]")
    console.print(f"👤 Username: {username}")
    console.print(f"📝 Bio:\n{description}")
    if social_links:
        console.print("\n🔗 [bold]Social Links:[/bold]")
        for platform, link in social_links.items():
            console.print(f"• {platform}: {link}")

    response = api_request("POST", "signup", {
        "username": username,
        "password": password,
        "bio": description,
        "social_links": social_links
    })

    if response.get("success"):
        save_user_locally(username, password, description, social_links)
        console.print("[green]✅ Account created and logged in successfully![/green]")
    else:
        console.print(f"[red]❌ Signup failed: {response.get('message', 'Unknown error')}[/red]")
