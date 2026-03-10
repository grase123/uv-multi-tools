# uv-multi-tools — Несколько CLI-инструментов в одном проекте

## Обзор

Учебный проект, демонстрирующий как организовать **несколько CLI-инструментов
из разных Python-пакетов** в одном репозитории с общей разделяемой библиотекой.
Все инструменты устанавливаются одной командой и живут **только внутри venv** —
глобально не видны.

| Команда        | Пакет / Модуль         | Назначение                                          |
|----------------|------------------------|-----------------------------------------------------|
| `greeter`      | `mytools.greeter`      | Генерирует приветствия (rich-вывод или JSON)         |
| `orchestrator` | `mytools.orchestrator` | Вызывает `greeter` через subprocess, сводит в таблицу|
| `sysinfo`      | `projtool.sysinfo`     | Показывает информацию о системе и окружении          |

Все три инструмента используют общий класс `UI` из `mytools.tools` для
единообразного стилизованного вывода в терминал.

---

## Структура проекта

```
uv-multi-tools/
├── pyproject.toml                # единый манифест для всех пакетов
├── README.md
└── src/
    ├── mytools/                  # пакет #1 — основные инструменты
    │   ├── __init__.py           # ре-экспорт UI для удобства
    │   ├── greeter.py            # CLI: greeter
    │   ├── orchestrator.py       # CLI: orchestrator
    │   └── tools/                # разделяемая библиотека
    │       ├── __init__.py       # экспортирует UI
    │       └── ui.py             # класс UI (Rich-обёртка)
    └── projtool/                 # пакет #2 — отдельный namespace
        ├── __init__.py
        └── sysinfo.py            # CLI: sysinfo
```

### Ключевая особенность: два пакета — один проект

В каталоге `src/` лежат **два независимых Python-пакета**: `mytools` и `projtool`.
Они имеют разные namespace'ы, но устанавливаются из одного `pyproject.toml`.
Пакет `projtool` **импортирует** общую библиотеку из `mytools.tools` —
это кросс-пакетный импорт внутри одного проекта.

---

## Архитектурные решения и их обоснование

### 1. Два пакета в одном wheel через hatchling

По умолчанию hatchling ищет один пакет, совпадающий по имени с проектом.
Чтобы включить оба пакета (`mytools` и `projtool`) в один wheel, нужна
явная настройка:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/mytools", "src/projtool"]
```

Без этой строки `projtool` **не попадёт** в собранный пакет и команда
`sysinfo` не будет работать после установки.

### 2. Разделяемая библиотека `mytools.tools`

Подпакет `mytools/tools/` содержит общий код, который используется
всеми инструментами. Сейчас там один модуль `ui.py` с классом `UI`,
но предполагается расширение (логирование, конфигурация и т.д.).

Цепочка экспортов:

```
mytools/tools/ui.py          — определяет класс UI
mytools/tools/__init__.py    — from mytools.tools.ui import UI
mytools/__init__.py           — from mytools.tools import UI (ре-экспорт)
```

Это даёт два рабочих варианта импорта:

```python
# Предпочтительный — явный путь к библиотеке
from mytools.tools import UI

# Короткий — через ре-экспорт корневого пакета
from mytools import UI
```

### 3. Кросс-пакетный импорт

Модуль `projtool.sysinfo` импортирует `UI` из другого пакета:

```python
# projtool/sysinfo.py
from mytools.tools import UI
```

Это работает потому что оба пакета устанавливаются в один и тот же venv
из одного `pyproject.toml`. Python видит оба пакета в `site-packages`
и кросс-импорт разрешается штатно.

### 4. Межпроцессное взаимодействие инструментов

`orchestrator` вызывает `greeter` **как внешний процесс**, а не через
прямой import. Это сознательное решение:

```
orchestrator greet-all Alice Bob
    │
    ├──▶ subprocess: greeter Alice --style casual --json
    │    └──▶ stdout: {"name":"Alice","style":"casual","message":"..."}
    │
    └──▶ subprocess: greeter Bob --style casual --json
         └──▶ stdout: {"name":"Bob","style":"casual","message":"..."}
```

Ключевые элементы паттерна:

- **`shutil.which("greeter")`** — находит исполняемый файл в `PATH`
  текущего venv. Если greeter не установлен — ранняя ошибка.
- **Флаг `--json`** — переключает greeter с rich-вывода на чистый JSON,
  пригодный для машинного парсинга.
- **`json.loads(stdout)`** — структурированный контракт между процессами.

Такая архитектура даёт чистую границу: orchestrator ничего не знает
о внутреннем устройстве greeter, общение идёт через stdin/stdout.

### 5. Единый класс UI

Все инструменты создают свой экземпляр `UI` с уникальным `app_name`:

```python
ui = UI(app_name="greeter")      # в greeter.py
ui = UI(app_name="orchestrator") # в orchestrator.py
ui = UI(app_name="sysinfo")      # в sysinfo.py
```

`app_name` используется как префикс в сообщениях об ошибках и info-строках.
Стили (цвета рамок, формат ошибок) одинаковы для всех — если нужно поменять
дизайн, правится один файл `tools/ui.py`.

---

## Установка

### Вариант A: `uv sync` (рекомендуется)

```bash
cd uv-multi-tools
uv sync
source .venv/bin/activate      # Linux / macOS
# или
.venv\Scripts\activate         # Windows
```

### Вариант B: `uv pip install -e .`

```bash
cd uv-multi-tools
uv venv
uv pip install -e .
source .venv/bin/activate      # Linux / macOS
# или
.venv\Scripts\activate         # Windows
```

### Вариант C: `uv tool install` (глобальный инструмент)

```bash
cd uv-multi-tools
uv tool install -e .
```

Инструменты (`greeter`, `orchestrator`, `sysinfo`) станут доступны глобально
в изолированном venv, управляемом `uv tool`.

### Разница между вариантами

**`uv sync`** — декларативный подход. Сам создаёт venv, генерирует `uv.lock`
с точными версиями зависимостей, удаляет лишние пакеты из venv. Lock-файл
коммитится в git — у всей команды идентичное окружение.

**`uv pip install -e .`** — императивный подход. Требует готовый venv, не создаёт
lock-файл, не удаляет лишнее. Подходит для экспериментов и добавления пакета
в существующее окружение.

**`uv tool install -e .`** — устанавливает инструменты глобально в изолированный venv,
управляемый `uv`. Команды доступны из любого каталога без активации venv.

Флаг `-e` (editable) означает, что изменения в исходниках **мгновенно**
подхватываются без переустановки.

---

## Использование

### greeter

```bash
# Rich-вывод в стилизованной панели
greeter Alice --style pirate

# JSON-вывод для машинного потребления
greeter Bob --style formal --json

# По умолчанию: casual стиль, имя "World"
greeter
```

Доступные стили: `casual`, `formal`, `pirate`.

### orchestrator

```bash
# Поприветствовать несколько человек — вызывает greeter для каждого имени
orchestrator greet-all Alice Bob Charlie --style pirate

# Проверить что greeter доступен в venv
orchestrator check
```

### sysinfo

```bash
# Базовая информация о системе
sysinfo show

# Расширенная информация (venv, рабочий каталог)
sysinfo show --verbose

# Добавить переменные окружения
sysinfo show --verbose --env

# Быстрая проверка работоспособности
sysinfo check
```

### Проверка изоляции venv

```bash
deactivate
which greeter        # Linux/macOS → ничего
where greeter        # Windows → ничего
```

---

## Общая библиотека `mytools.tools.UI`

Все утилиты используют единый класс `UI` для вывода в терминал.
Это обёртка над `rich.console.Console` с предустановленными стилями.

```python
from mytools.tools import UI

ui = UI(app_name="mytool")

ui.panel("Hello!", title="Greeting")   # панель с циановой рамкой
ui.success("All done")                 # зелёный текст
ui.error("Something broke")            # "mytool: error: Something broke" (красный)
ui.info("Processing...")               # "mytool: Processing..." (синий)
```

Методы для составных объектов:

```python
# Создать стилизованную таблицу
table = ui.table(
    title="Results",
    columns=[("Name", "cyan bold"), ("Value", "green")]
)
table.add_row("Python", "3.12")
ui.print(table)
```

### API класса UI

| Метод                        | Описание                                               |
|------------------------------|--------------------------------------------------------|
| `panel(text, title="")`      | Rich-панель со стилизованной рамкой                    |
| `success(text)`              | Зелёное сообщение об успехе                            |
| `error(text)`                | Красное сообщение с префиксом `app_name: error:`       |
| `info(text)`                 | Синее информационное сообщение с префиксом `app_name:` |
| `table(title, columns)`      | Создаёт Rich Table; `columns` — список `(header, style)` |
| `print(renderable)`          | Прокси к `Console.print` для любого Rich-объекта       |

### Цветовая схема

| Константа       | Значение       | Где используется                  |
|-----------------|----------------|-----------------------------------|
| `BORDER_STYLE`  | `cyan`         | Рамки панелей                     |
| `TITLE_STYLE`   | `bold green`   | Заголовки панелей                 |
| `ERROR_STYLE`   | `bold red`     | Сообщения об ошибках              |
| `SUCCESS_STYLE` | `green`        | Сообщения об успехе               |
| `INFO_STYLE`    | `bold blue`    | Информационные сообщения          |

---

## pyproject.toml — разбор ключевых секций

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

Зависимости минимальны: `typer` для CLI-фреймворка, `rich` для стилизованного
вывода (typer сам зависит от rich, но мы фиксируем версию явно).

```toml
[project.scripts]
greeter = "mytools.greeter:app"
orchestrator = "mytools.orchestrator:app"
sysinfo = "projtool.sysinfo:app"
```

Три entry point'а, причём `sysinfo` указывает на модуль из **другого пакета**
(`projtool`). Это работает потому что hatchling включает оба пакета в wheel.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mytools", "src/projtool"]
```

**Критическая секция.** Без `packages = [...]` hatchling включит только `mytools`
(по имени проекта), и `projtool` окажется за бортом. Пути указываются
относительно корня проекта и включают `src/` префикс.

---

## Добавление новых инструментов

### В существующий пакет `mytools`

1. Создать `src/mytools/new_tool.py` с `app = typer.Typer(...)`.
2. Использовать общий UI: `from mytools.tools import UI`.
3. Добавить entry point в `pyproject.toml`:
   ```toml
   [project.scripts]
   new-tool = "mytools.new_tool:app"
   ```
4. Переустановить: `uv sync` или `uv pip install -e .`.

### В новый пакет (новый namespace)

1. Создать каталог `src/newpkg/` с `__init__.py` и модулем.
2. Импортировать общие утилиты: `from mytools.tools import UI`.
3. Добавить пакет в hatchling:
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/mytools", "src/projtool", "src/newpkg"]
   ```
4. Добавить entry point и переустановить.

### Расширение общей библиотеки `tools`

Чтобы добавить новый модуль в `mytools/tools/`:

1. Создать файл, например `src/mytools/tools/config.py`.
2. Обновить `src/mytools/tools/__init__.py`:
   ```python
   from mytools.tools.ui import UI
   from mytools.tools.config import Config

   __all__ = ["UI", "Config"]
   ```
3. Все пакеты (`mytools`, `projtool`) получат доступ через `from mytools.tools import Config`.

---

## Технологический стек

| Компонент         | Технология        | Версия    |
|-------------------|-------------------|-----------|
| Язык              | Python            | >= 3.11   |
| Менеджер пакетов  | uv                | —         |
| Build backend     | hatchling         | —         |
| CLI framework     | Typer             | >= 0.15   |
| Терминальный вывод| Rich              | >= 13.0   |
| Layout            | src-layout        | —         |
