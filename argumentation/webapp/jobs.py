"""Bounded in-memory experiment jobs with instance-local, synchronized state."""

from copy import deepcopy
import logging
import threading
from typing import Callable
import uuid
from argumentation.experiments import run_experiments
from .validation import ExperimentRequest, JsonObject

LOGGER = logging.getLogger(__name__)


class ExperimentJobs:
    """One active job per app; retain at most max_jobs results in creation order.

    Inject a runner for deterministic lifecycle tests. Copy snapshots so API
    consumers cannot mutate the manager's stored evidence.
    """

    def __init__(self, max_jobs: int = 5, runner: Callable = run_experiments):
        if max_jobs < 1:
            raise ValueError("max_jobs must be positive.")
        self._max_jobs = max_jobs
        self._runner = runner
        self._jobs: dict[str, JsonObject] = {}
        self._lock = threading.Lock()

    def start(self, request: ExperimentRequest) -> JsonObject:
        with self._lock:
            if any(job["status"] == "running" for job in self._jobs.values()):
                raise ValueError("An experiment is already running. Wait for it to finish.")
            if len(self._jobs) >= self._max_jobs:
                del self._jobs[next(iter(self._jobs))]
            job_id = uuid.uuid4().hex
            self._jobs[job_id] = {
                "status": "running",
                "done": 0,
                "total": request.count * len(request.probabilities),
            }
        threading.Thread(
            target=self._run,
            args=(job_id, request),
            daemon=True,
            name=f"experiment-{job_id[:8]}",
        ).start()
        return {"job_id": job_id}

    def get(self, job_id: str) -> JsonObject | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return deepcopy(job) if job is not None else None

    def _run(self, job_id: str, request: ExperimentRequest) -> None:
        def progress(done: int, total: int) -> None:
            with self._lock:
                self._jobs[job_id].update(done=done, total=total)

        try:
            result = self._runner(
                request.count,
                request.probabilities,
                request.seed,
                request.self_attacks,
                progress,
            )
            with self._lock:
                self._jobs[job_id].update(
                    status="completed",
                    result=result,
                    done=request.count * len(request.probabilities),
                )
        except Exception:
            LOGGER.exception("Experiment job %s failed", job_id)
            with self._lock:
                self._jobs[job_id].update(
                    status="failed",
                    error="Experiment failed. Check the server log for details.",
                )
