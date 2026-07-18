import re

import taskboard_board as board
import taskboard_runtime as runtime
from taskboard_validation import (
    MANAGED_TAGS,
    clean_date,
    clean_dependencies,
    clean_modified,
    clean_priority,
    clean_project,
    clean_tags,
    clean_text,
    require_uuid,
)


class TaskConflictError(RuntimeError):
    def __init__(self, task):
        self.current_task = task
        super().__init__(f'"{task["description"]}" changed in another Taskwarrior client')


def find_task(uuid, tasks=None):
    uuid = require_uuid(uuid)
    if tasks is None:
        tasks = runtime.export_tasks()
    for task in tasks:
        if task.get("uuid", "").lower() == uuid:
            return board.compact_task(task)
    raise ValueError("task not found")


def ensure_current(task, payload):
    expected = clean_modified(payload.get("expected_modified"))
    if task.get("modified") != expected:
        raise TaskConflictError(task)


def task_id_from_add(result):
    match = re.search(r"Created task (\d+)", result.stdout)
    if not match:
        raise runtime.TaskCommandError(
            ["add"],
            result.returncode,
            result.stdout,
            "Taskwarrior did not report the created task ID",
        )
    return match.group(1)


def command_for_column(task, column):
    uuid = require_uuid(task["uuid"])
    tags = set(task.get("tags") or [])
    active = bool(task.get("start"))
    commands = []

    if column == "done":
        if task.get("status") != "completed":
            commands.append([uuid, "done"])
        return commands

    if task.get("status") == "completed":
        commands.append([uuid, "modify", "status:pending"])

    if active and column != "doing":
        commands.append([uuid, "stop"])

    if column == "backlog":
        commands.append([uuid, "modify", "-next", "-waiting", "wait:"])
    elif column == "ready":
        commands.append([uuid, "modify", "+next", "-waiting", "wait:"])
    elif column == "doing":
        if "next" not in tags or "waiting" in tags:
            commands.append([uuid, "modify", "+next", "-waiting", "wait:"])
        if not active:
            commands.append([uuid, "start"])
    elif column == "waiting":
        commands.append([uuid, "modify", "-next", "+waiting"])
    else:
        raise ValueError("unknown board column")

    return commands


def ensure_no_dependency_cycle(uuid, dependencies, tasks):
    if uuid in dependencies:
        raise ValueError("a task cannot depend on itself")

    graph = {}
    for task in tasks:
        task_uuid = task.get("uuid", "").lower()
        if task_uuid:
            graph[task_uuid] = {str(item).lower() for item in task.get("depends") or []}
    graph[uuid] = set(dependencies)

    pending = list(dependencies)
    visited = set()
    while pending:
        dependency = pending.pop()
        if dependency == uuid:
            raise ValueError("dependency cycle detected")
        if dependency in visited:
            continue
        visited.add(dependency)
        pending.extend(graph.get(dependency, ()))


def move_task(uuid, column, payload):
    if column not in board.COLUMN_ORDER:
        raise ValueError("unknown board column")
    with runtime.TASK_LOCK:
        runtime.sync_tasks(allow_failure=True)
        task = find_task(uuid)
        ensure_current(task, payload)
        for command in command_for_column(task, column):
            runtime.run_task(command)
        runtime.sync_tasks(allow_failure=True)
    return board.build_board(sync=False)


def add_task(payload):
    description = clean_text(payload.get("description"), "description", 500)
    if not description:
        raise ValueError("description is required")

    column = clean_text(payload.get("column") or "backlog", "column", 20)
    if column not in {"backlog", "ready", "doing", "waiting"}:
        raise ValueError("new tasks can be added only to backlog, ready, doing, or waiting")

    args = ["add"]
    project = clean_project(payload.get("project"))
    priority = clean_priority(payload.get("priority"))
    due = clean_date(payload.get("due"), "due")
    tags = clean_tags(payload.get("tags"))

    if project:
        args.append(f"project:{project}")
    if priority:
        args.append(f"priority:{priority}")
    if due:
        args.append(f"due:{due}")
    args.extend(f"+{tag}" for tag in tags)
    if column in {"ready", "doing"}:
        args.append("+next")
    if column == "waiting":
        args.append("+waiting")
    args.extend(["--", description])

    with runtime.TASK_LOCK:
        runtime.sync_tasks(allow_failure=True)
        result = runtime.run_task(args)
        if column == "doing":
            match = re.search(r"Created task (\d+)", result.stdout)
            if match:
                runtime.run_task([match.group(1), "start"])
        runtime.sync_tasks(allow_failure=True)
    return board.build_board(sync=False)


def create_dependency(uuid, payload):
    uuid = require_uuid(uuid)
    description = clean_text(payload.get("description"), "description", 500)
    if not description:
        raise ValueError("description is required")

    with runtime.TASK_LOCK:
        runtime.sync_tasks(allow_failure=True)
        tasks = runtime.export_tasks()
        parent = find_task(uuid, tasks)
        ensure_current(parent, payload)
        args = ["add"]
        if parent.get("project"):
            args.append(f"project:{parent['project']}")
        args.extend(["--", description])
        result = runtime.run_task(args)
        task_id = task_id_from_add(result)
        uuid_output = runtime.run_task(["_get", f"{task_id}.uuid"]).stdout
        uuid_match = re.search(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            uuid_output,
        )
        created_uuid = uuid_match.group(0).lower() if uuid_match else ""
        try:
            created_uuid = require_uuid(created_uuid)
            dependencies = [str(item).lower() for item in parent.get("depends") or []]
            dependencies.append(created_uuid)
            runtime.run_task([uuid, "modify", f"depends:{','.join(dependencies)}"])
        except Exception:
            runtime.run_task([task_id, "delete"], allow_failure=True)
            raise
        runtime.sync_tasks(allow_failure=True)
    return {"board": board.build_board(sync=False), "created_uuid": created_uuid}


def modify_args(task, payload):
    args = []
    if "project" in payload:
        args.append(f"project:{clean_project(payload.get('project'))}")
    if "priority" in payload:
        args.append(f"priority:{clean_priority(payload.get('priority'))}")
    if "due" in payload:
        args.append(f"due:{clean_date(payload.get('due'), 'due')}")
    if "tags" in payload:
        current = set(task.get("tags") or []) - MANAGED_TAGS
        desired = set(clean_tags(payload.get("tags")))
        args.extend(f"-{tag}" for tag in sorted(current - desired))
        args.extend(f"+{tag}" for tag in sorted(desired - current))
    return args


def update_task(uuid, payload):
    uuid = require_uuid(uuid)
    args = []
    annotation = ""
    description = ""

    if "description" in payload:
        description = clean_text(payload.get("description"), "description", 500)
        if not description:
            raise ValueError("description cannot be empty")
    if "wait" in payload:
        args.append(f"wait:{clean_date(payload.get('wait'), 'wait')}")
    if "scheduled" in payload:
        args.append(f"scheduled:{clean_date(payload.get('scheduled'), 'scheduled')}")
    if "annotation" in payload:
        annotation = clean_text(payload.get("annotation"), "annotation", 2000)

    with runtime.TASK_LOCK:
        runtime.sync_tasks(allow_failure=True)
        tasks = runtime.export_tasks()
        task = find_task(uuid, tasks)
        ensure_current(task, payload)
        args.extend(modify_args(task, payload))
        if "depends" in payload:
            dependencies = clean_dependencies(payload.get("depends"))
            ensure_no_dependency_cycle(uuid, dependencies, tasks)
            args.append(f"depends:{','.join(dependencies)}")
        if description:
            args.extend(["--", description])
        if args:
            runtime.run_task([uuid, "modify", *args])
        if annotation:
            runtime.run_task([uuid, "annotate", annotation])
        runtime.sync_tasks(allow_failure=True)
    return board.build_board(sync=False)


def bulk_update(payload):
    selections = payload.get("tasks")
    changes = payload.get("changes")
    if not isinstance(selections, list) or not selections:
        raise ValueError("tasks must be a non-empty list")
    if len(selections) > 100:
        raise ValueError("at most 100 tasks can be changed at once")
    if not isinstance(changes, dict) or not changes:
        raise ValueError("changes must not be empty")
    allowed = {"project", "tags", "priority", "due", "column"}
    if set(changes) - allowed:
        raise ValueError("unsupported bulk change")
    column = clean_text(changes.get("column"), "column", 20) if "column" in changes else ""
    if column and column not in board.COLUMN_ORDER:
        raise ValueError("unknown board column")

    with runtime.TASK_LOCK:
        runtime.sync_tasks(allow_failure=True)
        exported = runtime.export_tasks()
        selected = []
        seen = set()
        for selection in selections:
            if not isinstance(selection, dict):
                raise ValueError("each selected task must include uuid and expected_modified")
            uuid = require_uuid(selection.get("uuid", ""))
            if uuid in seen:
                continue
            task = find_task(uuid, exported)
            ensure_current(task, selection)
            seen.add(uuid)
            selected.append(task)

        commands = []
        for task in selected:
            args = modify_args(task, changes)
            if args:
                commands.append([task["uuid"], "modify", *args])
            if column:
                commands.extend(command_for_column(task, column))
        if not commands:
            raise ValueError("bulk change would not modify any tasks")
        for command in commands:
            runtime.run_task(command)
        runtime.sync_tasks(allow_failure=True)
    return board.build_board(sync=False)


def delete_task(uuid, payload):
    uuid = require_uuid(uuid)
    with runtime.TASK_LOCK:
        runtime.sync_tasks(allow_failure=True)
        task = find_task(uuid)
        ensure_current(task, payload)
        runtime.run_task([uuid, "delete"])
        runtime.sync_tasks(allow_failure=True)
    return board.build_board(sync=False)


def sync_and_board():
    with runtime.TASK_LOCK:
        runtime.sync_tasks(allow_failure=False)
    return board.build_board(sync=False)
