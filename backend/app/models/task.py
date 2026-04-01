"""
Task Status Management
Tracks long-running tasks (like graph building) with disk persistence.
Tasks survive backend restarts — stored in uploads/tasks.json.
"""

import json
import logging
import os
import threading
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Persist tasks next to the uploads folder so they survive restarts
_TASKS_FILE = os.path.join(os.path.dirname(__file__), "../../uploads/tasks.json")


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Task data class"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0
    message: str = ""
    result: Optional[Dict] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    progress_detail: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.progress,
            "message": self.message,
            "progress_detail": self.progress_detail,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Task":
        return cls(
            task_id=d["task_id"],
            task_type=d["task_type"],
            status=TaskStatus(d["status"]),
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
            progress=d.get("progress", 0),
            message=d.get("message", ""),
            result=d.get("result"),
            error=d.get("error"),
            metadata=d.get("metadata", {}),
            progress_detail=d.get("progress_detail", {}),
        )


class TaskManager:
    """
    Thread-safe task manager with disk persistence.
    Tasks are saved to uploads/tasks.json on every write so they survive
    backend restarts (important for long LLM calls that can take 30+ minutes).
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Task] = {}
                    cls._instance._task_lock = threading.Lock()
                    cls._instance._load_from_disk()
        return cls._instance

    # ------------------------------------------------------------------
    # Disk persistence
    # ------------------------------------------------------------------

    def _load_from_disk(self):
        """Load persisted tasks from disk on startup."""
        path = os.path.abspath(_TASKS_FILE)
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data.values():
                try:
                    task = Task.from_dict(d)
                    self._tasks[task.task_id] = task
                except Exception as e:
                    logger.warning(f"Skipping corrupt task record: {e}")
            logger.info(f"TaskManager: loaded {len(self._tasks)} tasks from disk")
        except Exception as e:
            logger.warning(f"TaskManager: could not load tasks from disk: {e}")

    def _save_to_disk(self):
        """Write all tasks to disk. Called inside _task_lock."""
        path = os.path.abspath(_TASKS_FILE)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            data = {tid: task.to_dict() for tid, task in self._tasks.items()}
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, path)  # atomic on POSIX
        except Exception as e:
            logger.warning(f"TaskManager: could not save tasks to disk: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_task(self, task_type: str, metadata: Optional[Dict] = None) -> str:
        task_id = str(uuid.uuid4())
        now = datetime.now()
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        with self._task_lock:
            self._tasks[task_id] = task
            self._save_to_disk()
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._task_lock:
            return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        progress_detail: Optional[Dict] = None,
    ):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task:
                task.updated_at = datetime.now()
                if status is not None:
                    task.status = status
                if progress is not None:
                    task.progress = progress
                if message is not None:
                    task.message = message
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                if progress_detail is not None:
                    task.progress_detail = progress_detail
                self._save_to_disk()

    def complete_task(self, task_id: str, result: Dict):
        self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message="Task completed",
            result=result,
        )

    def fail_task(self, task_id: str, error: str):
        self.update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="Task failed",
            error=error,
        )

    def list_tasks(self, task_type: Optional[str] = None) -> list:
        with self._task_lock:
            tasks = list(self._tasks.values())
            if task_type:
                tasks = [t for t in tasks if t.task_type == task_type]
            return [t.to_dict() for t in sorted(tasks, key=lambda x: x.created_at, reverse=True)]

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Remove completed/failed tasks older than max_age_hours."""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        with self._task_lock:
            old_ids = [
                tid for tid, task in self._tasks.items()
                if task.created_at < cutoff
                and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            ]
            for tid in old_ids:
                del self._tasks[tid]
            if old_ids:
                self._save_to_disk()
