# backend/workers/tasks.py

import threading
import time
from datetime import datetime

# In-memory task queue (simple, no external dependency)
_task_queue = []
_task_results = {}
_task_lock = threading.Lock()
_worker_running = False

def add_task(task_type: str, func, *args, **kwargs) -> int:
    """Add a task to the queue and return task ID."""
    with _task_lock:
        task_id = len(_task_queue) + 1
        _task_queue.append({
            "id": task_id,
            "type": task_type,
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "status": "pending",
            "created_at": datetime.now(),
            "result": None
        })
    return task_id

def get_task_status(task_id: int) -> dict:
    """Get the status of a task."""
    with _task_lock:
        if task_id <= len(_task_queue):
            task = _task_queue[task_id - 1]
            return {
                "id": task["id"],
                "type": task["type"],
                "status": task["status"],
                "created_at": task["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                "result": str(task["result"])[:500] if task["result"] else None
            }
    return {"error": "Task not found"}

def process_tasks():
    """Background worker that processes tasks from the queue."""
    global _worker_running
    _worker_running = True
    
    while _worker_running:
        with _task_lock:
            pending = [t for t in _task_queue if t["status"] == "pending"]
        
        for task in pending:
            with _task_lock:
                task["status"] = "running"
            
            try:
                result = task["func"](*task["args"], **task["kwargs"])
                with _task_lock:
                    task["status"] = "completed"
                    task["result"] = result
            except Exception as e:
                with _task_lock:
                    task["status"] = "failed"
                    task["result"] = str(e)
        
        time.sleep(0.5)  # Check every 500ms

def start_worker():
    """Start the background worker thread."""
    worker = threading.Thread(target=process_tasks, daemon=True)
    worker.start()
    print("✅ Background worker started")

def stop_worker():
    """Stop the background worker."""
    global _worker_running
    _worker_running = False