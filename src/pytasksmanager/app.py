import json
import os
import uuid
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

DATA_FILE = 'tasks.json'
console = Console()

class Task:
    def __init__(self, id, title, main_state, sub_state, created_at, history):
        self.id = id
        self.title = title
        self.main_state = main_state
        self.sub_state = sub_state
        self.created_at = created_at
        self.history = history  # List of history log strings

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'main_state': self.main_state,
            'sub_state': self.sub_state,
            'created_at': self.created_at,
            'history': self.history,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            title=data['title'],
            main_state=data['main_state'],
            sub_state=data['sub_state'],
            created_at=data['created_at'],
            history=data.get('history', [])
        )

def load_tasks():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return [Task.from_dict(item) for item in data]
    return []

def save_tasks(tasks):
    with open(DATA_FILE, 'w') as f:
        json.dump([task.to_dict() for task in tasks], f, indent=4)

def display_tasks(tasks, filter_main_state=None):
    table = Table(title="Task List")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Main State")
    table.add_column("Sub State")
    table.add_column("Created At")

    for task in tasks:
        if filter_main_state and task.main_state != filter_main_state:
            continue

        # Define colors based on task state
        color = "white"
        if task.main_state == "done":
            color = "green"
        elif task.main_state == "not started":
            if task.sub_state.lower() == "urgent":
                color = "red"
            else:
                color = "yellow"
        elif task.main_state == "in progress":
            color = "blue"
        elif task.main_state == "in pause":
            color = "magenta"

        table.add_row(
            task.id,
            task.title,
            f"[{color}]{task.main_state}[/{color}]",
            task.sub_state,
            task.created_at
        )
    console.print(table)

def add_task(tasks):
    title = Prompt.ask("Enter task title")
    main_state = Prompt.ask("Enter main state", choices=["not started", "in progress", "in pause", "done"], default="not started")
    sub_state = Prompt.ask("Enter sub state (e.g., Urgent, To the future, Need info to continue)", default="None")
    
    task_id = str(uuid.uuid4())[:8]  # Generate a short unique id
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history = [f"{created_at}: Task created with state '{main_state}' and sub-state '{sub_state}'."]
    
    new_task = Task(task_id, title, main_state, sub_state, created_at, history)
    tasks.append(new_task)
    save_tasks(tasks)
    console.print("[green]Task added successfully![/green]")

def change_task(tasks):
    display_tasks(tasks)
    task_id = Prompt.ask("Enter the ID of the task you want to change")
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        console.print("[red]Task not found.[/red]")
        return

    console.print(f"Current main state: {task.main_state}, Sub state: {task.sub_state}")
    new_main_state = Prompt.ask("Enter new main state", choices=["not started", "in progress", "in pause", "done"], default=task.main_state)
    new_sub_state = Prompt.ask("Enter new sub state", default=task.sub_state)
    if Confirm.ask("Are you sure you want to apply these changes?"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        change_entry = f"{now}: Changed main state from '{task.main_state}' to '{new_main_state}', sub state from '{task.sub_state}' to '{new_sub_state}'."
        task.main_state = new_main_state
        task.sub_state = new_sub_state
        task.history.append(change_entry)
        save_tasks(tasks)
        console.print("[green]Task updated successfully![/green]")
    else:
        console.print("[yellow]Change cancelled.[/yellow]")

def view_history(tasks):
    display_tasks(tasks)
    task_id = Prompt.ask("Enter the ID of the task to view history")
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        console.print("[red]Task not found.[/red]")
        return
    console.print(f"\n[bold]History for task:[/bold] {task.title}")
    for entry in task.history:
        console.print(entry)

def filter_tasks(tasks):
    state_filter = Prompt.ask("Enter the main state to filter by", choices=["not started", "in progress", "in pause", "done"])
    display_tasks(tasks, filter_main_state=state_filter)

def run_app():
    tasks = load_tasks()
    while True:
        console.print("\n[bold underline]Task Manager Menu[/bold underline]")
        console.print("1. List all tasks")
        console.print("2. Add a task")
        console.print("3. Change a task")
        console.print("4. View task history")
        console.print("5. Filter tasks")
        console.print("6. Exit")
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6"])
        
        if choice == "1":
            display_tasks(tasks)
        elif choice == "2":
            add_task(tasks)
        elif choice == "3":
            change_task(tasks)
        elif choice == "4":
            view_history(tasks)
        elif choice == "5":
            filter_tasks(tasks)
        elif choice == "6":
            console.print("Exiting. Goodbye!")
            break
