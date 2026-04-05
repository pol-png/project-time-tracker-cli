# free, project time tracking cli


A high-performance, aesthetically pleasing Command Line Interface (CLI) for tracking work hours across multiple projects. Built with ``Python``, ``SQLite``, and ``Rich``, featuring a live-updating dashboard.

Completely free of charge, for you or anyone else.

**I do not guarantee anything, it's a python file. Read it yourself. For any issues, suggestions or such. Idk, fork it and do that.**

Created mostly with the help of AI, I am busy on my own project but I couldn't bother to search for a CLI based time-tracker, and most of the UI based ones are paid. Like seriously? I have to pay to **track time**?

---

## Features

* **Project Contexts:** Automatically detects the current folder or allows manual project switching.
* **Live Dashboard:** Real-time ticking clock for your active task.
* **Matrix Mode:** High-performance "falling code" animation for focused deep work.
* **Nerd Font Support:** Beautiful icons for projects, tasks, and timers.
* **SQLite Backend:** All your data is stored locally in a lightweight database.
* **Editable Install:** Make changes to the code and see them instantly in the CLI.

---

## Installation

### 1. Requirements
* **Python 3.10+**
* **Nerd Font:** For the best experience, install a [Nerd Font](https://www.nerdfonts.com/) (like ``JetBrains Mono Nerd Font``) and set it as your terminal's font.

## 2. Setup
Clone or move into your project folder and run:

### Install dependencies

```python -m pip install rich```

### Install the tool globally (Windows/Linux)
#### You have to be in the root folder of the project.

```python -m pip install --editable .```

---

## How to Use

### Basic Workflow
1. **Initialize a Project:**
   ``tracker add my-awesome-app``
2. **Start a Task:**
   ``tracker new "Implementing Auth"``
3. **Check Status**
   ``tracker current``
4. **Open the Dashboard:**
   ``tracker dash``
5. **Stop for the day:**
   ``tracker stop``

### Command Reference
| Command | Description |
| :--- | :--- |
| ``tracker add <name>`` | Create a new project or switch to an existing one. |
| ``tracker list`` | Show all registered projects and their paths. |
| ``tracker new <task>`` | Stop current task and start a new one. |
| ``tracker continue`` | Choose from the last 5 tasks to resume. |
| ``tracker total`` | View a progress bar and total hours for the active project. |
| ``tracker dash`` | Open the simple live-updating UI. |

---

## Maintenance & Deletion

### Resetting the Database
If you want to wipe all your history and start fresh, delete the hidden database file in your user folder:
* ``**Windows:**`` !!del $HOME\.time_tracker.db!!
* ``**Linux/macOS:**`` !!rm ~/.time_tracker.db!!

### Uninstalling the CLI
To remove the ``tracker`` command from your system:
``bash
python -m pip uninstall my-tracker -y
``

---

### Project Structure
* ``tracker.py``: The core logic, database management, and Rich UI.
* ``setup.py``: Configuration for the !!pip!! installation and entry points.
* ``README.md``: This guide.

---

### Customization
You can change your **Daily Goal** (currently set to 8 hours) by editing the ``goal_seconds`` variable in ``tracker.py`` inside the ``show_fancy_total`` function.
___
<p align="center">
  <img src="https://i.imgur.com/f12Lbyq.gif" width="100" height="100"/>
  <p align="center">Happy time tracking and programming.</p>
</p>


