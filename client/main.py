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
from profile import create_social_links_panel, create_bio_panel, lookup_user, display_current_profile, edit_bio, edit_social_links, update_user_profile, edit_profile

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
