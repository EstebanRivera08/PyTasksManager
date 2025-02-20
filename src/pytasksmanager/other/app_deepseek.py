import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Callable, Optional
from textwrap import shorten

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, ListView, ListItem, Button, Static, Label, Input
from textual.containers import Horizontal, Vertical, Center
from textual.events import Key

# File names for persistence
DATA_FILE = "tasks.json"
ARCHIVE_FILE = "archived_tasks.json"
TABS_FILE = "tabs.json"

@dataclass
class Task:
    id: int
    tab: str
    title: str
    comment: str
    state: str
    created_at: str
    last_modified: str
    history: List[str]

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return Task(**data)

def load_tasks() -> List[Task]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return [Task.from_dict(item) for item in json.load(f)]
    return []

def save_tasks(tasks: List[Task]):
    with open(DATA_FILE, "w") as f:
        json.dump([task.to_dict() for task in tasks], f, indent=4)

def load_archived_tasks() -> List[Task]:
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r") as f:
            return [Task.from_dict(item) for item in json.load(f)]
    return []

def save_archived_tasks(tasks: List[Task]):
    with open(ARCHIVE_FILE, "w") as f:
        json.dump([task.to_dict() for task in tasks], f, indent=4)

def load_tabs() -> List[str]:
    if os.path.exists(TABS_FILE):
        with open(TABS_FILE, "r") as f:
            return json.load(f)
    return []

def save_tabs(tabs: List[str]):
    with open(TABS_FILE, "w") as f:
        json.dump(tabs, f, indent=4)

state_colors = {
    "urgent": "red",
    "in progress": "orange1",
    "in pause": "blue",
    "finished": "green",
}

class InputModal(Static):
    def __init__(self, prompt: str, callback: Callable[[str], None], initial_value: str = "", **kwargs):
        super().__init__(**kwargs)
        self.prompt_text = prompt
        self.callback = callback
        self.initial_value = initial_value

    def compose(self) -> ComposeResult:
        yield Center(Label(self.prompt_text))
        self.input_field = Input(placeholder="Enter value here", value=self.initial_value)
        yield Center(self.input_field)
        with Center():
            with Horizontal():
                yield Button("OK", id="ok")
                yield Button("Cancel", id="cancel")

    async def on_key(self, event: Key) -> None:
        if event.key == "enter":
            self.callback(self.input_field.value)
            self.remove()
        
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            self.callback(self.input_field.value)
            self.remove()
        elif event.button.id == "cancel":
            self.remove()

class OptionModal(Static):
    def __init__(self, prompt: str, options: List[str], callback: Callable[[str], None], **kwargs):
        super().__init__(**kwargs)
        self.prompt_text = prompt
        self.options = options
        self.callback = callback
        self.option_ids = {opt.replace(" ", "_"): opt for opt in options}

    def compose(self) -> ComposeResult:
        yield Center(Label(self.prompt_text))
        with Center():
            with Horizontal():
                for valid_id, opt in self.option_ids.items():
                    yield Button(opt, id=valid_id)
            yield Button("Cancel", id="cancel", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.remove()
        else:
            selected_option = self.option_ids.get(event.button.id)
            self.callback(selected_option)
            self.remove()

class ConfirmationModal(Static):
    def __init__(self, message: str, callback: Callable[[bool], None], **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.callback = callback

    def compose(self) -> ComposeResult:
        yield Center(Label(self.message))
        with Center():
            with Horizontal():
                yield Button("Yes", id="yes")
                yield Button("No", id="no")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.callback(True)
        else:
            self.callback(False)
        self.remove()

class TaskManagerApp(App):
    CSS_PATH = "task_manager.css"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tasks: List[Task] = load_tasks()
        self.selected_tab = "All"
        self.selected_task_id: Optional[int] = None
        self.tabs = load_tabs()
        self.next_id = max((task.id for task in self.tasks), default=0) + 1
        self.modify_task_data: Optional[Task] = None

        for task in self.tasks:
            if task.tab not in self.tabs:
                self.tabs.append(task.tab)
        save_tabs(self.tabs)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(classes="sidebar"):
                yield Label("Tabs", classes="sidebar-title")
                self.tab_list = ListView(*[ListItem(Label(tab)) for tab in ["All"] + sorted(self.tabs)])
                yield self.tab_list
                with Horizontal(classes="tab-buttons"):
                    yield Button("Add Tab", id="add_tab")
                    yield Button("Modify Tab", id="modify_tab")
                    yield Button("Delete Tab", id="delete_tab")
            
            with Vertical(classes="main-content"):
                self.task_table = DataTable()
                self.task_table.add_columns("ID", "Title", "Created", "Last Modified", "Comments")
                self.task_table.cursor_type = "row"
                yield self.task_table
                with Horizontal(classes="task-buttons"):
                    yield Button("Add Task (a)", id="add_task")
                    yield Button("Modify Task (m)", id="modify_task")
                    yield Button("Delete Task (d)", id="delete_task")
                    yield Button("File Finished (f)", id="file_tasks")
                    yield Button("Exit (q)", id="exit")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_tabs()
        self.refresh_tasks_table()

    def refresh_tabs(self):
        self.tab_list.clear()
        for tab in ["All"] + sorted(self.tabs):
            item = ListItem(Label(tab))
            if tab == self.selected_tab:
                item.add_class("selected")
            self.tab_list.append(item)

    def refresh_tasks_table(self):
        self.task_table.clear()
        tasks_to_show = [t for t in self.tasks if self.selected_tab == "All" or t.tab == self.selected_tab]
        
        for task in tasks_to_show:
            comment_preview = shorten(task.comment, width=20, placeholder="...")
            self.task_table.add_row(
                str(task.id),
                task.title,
                task.created_at,
                task.last_modified,
                comment_preview
            )

    def show_input_modal(self, prompt: str, callback: Callable[[str], None], initial_value: str = ""):
        self.mount(InputModal(prompt, callback, initial_value))

    def show_option_modal(self, prompt: str, options: List[str], callback: Callable[[str], None]):
        self.mount(OptionModal(prompt, options, callback))

    def show_confirmation_modal(self, message: str, callback: Callable[[bool], None]):
        self.mount(ConfirmationModal(message, callback))

    async def action_toggle_color(self):
        self.color_coding = not self.color_coding
        self.refresh_tasks_table()

    async def action_add_task(self):
        if self.selected_tab == "All":
            self.console.print("Select a tab first!")
            return
        
        self.new_task_data = {"tab": self.selected_tab}
        self.show_input_modal("Enter task title:", self.add_task_title)

    def add_task_title(self, title: str):
        self.new_task_data["title"] = title
        self.show_input_modal("Enter task comment (optional):", self.add_task_comment)

    def add_task_comment(self, comment: str):
        self.new_task_data["comment"] = comment
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_task = Task(
            id=self.next_id,
            tab=self.new_task_data["tab"],
            title=self.new_task_data["title"],
            comment=self.new_task_data["comment"],
            state="in progress",
            created_at=now,
            last_modified=now,
            history=[f"{now}: Task created"]
        )
        self.next_id += 1
        self.tasks.append(new_task)
        save_tasks(self.tasks)
        self.refresh_tasks_table()

    async def action_delete_task(self):
        if not self.selected_task_id:
            self.console.print("Select a task first!")
            return
        
        task = next((t for t in self.tasks if t.id == self.selected_task_id), None)
        if not task:
            self.console.print("Task not found!")
            return

        def delete_confirmed(confirmed: bool):
            if confirmed:
                self.tasks = [t for t in self.tasks if t.id != self.selected_task_id]
                save_tasks(self.tasks)
                self.selected_task_id = None
                self.refresh_tasks_table()
        
        self.show_confirmation_modal(
            f"Delete task '{task.title}' (ID: {task.id})?",
            delete_confirmed
        )

    async def action_modify_task(self):
        if not self.selected_task_id:
            self.console.print("Select a task first!")
            return
        
        task = next((t for t in self.tasks if t.id == self.selected_task_id), None)
        if not task:
            self.console.print("Task not found!")
            return

        self.modify_task_data = task
        self.show_option_modal(
            "Select field to modify:",
            ["Title", "Comment", "State", "Tab"],
            self.handle_modify_choice
        )

    def handle_modify_choice(self, choice: str):
        if choice == "Title":
            self.show_input_modal(
                "New title:", 
                lambda val: self.update_task_field("title", val),
                initial_value=self.modify_task_data.title
            )
        elif choice == "Comment":
            self.show_input_modal(
                "New comment:", 
                lambda val: self.update_task_field("comment", val),
                initial_value=self.modify_task_data.comment
            )
        elif choice == "State":
            self.show_option_modal(
                "Select new state:", 
                list(state_colors.keys()), 
                lambda val: self.update_task_field("state", val)
            )
        elif choice == "Tab":
            self.show_option_modal(
                "Select new tab:", 
                self.tabs, 
                lambda val: self.update_task_field("tab", val)
            )

    def update_task_field(self, field: str, value: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        old_value = getattr(self.modify_task_data, field)
        setattr(self.modify_task_data, field, value)
        self.modify_task_data.last_modified = now
        self.modify_task_data.history.append(
            f"{now}: Changed {field} from '{old_value}' to '{value}'"
        )
        save_tasks(self.tasks)
        self.refresh_tasks_table()

    async def action_add_tab(self):
        self.show_input_modal("Enter new tab name:", self.add_new_tab)

    def add_new_tab(self, tab: str):
        if tab and tab not in self.tabs:
            self.tabs.append(tab)
            save_tabs(self.tabs)
            self.refresh_tabs()

    async def action_modify_tab(self):
        if self.selected_tab == "All":
            self.console.print("Select a tab to modify!")
            return
        self.show_input_modal(f"Rename '{self.selected_tab}':", self.modify_tab_callback)

    def modify_tab_callback(self, new_tab: str):
        if not new_tab or new_tab in self.tabs:
            return

        old_tab = self.selected_tab
        self.tabs[self.tabs.index(old_tab)] = new_tab
        save_tabs(self.tabs)
        for task in self.tasks:
            if task.tab == old_tab:
                task.tab = new_tab
        save_tasks(self.tasks)
        self.selected_tab = new_tab
        self.refresh_tabs()
        self.refresh_tasks_table()

    async def action_delete_tab(self):
        if self.selected_tab == "All":
            self.console.print("Select a tab to delete!")
            return
        
        def delete_confirmed(confirmed: bool):
            if confirmed:
                self.tabs.remove(self.selected_tab)
                self.tasks = [t for t in self.tasks if t.tab != self.selected_tab]
                save_tabs(self.tabs)
                save_tasks(self.tasks)
                self.selected_tab = "All"
                self.refresh_tabs()
                self.refresh_tasks_table()
        
        self.show_confirmation_modal(
            f"Delete '{self.selected_tab}' and all its tasks?",
            delete_confirmed
        )

    async def action_file_tasks(self):
        finished = [t for t in self.tasks if t.state == "finished"]
        if finished:
            archived = load_archived_tasks()
            archived.extend(finished)
            save_archived_tasks(archived)
            self.tasks = [t for t in self.tasks if t.state != "finished"]
            save_tasks(self.tasks)
            self.refresh_tasks_table()

    async def action_exit(self):
        self.exit()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        actions = {
            "toggle_color": self.action_toggle_color,
            "add_task": self.action_add_task,
            "modify_task": self.action_modify_task,
            "delete_task": self.action_delete_task,
            "file_tasks": self.action_file_tasks,
            "add_tab": self.action_add_tab,
            "modify_tab": self.action_modify_tab,
            "delete_tab": self.action_delete_tab,
            "exit": self.action_exit
        }

        if button_id in actions:
            await actions[button_id]()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.selected_tab = str(event.item.query_one(Label).renderable)
        self.refresh_tabs()
        self.refresh_tasks_table()

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row = self.task_table.get_row_at(event.cursor_row)
        self.selected_task_id = int(row[0])

    # async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
    #     row = self.task_table.get_row_at(event.row_key)
    #     self.selected_task_id = int(row[0])
    #     task = next((t for t in self.tasks if t.id == self.selected_task_id), None)
    #     if task:
    #         history = "\n".join(task.history)
    #         self.console.print(f"""
    #         [bold]Task Details:[/bold]
    #         ID: {task.id}
    #         Title: {task.title}
    #         Tab: {task.tab}
    #         State: {task.state}
    #         Comment: {task.comment}
            
    #         [bold]History:[/bold]
    #         {history}
    #         """)

    async def on_key(self, event: Key) -> None:
        keys = {
            "a": self.action_add_task,
            "c": self.action_toggle_color,
            "d": self.action_delete_task,
            "f": self.action_file_tasks,
            "m": self.action_modify_task,
            "q": self.action_exit
        }
        if event.key in keys:
            await keys[event.key]()

if __name__ == "__main__":
    TaskManagerApp().run()