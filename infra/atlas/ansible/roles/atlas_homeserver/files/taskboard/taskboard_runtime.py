import datetime as dt
import json
import os
import subprocess
import threading

TASK_LOCK = threading.RLock()
STATE = {
    "last_sync_attempt_at": None,
    "last_sync_at": None,
    "last_sync_error": None,
}


class TaskCommandError(RuntimeError):
    def __init__(self, args, returncode, stdout, stderr):
        self.args_run = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        message = stderr.strip() or stdout.strip() or f"task exited {returncode}"
        super().__init__(message)


def iso_now():
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def task_base_args():
    return [
        "rc.confirmation=no",
        "rc.color=off",
        "rc.verbose=default,-override",
        "rc.json.array=on",
    ]


def run_task(args, allow_failure=False):
    command = [os.environ.get("TASKBOARD_TASK_BIN", "task"), *task_base_args(), *args]
    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )
    if result.returncode != 0 and not allow_failure:
        raise TaskCommandError(args, result.returncode, result.stdout, result.stderr)
    return result


def parse_export(stdout):
    stripped = stdout.strip()
    if not stripped:
        return []
    start = stripped.find("[")
    if start < 0:
        return []
    return json.loads(stripped[start:])


def sync_tasks(allow_failure=False):
    STATE["last_sync_attempt_at"] = iso_now()
    if os.environ.get("TASKBOARD_SYNC_ENABLED", "1").lower() in {"0", "false", "no", "off"}:
        STATE["last_sync_at"] = iso_now()
        STATE["last_sync_error"] = None
        return
    try:
        result = run_task(["sync"], allow_failure=True)
    except Exception as error:
        STATE["last_sync_error"] = str(error) or error.__class__.__name__
        raise
    if result.returncode == 0:
        STATE["last_sync_at"] = iso_now()
        STATE["last_sync_error"] = None
        return

    message = result.stderr.strip() or result.stdout.strip() or "task sync failed"
    STATE["last_sync_error"] = message
    if not allow_failure:
        raise TaskCommandError(["sync"], result.returncode, result.stdout, result.stderr)


def export_tasks():
    pending = parse_export(run_task(["status:pending", "export"]).stdout)

    done_days = int(os.environ.get("TASKBOARD_DONE_DAYS", "14"))
    cutoff = (dt.datetime.now() - dt.timedelta(days=done_days)).strftime("%Y-%m-%d")
    completed = parse_export(run_task(["status:completed", f"end.after:{cutoff}", "export"]).stdout)
    tasks = {}
    for task in pending + completed:
        if task.get("uuid"):
            tasks[task["uuid"]] = task
    return list(tasks.values())


def export_task(uuid):
    result = run_task([uuid, "export"], allow_failure=True)
    if result.returncode != 0:
        return None
    tasks = parse_export(result.stdout)
    return tasks[0] if tasks else None
