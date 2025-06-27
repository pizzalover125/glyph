# imports
from dotenv import load_dotenv # type: ignore
import re
import os
import json
from rich.console import Console # type: ignore
from rich.prompt import Prompt, Confirm # type: ignore
from supabase import create_client # type: ignore
from datetime import datetime, timedelta # type: ignore
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
import requests # type: ignore

# supabase
load_dotenv() 

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# github helper functions
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
                contributions[date] = contributions.get(date, 0) + 1
        
        return contributions
    except Exception:
        return {}

def create_contribution_graph(contributions):
    today = datetime.now().date()
    start_date = today - timedelta(days=83)
    
    graph = Text()
    
    for week in range(12):
        for day in range(7):
            current_date = start_date + timedelta(days=week * 7 + day)
            if current_date > today:
                break
            
            count = contributions.get(current_date, 0)
            
            if count == 0:
                color = "dim white"
                char = "⬜"
            elif count <= 2:
                color = "green"
                char = "🟩"
            elif count <= 5:
                color = "bright_green"
                char = "🟩"
            else:
                color = "bright_green"
                char = "🟦"
            
            graph.append(char, style=color)
        
        if week < 11:
            graph.append("\n")
    
    return graph

# panel height padding adjustment helper function
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

# github panel creation 
def create_github_stats_panel(gh_info, contributions):
    stats_table = Table(show_header=False, box=None, padding=(0, 1))
    stats_table.add_column("Metric", style="bold cyan", width=15)
    stats_table.add_column("Value", style="white", width=10)
    stats_table.add_row("📁 Repositories", f"{gh_info.get('public_repos', 0):,}")
    stats_table.add_row("👥 Followers", f"{gh_info.get('followers', 0):,}")

    total_stars = 0
    username = gh_info.get("login")
    if username:
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
            total_stars = stars
        except Exception:
            total_stars = "?"
    stats_table.add_row("⭐ Total Stars", f"{total_stars:,}" if isinstance(total_stars, int) else total_stars)
    location = gh_info.get("location", "Not specified")
    stats_table.add_row("📍 Location", location)
    created_at = gh_info.get("created_at")
    if created_at:
        date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        formatted_date = date_obj.strftime("%B %Y")
        stats_table.add_row("📅 Member since", formatted_date)
    
    contrib_graph = create_contribution_graph(contributions)
    stats_table.add_row("", "")
    stats_table.add_row("📊 Recent Activity", "")
    
    content = Group(stats_table, contrib_graph)
    
    return Panel(
        content,
        title=f"[bold green]GitHub: {gh_info.get('login', 'Unknown')}[/bold green]",
        border_style="green",
        box=ROUNDED,
        padding=(1, 2)
    )

# social panel creation 
def create_social_links_panel(social_links):
    if not social_links:
        return Panel(
            "[italic dim]No social links available[/italic dim]",
            title="[bold blue]Social Links[/bold blue]",
            border_style="blue",
            box=ROUNDED
        )
    social_table = Table(show_header=False, box=None, padding=(0, 1))
    social_table.add_column("Platform", style="bold blue", width=12)
    social_table.add_column("Link", style="dim", overflow="fold")
    platform_icons = {
        "Github": "🐙",
        "Linkedin": "💼",
        "Website": "🌐",
        "Email": "📧",
        "YouTube": "📺",
    }
    for platform, link in social_links.items():
        icon = platform_icons.get(platform, "🔗")
        social_table.add_row(f"{icon} {platform}", link)
    return Panel(
        social_table,
        title="[bold blue]Social Links[/bold blue]",
        border_style="blue",
        box=ROUNDED,
        padding=(1, 2)
    )

# bio panel creation 
def create_bio_panel(bio):
    bio_content = bio if bio and bio.strip() != "" else "[italic dim]No bio available[/italic dim]"
    return Panel(
        bio_content,
        title="[bold yellow]Biography[/bold yellow]",
        border_style="yellow",
        box=ROUNDED,
        padding=(1, 2)
    )

# user lookup function
def lookup_user():
    console = Console()
    console.clear()
    header = Panel(
        Align.center("[bold cyan]Profile Lookup[/bold cyan]\n[dim]Enter a username to view their profile[/dim]"),
        box=ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(header)
    console.print()
    username = Prompt.ask("[bold green]👤 Enter Username[/bold green]")
    console.print()
    with console.status("[bold green]Fetching user data...", spinner="dots"):
        response = supabase.table("Users").select("*").eq("username", username).execute()
        user_data = response.data
    console.clear()
    if user_data and len(user_data) > 0:
        user = user_data[0]
        description = user.get("bio", "")
        social_links = user.get("social", {})
        user_header = Panel(
            Align.center(f"[bold white]Profile: {username}[/bold white]"),
            box=ROUNDED,
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(user_header)
        console.print()
        bio_panel = create_bio_panel(description)
        social_panel = create_social_links_panel(social_links)
        panels = [bio_panel, social_panel]
        github_username = get_github_username(social_links)
        if github_username:
            with console.status("[bold green]Fetching GitHub data...", spinner="dots"):
                gh_info = fetch_github_info(github_username)
                contributions = fetch_github_contributions(github_username)
            if gh_info:
                github_panel = create_github_stats_panel(gh_info, contributions)
                panels.append(github_panel)
            else:
                error_panel = Panel(
                    "[yellow]⚠️ Could not fetch GitHub information[/yellow]",
                    title="[bold red]GitHub Error[/bold red]",
                    border_style="red",
                    box=ROUNDED
                )
                panels.append(error_panel)

        rendered_heights = []
        for panel in panels:
            temp_console = Console(width=console.width)
            with temp_console.capture() as capture:
                temp_console.print(panel)
            rendered_heights.append(len(capture.get().splitlines()))

        max_height = max(rendered_heights)
        padded_panels = [pad_panel_to_height(panel, max_height) for panel in panels]

        panel_width = int(console.width * 0.30)
        panel_padding = int(console.width * 0.03)

        rows = [
            Columns(
                padded_panels[i:i+3],
                expand=False,
                equal=False,
                padding=(0, panel_padding),
                width=panel_width
            )
            for i in range(0, len(padded_panels), 3)
        ]

        console.print(Group(*rows))
        console.print()
    else:
        error_panel = Panel(
            Align.center("[bold red]❌ User not found[/bold red]\n[dim]Please check the username and try again[/dim]"),
            border_style="red",
            box=ROUNDED,
            padding=(1, 2)
        )
        console.print(error_panel)

# user auth setup
def authenticate_user(username, password):
    response = supabase.table("Users").select("*").eq("username", username).eq("password", password).execute()
    if len(response.data) == 0:
        return None
    return response.data[0]

# current profile display
def display_current_profile(user_data):
    console = Console()
    profile_panel = Panel(
        Align.center(f"[bold white]Current Profile: {user_data['username']}[/bold white]"),
        box=ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(profile_panel)
    console.print(f"\n[bold green]📝 Current Bio:[/bold green]")
    console.print(f"{user_data.get('bio', 'No bio set')}")
    if user_data.get('social'):
        console.print(f"\n[bold green]🔗 Current Social Links:[/bold green]")
        for platform, link in user_data['social'].items():
            console.print(f"• {platform}: {link}")
    else:
        console.print(f"\n[bold green]🔗 Social Links:[/bold green] None set")

# edit bio display
def edit_bio(current_bio):
    console = Console()
    if Confirm.ask("\nWould you like to edit your bio?"):
        console.print("\n[bold green]Enter your new bio (press Enter twice to finish):[/bold green]")
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        new_bio = "\n".join(lines)
        return new_bio if new_bio.strip() else current_bio
    return current_bio

# edit social display (FIX IF ELIF AND CONVERT TO FOR LOOP)
def edit_social_links(current_social):
    console = Console()
    social_links = current_social.copy() if current_social else {}

    if not Confirm.ask("\nWould you like to edit your social links?"):
        return social_links
    while True:
        choices = ["Add/Update Github", "Add/Update LinkedIn", "Add/Update Personal Website", 
                  "Add/Update Email", "Add/Update YouTube", "Remove a link", "Finish editing"]
        action = questionary.select(
            "What would you like to do?",
            choices=choices
        ).ask()
        if action == "Finish editing":
            break
        elif action == "Remove a link":
            if not social_links:
                console.print("[yellow]No links to remove![/yellow]")
                continue
            link_to_remove = questionary.select(
                "Which link would you like to remove?",
                choices=list(social_links.keys()) + ["Cancel"]
            ).ask()
            if link_to_remove != "Cancel":
                del social_links[link_to_remove]
                console.print(f"[green]Removed {link_to_remove} link[/green]")
        elif action == "Add/Update Github":
            github = Prompt.ask("[bold blue]Github Username[/bold blue]", 
                              default=social_links.get("Github", "").replace("https://github.com/", "") if "Github" in social_links else "")
            if github.strip():
                social_links["Github"] = f"https://github.com/{github}"
        elif action == "Add/Update Personal Website":
            website = Prompt.ask("[bold blue]Personal Website URL[/bold blue]", 
                               default=social_links.get("Website", ""))
            if website.strip():
                social_links["Website"] = website
        elif action == "Add/Update LinkedIn":
            linkedin = Prompt.ask("[bold blue]LinkedIn URL[/bold blue]", 
                                default=social_links.get("Linkedin", ""))
            if linkedin.strip():
                social_links["Linkedin"] = linkedin
        elif action == "Add/Update Email":
            email = Prompt.ask("[bold blue]Email Address[/bold blue]", 
                             default=social_links.get("Email", ""))
            if email.strip():
                social_links["Email"] = email
        elif action == "Add/Update YouTube":
            youtube = Prompt.ask("[bold blue]YouTube Channel URL[/bold blue]", 
                               default=social_links.get("YouTube", ""))
            if youtube.strip():
                social_links["YouTube"] = youtube
    return social_links

# update user profile helper function 
def update_user_profile(username, bio, social_links):
    try:
        supabase.table("Users").update({
            "bio": bio,
            "social": social_links
        }).eq("username", username).execute()
        return True
    except Exception as e:
        print(f"Error updating profile: {e}")
        return False

# edit user profile display
def edit_profile():
    console = Console()
    console.clear()
    
    local_user = load_user_locally()
    
    if local_user:
        username = local_user["username"]
        response = supabase.table("Users").select("*").eq("username", username).execute()
        if response.data:
            user_data = response.data[0]
            console.print(f"[green]✅ Welcome back, {username}![/green]")
        else:
            console.print("[red]❌ Local user data not found in database![/red]")
            return
    else:
        header = Panel(
            Align.center(f"[bold white]Edit User Profile[/bold white]"),
            box=ROUNDED,
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(header)
        console.print("\n[bold yellow]Please login to edit your profile[/bold yellow]")
        username = Prompt.ask("[bold green]👤 Username[/bold green]")
        password = Prompt.ask("[bold green]🔒 Password[/bold green]")
        user_data = authenticate_user(username, password)
        if not user_data:
            console.print("[red]❌ Invalid username or password![/red]")
            return
        console.print(f"[green]✅ Welcome back, {username}![/green]")
        save_user_locally(username, password, user_data.get('bio', ''), user_data.get('social', {}))
    
    display_current_profile(user_data)
    new_bio = edit_bio(user_data.get('bio', ''))
    new_social_links = edit_social_links(user_data.get('social', {}))
    console.print("\n" + "="*50)
    console.print("[bold cyan]📋 Updated Profile Summary[/bold cyan]")
    console.print(f"👤 Username: {username}")
    console.print(f"📝 Bio:\n{new_bio}")
    if new_social_links:
        console.print("\n🔗 [bold]Social Links:[/bold]")
        for platform, link in new_social_links.items():
            console.print(f"• {platform}: {link}")
    else:
        console.print("\n🔗 [bold]Social Links:[/bold] None")
    if Confirm.ask("\n[bold yellow]Save these changes?[/bold yellow]"):
        if update_user_profile(username, new_bio, new_social_links):
            console.print("[green]✅ Profile updated successfully![/green]")
            save_user_locally(username, local_user["password"] if local_user else "", new_bio, new_social_links)
        else:
            console.print("[red]❌ Failed to update profile. Please try again.[/red]")
    else:
        console.print("[yellow]Changes discarded.[/yellow]")

# validate username and password
def is_valid_username(username):
    return re.match(r"^[a-zA-Z0-9_]{3,20}$", username) is not None

def is_unique_username(username):
    response = supabase.table("Users").select("username").eq("username", username).execute()
    return len(response.data) == 0

def is_valid_password(password):
    return len(password) >= 8

# save user data locally to Glyph folder (ENCRYPT THIS LATER)
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

# load user data locally from Glyph folder
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

# logout and delete local user data
def logout_user():
    home_dir = os.path.expanduser("~")
    glyph_dir = os.path.join(home_dir, "glyph")
    file_path = os.path.join(glyph_dir, "user_data.json")
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

# login user display + function
def login_user():
    console = Console()
    console.clear()
    header = Panel(
        Align.center(f"[bold white]Login[/bold white]"),
        box=ROUNDED,
        border_style="cyan",
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


# signup user display + function (FIX IF ELIF AND CONVERT TO FOR LOOP)
def sign_up():
    console = Console()
    console.clear()
    user_header = Panel(
        Align.center(f"[bold white]Sign Up:[/bold white]"),
        box=ROUNDED,
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(user_header)

    while True:
        username = Prompt.ask("[bold green]👤 Username[/bold green]")
        if not is_valid_username(username):
            console.print("[red]Username must be 3-20 characters, only letters, numbers, and underscores.[/red]")
            continue
        if not is_unique_username(username):
            console.print("[red]Username already taken. Please choose another.[/red]")
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

    console.print("\n[bold cyan]Summary[/bold cyan]")
    console.print(f"👤 Username: {username}")
    console.print(f"📝 Bio:\n{description}")
    if social_links:
        console.print("\n🔗 [bold]Social Links:[/bold]")
        for platform, link in social_links.items():
            console.print(f"• {platform}: {link}")

    supabase.table("Users").insert({
        "username": username,
        "password": password,  
        "social": social_links,
        "bio": description
    }).execute()

    save_user_locally(username, password, description, social_links)
    console.print("[green]✅ Account created and logged in successfully![/green]")


# main function to run the application
def main():
    console = Console()
    console.clear()
    
    local_user = load_user_locally()
    
    if local_user:
        while True:
            header = Panel(
                Align.center(f"[bold cyan]Welcome back to Glyph, {local_user['username']}![/bold cyan]\n[dim]Choose an option to get started[/dim]"),
                box=ROUNDED,
                border_style="cyan",
                padding=(1, 2)
            )
            console.print(header)
            console.print()
            choices = [
                "👀 Lookup User Profile",
                "✏️ Edit My Profile",
                "🔓 Logout",
                "🚪 Exit"
            ]
            
            action = questionary.select(
                "What would you like to do?",
                choices=choices
            ).ask()
            
            if action == "👀 Lookup User Profile":
                lookup_user()
                input("\nPress [Enter] to return to the home page...")
                console.clear()
                continue
            elif action == "✏️ Edit My Profile":
                edit_profile()
                input("\nPress [Enter] to return to the home page...")
                console.clear()
                continue
            elif action == "🔓 Logout":
                logout_user()
                console.print("[bold cyan]You have been logged out![/bold cyan]")
                console.clear()
                main()
                break
            elif action == "🚪 Exit":
                console.print("[bold cyan]Thanks for using Glyph![/bold cyan]")
                break
    else:
        while True:
            header = Panel(
                Align.center("[bold cyan]Glyph[/bold cyan]\n[dim]Choose an option to get started[/dim]"),
                box=ROUNDED,
                border_style="cyan",
                padding=(1, 2)
            )
            console.print(header)
            console.print()

            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "👀 Lookup User Profile",
                    "🔑 Login",
                    "📝 Sign Up",
                    "🚪 Exit"
                ]
            ).ask()
            
            if action == "👀 Lookup User Profile":
                lookup_user()
                input("\nPress [Enter] to return to the home page...")
                console.clear()
                continue
            elif action == "🔑 Login":
                user_data = login_user()
                if user_data:
                    input("\nPress [Enter] to return to the home page...")
                    console.clear()
                    main()
                    break
                else:
                    input("\nPress [Enter] to return to the home page...")
                    console.clear()
                    continue
            elif action == "📝 Sign Up":
                sign_up()
                input("\nPress [Enter] to return to the home page...")
                console.clear()
                main()
                break
            elif action == "🚪 Exit":
                console.print("[bold cyan]Thanks for using Glyph![/bold cyan]")
                break

if __name__ == "__main__":
    main()