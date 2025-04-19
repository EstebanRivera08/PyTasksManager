# Simple package to manage your tasks

This python package `PyTaskManager` contains the executable `pytasksmanager` to produce an
easy and friendly command window app to store tasks informations.

## Quickstart

The quickest way to start using `PyTasksManager` is by installing `uv`, a fast Python
package and project manager (https://github.com/astral-sh/uv). Check for the install
commands [here](https://github.com/astral-sh/uv#installation). I recommend the pipx way.

Once you have `uv`, from the repository path, you can run `uv run pytasksmanager`
to run the app.

For example, in my case where I have already created the tab "SonoGenetics", and the tasks
within this tab, this is how it looks like:

```console
uv run pytasksmanager

 WELCOME TO ....

██████╗ ██╗   ██╗████████╗ █████╗ ███████╗██╗  ██╗███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ ██╗
██╔══██╗╚██╗ ██╔╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗██║
██████╔╝ ╚████╔╝    ██║   ███████║███████╗█████╔╝ ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝██║
██╔═══╝   ╚██╔╝     ██║   ██╔══██║╚════██║██╔═██╗ ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗╚═╝
██║        ██║      ██║   ██║  ██║███████║██║  ██╗██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║██╗
╚═╝        ╚═╝      ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝

Created by:  Esteban Rivera

Task Manager 2.0

      Tabs Manager
╭────────┬──────────────╮
│ Number │ Tab Name     │
├────────┼──────────────┤
│ 1      │ SonoGenetics │
│ ----   │ -------      │
│ m      │ Modify Tab   │
│ n      │ New Tab      │
│ e      │ Exit         │
╰────────┴──────────────╯
Select tab or action [1/m/n/e]: 1
                                                   SonoGenetics Tasks
╭────┬────────────────────────────────┬──────────┬─────────────────────┬─────────────────────┬─────────────────────────╮
│ ID │ Title                          │ State    │ Created             │ Modified            │ Comment                 │
├────┼────────────────────────────────┼──────────┼─────────────────────┼─────────────────────┼─────────────────────────┤
│ 1  │ Figures for _______            │ Urgent   │ 2025-02-21 09:38:17 │ 2025-02-21 09:39:31 │ Read the notebook wi... │
│    │ (simulations)                  │          │                     │                     │                         │
│ 2  │ Create the protocol for        │ Urgent   │ 2025-02-21 09:40:15 │ 2025-02-21 09:40:15 │ Check the material i... │
│    │ calibration                    │          │                     │                     │                         │
│ 3  │ Create the monoelement setup   │ In Pause │ 2025-02-21 09:41:11 │ 2025-02-21 09:41:11 │ We have already the ... │
│ 4  │ Do the vera's tutos            │ Finished │ 2025-02-21 09:42:47 │ 2025-02-21 09:42:47 │ Do the veras tutos t... │
╰────┴────────────────────────────────┴──────────┴─────────────────────┴─────────────────────┴─────────────────────────╯
1. Show Tasks
2. New Task
3. Modify Task
4. Delete Task
5. View Task Info
6. Filter Tasks
7. Back to Tabs
8. Exit Program
Choose action [1/2/3/4/5/6/7/8]: 8
Goodbye! See you soon!
```

## Author
- Esteban Rivera <deyver818@gmail.com>

