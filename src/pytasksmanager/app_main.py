import json
import os
import uuid
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich import box
import sys  


DATA_DIR = 'task_data'
TABS_FILE = os.path.join(DATA_DIR, 'tabs.json')
console = Console()

class Tab:
    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks
        self.task_counter = len(tasks) + 1 if tasks else 1

    def to_dict(self):
        return {
            'name': self.name,
            'tasks': [task.to_dict() for task in self.tasks],
            'task_counter': self.task_counter
        }

    @classmethod
    def from_dict(cls, data):
        tab = cls(
            name=data['name'],
            tasks=[Task.from_dict(task_data) for task_data in data['tasks']]
        )
        tab.task_counter = data.get('task_counter', len(data['tasks']) + 1)
        return tab

class Task:
    STATE_MAP = {
        'u': ('Urgent', 'red'),
        'p': ('In Pause', 'blue'),
        'g': ('Started', 'yellow'),
        'f': ('Finished', 'green')
    }

    def __init__(self, id, title, state, comment, created_at, modified_at, history):
        self.id = id
        self.title = title
        self.state = state
        self.comment = comment
        self.created_at = created_at
        self.modified_at = modified_at
        self.history = history

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'state': self.state,
            'comment': self.comment,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'history': self.history
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            title=data['title'],
            state=data['state'],
            comment=data['comment'],
            created_at=data['created_at'],
            modified_at=data['modified_at'],
            history=data['history']
        )

def load_tabs():
    tabs = []
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith('.json'):
                with open(os.path.join(DATA_DIR, filename), 'r') as f:
                    data = json.load(f)
                    tabs.append(Tab.from_dict(data))
    return tabs

def save_tabs(tabs):
    os.makedirs(DATA_DIR, exist_ok=True)
    for tab in tabs:
        tab_file = os.path.join(DATA_DIR, f"{tab.name}.json")
        with open(tab_file, 'w') as f:
            json.dump(tab.to_dict(), f, indent=4)

def display_tabs(tabs):
    table = Table(box=box.ROUNDED, title="Tabs Manager")
    table.add_column("Number", style="cyan")
    table.add_column("Tab Name", style="magenta")
    
    if not tabs:
        console.print("\n[bold yellow][No tabs. Add new tab.][/bold yellow]\n")
    
    for idx, tab in enumerate(tabs, 1):
        table.add_row(str(idx), tab.name)
    
    table.add_row("----", "-------")
    table.add_row("m", "[yellow]Modify Tab[/yellow]")
    table.add_row("n", "[green]New Tab[/green]")
    table.add_row("e", "[red]Exit[/red]")
    
    console.print(table)

def create_tab(tabs):
    name = Prompt.ask("Enter tab name")
    new_tab = Tab( name=name, tasks=[])
    tabs.append(new_tab)
    save_tabs(tabs)
    console.print(f"[green]Tab '{name}' created successfully![/green]")

def modify_tab(tabs):
    tab_number = Prompt.ask("Enter tab number to modify")
    try:
        tab_idx = int(tab_number) - 1
        if 0 <= tab_idx < len(tabs):
            tab = tabs[tab_idx]
            action = Prompt.ask(
                "Choose action: (c) Change name, (d) Delete tab",
                choices=["c", "d"]
            )
            
            if action == "c":
                new_name = Prompt.ask("Enter new name")
                tab.name = new_name
                save_tabs(tabs)
                console.print("[green]Tab name updated![/green]")
            elif action == "d":
                if Confirm.ask(f"[red]Delete tab '{tab.name}' and all its tasks?[/red]"):
                    del tabs[tab_idx]
                    save_tabs(tabs)
                    console.print("[red]Tab deleted![/red]")
        else:
            console.print("[red]Invalid tab number![/red]")
    except ValueError:
        console.print("[red]Please enter a valid number![/red]")

def display_tasks(tab, filtered_tasks=None):
    tasks = filtered_tasks if filtered_tasks else tab.tasks
    title = f"[bold magenta]{tab.name}[/bold magenta] Tasks"
    
    if not tasks:
        console.print("\n[bold yellow][No tasks. Add new task.][/bold yellow]\n")
        return
    
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    columns = [
        ("ID", "cyan"),
        ("Title", "white"),
        ("State", ""),
        ("Created", "dim"),
        ("Modified", "dim"),
        ("Comment", "yellow")
    ]
    
    for col, style in columns:
        table.add_column(col, style=style)
    
    for task in tasks:
        state_name, color = Task.STATE_MAP.get(task.state, ('Unknown', 'white'))
        comment_preview = (task.comment[:20] + '...') if len(task.comment) > 20 else task.comment
        
        row = [
            str(task.id),
            task.title,
            Text(state_name, style=color),
            task.created_at,
            task.modified_at,
            comment_preview
        ]
        table.add_row(*row)
    
    console.print(table)

def task_operations(tab):
    while True:
        console.print("\n1. Show Tasks\n2. New Task\n3. Modify Task\n4. Delete Task\n5. View Task Info\n6. Filter Tasks\n7. Back to Tabs \n8. Exit Program")
        choice = Prompt.ask("Choose action", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
        
        if choice == "1":
            display_tasks(tab)
        elif choice == "2":
            add_task(tab)
        elif choice == "3":
            modify_task(tab)
        elif choice == "4":
            delete_task(tab)
        elif choice == "5":
            view_task_info(tab)
        elif choice == "6":
            filter_tasks(tab)
        elif choice == "7":
            break
        elif choice == "8":
            console.print("[green]Goodbye! See you soon![/green]")
            sys.exit()

def validate_id(input):
    try:
        return int(input)
    except ValueError:
        console.print("[red]Invalid ID! Please enter a number.[/red]")
        return None

def add_task(tab):
    title = Prompt.ask("Enter task title")
    state = Prompt.ask(
        "State (u=Urgent, p=Pause, g=Progress, f=Finished)",
        choices=["u", "p", "g", "f"],
        default="u"
    )
    comment = Prompt.ask("Enter comment")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_task = Task(
        id=tab.task_counter,
        title=title,
        state=state,
        comment=comment,
        created_at=now,
        modified_at=now,
        history=[f"{now}: Task created"]
    )
    
    tab.tasks.append(new_task)
    tab.task_counter += 1
    save_tabs([tab])
    console.print("[green]Task added![/green]")

def modify_task(tab):
    task_id = Prompt.ask("Enter task ID")
    task_id = validate_id(task_id)
    if task_id is None:
        return
    
    task = next((t for t in tab.tasks if t.id == task_id), None)
    if not task:
        console.print("[red]Task not found![/red]")
        return
    
    new_title = Prompt.ask("New title", default=task.title)
    new_state = Prompt.ask(
        "New state (u/p/g/f)",
        choices=["u", "p", "g", "f"],
        default=task.state
    )
    new_comment = Prompt.ask("New comment", default=task.comment)
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    changes = []
    if new_title != task.title:
        changes.append(f"Title changed from '{task.title}' to '{new_title}'")
    if new_state != task.state:
        old_state = Task.STATE_MAP[task.state][0]
        new_state_name = Task.STATE_MAP[new_state][0]
        changes.append(f"State changed from '{old_state}' to '{new_state_name}'")
    if new_comment != task.comment:
        changes.append(f"Comment updated from '{task.comment[:20]}...' to '{new_comment[:20]}...'")
    
    if changes:
        task.title = new_title
        task.state = new_state
        task.comment = new_comment
        task.modified_at = now
        change_log = f"{now}: " + " | ".join(changes)
        task.history.append(change_log)
        save_tabs([tab])
        console.print("[green]Task updated![/green]")
    else:
        console.print("[yellow]No changes made.[/yellow]")

def delete_task(tab):
    task_id = Prompt.ask("Enter task ID to delete")
    task_id = validate_id(task_id)
    if task_id is None:
        return
    
    task = next((t for t in tab.tasks if t.id == task_id), None)
    if not task:
        console.print("[red]Task not found![/red]")
        return
    
    if Confirm.ask(f"[bold red]Are you sure you want to delete task '{task.title}'?[/bold red]"):
        tab.tasks.remove(task)
        save_tabs([tab])
        console.print("[bold red]Task deleted permanently![/bold red]")
        
        # Show updated task list
        display_tasks(tab)
    else:
        console.print("[yellow]Deletion cancelled[/yellow]")

def view_task_info(tab):
    task_id = Prompt.ask("Enter task ID")
    task_id = validate_id(task_id)
    
    if task_id is None:
        return
    
    task = next((t for t in tab.tasks if t.id == int(task_id)), None)
    if not task:
        console.print("[red]Task not found![/red]")
        return
    
    console.print(f"\n[bold underline]{task.title}[/bold underline]")
    console.print(f"State: [{Task.STATE_MAP[task.state][1]}]{Task.STATE_MAP[task.state][0]}[/]")
    console.print(f"Created: {task.created_at}")
    console.print(f"Last Modified: {task.modified_at}")
    console.print(f"\n[bold]Comment:[/bold] {task.comment}")
    
    console.print("\n[bold underline]History[/bold underline]")
    for idx, entry in enumerate(task.history, 1):
        console.print(f"{idx}. [dim]{entry}[/dim]")
    
    if Confirm.ask("\n[bold]View detailed change log?[/bold]"):
        try:
            log_number = IntPrompt.ask("Enter log number to view details", show_choices=False)
            if 1 <= log_number <= len(task.history):
                entry = task.history[log_number-1]
                console.print(f"\n[bold underline]Change Details:[/bold underline]")
                for change in entry.split("|"):
                    console.print(f"  • {change.strip()}")
            else:
                console.print("[red]Invalid log number![/red]")
        except ValueError:
            console.print("[red]Please enter a valid number![/red]")

def filter_tasks(tab):
    state_help = ", ".join([f"{k}={v[0]}" for k, v in Task.STATE_MAP.items()])
    state = Prompt.ask(
        f"Filter by state ({state_help})",
        choices=["u", "p", "g", "f"]
    )
    filtered = [t for t in tab.tasks if t.state == state]
    
    if filtered:
        state_name = Task.STATE_MAP[state][0]
        console.print(f"\n[bold]{len(filtered)} {state_name} tasks:[/bold]")
        display_tasks(tab, filtered)
    else:
        console.print("[yellow]No tasks found[/yellow]")

def run_app():
    tabs = load_tabs()
    
    while True:
        console.clear()
        console.print(" WELCOME TO .... ")
        console.print("""
██████╗ ██╗   ██╗████████╗ █████╗ ███████╗██╗  ██╗███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ ██╗
██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗██║
██████╔╝ ╚████╔╝    ██║   ███████║███████╗█████╔╝ ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝██║
██╔═══╝   ╚██╔╝     ██║   ██╔══██║╚════██║██╔═██╗ ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗╚═╝
██║        ██║      ██║   ██║  ██║███████║██║  ██╗██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║██╗
╚═╝        ╚═╝      ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝
""")
        console.print("Created by: [bold underline] Esteban Rivera [/bold underline]\n")
        console.print("[bold underline]Task Manager 2.0[/bold underline]\n")
        display_tabs(tabs)
        
        if not tabs:
            choice = Prompt.ask("Select action", choices=["n", "e"], default="n")
        else:
            choices = [str(i) for i in range(1, len(tabs)+1)] + ["m", "n", "e"]
            choice = Prompt.ask("Select tab or action", choices=choices)
        
        if choice == "m":
            modify_tab(tabs)
        elif choice == "n":
            create_tab(tabs)
        elif choice == "e":
            console.print("[green]Goodbye! see you soon![/green]")
            break
        else:
            tab_idx = int(choice) - 1
            if 0 <= tab_idx < len(tabs):
                selected_tab = tabs[tab_idx]
                display_tasks(selected_tab)
                task_operations(selected_tab)
                save_tabs(tabs)

# if __name__ == "__main__":
#     main()