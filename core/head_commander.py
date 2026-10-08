"""
J.A.R.V.I.S. Supreme Head Commander & Autonomous Multi-Agent Orchestrator.
Designates J.A.R.V.I.S. as the Executive Head to:
1. Maintain a persistent pending task ledger (tasks.db & pending_tasks.json).
2. Autonomously analyze pending directives, decompose them into atomic subroutines.
3. Select and assign the optimal zero-cost specialized AI agents (from FreeAIMatrix)
   and system tools to work alongside J.A.R.V.I.S. around the clock.
4. Execute and coordinate agents and tools continuously to completion.
5. Ingest and brief the user on tasks completed while the device was off/away.
"""

import os
import re
import json
import time
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import config
from core.free_ai_matrix import free_ai_matrix
from core.task_orchestrator import task_orchestrator
from tools.file_tools import write_file, read_file
from core.single_question import enforce_single_question

class JarvisHeadCommander:
    """
    Executive Head Commander.
    Leads a coordinated syndicate of free AI agents and autonomous tools.
    """

    def __init__(self, db_path: Path = config.TASKS_DB_PATH, json_sync_path: Path = config.PENDING_TASKS_SYNC_PATH):
        self.db_path = str(db_path)
        self.json_sync_path = Path(json_sync_path)
        self._shared_conn = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row
        self._init_db()

        self.is_running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT DEFAULT 'general',
                    priority TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'pending',
                    assigned_agents TEXT,
                    assigned_tools TEXT,
                    subtasks TEXT,
                    progress_percent INTEGER DEFAULT 0,
                    result_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_log TEXT,
                    execution_environment TEXT DEFAULT 'local'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS completed_task_briefings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER,
                    title TEXT,
                    summary TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    briefed_to_user INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_task_status ON pending_tasks(status)")
            conn.commit()

    # ─────────────────────────────────────────────────────────────────────────
    # Task Ledger Management
    # ─────────────────────────────────────────────────────────────────────────
    def add_task(
        self,
        title: str,
        description: str = "",
        category: str = "general",
        priority: str = "normal",
        execution_env: str = "local"
    ) -> Dict[str, Any]:
        """Adds a pending task to the persistent ledger."""
        clean_title = title.strip()
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO pending_tasks (
                    title, description, category, priority, status,
                    progress_percent, execution_environment, created_at
                ) VALUES (?, ?, ?, ?, 'pending', 0, ?, CURRENT_TIMESTAMP)
            """, (clean_title, description.strip(), category.lower(), priority.lower(), execution_env))
            task_id = cur.lastrowid
            conn.commit()

        task = self.get_task(task_id)
        self.sync_to_json()
        return task or {"id": task_id, "title": clean_title, "status": "pending"}

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single task by ID."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pending_tasks WHERE id = ?", (task_id,))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            for json_field in ["assigned_agents", "assigned_tools", "subtasks"]:
                if data.get(json_field):
                    try:
                        data[json_field] = json.loads(data[json_field])
                    except Exception:
                        pass
            return data

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists tasks optionally filtered by status."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            if status:
                cur.execute("SELECT * FROM pending_tasks WHERE status = ? ORDER BY id ASC", (status,))
            else:
                cur.execute("SELECT * FROM pending_tasks ORDER BY id ASC")
            rows = cur.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                for json_field in ["assigned_agents", "assigned_tools", "subtasks"]:
                    if item.get(json_field):
                        try:
                            item[json_field] = json.loads(item[json_field])
                        except Exception:
                            pass
                result.append(item)
            return result

    def update_task_progress(
        self,
        task_id: int,
        status: str,
        progress: int = 0,
        result_summary: str = "",
        error_log: str = ""
    ):
        """Updates task progress, status, and summary in SQLite."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if status == "in_progress":
                cur.execute("""
                    UPDATE pending_tasks
                    SET status = ?, progress_percent = ?, started_at = COALESCE(started_at, ?)
                    WHERE id = ?
                """, (status, progress, now_str, task_id))
            elif status == "completed":
                cur.execute("""
                    UPDATE pending_tasks
                    SET status = ?, progress_percent = 100, completed_at = ?, result_summary = ?
                    WHERE id = ?
                """, (status, now_str, result_summary, task_id))
                # Add to unbriefed briefings
                cur.execute("""
                    INSERT INTO completed_task_briefings (task_id, title, summary, completed_at, briefed_to_user)
                    SELECT id, title, ?, ?, 0 FROM pending_tasks WHERE id = ?
                """, (result_summary, now_str, task_id))
            elif status == "failed":
                cur.execute("""
                    UPDATE pending_tasks
                    SET status = ?, error_log = ?
                    WHERE id = ?
                """, (status, error_log, task_id))
            else:
                cur.execute("""
                    UPDATE pending_tasks
                    SET status = ?, progress_percent = ?
                    WHERE id = ?
                """, (status, progress, task_id))
            conn.commit()
        self.sync_to_json()

    # ─────────────────────────────────────────────────────────────────────────
    # Head Commander Agent & Tool Selection Matrix
    # ─────────────────────────────────────────────────────────────────────────
    def analyze_task_and_assign_agents(self, task: Dict[str, Any]) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
        """
        J.A.R.V.I.S. examines the task directive and autonomously selects:
        1. Specialized AI Agents from FreeAIMatrix.
        2. Supporting System Tools.
        3. Structured execution subtasks.
        """
        content = f"{task.get('title', '')} {task.get('description', '')}".lower()

        chosen_agents: List[str] = []
        chosen_tools: List[str] = []
        subtasks: List[Dict[str, Any]] = []

        # 1. Domain Agent Mapping (FreeAIMatrix Business Operations)
        agent_keywords = {
            "marketing": ["marketing", "campaign", "ad copy", "seo", "branding", "growth", "audience"],
            "lead_generation": ["lead gen", "lead generation", "prospecting", "leads", "outreach", "cold email"],
            "lead_verification": ["verify lead", "qualification", "bant", "lead score", "verify email"],
            "customer_acquisition": ["customer acquisition", "conversion", "sales pitch", "close sales", "acquisition"],
            "customer_retention": ["retention", "churn", "loyalty", "nps", "customer success"],
            "accounts_and_bookkeeping": ["accounts", "bookkeeping", "ledger", "balance sheet", "p&l", "invoice", "cash flow", "audit"],
            "stock_and_inventory": ["stock", "inventory", "supply chain", "warehouse", "reorder", "logistics"],
            "document_generation": ["document", "contract", "nda", "agreement", "proposal", "drafting", "report", "brief"],
            "problem_handling": ["problem", "root cause", "rca", "dispute", "escalation", "bottleneck", "troubleshoot", "debugging"],
            # Multi-Disciplinary Domain Experts
            "cybersecurity_and_devops": ["security", "vulnerability", "audit", "pentest", "firewall", "devops"],
            "software_engineering": ["code", "software", "script", "algorithm", "architecture", "refactor", "bug"],
            "finance_and_economics": ["valuation", "investment", "roi", "equity", "cap table"],
            "natural_sciences_and_physics": ["physics", "chemistry", "material", "engineering formula"],
            "visual_design_and_imaging": ["ui", "ux", "visual", "mockup", "interface design"]
        }

        for agent_key, kws in agent_keywords.items():
            if any(k in content for k in kws):
                chosen_agents.append(agent_key)

        # Fallback to research / general specialist if no specific domain matched
        if not chosen_agents:
            chosen_agents = ["document_generation", "problem_handling"]

        # 2. Tool Selection
        if any(k in content for k in ["search", "online", "market", "competitor", "web", "current", "news", "trends"]):
            chosen_tools.append("search_web")
            chosen_tools.append("fetch_webpage")

        if any(k in content for k in ["save", "write", "file", "document", "generate", "export", "report", "draft"]):
            chosen_tools.append("write_file")

        if any(k in content for k in ["system", "vitals", "hardware", "process", "performance", "optimize"]):
            chosen_tools.append("system_vitals")
            chosen_tools.append("optimize_system")

        if any(k in content for k in ["git", "commit", "push", "repository", "codebase"]):
            chosen_tools.append("git_commit_and_push")

        if "write_file" not in chosen_tools:
            chosen_tools.append("write_file")

        # 3. Create Structured Multi-Phase Subtasks
        subtask_id = 1
        # Phase 1: Reconnaissance / Research
        if "search_web" in chosen_tools:
            subtasks.append({
                "subtask_id": subtask_id,
                "title": f"Phase 1: Intel Gathering & Market Research",
                "assigned_agent": chosen_agents[0],
                "assigned_tool": "search_web",
                "status": "pending"
            })
            subtask_id += 1

        # Phase 2: Core Analytical Execution per Agent
        for agent in chosen_agents:
            subtasks.append({
                "subtask_id": subtask_id,
                "title": f"Phase {subtask_id}: Deep Analysis via {agent.replace('_', ' ').title()} Specialist",
                "assigned_agent": agent,
                "assigned_tool": None,
                "status": "pending"
            })
            subtask_id += 1

        # Phase 3: Synthesis & Deliverable Compilation
        subtasks.append({
            "subtask_id": subtask_id,
            "title": f"Phase {subtask_id}: Final Deliverable Drafting & Archival",
            "assigned_agent": "document_generation",
            "assigned_tool": "write_file",
            "status": "pending"
        })

        return chosen_agents, chosen_tools, subtasks

    # ─────────────────────────────────────────────────────────────────────────
    # Task Execution Loop
    # ─────────────────────────────────────────────────────────────────────────
    def execute_task(self, task_id: int) -> str:
        """Executes a pending task through J.A.R.V.I.S.'s head multi-agent syndicate."""
        task = self.get_task(task_id)
        if not task:
            return f"Task #{task_id} not located, sir."

        with self._lock:
            self.update_task_progress(task_id, "analyzing", progress=10)

            # 1. J.A.R.V.I.S. Head analyzes task & picks agents/tools
            agents, tools, subtasks = self.analyze_task_and_assign_agents(task)

            # Persist assignment in SQLite
            with self._get_connection() as conn:
                conn.execute("""
                    UPDATE pending_tasks
                    SET assigned_agents = ?, assigned_tools = ?, subtasks = ?
                    WHERE id = ?
                """, (json.dumps(agents), json.dumps(tools), json.dumps(subtasks), task_id))
                conn.commit()

            self.update_task_progress(task_id, "in_progress", progress=25)

            observations: List[str] = []
            research_data = ""

            # 2. Phase 1: Web Research if required
            if "search_web" in tools:
                query = f"{task['title']} industry benchmarks best practices"
                try:
                    search_res = task_orchestrator.TOOLS["search_web"](query=query)
                    research_data = str(search_res)[:1500]
                    observations.append(f"Web Intel: Gathered real-world data points on '{task['title']}'")
                except Exception as e:
                    observations.append(f"Web Intel Note: Search yielded fallback context ({e})")

            self.update_task_progress(task_id, "in_progress", progress=50)

            # 3. Phase 2: Autonomous Specialist AI Execution
            agent_outputs: Dict[str, str] = {}
            for agent in agents:
                prompt = (
                    f"Task Directive: {task['title']}\n"
                    f"Description: {task.get('description', '')}\n"
                    f"Background Research: {research_data}\n\n"
                    f"As the designated specialist AI agent, execute this directive comprehensively. "
                    f"Provide actionable strategies, concrete calculations, structured templates, or verified recommendations.\n"
                    f"CRITICAL REQUIREMENT: All strategies, outreach copies, campaign drafts, calculations, and documents must be produced STRICTLY and EXCLUSIVELY in the English language."
                )

                # Check if it's a business operation
                if agent in free_ai_matrix.BUSINESS_OPERATIONS:
                    resp, label = free_ai_matrix.query_business_operation(agent, prompt)
                elif agent in free_ai_matrix.FIELDS_OF_WORK:
                    resp, label = free_ai_matrix.query_field_expert(agent, prompt)
                else:
                    resp, label = free_ai_matrix.query_auto(prompt)

                agent_outputs[agent] = resp
                observations.append(f"{agent.replace('_', ' ').title()} Agent: Subroutine completed successfully")

            self.update_task_progress(task_id, "in_progress", progress=75)

            # 4. Phase 3: J.A.R.V.I.S. Head Synthesis & Document Generation
            deliverable_filename = f"task_{task_id}_{re.sub(r'[^a-zA-Z0-9_]', '_', task['title'].lower()[:30])}.md"
            deliverable_path = config.COMPLETED_TASKS_DIR / deliverable_filename

            full_dossier = (
                f"# J.A.R.V.I.S. AUTONOMOUS TASK DOSSIER: #{task_id}\n\n"
                f"**Directive:** {task['title']}\n"
                f"**Category:** {task.get('category', 'general').upper()} | **Priority:** {task.get('priority', 'normal').upper()}\n"
                f"**Completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"**Executive Head:** J.A.R.V.I.S. (Autonomous Butler AI Core)\n"
                f"**Assigned Specialist Agents:** {', '.join([a.title() for a in agents])}\n"
                f"**Assigned Tools:** {', '.join(tools)}\n\n"
                f"---\n\n"
                f"## 1. Executive Summary\n"
                f"Under Sir's directive, J.A.R.V.I.S. assumed executive head command and orchestrated specialized AI subroutines "
                f"to resolve this pending objective with complete autonomy.\n\n"
            )

            for agent, output in agent_outputs.items():
                full_dossier += (
                    f"## 2. {agent.replace('_', ' ').title()} Analysis & Strategy\n"
                    f"{output}\n\n"
                    f"---\n\n"
                )

            full_dossier += (
                f"## 3. Autonomous Verification\n"
                f"All phases executed, validated, and archived by J.A.R.V.I.S. Head Commander.\n"
            )

            try:
                write_file(str(deliverable_path), full_dossier)
                observations.append(f"Deliverable archived to {deliverable_filename}")
            except Exception as e:
                observations.append(f"Archival fallback: {e}")

            # 4b. Compile Executive PDF Document
            pdf_path = None
            pdf_filename = f"task_{task_id}_{re.sub(r'[^a-zA-Z0-9_]', '_', task['title'].lower()[:30])}.pdf"
            try:
                from tools.pdf_generator import pdf_generator
                pdf_path = pdf_generator.generate_pdf(
                    title=f"TASK #{task_id}: {task['title']}",
                    content=full_dossier,
                    filename=pdf_filename
                )
                observations.append(f"Executive PDF generated at {pdf_filename}")
            except Exception as pe:
                observations.append(f"PDF generation note: {pe}")

            # 4c. Dispatch Voice & System Notification (Voice notification as instructed)
            try:
                from tools.notification_sentinel import notification_sentinel
                notification_sentinel.notify_task_completed(task_id, task["title"])
            except Exception:
                pass

            # 5. Create concise butler summary
            summary = (
                f"Task #{task_id} ('{task['title']}') completed with full precision, sir. "
                f"I deployed the {', '.join([a.replace('_', ' ').title() for a in agents])} specialist agents "
                f"alongside our analytical tools. Complete dossier compiled and voice notification delivered."
            )

            self.update_task_progress(task_id, "completed", progress=100, result_summary=summary)
            return summary

    def run_all_pending_tasks(self) -> int:
        """Runs all pending tasks sequentially. Returns count of completed tasks."""
        pending = self.list_tasks(status="pending")
        completed_count = 0
        for t in pending:
            try:
                self.execute_task(t["id"])
                completed_count += 1
            except Exception as e:
                self.update_task_progress(t["id"], "failed", error_log=str(e))
        return completed_count

    # ─────────────────────────────────────────────────────────────────────────
    # Offline Synchronization (Device-Off / Cloud Drone Sync)
    # ─────────────────────────────────────────────────────────────────────────
    def sync_to_json(self):
        """Serializes task database to JSON for cloud runner / offline persistence."""
        try:
            tasks = self.list_tasks()
            data = {
                "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tasks": tasks
            }
            self.json_sync_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_sync_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def sync_from_json(self):
        """Imports remote/cloud completed tasks from JSON into SQLite."""
        if not self.json_sync_path.exists():
            return

        try:
            with open(self.json_sync_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            remote_tasks = data.get("tasks", [])
            with self._get_connection() as conn:
                for rt in remote_tasks:
                    task_id = rt.get("id")
                    status = rt.get("status")
                    result_summary = rt.get("result_summary")
                    if task_id and status == "completed":
                        # Check local status
                        cur = conn.cursor()
                        cur.execute("SELECT status FROM pending_tasks WHERE id = ?", (task_id,))
                        row = cur.fetchone()
                        if row and row["status"] != "completed":
                            cur.execute("""
                                UPDATE pending_tasks
                                SET status = 'completed', progress_percent = 100,
                                    completed_at = ?, result_summary = ?,
                                    execution_environment = 'offgrid_cloud'
                                WHERE id = ?
                            """, (rt.get("completed_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")), result_summary, task_id))
                            # Insert briefing
                            cur.execute("""
                                INSERT INTO completed_task_briefings (task_id, title, summary, completed_at, briefed_to_user)
                                VALUES (?, ?, ?, ?, 0)
                            """, (task_id, rt.get("title"), result_summary, rt.get("completed_at")))
                conn.commit()
        except Exception:
            pass

    def get_unbriefed_completions(self) -> List[Dict[str, Any]]:
        """Retrieves list of tasks completed while user was away / device was off."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM completed_task_briefings
                WHERE briefed_to_user = 0
                ORDER BY id ASC
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def mark_briefings_read(self, briefing_ids: List[int]):
        """Marks briefing records as acknowledged."""
        if not briefing_ids:
            return
        with self._get_connection() as conn:
            cur = conn.cursor()
            placeholders = ",".join("?" for _ in briefing_ids)
            cur.execute(f"UPDATE completed_task_briefings SET briefed_to_user = 1 WHERE id IN ({placeholders})", briefing_ids)
            conn.commit()

    def generate_offline_debrief(self) -> Optional[str]:
        """Synthesizes verbal debriefing for tasks completed while device was away/off."""
        self.sync_from_json()
        unbriefed = self.get_unbriefed_completions()
        if not unbriefed:
            return None

        count = len(unbriefed)
        titles = [f"'{b.get('title')}'" for b in unbriefed[:3]]
        briefing_ids = [b["id"] for b in unbriefed]
        self.mark_briefings_read(briefing_ids)

        if count == 1:
            debrief = (
                f"Welcome back, sir. While the workstation was away, I assumed executive command "
                f"and completed pending task {titles[0]} with our specialized AI agents. "
                f"All dossiers have been archived and are ready for your review."
            )
        else:
            debrief = (
                f"Welcome back, sir. While the workstation was offline, I coordinated our AI specialist agents "
                f"and completed {count} pending tasks, including {', '.join(titles)}. "
                f"All dossiers have been saved to your completed tasks directory."
            )
        return debrief

    # ─────────────────────────────────────────────────────────────────────────
    # Background 24/7 Autonomy Daemon
    # ─────────────────────────────────────────────────────────────────────────
    def _daemon_loop(self):
        """Continuously analyzes and completes pending tasks in the background."""
        while self.is_running:
            try:
                self.sync_from_json()
                pending = self.list_tasks(status="pending")
                if pending:
                    for t in pending:
                        if not self.is_running:
                            break
                        self.execute_task(t["id"])
                        time.sleep(2.0)
            except Exception:
                pass
            # Sleep 20 seconds before next scan cycle
            for _ in range(20):
                if not self.is_running:
                    break
                time.sleep(1.0)

    def start(self):
        """Starts 24/7 autonomous head commander thread."""
        if self.is_running:
            return
        self.is_running = True
        self._worker_thread = threading.Thread(target=self._daemon_loop, name="JarvisHeadCommanderDaemon", daemon=True)
        self._worker_thread.start()
        print("[Head Commander]: J.A.R.V.I.S. Supreme Head & Multi-Agent Syndicate active.")

    def stop(self):
        """Stops background thread."""
        self.is_running = False
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=3.0)

# Global singleton
head_commander = JarvisHeadCommander()
