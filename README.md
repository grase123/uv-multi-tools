# uv-multi-tools — Multiple CLI Tools in a Single Project

## Overview

A learning project demonstrating how to organize **multiple CLI tools
from different Python packages** in a single repository with a shared library.
All tools are installed with a single command and live **only inside the venv** —
they are not visible globally.

| Command        | Package / Module       | Purpose                                              |
|----------------|------------------------|------------------------------------------------------|
| `greeter`      | `mytools.greeter`      | Generates greetings (rich output or JSON)             |
| `orchestrator` | `mytools.orchestrator` | Calls `greeter` via subprocess, displays summary table|
| `sysinfo`      | `projtool.sysinfo`     | Shows system and environment information              |

All three tools use the shared `UI` class from `mytools.tools` for
consistent styled terminal output.

---

## Project Structure

```
uv-multi-tools/
├── pyproject.toml                # single manifest for all packages
├── README.md
└── src/
    ├── mytools/                  # package #1 — main tools
    │   ├── __init__.py           # re-exports UI for convenience
    │   ├── greeter.py            # CLI: greeter
    │   ├── orchestrator.py       # CLI: orchestrator
    │   └── tools/                # shared library
    │       ├── __init__.py       # exports UI
    │       └── ui.py             # UI class (Rich wrapper)
    └── projtool/                 # package #2 — separate namespace
        ├── __init__.py
        └── sysinfo.py            # CLI: sysinfo
```

### Key Feature: Two Packages — One Project

The `src/` directory contains **two independent Python packages**: `mytools` and `projtool`.
They have different namespaces but are installed from a single `pyproject.toml`.
The `projtool` package **imports** the shared library from `mytools.tools` —
this is a cross-package import within a single project.

---

## Architectural Decisions and Rationale

### 1. Two Packages in One Wheel via Hatchling

By default, hatchling looks for a single package matching the project name.
To include both packages (`mytools` and `projtool`) in one wheel, explicit
configuration is required:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/mytools", "src/projtool"]
```

Without this line, `projtool` **will not be included** in the built package
and the `sysinfo` command will not work after installation.

### 2. Shared Library `mytools.tools`

The subpackage `mytools/tools/` contains shared code used by all tools.
Currently it has a single module `ui.py` with the `UI` class,
but is designed for extension (logging, configuration, etc.).

Export chain:

```
mytools/tools/ui.py          — defines the UI class
mytools/tools/__init__.py    — from mytools.tools.ui import UI
mytools/__init__.py           — from mytools.tools import UI (re-export)
```

This provides two working import options:

```python
# Preferred — explicit path to the library
from mytools.tools import UI

# Short — via root package re-export
from mytools import UI
```

### 3. Cross-Package Import

The `projtool.sysinfo` module imports `UI` from another package:

```python
# projtool/sysinfo.py
from mytools.tools import UI
```

This works because both packages are installed into the same venv
from a single `pyproject.toml`. Python sees both packages in `site-packages`
and the cross-import resolves normally.

### 4. Inter-Process Tool Communication

`orchestrator` calls `greeter` **as an external process**, not via
direct import. This is a deliberate design choice:

```
orchestrator greet-all Alice Bob
    │
    ├──▶ subprocess: greeter Alice --style casual --json
    │    └──▶ stdout: {"name":"Alice","style":"casual","message":"..."}
    │
    └──▶ subprocess: greeter Bob --style casual --json
         └──▶ stdout: {"name":"Bob","style":"casual","message":"..."}
```

Key elements of the pattern:

- **`shutil.which("greeter")`** — locates the executable in the current
  venv's `PATH`. If greeter is not installed — early failure.
- **`--json` flag** — switches greeter from rich output to clean JSON,
  suitable for machine parsing.
- **`json.loads(stdout)`** — structured contract between processes.

This architecture provides a clean boundary: orchestrator knows nothing
about greeter's internals, communication happens via stdin/stdout.

### 5. Unified UI Class

All tools create their own `UI` instance with a unique `app_name`:

```python
ui = UI(app_name="greeter")      # in greeter.py
ui = UI(app_name="orchestrator") # in orchestrator.py
ui = UI(app_name="sysinfo")      # in sysinfo.py
```

`app_name` is used as a prefix in error and info messages.
Styles (border colors, error formatting) are the same for all — if you need
to change the design, you edit a single file `tools/ui.py`.

---

## Installation

### Option A: `uv sync` (recommended)

```bash
cd uv-multi-tools
uv sync
source .venv/bin/activate      # Linux / macOS
# or
.venv\Scripts\activate         # Windows
```

### Option B: `uv pip install -e .`

```bash
cd uv-multi-tools
uv venv
uv pip install -e .
source .venv/bin/activate      # Linux / macOS
# or
.venv\Scripts\activate         # Windows
```

### Option C: `uv tool install` (global tool)

```bash
cd uv-multi-tools
uv tool install -e .
```

The tools (`greeter`, `orchestrator`, `sysinfo`) will become globally available
in an isolated venv managed by `uv tool`.

### Differences Between Options

**`uv sync`** — declarative approach. Creates the venv automatically, generates `uv.lock`
with pinned dependency versions, removes extra packages from the venv. The lock file
is committed to git — the entire team gets an identical environment.

**`uv pip install -e .`** — imperative approach. Requires an existing venv, does not create
a lock file, does not remove extras. Suitable for experiments and adding a package
to an existing environment.

**`uv tool install -e .`** — installs tools globally in an isolated venv managed by `uv`.
Commands are available from any directory without activating a venv.

The `-e` (editable) flag means that source code changes are **immediately**
picked up without reinstalling.

---

## Usage

### greeter

```bash
# Rich output in a styled panel
greeter Alice --style pirate

# JSON output for machine consumption
greeter Bob --style formal --json

# Defaults: casual style, name "World"
greeter
```

Available styles: `casual`, `formal`, `pirate`.

### orchestrator

```bash
# Greet multiple people — calls greeter for each name
orchestrator greet-all Alice Bob Charlie --style pirate

# Verify that greeter is available in the venv
orchestrator check
```

### sysinfo

```bash
# Basic system information
sysinfo show

# Extended information (venv, working directory)
sysinfo show --verbose

# Include environment variables
sysinfo show --verbose --env

# Quick health check
sysinfo check
```

### Verifying venv Isolation

```bash
deactivate
which greeter        # Linux/macOS → nothing
where greeter        # Windows → nothing
```

---

## Shared Library `mytools.tools.UI`

All utilities use the unified `UI` class for terminal output.
It is a wrapper around `rich.console.Console` with preset styles.

```python
from mytools.tools import UI

ui = UI(app_name="mytool")

ui.panel("Hello!", title="Greeting")   # panel with cyan border
ui.success("All done")                 # green text
ui.error("Something broke")            # "mytool: error: Something broke" (red)
ui.info("Processing...")               # "mytool: Processing..." (blue)
```

Methods for composite objects:

```python
# Create a styled table
table = ui.table(
    title="Results",
    columns=[("Name", "cyan bold"), ("Value", "green")]
)
table.add_row("Python", "3.12")
ui.print(table)
```

### UI Class API

| Method                       | Description                                            |
|------------------------------|--------------------------------------------------------|
| `panel(text, title="")`      | Rich panel with styled border                          |
| `success(text)`              | Green success message                                  |
| `error(text)`                | Red error message prefixed with `app_name: error:`     |
| `info(text)`                 | Blue informational message prefixed with `app_name:`   |
| `table(title, columns)`      | Creates a Rich Table; `columns` is a list of `(header, style)` |
| `print(renderable)`          | Proxy to `Console.print` for any Rich renderable       |

### Color Scheme

| Constant        | Value          | Used For                          |
|-----------------|----------------|-----------------------------------|
| `BORDER_STYLE`  | `cyan`         | Panel borders                     |
| `TITLE_STYLE`   | `bold green`   | Panel titles                      |
| `ERROR_STYLE`   | `bold red`     | Error messages                    |
| `SUCCESS_STYLE` | `green`        | Success messages                  |
| `INFO_STYLE`    | `bold blue`    | Informational messages            |

---

## pyproject.toml — Key Sections Explained

```toml
[project]
name = "mytools"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.15",
    "rich>=13.0",
]
```

Dependencies are minimal: `typer` for the CLI framework, `rich` for styled
output (typer itself depends on rich, but we pin the version explicitly).

```toml
[project.scripts]
greeter = "mytools.greeter:app"
orchestrator = "mytools.orchestrator:app"
sysinfo = "projtool.sysinfo:app"
```

Three entry points, where `sysinfo` points to a module from a **different package**
(`projtool`). This works because hatchling includes both packages in the wheel.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mytools", "src/projtool"]
```

**Critical section.** Without `packages = [...]`, hatchling will only include `mytools`
(matching the project name), leaving `projtool` out. Paths are specified
relative to the project root and include the `src/` prefix.

---

## Adding New Tools

### To the Existing `mytools` Package

1. Create `src/mytools/new_tool.py` with `app = typer.Typer(...)`.
2. Use the shared UI: `from mytools.tools import UI`.
3. Add an entry point in `pyproject.toml`:
   ```toml
   [project.scripts]
   new-tool = "mytools.new_tool:app"
   ```
4. Reinstall: `uv sync` or `uv pip install -e .`.

### To a New Package (new namespace)

1. Create a directory `src/newpkg/` with `__init__.py` and a module.
2. Import shared utilities: `from mytools.tools import UI`.
3. Add the package to hatchling:
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/mytools", "src/projtool", "src/newpkg"]
   ```
4. Add an entry point and reinstall.

### Extending the Shared `tools` Library

To add a new module to `mytools/tools/`:

1. Create a file, e.g. `src/mytools/tools/config.py`.
2. Update `src/mytools/tools/__init__.py`:
   ```python
   from mytools.tools.ui import UI
   from mytools.tools.config import Config

   __all__ = ["UI", "Config"]
   ```
3. All packages (`mytools`, `projtool`) gain access via `from mytools.tools import Config`.

---

## Technology Stack

| Component          | Technology        | Version   |
|--------------------|-------------------|-----------|
| Language           | Python            | >= 3.11   |
| Package manager    | uv                | —         |
| Build backend      | hatchling         | —         |
| CLI framework      | Typer             | >= 0.15   |
| Terminal output    | Rich              | >= 13.0   |
| Layout             | src-layout        | —         |
