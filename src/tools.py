import re
from datetime import date
from typing import Any

import aiosqlite

from src import db as db_module
from src.config import Config
from src.state import UserState


TOOLS = [
    {
        "name": "save_note",
        "description": "Сохранить заметку в базе данных, при необходимости привязав её к проекту.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Текст заметки."},
                "project_slug": {"type": "string", "description": "Slug проекта для привязки заметки."},
            },
            "required": ["content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "save_idea",
        "description": "Сохранить идею в базе данных, при необходимости привязав её к проекту.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Текст идеи."},
                "project_slug": {"type": "string", "description": "Slug проекта для привязки идеи."},
            },
            "required": ["content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "save_deadline",
        "description": "Сохранить дедлайн с датой в формате YYYY-MM-DD и необязательной привязкой к проекту.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Название дедлайна."},
                "due_date": {
                    "type": "string",
                    "description": "Дата дедлайна в формате ISO YYYY-MM-DD.",
                },
                "project_slug": {"type": "string", "description": "Slug проекта для привязки дедлайна."},
            },
            "required": ["title", "due_date"],
            "additionalProperties": False,
        },
    },
    {
        "name": "save_homework",
        "description": "Сохранить домашнее задание с датой, курсом, описанием и необязательной привязкой к проекту.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Название задания."},
                "due_date": {
                    "type": "string",
                    "description": "Дата сдачи в формате ISO YYYY-MM-DD.",
                },
                "course": {"type": "string", "description": "Название курса."},
                "description": {"type": "string", "description": "Описание задания."},
                "project_slug": {"type": "string", "description": "Slug проекта для привязки задания."},
            },
            "required": ["title", "due_date"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_items",
        "description": "Показать список заметок, идей, дедлайнов или домашних заданий.",
        "input_schema": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["notes", "ideas", "deadlines", "homework"],
                    "description": "Тип записей для вывода.",
                },
                "project_slug": {"type": "string", "description": "Slug проекта для фильтрации."},
                "status": {"type": "string", "description": "Статус для дедлайнов или домашних заданий."},
                "limit": {"type": "integer", "description": "Максимум записей для вывода.", "default": 10},
            },
            "required": ["type"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search",
        "description": "Искать по заметкам, идеям или сразу по обоим типам записей.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос."},
                "type": {
                    "type": "string",
                    "enum": ["notes", "ideas", "all"],
                    "description": "Где выполнять поиск.",
                    "default": "all",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "create_project",
        "description": "Создать новый проект с именем, slug и необязательным описанием.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Название проекта."},
                "slug": {"type": "string", "description": "Уникальный slug проекта."},
                "description": {"type": "string", "description": "Описание проекта."},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "set_active_project",
        "description": "Сделать проект активным по его slug.",
        "input_schema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Slug проекта."},
            },
            "required": ["slug"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_projects",
        "description": "Показать список проектов, при необходимости включая архивные.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_archived": {
                    "type": "boolean",
                    "description": "Включать ли архивные проекты в список.",
                    "default": False,
                },
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_status",
        "description": "Показать краткую сводку по активным дедлайнам, заданиям, заметкам и идеям.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
]


def _truncate_text(text: str, limit: int = 60) -> str:
    return text[:limit]


def _slugify(name: str) -> str:
    slug = name.strip().lower().replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "project"


async def _resolve_project(
    db: aiosqlite.Connection,
    user_state: UserState,
    project_slug: str | None,
) -> tuple[int | None, str | None]:
    """Return (project_id, error_string_or_None).

    Second element is None on success, a Russian error string on failure.
    """
    if project_slug is None:
        return user_state.active_project_id, None

    project = await db_module.get_project_by_slug(db, project_slug)
    if project is None:
        return None, "Проект не найден: {}".format(project_slug)
    return int(project["id"]), None


async def _count_rows(
    db: aiosqlite.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> int:
    cursor = await db.execute(query, params)
    row = await cursor.fetchone()
    await cursor.close()
    return int(row[0]) if row else 0


def _format_list_items(item_type: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return "Записей не найдено."

    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        if item_type == "notes":
            lines.append("{}. {}".format(index, item["content"]))
        elif item_type == "ideas":
            lines.append("{}. {}".format(index, item["content"]))
        elif item_type == "deadlines":
            lines.append("{}. {} — {}".format(index, item["title"], item["due_date"]))
        else:
            lines.append("{}. {} — {}".format(index, item["title"], item["due_date"]))
    return "\n".join(lines)


def _format_search_results(results: list[tuple[str, dict[str, Any]]], query: str) -> str:
    if not results:
        return "Ничего не найдено по запросу: {}".format(query)

    lines: list[str] = []
    for index, (item_type, item) in enumerate(results, start=1):
        if item_type == "notes":
            lines.append("{}. [Заметка] {}".format(index, item["content"]))
        else:
            lines.append("{}. [Идея] {}".format(index, item["content"]))
    return "\n".join(lines)


def _format_projects(items: list[dict[str, Any]], include_archived: bool) -> str:
    if not items:
        if include_archived:
            return "Проекты не найдены."
        return "Нет активных проектов."

    lines = []
    for index, item in enumerate(items, start=1):
        status = item.get("status", "unknown")
        status_label = {"active": "активный", "archived": "архивный"}.get(status, "неизвестный")
        lines.append("{}. {} ({}) — {}".format(index, item["name"], item["slug"], status_label))
    return "\n".join(lines)


async def execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    db: aiosqlite.Connection,
    config: Config,
    user_state: UserState,
) -> str:
    del config

    if tool_name == "save_note":
        project_id, error = await _resolve_project(db, user_state, tool_input.get("project_slug"))
        if error is not None:
            return error
        content = str(tool_input["content"])
        await db_module.create_note(db, content=content, project_id=project_id, source="text")
        return "Заметка сохранена: {}".format(_truncate_text(content))

    if tool_name == "save_idea":
        project_id, error = await _resolve_project(db, user_state, tool_input.get("project_slug"))
        if error is not None:
            return error
        content = str(tool_input["content"])
        await db_module.create_idea(db, content=content, project_id=project_id, source="text")
        return "Идея сохранена: {}".format(_truncate_text(content))

    if tool_name == "save_deadline":
        project_id, error = await _resolve_project(db, user_state, tool_input.get("project_slug"))
        if error is not None:
            return error
        title = str(tool_input["title"])
        due_date = tool_input.get("due_date")
        if due_date is not None:
            due_date = str(due_date)
            try:
                date.fromisoformat(due_date)
            except ValueError:
                due_date = None
        await db_module.create_deadline(db, title=title, due_date=due_date, project_id=project_id, source="text")
        return "Дедлайн сохранён: {} — {}".format(title, due_date)

    if tool_name == "save_homework":
        project_id, error = await _resolve_project(db, user_state, tool_input.get("project_slug"))
        if error is not None:
            return error
        title = str(tool_input["title"])
        due_date = tool_input.get("due_date")
        if due_date is not None:
            due_date = str(due_date)
            try:
                date.fromisoformat(due_date)
            except ValueError:
                due_date = None
        await db_module.create_homework(
            db,
            title=title,
            due_date=due_date,
            course=tool_input.get("course"),
            project_id=project_id,
            description=tool_input.get("description"),
            source="text",
        )
        return "Задание сохранено: {} — {}".format(title, due_date)

    if tool_name == "list_items":
        item_type = str(tool_input["type"])
        limit = int(tool_input.get("limit", 10))
        status = tool_input.get("status")
        project_id, error = await _resolve_project(db, user_state, tool_input.get("project_slug"))
        if error is not None:
            return error

        if item_type == "notes":
            items = await db_module.list_notes(db, project_id=project_id, limit=limit, offset=0)
        elif item_type == "ideas":
            items = await db_module.list_ideas(db, project_id=project_id, limit=limit, offset=0)
        elif item_type == "deadlines":
            items = await db_module.list_deadlines(db, status=status, project_id=project_id, limit=limit, offset=0)
        else:
            items = await db_module.list_homework(db, status=status, project_id=project_id, limit=limit, offset=0)
        return _format_list_items(item_type, items)

    if tool_name == "search":
        query = str(tool_input["query"])
        search_type = str(tool_input.get("type", "all"))

        if search_type == "notes":
            results = [("notes", item) for item in await db_module.search_notes(db, query)]
        elif search_type == "ideas":
            results = [("ideas", item) for item in await db_module.search_ideas(db, query)]
        else:
            note_results = [("notes", item) for item in await db_module.search_notes(db, query)]
            idea_results = [("ideas", item) for item in await db_module.search_ideas(db, query)]
            results = note_results + idea_results
        return _format_search_results(results, query)

    if tool_name == "create_project":
        name = str(tool_input["name"])
        slug = str(tool_input.get("slug") or _slugify(name))
        description = tool_input.get("description")
        await db_module.create_project(db, name=name, slug=slug, description=description)
        return "Проект создан: {}".format(name)

    if tool_name == "set_active_project":
        slug = str(tool_input["slug"])
        project = await db_module.get_project_by_slug(db, slug)
        if project is None:
            return "Проект не найден: {}".format(slug)
        user_state.active_project_id = int(project["id"])
        user_state.active_project_name = str(project["name"])
        return "Активный проект: {}".format(project["name"])

    if tool_name == "list_projects":
        include_archived = bool(tool_input.get("include_archived", False))
        if include_archived:
            items = await db_module.list_all_projects(db)
        else:
            items = await db_module.list_projects(db, status="active")
        return _format_projects(items, include_archived)

    if tool_name == "get_status":
        active_deadlines = await _count_rows(db, "SELECT COUNT(*) FROM deadlines WHERE status = ?", ("active",))
        pending_homework = await _count_rows(db, "SELECT COUNT(*) FROM homework WHERE status = ?", ("pending",))
        notes = await _count_rows(db, "SELECT COUNT(*) FROM notes")
        ideas = await _count_rows(db, "SELECT COUNT(*) FROM ideas")
        return (
            "Статус системы: активных дедлайнов — {}, домашних заданий к сдаче — {}, заметок — {}, идей — {}."
        ).format(active_deadlines, pending_homework, notes, ideas)

    return "Неизвестный инструмент: {}".format(tool_name)
