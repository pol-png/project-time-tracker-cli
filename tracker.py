import argparse
import os
import sqlite3
import time
from datetime import datetime, timedelta

# Rich UI imports
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn

DB_PATH = os.path.expanduser("~/.time_tracker.db")
console = Console()

# Nerd Font Icons (Requires a Nerd Font installed in your terminal)
ICON_CLOCK = "\uf017"     # Clock
ICON_PROJECT = "\uf413"   # Folder
ICON_TASK = "\uf0ae"      # Tasks
ICON_CALENDAR = "\uf073"  # Calendar
ICON_STOP = "\uf04d"      # Stop
ICON_LIST = "\uf03a"      # List
ICON_CHECK = "\uf00c"      # Check
ICON_X = "\uf00d"          # X/Error
ICON_SWAP = "\uf362"   # 
ICON_TRASH = "\uf1f8"  # 

# --- Database Setup ---

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS projects
                        (id INTEGER PRIMARY KEY, name TEXT UNIQUE, root_path TEXT)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS logs
                        (id INTEGER PRIMARY KEY, project_id INTEGER, task_name TEXT,
                         start_time TIMESTAMP, end_time TIMESTAMP)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS config
                        (key TEXT PRIMARY KEY, value TEXT)""")

def get_config(key):
    with sqlite3.connect(DB_PATH) as conn:
        res = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        return res[0] if res else None

def set_config(key, value):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))

def format_delta(delta):
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# --- CLI Actions ---

def project_add(name):
    path = os.getcwd()
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("INSERT INTO projects (name, root_path) VALUES (?, ?)", (name, path))
        console.print(f"[bold green]{ICON_CHECK} Project '{name}' created at:[/bold green] {path}")
        set_config("active_project", name)
    except sqlite3.IntegrityError:
        console.print(f"[bold yellow]{ICON_LIST} Project '{name}' already exists. Switching context.[/bold yellow]")
        set_config("active_project", name)

def project_switch(name):
    with sqlite3.connect(DB_PATH) as conn:
        project = conn.execute("SELECT name FROM projects WHERE name = ?", (name,)).fetchone()

    if project:
        set_config("active_project", name)
        console.print(f"[bold green]{ICON_SWAP} Switched context to:[/bold green] {name}")
    else:
        console.print(f"[bold red]{ICON_X} Project '{name}' not found. Use 'list' to see options.[/bold red]")

def project_delete(name):
    # Security check: Don't delete the active project without warning
    active = get_config("active_project")

    confirm = console.input(f"[bold red]!! WARNING !![/bold red] Delete project '{name}' and ALL logs? (y/n): ")
    if confirm.lower() != 'y':
        console.print("[dim]Delete cancelled.[/dim]")
        return

    with sqlite3.connect(DB_PATH) as conn:
        # Get ID first for clean cascading
        res = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
        if not res:
            console.print(f"[bold red]{ICON_X} Project '{name}' does not exist.[/bold red]")
            return

        p_id = res[0]
        conn.execute("DELETE FROM logs WHERE project_id = ?", (p_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (p_id,))

    if active == name:
        set_config("active_project", None)

    console.print(f"[bold orange3]{ICON_TRASH} Project '{name}' and its history have been wiped.[/bold orange3]")


def list_projects():
    with sqlite3.connect(DB_PATH) as conn:
        projects = conn.execute("SELECT name, root_path FROM projects").fetchall()

    table = Table(title="Registered Projects", border_style="cyan", box=None)
    table.add_column("Project Name", style="bold magenta")
    table.add_column("Root Path", style="dim")

    for name, path in projects:
        table.add_row(name, path)
    console.print(table)

def start_timer(task_name):
    project_name = get_config("active_project")
    if not project_name:
        console.print(f"[bold yellow]{ICON_X} No active project. Use: tracker add <name>[/bold yellow]")
        return

    with sqlite3.connect(DB_PATH) as conn:
        p_row = conn.execute("SELECT id FROM projects WHERE name = ?", (project_name,)).fetchone()
        if not p_row:
            console.print(f"[bold red]{ICON_X} Project '{project_name}' not found.[/bold red]")
            return

        p_id = p_row[0]
        conn.execute("UPDATE logs SET end_time = ? WHERE end_time IS NULL", (datetime.now(),))
        conn.execute("INSERT INTO logs (project_id, task_name, start_time) VALUES (?, ?, ?)",
                     (p_id, task_name, datetime.now()))

    console.print(Panel(f"{ICON_CLOCK} Started tracking: [bold cyan]{task_name}[/bold cyan]\nProject: [dim]{project_name}[/dim]", border_style="green"))

def stop_timer():
    with sqlite3.connect(DB_PATH) as conn:
        active = conn.execute("SELECT id, task_name FROM logs WHERE end_time IS NULL").fetchone()
        if active:
            conn.execute("UPDATE logs SET end_time = ? WHERE id = ?", (datetime.now(), active[0]))
            console.print(f"[bold orange3]{ICON_STOP} Stopped tracking '{active[1]}'.[/bold orange3]")
        else:
            console.print(f"[bold red]{ICON_X} No active timer to stop.[/bold red]")

def continue_task():
    project_name = get_config("active_project")
    if not project_name:
        console.print(f"[bold red]{ICON_X} No active project selected.[/bold red]")
        return

    with sqlite3.connect(DB_PATH) as conn:
        tasks = conn.execute('''SELECT DISTINCT task_name FROM logs l
                                JOIN projects p ON l.project_id = p.id
                                WHERE p.name = ?
                                ORDER BY l.id DESC LIMIT 5''', (project_name,)).fetchall()

        if not tasks:
            console.print(f"[bold yellow]{ICON_LIST} No history found for this project.[/bold yellow]")
            return

        table = Table(title=f"Recent Tasks: {project_name}", border_style="magenta", box=None)
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("Task Name", style="white")

        for idx, (name,) in enumerate(tasks, 1):
            table.add_row(str(idx), name)

        console.print(table)
        choice = console.input("[bold green]Select ID to resume (Enter to cancel): [/bold green]")

        if choice.isdigit() and 0 < int(choice) <= len(tasks):
            selected_task = tasks[int(choice) - 1][0]
            start_timer(selected_task)
        else:
            console.print("[italic gray]Action cancelled.[/italic gray]")

def show_current():
        active_p = get_config("active_project")
        if not active_p:
          console.print(f"[dim]{ICON_LIST} No active project selected. Start with 'tracker add <name>'[/dim]")
        return
        with sqlite3.connect(DB_PATH) as conn:
          row = conn.execute('''SELECT p.name, l.task_name, l.start_time FROM logs l
                              JOIN projects p ON l.project_id = p.id
                              WHERE l.end_time IS NULL''').fetchone()
        if row:
            elapsed = datetime.now() - datetime.fromisoformat(row[2])
            console.print(Panel(f"[bold]{ICON_PROJECT} Project:[/bold] {row[0]}\n[bold]{ICON_TASK} Task:[/bold] {row[1]}\n[bold green]{ICON_CLOCK} Time:[/bold green] {format_delta(elapsed)}",
                                title="Active Session", expand=False))
        else:
            console.print(f"[italic gray]{ICON_LIST} No active timer.[/italic gray]")

def display_dashboard():
    with sqlite3.connect(DB_PATH) as conn:
        active = conn.execute('''SELECT p.name, l.task_name, l.start_time FROM logs l
                                 JOIN projects p ON l.project_id = p.id
                                 WHERE l.end_time IS NULL''').fetchone()

    if not active:
        console.print(f"[bold red]{ICON_X} No active timer running![/bold red]")
        return

    project, task, start_str = active
    start_time = datetime.fromisoformat(start_str)

    with Live(console=console, refresh_per_second=1, screen=False) as live:
        try:
            while True:
                elapsed = datetime.now() - start_time
                time_str = format_delta(elapsed)

                table = Table(show_header=True, header_style="bold blue", box=None)
                table.add_column(f"{ICON_PROJECT} Project", style="bright_cyan")
                table.add_column(f"{ICON_TASK} Task", style="bright_white")
                table.add_column(f"{ICON_CLOCK} Elapsed", style="bright_green bold", justify="right")
                table.add_row(project, task, time_str)

                live.update(
                    Panel(
                        table,
                        title=f"[bold] {ICON_CALENDAR} SESSION ACTIVE [/]",
                        subtitle="CTRL+C TO DETACH",
                        border_style="bright_magenta",
                        padding=(1, 2)
                    )
                )
                time.sleep(1)
        except KeyboardInterrupt:
            pass

def show_fancy_total():
    project_name = get_config("active_project")
    if not project_name:
        console.print(f"[bold red]{ICON_X} No active project selected.[/bold red]")
        return

    with sqlite3.connect(DB_PATH) as conn:
        logs = conn.execute('''SELECT start_time, end_time FROM logs l
                               JOIN projects p ON l.project_id = p.id
                               WHERE p.name = ?''', (project_name,)).fetchall()

    total_sec = 0
    for start, end in logs:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end) if end else datetime.now()
        total_sec += (end_dt - start_dt).total_seconds()

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None, complete_style="green", finished_style="bold green"),
        TextColumn("[bold green]{task.percentage:>3.0f}%"),
        console=console
    )

    goal_seconds = 8 * 3600
    task_id = progress.add_task("Daily Goal (8h)", total=goal_seconds)
    progress.update(task_id, completed=min(total_sec, goal_seconds))

    console.print(Panel(f"{ICON_LIST} [bold cyan]{project_name}[/bold cyan] Stats\n"
                        f"Accumulated Time: [bold green]{format_delta(timedelta(seconds=total_sec))}[/bold green]",
                        border_style="bright_blue"))
    progress.start()
    progress.stop()
    print("\n")

def show_help():
    table = Table(title=f"{ICON_CLOCK} How to use the CLI?", show_header=True, header_style="bold magenta", box=None)
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Arguments", style="dim")
    table.add_column("Description", style="white")

    # Add your rows manually to match your tool
    table.add_row(f"{ICON_PROJECT} add", "<name>", "Initialize or switch project context")
    table.add_row(f"{ICON_CLOCK} new", "<task>", "Start a fresh task timer")
    table.add_row(f"{ICON_SWAP} switch", "<name>", "Change your active project focus")
    table.add_row(f"{ICON_TRASH} delete", "<name>", "Nuclear option: Wipe project & data")
    table.add_row(f"{ICON_STOP} stop", "", "Stop the current active timer")
    table.add_row(f"{ICON_CALENDAR} continue", "", "Resume a previous task from history")
    table.add_row(f"{ICON_CLOCK} dash", "[matrix]", "Open live dashboard (simple/matrix)")
    table.add_row(f"{ICON_CHECK} total", "", "Show total work time & daily goal")
    table.add_row(f"{ICON_LIST} list", "", "List all registered projects")
    table.add_row(f"{ICON_LIST} current", "", "Check what's running right now")

    console.print(Panel(table, border_style="bright_blue", expand=False))
    console.print("[dim]I wish you and your project success, good luck! :3[/dim]\n")

# --- Main Entry ---

def main():
    init_db()
    parser = argparse.ArgumentParser(description="Project Time Tracker CLI", add_help=False)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("add", help="Add/Switch project").add_argument("name")
    subparsers.add_parser("list", help="List all projects")
    subparsers.add_parser("new", help="Start task").add_argument("task")
    subparsers.add_parser("switch", help="Change active project").add_argument("name")
    subparsers.add_parser("delete", help="Remove project and history").add_argument("name")
    subparsers.add_parser("stop", help="Stop timer")
    subparsers.add_parser("continue", help="Resume recent task")
    subparsers.add_parser("current", help="Status check")
    subparsers.add_parser("dash", help="Live dashboard")
    subparsers.add_parser("total", help="Time summary")

    args = parser.parse_args()

    if args.command == "add": project_add(args.name)
    elif args.command == "list": list_projects()
    elif args.command == "new": start_timer(args.task)
    elif args.command == "switch": project_switch(args.name)
    elif args.command == "delete": project_delete(args.name)
    elif args.command == "stop": stop_timer()
    elif args.command == "continue": continue_task()
    elif args.command == "current": show_current()
    elif args.command == "dash": display_dashboard()
    elif args.command == "total": show_fancy_total()
    else:
        show_help()

if __name__ == "__main__":
    main()
