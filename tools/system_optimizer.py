"""
J.A.R.V.I.S. Autonomous System Optimizer & Hardware Janitor.
Optimizes workstation performance by flushing process working set memory,
safely purging stale temporary files, and auditing top resource-consuming processes.
"""

import os
import gc
import time
import ctypes
from typing import Dict, Any, List, Tuple
from pathlib import Path
import psutil

class SystemOptimizer:
    """
    Stark Autonomous Maintenance Sentinel.
    Maintains workstation speed, frees RAM, and purges temporary files.
    """

    def __init__(self):
        self._kernel32 = ctypes.windll.kernel32
        self._kernel32.SetProcessWorkingSetSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t]
        self._kernel32.SetProcessWorkingSetSize.restype = ctypes.c_bool

    def flush_memory(self) -> Dict[str, Any]:
        """
        Triggers garbage collection and flushes Windows working sets to trim RAM usage.
        """
        vm_before = psutil.virtual_memory()
        ram_before_used = vm_before.used / (1024 * 1024)
        pct_before = vm_before.percent

        # 1. Python GC cycle
        gc.collect()

        # 2. Trim current process working set
        current_proc = self._kernel32.GetCurrentProcess()
        self._kernel32.SetProcessWorkingSetSize(
            current_proc,
            ctypes.c_size_t(-1).value,
            ctypes.c_size_t(-1).value
        )

        time.sleep(0.1)
        vm_after = psutil.virtual_memory()
        ram_after_used = vm_after.used / (1024 * 1024)
        pct_after = vm_after.percent

        freed_mb = max(0.0, ram_before_used - ram_after_used)

        return {
            "ram_before_mb": round(ram_before_used, 1),
            "ram_after_mb": round(ram_after_used, 1),
            "ram_freed_mb": round(freed_mb, 1),
            "percent_before": pct_before,
            "percent_after": pct_after
        }

    def clean_temp_cache(self, max_age_hours: float = 2.0) -> Dict[str, Any]:
        """
        Safely purges stale temporary files from %TEMP% directory.
        Ignores active in-use or locked files without throwing errors.
        """
        temp_dir = os.environ.get("TEMP") or os.environ.get("TMP")
        if not temp_dir or not os.path.exists(temp_dir):
            return {"files_deleted": 0, "space_freed_mb": 0.0}

        now = time.time()
        cutoff = now - (max_age_hours * 3600)
        files_deleted = 0
        bytes_freed = 0

        # Sweep top-level temp files and empty folders
        try:
            for entry in os.scandir(temp_dir):
                try:
                    if entry.is_file(follow_symlinks=False):
                        stat = entry.stat()
                        if stat.st_mtime < cutoff:
                            size = stat.st_size
                            os.remove(entry.path)
                            files_deleted += 1
                            bytes_freed += size
                except (PermissionError, FileNotFoundError, OSError):
                    continue
        except Exception:
            pass

        return {
            "files_deleted": files_deleted,
            "space_freed_mb": round(bytes_freed / (1024 * 1024), 2)
        }

    def get_top_processes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Identifies top resource-consuming processes by memory utilization."""
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                mem_bytes = p.info['memory_info'].rss if p.info.get('memory_info') else 0
                mem_mb = round(mem_bytes / (1024 * 1024), 1)
                procs.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "memory_mb": mem_mb,
                    "cpu_percent": p.info.get('cpu_percent', 0.0)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        procs.sort(key=lambda x: x["memory_mb"], reverse=True)
        return procs[:limit]

    def format_top_processes_summary(self, limit: int = 5) -> str:
        """Formats top memory consumers into an articulate butler report."""
        top = self.get_top_processes(limit)
        if not top:
            return "Unable to sample active system processes at this time, sir."

        lines = [f"Top {len(top)} resource-consuming processes, sir:"]
        for p in top:
            lines.append(f"- {p['name']} (PID: {p['pid']}): {p['memory_mb']} MB RAM")
        return "\n".join(lines)

    def optimize_all(self) -> str:
        """Executes full workstation memory optimization and temporary cache cleaning."""
        mem_res = self.flush_memory()
        temp_res = self.clean_temp_cache(max_age_hours=2.0)

        freed_mb = mem_res["ram_freed_mb"]
        curr_pct = mem_res["percent_after"]
        temp_freed = temp_res["space_freed_mb"]
        temp_count = temp_res["files_deleted"]

        return (
            f"Workstation optimization complete, sir. "
            f"Flushed process working sets and internal garbage collection. "
            f"Swept {temp_count} stale cache files recovering {temp_freed} MB of storage. "
            f"System RAM utilization is now holding steady at {curr_pct}%."
        )

    def optimize_system(self) -> Dict[str, Any]:
        """Executes system memory and cache optimization returning structured metrics."""
        mem_res = self.flush_memory()
        temp_res = self.clean_temp_cache(max_age_hours=2.0)
        return {
            "status": "success",
            "memory_reclaimed_mb": mem_res["ram_freed_mb"],
            "space_freed_mb": temp_res["space_freed_mb"],
            "files_deleted": temp_res["files_deleted"],
            "percent_after": mem_res["percent_after"]
        }

# Global singleton
system_optimizer = SystemOptimizer()

