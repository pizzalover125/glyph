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
from github import create_github_stats_panel
from utils import is_valid_username, is_valid_password, pad_panel_to_height, api_request
from posts import create_post, view_random_posts
from auth import logout_user, login_user, sign_up, authenticate_user, save_user_locally, load_user_locally

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