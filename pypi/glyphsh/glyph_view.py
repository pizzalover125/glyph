import re
import sys
import argparse
import json
from rich.console import Console # type: ignore
from rich.panel import Panel # type: ignore
from rich.table import Table # type: ignore
from rich.columns import Columns # type: ignore 
from rich.text import Text # type: ignore
from rich.align import Align # type: ignore
from rich.box import ROUNDED # type: ignore
from rich.console import Group # type: ignore
from datetime import datetime, timedelta
from utils import api_request
from github import get_github_username, create_contribution_graph, create_github_stats_panel
from profile import create_social_links_panel, create_bio_panel

console = Console()

def create_posts_panel(posts):
    """Create a panel displaying recent posts."""
    if not posts:
        return Panel(
            "[italic dim]No posts yet[/italic dim]",
            title="[bold cyan]Recent Posts[/bold cyan]",
            border_style="cyan",
            box=ROUNDED,
            padding=(1, 2)
        )
    
    posts_content = []
    for i, post in enumerate(posts[:3]): 
        post_header = post.get("header", "")
        post_text = post.get("content", "")
        created_at = post.get("created_at", "")
        
        created_at_str = ""
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at.replace(" ", "T").split("+")[0])
                created_at_str = dt.strftime("%b %d, %Y")
            except Exception:
                created_at_str = created_at

        if len(post_text) > 100:
            post_text = post_text[:100] + "..."
        
        post_content = f"[bold]{post_header}[/bold]\n{post_text}"
        if created_at_str:
            post_content += f"\n[dim italic]{created_at_str}[/dim italic]"
        
        posts_content.append(post_content)
        
        if i < min(len(posts), 3) - 1:
            posts_content.append("─" * 40)
    
    return Panel(
        "\n".join(posts_content),
        title="[bold cyan]Recent Posts[/bold cyan]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2)
    )

def display_user_profile(username):
    """Display a complete user profile with all panels."""
    console.print(f"\n[bold green]Fetching profile for @{username}...[/bold green]")
    
    response = api_request("GET", f"user/{username}")
    
    if not response.get("success"):
        console.print(f"[bold red]❌ Error: {response.get('message', 'User not found')}[/bold red]")
        return False
    
    user = response["user"]
    github_data = response.get("github_data")
    description = user.get("bio", "")
    social_links = user.get("social", {})
    
    user_header = Panel(
        Align.center(f"[bold white]@{username}[/bold white]"),
        box=ROUNDED,
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(user_header)
    
    bio_panel = create_bio_panel(description)
    social_panel = create_social_links_panel(social_links)
    panels = [bio_panel, social_panel]
    
    if github_data:
        gh_info = github_data["info"]
        contributions = github_data["contributions"]
        total_stars = github_data["total_stars"]
        github_panel = create_github_stats_panel(gh_info, contributions, total_stars)
        panels.append(github_panel)
    
    if len(panels) > 1:
        columns = Columns(panels, expand=True, padding=(0, 1))
        console.print(columns)
    else:
        console.print(panels[0])
    
    posts_response = api_request("GET", f"posts/{username}")
    if posts_response.get("success"):
        posts = posts_response["posts"]
        posts_panel = create_posts_panel(posts)
        console.print(posts_panel)
    
    return True

def main():
    """Main function to handle command line arguments and execute the profile viewer."""
    parser = argparse.ArgumentParser(
        description="View user profiles on Glyph",
        prog="glyph-view"
    )
    parser.add_argument(
        "--username", "-u",
        required=True,
        help="Username to view profile for"
    )
    parser.add_argument(
        "--compact", "-c",
        action="store_true",
        help="Display in compact mode"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON data"
    )
    
    try:
        args = parser.parse_args()
    except SystemExit:
        return
    
    username = args.username.strip()
    
    if not username:
        console.print("[bold red]❌ Username cannot be empty[/bold red]")
        return
    
    if username.startswith("@"):
        username = username[1:]
    
    if args.json:
        response = api_request("GET", f"user/{username}")
        print(json.dumps(response, indent=2))
    else:
        success = display_user_profile(username)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()