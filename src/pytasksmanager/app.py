import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Callable

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, ListView, ListItem, Button, Static, Label, Input
from textual.containers import Horizontal, Vertical, Center
from textual.events import Key  # Removed ButtonPressed import

# File names for persistence
DATA_FILE = "tasks.json"
ARCHIVE_FILE = "archived_tasks.json"
LABELS_FILE = "labels.json"

# Data model for a task
@dataclass
class Task:
    id: int
    label: str
    title: str
    comment: str
    state: str  # "urgent", "in progress", "in pause", "finished"
    created_at: str
    last_modified: str
    history: List[str]

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Task(**data)

# Persistence functions for tasks and labels
def load_tasks() -> List[Task]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            tasks = []
            for item in data:
                # Migrate legacy keys if needed
                if "main_state" in item:
                    item["state"] = item.pop("main_state")
                if "sub_state" in item:
                    del item["sub_state"]
                tasks.append(Task.from_dict(item))
            return tasks
    return []

def save_tasks(tasks: List[Task]):
    with open(DATA_FILE, "w") as f:
        json.dump([task.to_dict() for task in tasks], f, indent=4)

def load_archived_tasks() -> List[Task]:
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r") as f:
            data = json.load(f)
            return [Task.from_dict(item) for item in data]
    return []

def save_archived_tasks(tasks: List[Task]):
    with open(ARCHIVE_FILE, "w") as f:
        json.dump([task.to_dict() for task in tasks], f, indent=4)

def load_labels() -> List[str]:
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, "r") as f:
            return json.load(f)
    return []

def save_labels(labels: List[str]):
    with open(LABELS_FILE, "w") as f:
        json.dump(labels, f, indent=4)

# Define state colors
state_colors = {
    "urgent": "red",
    "in progress": "orange1",
    "in pause": "blue",
    "finished": "green",
}

# A simple modal for text input
class InputModal(Static):
    def __init__(self, prompt: str, callback: Callable[[str], None], **kwargs):
        super().__init__(**kwargs)
        self.prompt_text = prompt
        self.callback = callback

    def compose(self) -> ComposeResult:
        yield Center(Label(self.prompt_text))
        self.input_field = Input(placeholder="Enter value here")
        yield Center(self.input_field)
        with Center():
            with Horizontal():
                yield Button("OK", id="ok")
                yield Button("Cancel", id="cancel")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            value = self.input_field.value
            self.callback(value)
            self.remove()  # Remove the modal
        elif event.button.id == "cancel":
            self.remove()

# Main TUI application
class TaskManagerApp(App):
    CSS_PATH = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tasks: List[Task] = load_tasks()
        self.color_coding = True
        self.selected_label = "All"
        # Load predefined labels (and add any missing ones from tasks)
        self.labels = load_labels()
        for task in self.tasks:
            if task.label not in self.labels:
                self.labels.append(task.label)
        save_labels(self.labels)
        self.next_id = max((task.id for task in self.tasks), default=0) + 1
        self.new_task_data = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Labels", id="label_title")
                self.label_list = ListView(id="labels")
                yield self.label_list
                with Horizontal():
                    yield Button("Add Label", id="add_label")
                    yield Button("Modify Label", id="modify_label")
            with Vertical(id="main"):
                self.task_table = DataTable(id="task_table")
                yield self.task_table
                with Horizontal():
                    yield Button("Toggle Color Coding (c)", id="toggle_color")
                    yield Button("Add Task (a)", id="add_task")
                    yield Button("File Finished Tasks (f)", id="file_tasks")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_labels()
        self.refresh_tasks_table()

    def refresh_labels(self):
        labels_list = ["All"] + sorted(self.labels)
        self.label_list.clear()
        for label in labels_list:
            self.label_list.append(ListItem(Label(label)))

    def refresh_tasks_table(self):
        self.task_table.clear()
        self.task_table.add_columns("ID", "Title", "State", "Last Modified")
        if self.selected_label == "All":
            tasks_to_show = self.tasks
        else:
            tasks_to_show = [t for t in self.tasks if t.label == self.selected_label]

        for task in tasks_to_show:
            color = state_colors.get(task.state, "white")
            state_text = f"[{color}]{task.state}[/{color}]"
            if self.color_coding:
                row_id = f"[{color}]{task.id}[/{color}]"
                row_title = f"[{color}]{task.title}[/{color}]"
                row_state = f"[{color}]{task.state}[/{color}]"
                row_last_modified = f"[{color}]{task.last_modified}[/{color}]"
                self.task_table.add_row(row_id, row_title, row_state, row_last_modified)
            else:
                # Only color the state cell when color coding is off.
                row_state = f"[{color}]{task.state}[/{color}]"
                self.task_table.add_row(str(task.id), task.title, row_state, task.last_modified)


    def show_input_modal(self, prompt: str, callback: Callable[[str], None]):
        modal = InputModal(prompt, callback)
        self.mount(modal)

    async def action_toggle_color(self):
        self.color_coding = not self.color_coding
        self.refresh_tasks_table()

    async def action_add_task(self):
        self.new_task_data = {}
        # Start a chain of modals for task details.
        self.show_input_modal("Enter label for new task:", self.add_task_label)

    def add_task_label(self, label: str):
        if label not in self.labels:
            self.labels.append(label)
            save_labels(self.labels)
            self.refresh_labels()
        self.new_task_data["label"] = label
        self.show_input_modal("Enter task title:", self.add_task_title)

    def add_task_title(self, title: str):
        self.new_task_data["title"] = title
        self.show_input_modal("Enter task comment (optional):", self.add_task_comment)

    def add_task_comment(self, comment: str):
        self.new_task_data["comment"] = comment
        self.show_input_modal("Enter task state (urgent, in progress, in pause, finished):", self.add_task_state)

    def add_task_state(self, state: str):
        state = state.lower().strip()
        if state not in state_colors:
            state = "in progress"  # default fallback
        self.new_task_data["state"] = state
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_task = Task(
            id=self.next_id,
            label=self.new_task_data["label"],
            title=self.new_task_data["title"],
            comment=self.new_task_data["comment"],
            state=state,
            created_at=now,
            last_modified=now,
            history=[f"{now}: Task created with state '{state}'."]
        )
        self.next_id += 1
        self.tasks.append(new_task)
        save_tasks(self.tasks)
        self.refresh_tasks_table()

    async def action_add_label(self):
        self.show_input_modal("Enter new label name:", self.add_new_label)

    def add_new_label(self, label: str):
        if label and label not in self.labels:
            self.labels.append(label)
            save_labels(self.labels)
            self.refresh_labels()
            self.log("Label added: " + label)
        else:
            self.log("Label already exists or empty.")

    async def action_modify_label(self):
        # To modify a label, a specific label must be selected.
        if self.selected_label == "All":
            await self.console.print("Select a specific label to modify.")
            return
        prompt = f"Enter new name for label '{self.selected_label}':"
        self.show_input_modal(prompt, self.modify_label_callback)

    def modify_label_callback(self, new_label: str):
        if not new_label:
            self.log("No new label provided.")
            return
        if new_label in self.labels:
            self.log("Label name already exists.")
            return
        try:
            index = self.labels.index(self.selected_label)
        except ValueError:
            self.log("Selected label not found.")
            return
        old_label = self.selected_label
        self.labels[index] = new_label
        save_labels(self.labels)
        # Update tasks that have the old label
        for task in self.tasks:
            if task.label == old_label:
                task.label = new_label
                task.last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                task.history.append(f"{task.last_modified}: Label changed from '{old_label}' to '{new_label}'.")
        save_tasks(self.tasks)
        self.selected_label = new_label
        self.refresh_labels()
        self.refresh_tasks_table()

    async def action_file_tasks(self):
        finished_tasks = [t for t in self.tasks if t.state == "finished"]
        if finished_tasks:
            archived = load_archived_tasks()
            archived.extend(finished_tasks)
            save_archived_tasks(archived)
            self.tasks = [t for t in self.tasks if t.state != "finished"]
            save_tasks(self.tasks)
            self.refresh_labels()
            self.refresh_tasks_table()
            await self.console.print("Finished tasks have been filed.")
        else:
            await self.console.print("No finished tasks to file.")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "toggle_color":
            await self.action_toggle_color()
        elif button_id == "add_task":
            await self.action_add_task()
        elif button_id == "file_tasks":
            await self.action_file_tasks()
        elif button_id == "add_label":
            await self.action_add_label()
        elif button_id == "modify_label":
            await self.action_modify_label()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_label = str(event.item.query_one(Label).renderable)
        self.selected_label = selected_label
        self.refresh_tasks_table()

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row = self.task_table.get_row_at(event.row_key)
        task_id = int(row[0])
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task:
            details = "\n" + "=" * 40 + "\n"
            details += f"Task ID: {task.id}\nTitle: {task.title}\nLabel: {task.label}\nState: {task.state}\nComment: {task.comment}\nHistory:\n"
            for entry in task.history:
                details += f"  {entry}\n"
            details += "=" * 40 + "\n"
            await self.console.print(details)

    async def on_key(self, event: Key) -> None:
        # Keybindings for actions
        if event.key == "a":
            await self.action_add_task()
        elif event.key == "c":
            await self.action_toggle_color()
        elif event.key == "f":
            await self.action_file_tasks()
        elif event.key == "l":  # shortcut to add a label
            await self.action_add_label()
        elif event.key == "m":  # shortcut to modify a label
            await self.action_modify_label()

# if __name__ == "__main__":
#     TaskManagerApp().run()