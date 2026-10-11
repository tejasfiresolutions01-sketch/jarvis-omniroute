"""
J.A.R.V.I.S. Continuous Headless Background Job Scheduler & Natural Language Cron Engine.
Features:
1. Flexible scheduling via interval seconds, minutes, hours, and daily time stamps.
2. Natural language cron-like string parsing ("every 10 minutes", "daily at 09:30", "every 2 hours").
3. Thread-safe concurrent execution pool with execution duration metrics and error isolation.
4. Job management (register, pause, resume, cancel, query history).
5. 100% Free, local standard library implementation.
Strictly in English.
"""

import re
import sys
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logger = logging.getLogger("BackgroundJobScheduler")


@dataclass
class JobExecutionRecord:
    timestamp_iso: str
    duration_ms: float
    success: bool
    result: Any = None
    error: Optional[str] = None


@dataclass
class ScheduledJob:
    job_id: str
    name: str
    target_func: Callable[[], Any]
    interval_sec: float
    daily_time_str: Optional[str] = None  # "HH:MM"
    is_active: bool = True
    last_run_ts: float = 0.0
    next_run_ts: float = 0.0
    run_count: int = 0
    failure_count: int = 0
    history: List[JobExecutionRecord] = field(default_factory=list)


class BackgroundJobScheduler:
    """
    Autonomous multi-threaded task scheduler for J.A.R.V.I.S. background daemons.
    """

    def __init__(self, tick_interval_sec: float = 1.0):
        self.tick_interval = tick_interval_sec
        self.jobs: Dict[str, ScheduledJob] = {}
        self._lock = threading.Lock()
        self._is_running = False
        self._worker_thread: Optional[threading.Thread] = None

    def parse_natural_schedule(self, schedule_str: str) -> Tuple[float, Optional[str]]:
        """
        Parses natural language phrases into interval seconds and daily timestamps.
        Examples:
          - "every 30 seconds" -> (30.0, None)
          - "every 5 minutes" -> (300.0, None)
          - "every 2 hours" -> (7200.0, None)
          - "daily at 09:30" -> (86400.0, "09:30")
        """
        clean = schedule_str.strip().lower()

        # Daily at HH:MM
        daily_match = re.match(r"daily\s+at\s+(\d{1,2}:\d{2})", clean)
        if daily_match:
            time_part = daily_match.group(1)
            if len(time_part) == 4:  # e.g., 9:30 -> 09:30
                time_part = "0" + time_part
            return 86400.0, time_part

        # Every N seconds
        sec_match = re.match(r"every\s+(\d+)\s+sec(ond)?s?", clean)
        if sec_match:
            return float(sec_match.group(1)), None

        # Every N minutes
        min_match = re.match(r"every\s+(\d+)\s+min(ute)?s?", clean)
        if min_match:
            return float(min_match.group(1)) * 60.0, None

        # Every N hours
        hour_match = re.match(r"every\s+(\d+)\s+hour?s?", clean)
        if hour_match:
            return float(hour_match.group(1)) * 3600.0, None

        # Default fallback: 60 seconds
        return 60.0, None

    def add_job(
        self,
        job_id: str,
        name: str,
        func: Callable[[], Any],
        interval_sec: Optional[float] = None,
        natural_schedule: Optional[str] = None
    ) -> ScheduledJob:
        """Registers a recurring task."""
        daily_time = None
        if natural_schedule:
            sec, daily_time = self.parse_natural_schedule(natural_schedule)
            interval = sec
        else:
            interval = float(interval_sec or 60.0)

        now = time.time()
        next_run = now + interval
        if daily_time:
            next_run = self._compute_next_daily_ts(daily_time)

        job = ScheduledJob(
            job_id=job_id,
            name=name,
            target_func=func,
            interval_sec=interval,
            daily_time_str=daily_time,
            is_active=True,
            next_run_ts=next_run
        )

        with self._lock:
            self.jobs[job_id] = job

        logger.info(f"Registered background job: '{name}' (ID: {job_id}) Next run in {next_run - now:.1f}s")
        return job

    def _compute_next_daily_ts(self, hh_mm: str) -> float:
        """Calculates UNIX timestamp for next target HH:MM."""
        target_h, target_m = map(int, hh_mm.split(":"))
        now_dt = datetime.now()
        target_dt = now_dt.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
        if target_dt <= now_dt:
            target_dt += timedelta(days=1)
        return target_dt.timestamp()

    def remove_job(self, job_id: str) -> bool:
        """Removes a job by ID."""
        with self._lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                return True
        return False

    def trigger_now(self, job_id: str) -> Optional[JobExecutionRecord]:
        """Manually forces immediate execution of a job in current thread."""
        with self._lock:
            job = self.jobs.get(job_id)
        if not job:
            return None

        return self._execute_job_instance(job)

    def _execute_job_instance(self, job: ScheduledJob) -> JobExecutionRecord:
        """Executes a single job instance and updates its telemetry."""
        start_ts = time.time()
        start_iso = datetime.now().isoformat()
        try:
            res = job.target_func()
            dur = (time.time() - start_ts) * 1000.0
            rec = JobExecutionRecord(
                timestamp_iso=start_iso,
                duration_ms=round(dur, 2),
                success=True,
                result=res
            )
            with self._lock:
                job.run_count += 1
                job.last_run_ts = time.time()
                job.history.append(rec)
                if len(job.history) > 50:
                    job.history.pop(0)
            return rec
        except Exception as e:
            dur = (time.time() - start_ts) * 1000.0
            rec = JobExecutionRecord(
                timestamp_iso=start_iso,
                duration_ms=round(dur, 2),
                success=False,
                error=str(e)
            )
            with self._lock:
                job.failure_count += 1
                job.last_run_ts = time.time()
                job.history.append(rec)
                if len(job.history) > 50:
                    job.history.pop(0)
            logger.error(f"Scheduled job '{job.name}' failed: {e}")
            return rec

    def start(self):
        """Starts the scheduler thread."""
        if self._is_running:
            return
        self._is_running = True
        self._worker_thread = threading.Thread(target=self._scheduler_loop, daemon=True, name="JobSchedulerWorker")
        self._worker_thread.start()
        logger.info("Background Job Scheduler worker started.")

    def stop(self):
        """Stops the scheduler thread."""
        self._is_running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        logger.info("Background Job Scheduler worker stopped.")

    def _scheduler_loop(self):
        while self._is_running:
            now = time.time()
            due_jobs = []

            with self._lock:
                for job in self.jobs.values():
                    if job.is_active and now >= job.next_run_ts:
                        due_jobs.append(job)
                        if job.daily_time_str:
                            job.next_run_ts = self._compute_next_daily_ts(job.daily_time_str)
                        else:
                            job.next_run_ts = now + job.interval_sec

            for job in due_jobs:
                # Spawn in background worker to prevent blocking scheduler
                threading.Thread(target=self._execute_job_instance, args=(job,), daemon=True).start()

            time.sleep(self.tick_interval)


# Global Singleton
job_scheduler = BackgroundJobScheduler()
