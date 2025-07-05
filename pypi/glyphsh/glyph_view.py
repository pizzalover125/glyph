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
import requests # type: ignore

API_BASE_URL = "https://glyph-sh.pizzalover125.hackclub.app/api"

class GlyphViewCLI:
    def __init__(self):
        self.console = Console()
    
    def api_request(self, method, endpoint, data=None):
        url = f"{API_BASE_URL}/{endpoint}"
        headers = {"Content-Type": "application/json"}

        if method not in ["GET", "POST", "PUT"]:
            return {"success": False, "message": "Invalid HTTP method"}

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Connection error: {str(e)}"}
    
    def get_github_username(self, social_links):
        github_url = social_links.get("Github")
        if not github_url:
            return None
        match = re.match(r"(?:https?://github\.com/)?([A-Za-z0-9-]+)", github_url)
        if match:
            return match.group(1)
        return None
    
    def create_contribution_graph(self, contributions):
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
    
    def create_github_stats_panel(self, gh_info, contributions, total_stars):
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
        
        contrib_graph = self.create_contribution_graph(contributions)
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
    
    def create_social_links_panel(self, social_links):
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
    
    def create_bio_panel(self, bio):
        bio_content = bio if bio and bio.strip() != "" else "[italic dim]No bio available[/italic dim]"
        return Panel(
            bio_content,
            title="[bold yellow]Biography[/bold yellow]",
            border_style="yellow",
            box=ROUNDED,
            padding=(1, 2)
        )
    
    def create_posts_panel(self, posts):
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
    
    def display_user_profile(self, username):
        self.console.print(f"\n[bold green]Fetching profile for @{username}...[/bold green]")
        
        response = self.api_request("GET", f"user/{username}")
        
        if not response.get("success"):
            self.console.print(f"[bold red]❌ Error: {response.get('message', 'User not found')}[/bold red]")
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
        self.console.print(user_header)
        
        bio_panel = self.create_bio_panel(description)
        social_panel = self.create_social_links_panel(social_links)
        panels = [bio_panel, social_panel]
        
        if github_data:
            gh_info = github_data["info"]
            contributions = github_data["contributions"]
            total_stars = github_data["total_stars"]
            github_panel = self.create_github_stats_panel(gh_info, contributions, total_stars)
            panels.append(github_panel)
        
        if len(panels) > 1:
            columns = Columns(panels, expand=True, padding=(0, 1))
            self.console.print(columns)
        else:
            self.console.print(panels[0])
        
        posts_response = self.api_request("GET", f"posts/{username}")
        if posts_response.get("success"):
            posts = posts_response["posts"]
            posts_panel = self.create_posts_panel(posts)
            self.console.print(posts_panel)
        
        return True
    
    def run(self):
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
            self.console.print("[bold red]❌ Username cannot be empty[/bold red]")
            return
        
        if username.startswith("@"):
            username = username[1:]
        
        if args.json:
            response = self.api_request("GET", f"user/{username}")
            print(json.dumps(response, indent=2))
        else:
            success = self.display_user_profile(username)
            if not success:
                sys.exit(1)

def main():
    cli = GlyphViewCLI()
    cli.run()

if __name__ == "__main__":
    main()
