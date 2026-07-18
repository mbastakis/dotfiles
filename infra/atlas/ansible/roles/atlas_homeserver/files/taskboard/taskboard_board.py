import datetime as dt

import taskboard_runtime as runtime

COLUMN_ORDER = ["backlog", "ready", "doing", "waiting", "done"]
COLUMN_TITLES = {
    "backlog": "Backlog",
    "ready": "Ready",
    "doing": "Doing",
    "waiting": "Waiting",
    "done": "Done",
}


def parse_task_date(value):
    if not value:
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None


def compact_task(task):
    tags = task.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    dependencies = task.get("depends") or []
    if not isinstance(dependencies, list):
        dependencies = []
    return {
        "uuid": task.get("uuid"),
        "description": task.get("description", ""),
        "status": task.get("status", ""),
        "project": task.get("project", ""),
        "priority": task.get("priority", ""),
        "tags": tags,
        "due": task.get("due", ""),
        "wait": task.get("wait", ""),
        "scheduled": task.get("scheduled", ""),
        "entry": task.get("entry", ""),
        "modified": task.get("modified", ""),
        "end": task.get("end", ""),
        "start": task.get("start", ""),
        "urgency": task.get("urgency", 0),
        "annotations": task.get("annotations") or [],
        "linear_id": task.get("linear_id", ""),
        "linear_url": task.get("linear_url", ""),
        "depends": dependencies,
        "recur": task.get("recur", ""),
        "until": task.get("until", ""),
        "parent": task.get("parent", ""),
    }


def task_column(task):
    status = task.get("status")
    tags = set(task.get("tags") or [])
    if status == "completed":
        return "done"
    if task.get("start"):
        return "doing"
    if status == "waiting" or "waiting" in tags or task.get("wait") or task.get("blocked"):
        return "waiting"
    if "next" in tags:
        return "ready"
    return "backlog"


def task_sort_key(task):
    due = parse_task_date(task.get("due")) or dt.datetime.max
    entry = parse_task_date(task.get("entry")) or dt.datetime.max
    urgency = task.get("urgency") or 0
    return (due, -float(urgency), entry)


def enrich_dependencies(tasks, fetched_dependencies=None):
    tasks_by_uuid = {task["uuid"].lower(): task for task in tasks}
    displayed_uuids = set(tasks_by_uuid)
    tasks_by_uuid.update(fetched_dependencies or {})
    dependents = {uuid: [] for uuid in displayed_uuids}

    for task in tasks:
        if task.get("status") == "completed":
            continue
        dependent = {
            "uuid": task["uuid"],
            "description": task.get("description") or task["uuid"],
            "project": task.get("project", ""),
        }
        for dependency_uuid in task.get("depends") or []:
            dependency_key = str(dependency_uuid).lower()
            if dependency_key in dependents:
                dependents[dependency_key].append(dependent)

    for task in tasks:
        details = []
        for dependency_uuid in task.get("depends") or []:
            dependency_uuid = str(dependency_uuid)
            dependency = tasks_by_uuid.get(dependency_uuid.lower())
            status = dependency.get("status", "missing") if dependency else "missing"
            details.append(
                {
                    "uuid": dependency_uuid,
                    "description": (dependency.get("description") if dependency else None)
                    or dependency_uuid,
                    "project": dependency.get("project", "") if dependency else "",
                    "status": status,
                    "blocking": status in {"pending", "waiting"},
                    "resolved": status in {"completed", "deleted"},
                }
            )
        task["dependency_details"] = details
        task["dependent_tasks"] = dependents[task["uuid"].lower()]
        task["blocked"] = any(dependency["blocking"] for dependency in details)


def build_board(sync=True):
    with runtime.TASK_LOCK:
        if sync:
            runtime.sync_tasks(allow_failure=True)
        tasks = [compact_task(task) for task in runtime.export_tasks() if task.get("uuid")]
        displayed_uuids = {task["uuid"].lower() for task in tasks}
        dependency_uuids = {
            str(dependency).lower() for task in tasks for dependency in task.get("depends") or []
        }
        fetched_dependencies = {}
        for uuid in dependency_uuids - displayed_uuids:
            dependency = runtime.export_task(uuid)
            if dependency and dependency.get("uuid"):
                fetched_dependencies[uuid] = compact_task(dependency)

    enrich_dependencies(tasks, fetched_dependencies)
    grouped = {column: [] for column in COLUMN_ORDER}
    for task in tasks:
        grouped[task_column(task)].append(task)

    for column in COLUMN_ORDER:
        grouped[column].sort(key=task_sort_key)

    return {
        "columns": [
            {"id": column, "title": COLUMN_TITLES[column], "tasks": grouped[column]}
            for column in COLUMN_ORDER
        ],
        "last_sync_attempt_at": runtime.STATE["last_sync_attempt_at"],
        "last_sync_at": runtime.STATE["last_sync_at"],
        "last_sync_error": runtime.STATE["last_sync_error"],
        "generated_at": runtime.iso_now(),
    }
