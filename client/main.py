import re
import os
import json
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
import requests # type: ignore

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

def get_github_username(social_links):
    github_url = social_links.get("Github")
    if not github_url:
        return None
    match = re.match(r"(?:https?://github\.com/)?([A-Za-z0-9-]+)", github_url)
    if match:
        return match.group(1)
    return None

def create_contribution_graph(contributions):
    today = datetime.now().date()
    start_date = today - timedelta(days=83)
    
    graph = Text()
    
    for week in range(12):
        for day in range(7):
            current_date = start_date + timedelta(days=week * 7 + day)
            if current_date > today:
                break
            
            count = contributions.get(current_date.isoformat(), 0)
            
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

def create_github_stats_panel(gh_info, contributions, total_stars):
    stats_table = Table(show_header=False, box=None, padding=(0, 1))
    stats_table.add_column("Metric", style="bold magenta", width=15)
    stats_table.add_column("Value", style="white", width=10)
    stats_table.add_row("📁 Repositories", f"{gh_info.get('public_repos', 0):,}")
    stats_table.add_row("👥 Followers", f"{gh_info.get('followers', 0):,}")
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
        title=f"[bold magenta]GitHub: {gh_info.get('login', 'Unknown')}[/bold magenta]",
        border_style="magenta",
        box=ROUNDED,
        padding=(1, 2)
    )

def create_social_links_panel(social_links):
    if not social_links:
        return Panel(
            "[italic dim]No social links available[/italic dim]",
            title="[bold magenta]Social Links[/bold magenta]",
            border_style="magenta",
            box=ROUNDED
        )
    social_table = Table(show_header=False, box=None, padding=(0, 1))
    social_table.add_column("Platform", style="bold magenta", width=12)
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
        title="[bold magenta]Social Links[/bold magenta]",
        border_style="magenta",
        box=ROUNDED,
        padding=(1, 2)
    )

def create_bio_panel(bio):
    bio_content = bio if bio and bio.strip() != "" else "[italic dim]No bio available[/italic dim]"
    return Panel(
        bio_content,
        title="[bold yellow]Biography[/bold yellow]",
        border_style="yellow",
        box=ROUNDED,
        padding=(1, 2)
    )

def lookup_user():
    console = Console()
    console.clear()
    header = Panel(
        Align.center("[bold magenta]Profile Lookup[/bold magenta]\n[dim]Enter a username to view their profile[/dim]"),
        box=ROUNDED,
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(header)
    console.print()
    username = Prompt.ask("[bold green]👤 Enter Username[/bold green]")
    console.print()
    
    with console.status("[bold green]Fetching user data...", spinner="dots"):
        response = api_request("GET", f"user/{username}")
    
    console.clear()
    
    if response.get("success"):
        user = response["user"]
        github_data = response.get("github_data")
        description = user.get("bio", "")
        social_links = user.get("social", {})
        
        user_header = Panel(
            Align.center(f"[bold white]Profile: {username}[/bold white]"),
            box=ROUNDED,
            border_style="magenta",
            padding=(1, 2)
        )
        console.print(user_header)
        console.print()
        
        bio_panel = create_bio_panel(description)
        social_panel = create_social_links_panel(social_links)
        top_panels = [bio_panel, social_panel]
        
        if github_data:
            gh_info = github_data["info"]
            contributions = github_data["contributions"]
            total_stars = github_data["total_stars"]
            github_panel = create_github_stats_panel(gh_info, contributions, total_stars)
            top_panels.append(github_panel)

        rendered_heights = []
        for panel in top_panels:
            temp_console = Console(width=console.width)
            with temp_console.capture() as capture:
                temp_console.print(panel)
            rendered_heights.append(len(capture.get().splitlines()))

        max_height = max(rendered_heights)
        padded_top_panels = [pad_panel_to_height(panel, max_height) for panel in top_panels]

        panel_width = int(console.width * 0.30)
        panel_padding = int(console.width * 0.03)

        top_row = Columns(
            padded_top_panels,
            expand=False,
            equal=False,
            padding=(0, panel_padding),
            width=panel_width
        )
        console.print(top_row)
        console.print()

        posts_response = api_request("GET", f"posts/{username}")
        if posts_response.get("success"):
            posts = posts_response["posts"]
            if posts:
                for post in posts:
                    post_header = post.get("header", "")
                    post_text = post.get("content", "")
                    created_at = post.get("created_at", "")

                    created_at_str = ""
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace(" ", "T").split("+")[0])
                            created_at_str = dt.strftime("%b %d, %Y at %H:%M UTC")
                        except Exception:
                            created_at_str = created_at
                        created_at_str = f"[dim]{created_at_str}[/dim]"
                    
                    if len(post_text) > 150:
                        post_text = post_text[:150] + "..."
                    panel_content = f"[bold cyan]{post_header}[/bold cyan]\n\n{post_text}"
                    if created_at_str:
                        panel_content += f"\n\n{created_at_str}"
                    post_panel = Panel(
                        panel_content,
                        border_style="cyan",
                        box=ROUNDED,
                        padding=(1, 2)
                    )
                    console.print(post_panel, width=console.width)
                    console.print()
            else:
                post_panel = Panel(
                    "[italic dim]No posts yet[/italic dim]",
                    border_style="cyan",
                    box=ROUNDED,
                    padding=(1, 2)
                )
                console.print(post_panel, width=console.width)
                console.print()
    else:
        error_panel = Panel(
            Align.center("[bold red]❌ User not found[/bold red]\n[dim]Please check the username and try again[/dim]"),
            border_style="red",
            box=ROUNDED,
            padding=(1, 2)
        )
        console.print(error_panel)

def authenticate_user(username, password):
    response = api_request("POST", "authenticate", {
        "username": username,
        "password": password
    })
    
    if response.get("success"):
        return response["user"]
    return None

def display_current_profile(user_data):
    console = Console()
    profile_panel = Panel(
        Align.center(f"[bold white]Current Profile: {user_data['username']}[/bold white]"),
        box=ROUNDED,
        border_style="magenta",
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

def update_user_profile(username, password, bio, social_links):
    response = api_request("PUT", f"user/{username}/update", {
        "password": password,
        "bio": bio,
        "social_links": social_links
    })
    return response.get("success", False)

def edit_profile():
    console = Console()
    console.clear()
    
    local_user = load_user_locally()
    
    if local_user:
        username = local_user["username"]
        password = local_user["password"]
        user_data = authenticate_user(username, password)
        if user_data:
            console.print(f"[green]✅ Welcome back, {username}![/green]")
        else:
            console.print("[red]❌ Local user data authentication failed![/red]")
            return
    else:
        header = Panel(
            Align.center(f"[bold white]Edit User Profile[/bold white]"),
            box=ROUNDED,
            border_style="magenta",
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
    console.print("[bold magenta]📋 Updated Profile Summary[/bold magenta]")
    console.print(f"👤 Username: {username}")
    console.print(f"📝 Bio:\n{new_bio}")
    if new_social_links:
        console.print("\n🔗 [bold]Social Links:[/bold]")
        for platform, link in new_social_links.items():
            console.print(f"• {platform}: {link}")
    else:
        console.print("\n🔗 [bold]Social Links:[/bold] None")
    
    if Confirm.ask("\n[bold yellow]Save these changes?[/bold yellow]"):
        if update_user_profile(username, password, new_bio, new_social_links):
            console.print("[green]✅ Profile updated successfully![/green]")
            save_user_locally(username, password, new_bio, new_social_links)
        else:
            console.print("[red]❌ Failed to update profile. Please try again.[/red]")
    else:
        console.print("[yellow]Changes discarded.[/yellow]")

def is_valid_username(username):
    return re.match(r"^[a-zA-Z0-9_]{3,20}$", username) is not None

def is_valid_password(password):
    return len(password) >= 8

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

def create_post():
    console = Console()
    console.clear()
    
    local_user = load_user_locally()
    
    if not local_user:
        console.print("[red]❌ You need to be logged in to create a post![/red]")
        return
    
    header_panel = Panel(
        Align.center(f"[bold white]Create New Post[/bold white]"),
        box=ROUNDED,
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(header_panel)
    
    post_header = Prompt.ask("[bold green]Enter a header for your post[/bold green]")
    console.print("\n[bold green]Write your post (press Enter twice to finish):[/bold green]")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    
    content = "\n".join(lines)
    
    if not post_header.strip():
        console.print("[yellow]Header cannot be empty![/yellow]")
        return

    if not content.strip():
        console.print("[yellow]Post cannot be empty![/yellow]")
        return
    
    console.print("\n" + "="*50)
    console.print("[bold magenta]📋 Post Preview[/bold magenta]")
    console.print(f"👤 Author: {local_user['username']}")
    console.print(f"[bold cyan]Header:[/bold cyan] {post_header}")
    console.print(f"📝 Content:\n{content}")
    
    if Confirm.ask("\n[bold yellow]Post this content?[/bold yellow]"):
        response = api_request("POST", "posts", {
            "username": local_user['username'],
            "password": local_user['password'],
            "header": post_header,
            "content": content
        })
        
        if response.get("success"):
            console.print("[green]✅ Post created successfully![/green]")
        else:
            console.print(f"[red]❌ Failed to create post: {response.get('message', 'Unknown error')}[/red]")
    else:
        console.print("[yellow]Post discarded.[/yellow]")

def view_random_posts():
    console = Console()
    page = 1
    per_page = 5 

    while True:
        console.clear()
        with console.status("[bold green]Fetching random posts...", spinner="dots"):
            response = api_request("GET", f"posts/random?page={page}&per_page={per_page}")

        if response.get("success"):
            posts = response["posts"]
            if posts:
                console.print(f"[bold green]📰 Showing random posts (Page {page})[/bold green]")
                console.print()
                
                for post in posts:
                    username = post.get("username", "Unknown")
                    post_header = post.get("header", "")
                    post_text = post.get("content", "")
                    created_at = post.get("created_at", "")

                    created_at_str = ""
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at.replace(" ", "T").split("+")[0])
                            created_at_str = dt.strftime("%b %d, %Y at %H:%M UTC")
                        except Exception:
                            created_at_str = created_at
                        created_at_str = f"[dim]{created_at_str}[/dim]"
                    
                    if len(post_text) > 200:
                        post_text = post_text[:200] + "..."
                    
                    panel_content = f"[bold yellow]@{username}[/bold yellow]\n"
                    panel_content += f"[bold cyan]{post_header}[/bold cyan]\n\n{post_text}"
                    if created_at_str:
                        panel_content += f"\n\n{created_at_str}"
                    
                    post_panel = Panel(
                        panel_content,
                        title=f"[bold white]{post_header}[/bold white]",
                        border_style="cyan",
                        box=ROUNDED,
                        padding=(1, 2)
                    )
                    console.print(post_panel, width=console.width)
                    console.print()
            else:
                no_posts_panel = Panel(
                    "[italic dim]No posts available yet[/italic dim]",
                    border_style="cyan",
                    box=ROUNDED,
                    padding=(1, 2)
                )
                console.print(no_posts_panel, width=console.width)
                console.print()
                break
        else:
            error_panel = Panel(
                Align.center("[bold red]❌ Failed to fetch posts[/bold red]\n[dim]Please try again later[/dim]"),
                border_style="red",
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(error_panel)
            break

        choices = ["View more posts", "Return to home"]
        action = questionary.select(
            "What would you like to do?",
            choices=choices
        ).ask()
        if action == "View more posts":
            page += 1
            continue
        else:
            break

def main():
    console = Console()
    console.clear()
    
    local_user = load_user_locally()
    
    if local_user:
        while True:
            header = Panel(
                Align.center(f"[bold magenta]Welcome back to Glyph, {local_user['username']}![/bold magenta]\n[dim]Choose an option to get started[/dim]"),
                box=ROUNDED,
                border_style="magenta",
                padding=(1, 2)
            )
            console.print(header)
            console.print()
            choices = [
                "👀 Lookup User Profile",
                "📰 View Random Posts",  
                "✏️ Edit My Profile",
                "📝 Create Post",  
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
            elif action == "📰 View Random Posts": 
                view_random_posts()
                input("\nPress [Enter] to return to the home page...")
                console.clear()
                continue
            elif action == "✏️ Edit My Profile":
                edit_profile()
                input("\nPress [Enter] to return to the home page...")
                console.clear()
                continue
            elif action == "📝 Create Post":  
                create_post()
                input("\nPress [Enter] to return to the home page...")
                console.clear()
                continue
            elif action == "🔓 Logout":
                logout_user()
                console.print("[bold magenta]You have been logged out![/bold magenta]")
                console.clear()
                main()
                break
            elif action == "🚪 Exit":
                console.clear()
                console.print("[bold magenta]Thanks for using...[/bold magenta]")
                console.print(
                    "[bold magenta]\n"
                    " ░▒▓██████▓▒░░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "░▒▓█▓▒░      ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "░▒▓█▓▒▒▓███▓▒░▒▓█▓▒░    ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓████████▓▒░ \n"
                    "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ \n"
                    " ░▒▓██████▓▒░░▒▓████████▓▒░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "[/bold magenta]\n"
                )
                console.print(
                    "[bold magenta]a terminal-based social media service.[/bold magenta]"
                )
                break
    else:
        while True:
            
            header = Panel(
                Align.center("[bold magenta]Glyph[/bold magenta]\n[dim]Choose an option to get started[/dim]"),
                box=ROUNDED,
                border_style="magenta",
                padding=(1, 2)
            )
            console.print(header)
            console.print()

            action = questionary.select(
                "What would you like to do?",
                choices=[
                    "👀 Lookup User Profile",
                    "📰 View Random Posts",  
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
            elif action == "📰 View Random Posts":  
                view_random_posts()
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
                console.clear()
                console.print("[bold magenta]Thanks for using...[/bold magenta]")
                console.print(
                    "[bold magenta]\n"
                    " ░▒▓██████▓▒░░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "░▒▓█▓▒░      ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "░▒▓█▓▒▒▓███▓▒░▒▓█▓▒░    ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓████████▓▒░ \n"
                    "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ \n"
                    " ░▒▓██████▓▒░░▒▓████████▓▒░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ \n"
                    "[/bold magenta]\n"
                )
                break
if __name__ == "__main__":
    main()