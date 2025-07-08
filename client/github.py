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