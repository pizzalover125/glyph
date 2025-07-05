import argparse
import json
import os
import sys
from datetime import datetime
import requests # type: ignore
from rich.console import Console # type: ignore
from rich.panel import Panel # type: ignore
from rich.table import Table # type: ignore
from rich.text import Text # type: ignore
from rich.box import ROUNDED # type: ignore

API_BASE_URL = "https://glyph-sh.pizzalover125.hackclub.app/api"

def api_request(method, endpoint, data=None):
    """Make API request to Glyph service"""
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
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Connection error: {str(e)}"}

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

def create_post(header, message):
    """Create a new post"""
    console = Console()

    local_user = load_user_locally()
    if not local_user:
        console.print("[bold red]❌ Error: You must be logged in to create posts![/bold red]")
        console.print("[dim]Please run the main Glyph application and log in first.[/dim]")
        return False
    
    user_data = authenticate_user(local_user['username'], local_user['password'])
    if not user_data:
        console.print("[bold red]❌ Error: Authentication failed![/bold red]")
        console.print("[dim]Please log in again using the main Glyph application.[/dim]")
        return False

    if not header.strip():
        console.print("[bold red]❌ Error: Header cannot be empty![/bold red]")
        return False
    
    if not message.strip():
        console.print("[bold red]❌ Error: Message cannot be empty![/bold red]")
        return False

    console.print("\n[bold cyan]📝 Post Preview:[/bold cyan]")
    preview_panel = Panel(
        f"[bold white]Author:[/bold white] {local_user['username']}\n"
        f"[bold white]Header:[/bold white] {header}\n"
        f"[bold white]Message:[/bold white]\n{message}",
        title="[bold cyan]New Post[/bold cyan]",
        border_style="cyan",
        box=ROUNDED,
        padding=(1, 2)
    )
    console.print(preview_panel)

    with console.status("[bold green]Creating post...", spinner="dots"):
        response = api_request("POST", "posts", {
            "username": local_user['username'],
            "password": local_user['password'],
            "header": header,
            "content": message
        })
    
    if response.get("success"):
        console.print("[bold green]✅ Post created successfully![/bold green]")
        return True
    else:
        error_msg = response.get('message', 'Unknown error')
        console.print(f"[bold red]❌ Failed to create post: {error_msg}[/bold red]")
        return False

def show_post_history():
    console = Console()
    
    local_user = load_user_locally()
    if not local_user:
        console.print("[bold red]❌ Error: You must be logged in to view post history![/bold red]")
        console.print("[dim]Please run the main Glyph application and log in first.[/dim]")
        return False
    
    user_data = authenticate_user(local_user['username'], local_user['password'])
    if not user_data:
        console.print("[bold red]❌ Error: Authentication failed![/bold red]")
        console.print("[dim]Please log in again using the main Glyph application.[/dim]")
        return False
    
    with console.status("[bold green]Fetching your posts...", spinner="dots"):
        response = api_request("GET", f"posts/{local_user['username']}")
    
    if not response.get("success"):
        console.print("[bold red]❌ Failed to fetch posts![/bold red]")
        return False
    
    posts = response.get("posts", [])
    
    if not posts:
        console.print(f"[bold yellow]📭 No posts found for @{local_user['username']}[/bold yellow]")
        console.print("[dim]Create your first post using: glyph-post --header \"Title\" --message \"Your message\"[/dim]")
        return True

    posts_per_page = 3
    current_page = 0
    total_posts = len(posts)
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    
    while True:
        console.clear()
        console.print(f"[bold cyan]📚 Post History for @{local_user['username']}[/bold cyan]")
        console.print(f"[dim]Page {current_page + 1} of {total_pages} • Total: {total_posts} post(s)[/dim]\n")
        
        start_idx = current_page * posts_per_page
        end_idx = min(start_idx + posts_per_page, total_posts)
        
        for i in range(start_idx, end_idx):
            post = posts[i]
            header = post.get("header", "Untitled")
            content = post.get("content", "")
            created_at = post.get("created_at", "")
            
            date_str = ""
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace(" ", "T").split("+")[0])
                    date_str = dt.strftime("%b %d, %Y at %H:%M UTC")
                except Exception:
                    date_str = created_at
            
            display_content = content
            if len(content) > 200:
                display_content = content[:200] + "..."
            
            post_panel = Panel(
                f"[bold white]#{i + 1}[/bold white] [bold cyan]{header}[/bold cyan]\n\n"
                f"{display_content}\n\n"
                f"[dim]📅 {date_str}[/dim]",
                border_style="cyan",
                box=ROUNDED,
                padding=(1, 2)
            )
            console.print(post_panel)
            console.print()
        
        options = []
        if current_page > 0:
            options.append("← Previous")
        if current_page < total_pages - 1:
            options.append("Next →")
        options.append("Exit")
        
        if len(options) == 1:  
            console.print("[dim]Press Enter to exit...[/dim]")
            input()
            break
        
        console.print("[bold yellow]Navigation:[/bold yellow]")
        for i, option in enumerate(options, 1):
            console.print(f"[dim]{i}.[/dim] {option}")
        
        try:
            choice = input("\nEnter choice (1-{}) or press Enter to exit: ".format(len(options)))
            
            if not choice.strip():
                break
            
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(options):
                continue
            
            selected_option = options[choice_idx]
            
            if selected_option == "← Previous":
                current_page -= 1
            elif selected_option == "Next →":
                current_page += 1
            elif selected_option == "Exit":
                break
                
        except (ValueError, KeyboardInterrupt):
            break
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Glyph Post CLI - Create and manage posts from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  glyph-post --header "My First Post" --message "Hello, Glyph!"
  glyph-post --history
  glyph-post -t "Quick Update" -m "Just finished coding!"
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--header", "-t",
        help="Header/title (required)"
    )
    group.add_argument(
        "--history",
        action="store_true",
        help="Show your post history"
    )
    
    parser.add_argument(
        "--message", "-m",
        help="Message content (required)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="glyph-post 1.1.0"
    )
    
    args = parser.parse_args()
    
    console = Console()

    if args.history:
        success = show_post_history()
        sys.exit(0 if success else 1)

    if args.header:
        if not args.message:
            console.print("[bold red]❌ Error: --message is required when creating a post![/bold red]")
            console.print("[dim]Use: glyph-post --header \"Title\" --message \"Your message\"[/dim]")
            sys.exit(1)
        
        success = create_post(args.header, args.message)
        sys.exit(0 if success else 1)
    
    parser.print_help()
    sys.exit(1)

if __name__ == "__main__":
    main()

