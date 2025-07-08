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
from utils import is_valid_username, is_valid_password
from utils import api_request

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