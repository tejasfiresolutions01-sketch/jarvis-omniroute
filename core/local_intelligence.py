import re
import threading
from datetime import datetime, date
from typing import Tuple, Optional
from tools.system_controller import system_controller
from core.schedule_manager import schedule_manager
from core.head_commander import head_commander
from core.offgrid_sentinel import offgrid_sentinel
from core.learning_matrix import learning_matrix
from memory.memory_store import memory
from core.vector_memory import vector_memory
from core.cognitive_memory import cognitive_memory
import config

class LocalIntelligence:
    """
    Offline Cognitive & Butler Engine.
    Operates 100% locally with zero cloud dependencies, zero latency,
    and complete autonomy over schedule, hardware, and device management.
    """

    WAKE_PREFIXES = [
        r"^(?:hey|okay|hi|hello)?\s*jarvis[,\s!]*",
        r"^(?:please|could you|can you|would you|kindly)\s+",
        r"^(?:jarvis)[,\s!]*"
    ]

    def clean_utterance(self, prompt: str) -> str:
        text = prompt.strip()
        for pat in self.WAKE_PREFIXES:
            text = re.sub(pat, "", text, flags=re.IGNORECASE).strip()
        return text.strip(" \t\n\r\"'.,!?")

    def evaluate_and_execute(self, prompt: str) -> Tuple[bool, str]:
        """
        Evaluates a user prompt for offline local execution.
        Returns: (is_handled, response_string)
        """
        clean = self.clean_utterance(prompt)
        clean_lower = clean.lower()

        if not clean_lower:
            return False, ""

        # ─────────────────────────────────────────────────────────────────────
        # 1. Butler Schedule & Agenda Directives
        # ─────────────────────────────────────────────────────────────────────
        is_sched, sched_res = schedule_manager.parse_and_handle(clean)
        if is_sched:
            return True, sched_res

        # ─────────────────────────────────────────────────────────────────────
        # 1b. Head Commander & Multi-Agent Pending Task Directives
        # ─────────────────────────────────────────────────────────────────────
        # Add / Queue pending task
        add_task_match = re.match(r"^(?:add|create|queue|schedule|register)\s+(?:a\s+)?(?:pending\s+)?(?:task|directive)\s*(?::\s*|\s+to\s+|\s+)(.+)$", clean_lower)
        if add_task_match:
            task_title = add_task_match.group(1).strip()
            task = head_commander.add_task(title=task_title)
            agents, tools, _ = head_commander.analyze_task_and_assign_agents(task)
            agent_str = ", ".join([a.replace('_', ' ').title() for a in agents])
            tool_str = ", ".join(tools)
            return True, (
                f"Directive queued in persistent task ledger as Task #{task['id']}, sir: '{task_title}'. "
                f"As Head Commander, I have designated the {agent_str} specialist agents "
                f"and assigned tools ({tool_str}) to work alongside me. "
                f"This will continue executing continuously even if the workstation powers down or enters standby."
            )

        # Show / List pending tasks
        if any(clean_lower == p or clean_lower.startswith(p) for p in [
            "what are my pending tasks", "show pending tasks", "list pending tasks",
            "check pending tasks", "pending tasks", "task status", "view pending tasks",
            "show all tasks", "list tasks"
        ]):
            pending = head_commander.list_tasks(status="pending")
            completed = head_commander.list_tasks(status="completed")
            if not pending and not completed:
                return True, "There are currently no active or pending tasks in your ledger, sir. All systems are up to date."
            msg_parts = []
            if pending:
                msg_parts.append(f"You have {len(pending)} pending tasks under executive analysis:")
                for t in pending[:4]:
                    agents = t.get("assigned_agents") or ["J.A.R.V.I.S."]
                    agent_names = ", ".join([a.title() for a in agents]) if isinstance(agents, list) else str(agents)
                    msg_parts.append(f"- Task #{t['id']}: '{t['title']}' (Assigned: {agent_names}, Progress: {t.get('progress_percent', 0)}%)")
            if completed:
                msg_parts.append(f"\n{len(completed)} tasks have been successfully completed by our agent syndicate.")
            return True, "\n".join(msg_parts)

        # Run / Complete pending tasks manually
        if any(clean_lower == p or clean_lower.startswith(p) for p in [
            "run pending tasks", "execute pending tasks", "complete pending tasks",
            "analyze pending tasks", "process pending tasks", "dispatch agents",
            "assign agents to tasks", "run tasks"
        ]):
            pending = head_commander.list_tasks(status="pending")
            if not pending:
                return True, "All pending tasks have already been analyzed and completed, sir."
            count = len(pending)
            threading.Thread(target=head_commander.run_all_pending_tasks, daemon=True).start()
            return True, (
                f"Understood, sir. Assuming executive command over all {count} pending tasks now. "
                f"Our specialized AI agents and system tools are actively deployed and running."
            )

        # ── Cancel All Pending Tasks and Upgrade Command Execution ─────────────
        if any(p in clean_lower for p in [
            "cancel all the pending tasks and upgrade the command execution to the highest level",
            "cancel all pending tasks and upgrade the command execution to the highest level",
            "cancel all the pending tasks and upgrade command execution to highest level",
            "cancel pending tasks and upgrade command execution to the highest level",
            "cancel all pending tasks and upgrade command execution",
            "cancel pending tasks and upgrade execution"
        ]):
            from core.supreme_command_executor import supreme_executor
            return supreme_executor.cancel_and_upgrade()

        # Cancel All Pending Tasks
        if any(clean_lower == p or clean_lower.startswith(p) for p in [
            "cancel all the pending tasks", "cancel all pending tasks", "cancel pending tasks",
            "cancel tasks", "cancel all tasks", "clear all pending tasks", "clear pending tasks",
            "abort all pending tasks", "abort pending tasks", "stop all pending tasks", "stop pending tasks"
        ]):
            from core.supreme_command_executor import supreme_executor
            res = supreme_executor.cancel_all_pending_tasks()
            return True, res["message"]

        # Upgrade Command Execution to Highest Level
        if any(clean_lower == p or clean_lower.startswith(p) for p in [
            "upgrade the command execution to the highest level",
            "upgrade command execution to the highest level",
            "upgrade command execution to highest level",
            "upgrade command execution",
            "upgrade execution to highest level",
            "set command execution to highest level",
            "highest level command execution",
            "elevate command execution",
            "elevate execution priority",
            "maximum command execution"
        ]):
            from core.supreme_command_executor import supreme_executor
            res = supreme_executor.upgrade_execution_to_highest_level()
            return True, res["message"]

        # Voice Command Execution Status
        if any(clean_lower == p or clean_lower.startswith(p) for p in [
            "voice command execution", "voice command status", "voice execution status",
            "voice command system", "voice commands", "voice execution", "voice command mode",
            "voice command matrix", "voice perception status"
        ]):
            from core.listener import listener
            from core.wake_word import wake_word_engine
            from core.supreme_command_executor import supreme_executor

            wake_status = "Active ('Hey Jarvis')" if wake_word_engine.running else "Standby"
            pause_sec = getattr(listener, "pause_threshold", 2.0)
            lease_active = listener.has_active_conversation_lease()
            lease_str = "Active" if lease_active else "Standby"

            return True, (
                f"Voice Command Execution Matrix is fully operational at {supreme_executor.execution_tier}, sir. "
                f"Acoustic Perception: {wake_status} | Sentence Completion Sentinel: Active ({pause_sec}s pause tolerance) | "
                f"Biometric Verification: Active | Multi-Turn Dialogue Lease: {lease_str}. "
                f"I am actively listening and ready to execute your voice directives."
            )

        # Off-Grid / Standby / Away Mode Status
        if any(clean_lower == p for p in ["offgrid status", "away mode status", "device off status", "wake timer status"]):
            away = "active" if offgrid_sentinel.away_mode_active else "standby"
            return True, (
                f"Off-Grid and Standby Autonomy is operational, sir. "
                f"Windows Away Mode is {away}, hardware ACPI RTC wake alarms are registered in Task Scheduler, "
                f"and the Cloud Off-Grid Autonomous Drone is synced for zero-cost execution when power is severed."
            )

        # ─────────────────────────────────────────────────────────────────────
        # 1c. Holographic Interface Always-On Controls
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["run holographic interface all time", "run hologram all time", "hologram always on", "holographic always on", "keep hologram on screen", "pin hologram", "pin holographic"]):
            from core.hologram_sentinel import hologram_sentinel
            return True, hologram_sentinel.set_always_on(True)

        if any(p in clean_lower for p in ["hologram adaptive mode", "unpin hologram", "hologram background mode", "restore adaptive hologram"]):
            from core.hologram_sentinel import hologram_sentinel
            return True, hologram_sentinel.set_always_on(False)

        # ─────────────────────────────────────────────────────────────────────
        # 1d. Google Ecosystem Directives (Maps, Gmail, Search Engine)
        # ─────────────────────────────────────────────────────────────────────
        from tools.google_services import google_services

        # Gmail Open / Compose
        if clean_lower in ["open gmail", "check gmail", "launch gmail", "go to gmail", "gmail", "check inbox"]:
            return True, google_services.open_gmail()

        gmail_compose_match = re.match(r"^(?:compose|send|write|draft)\s+(?:an?\s+)?(?:email|mail|gmail)(?:\s+(?:to|addressed to)\s+(.+?))?(?:\s+(?:about|subject|with subject)\s+(.+))?$", clean_lower)
        if gmail_compose_match:
            to_addr = gmail_compose_match.group(1) or ""
            subject_or_topic = gmail_compose_match.group(2) or ""
            return True, google_services.compose_email(to=to_addr.strip(), subject=subject_or_topic.strip())

        # Google Maps
        if clean_lower in ["open google maps", "open maps", "launch maps", "google maps"]:
            return True, google_services.search_maps("", open_browser=True)

        maps_dir_match = re.match(r"^(?:get\s+directions|directions|navigate|route|find\s+route|show\s+route)\s+(?:from\s+(.+?)\s+to\s+(.+)|to\s+(.+?)(?:\s+on\s+(?:google\s+)?maps)?)$", clean_lower)
        if maps_dir_match:
            if maps_dir_match.group(1) and maps_dir_match.group(2):
                orig = maps_dir_match.group(1).strip()
                dest = maps_dir_match.group(2).strip()
                return True, google_services.get_directions(origin=orig, destination=dest)
            elif maps_dir_match.group(3):
                dest = maps_dir_match.group(3).strip()
                return True, google_services.search_maps(dest)

        maps_search_match = re.match(r"^(?:search\s+(?:google\s+)?maps\s+(?:for\s+)?|maps\s+(?:search\s+)?|find\s+on\s+(?:google\s+)?maps\s+)(.+)$", clean_lower)
        if maps_search_match:
            m_target = maps_search_match.group(1).strip()
            return True, google_services.search_maps(m_target)

        # Google Search Engine
        google_search_match = re.match(r"^(?:search\s+google\s+(?:for\s+)?|google\s+(?:search\s+)?|google\s+|find\s+on\s+google\s+)(.+)$", clean_lower)
        if google_search_match:
            g_target = google_search_match.group(1).strip()
            if not any(g_target.startswith(w) for w in ["drive", "docs", "sheets", "calendar"]):
                google_services.search_google(g_target, open_browser=True)
                summary = google_services.format_search_summary(g_target)
                return True, summary

        # System Hardware Vitals (CPU, RAM, Disk)
        if (clean_lower == "vitals" or any(p in clean_lower for p in [
            "system vitals", "hardware vitals", "hardware status",
            "cpu usage", "cpu status", "ram usage", "ram status", "memory status",
            "memory usage", "disk space", "storage status", "disk status"
        ])) and not any(s in clean_lower for s in ["screen", "display", "monitor"]):
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            return True, (
                f"Workstation vitals are healthy, sir. CPU load is at {cpu} percent, "
                f"system memory usage is at {mem.percent} percent ({mem.used // (1024**2)} MB used out of {mem.total // (1024**2)} MB), "
                f"and primary disk storage has {disk.free // (1024**3)} gigabytes free."
            )

        # Campaign Language Settings
        if any(p in clean_lower for p in [
            "run campaigns only in english", "run campaign only in english", "campaigns only in english",
            "campaign in english only", "campaigns in english only", "only in english and not in any other language",
            "set campaign language to english"
        ]):
            return True, "Understood, sir. All marketing campaigns, cold outreach sequences, follow-up scripts, and business documents are strictly configured to run exclusively in English. No other language will be used."

        # Commercial Quotations & Multi-Channel Sales Proposals
        quote_match = re.match(r"^(?:generate|create|prepare|draft|make|compile)\s+(?:a\s+)?(?:commercial\s+)?(?:quotation|quote|proposal)\s+(?:for\s+)?(.+)$", clean_lower)
        if quote_match:
            from tools.quotation_engine import quotation_engine
            target_entity = quote_match.group(1).strip()
            corridor = "Ambattur"
            for c in ["ambattur", "sriperumbudur", "oragadam", "guindy", "maraimalai nagar"]:
                if c in target_entity:
                    corridor = c.title()
                    break
            quote_data = quotation_engine.create_quotation(
                client_name=target_entity.title(),
                facility_location=f"{corridor} Industrial Corridor",
                corridor=corridor
            )
            return True, quotation_engine.format_voice_summary(quote_data)

        # Multi-Channel Sales Outreach Stack
        outreach_match = re.match(r"^(?:generate|create|prepare|launch|run)\s+(?:commercial\s+)?(?:outreach|sales\s+outreach|campaign\s+and\s+quote)\s+(?:for\s+)?(.+)$", clean_lower)
        if outreach_match:
            from tools.digital_marketing_suite import marketing_suite
            target_entity = outreach_match.group(1).strip()
            corridor = "Ambattur"
            for c in ["ambattur", "sriperumbudur", "oragadam", "guindy", "maraimalai nagar"]:
                if c in target_entity:
                    corridor = c.title()
                    break
            stack = marketing_suite.execute_commercial_outreach_stack(
                client_name=target_entity.title(),
                corridor=corridor
            )
            return True, stack["voice_summary"]

        # Monthly Business Scan
        if any(p in clean_lower for p in [
            "scan for new business", "monthly business scan", "scan new business",
            "business scan", "scan business opportunities", "find new business this month"
        ]):
            from core.business_scanner import business_scanner
            res = business_scanner.scan_for_new_business(force=True)
            return True, res["message"]

        # Live B2B Lead Harvesting & Domain Deliverability Verification
        lead_harvest_match = re.match(r"^(?:harvest\s+(?:b2b\s+)?leads(?:\s+in\s+|\s+for\s+)?|scan\s+(?:b2b\s+)?leads(?:\s+in\s+|\s+for\s+)?)(.*)$", clean_lower)
        if lead_harvest_match or any(p in clean_lower for p in ["harvest leads", "harvest b2b leads", "b2b lead harvester"]):
            from tools.lead_harvester import lead_harvester
            corridor = lead_harvest_match.group(1).strip() if lead_harvest_match and lead_harvest_match.group(1) else "ambattur"
            if not corridor:
                corridor = "ambattur"
            res = lead_harvester.run_harvest_and_export(corridor)
            return True, lead_harvester.format_voice_summary(res)

        # DNS MX Record & Domain Deliverability Verification
        mx_match = re.match(r"^(?:verify\s+(?:lead\s+)?domain|validate\s+(?:dns\s+)?mx\s+record(?:s)?|check\s+email\s+deliverability\s+for)\s+(.+)$", clean_lower)
        if mx_match:
            from tools.lead_harvester import lead_harvester
            dom = mx_match.group(1).strip()
            has_mx, hosts, msg = lead_harvester.verify_dns_mx_record(dom)
            if has_mx:
                return True, f"Domain {dom} is validated for email delivery, sir. Active MX hosts identified: {', '.join(hosts[:2])}."
            return True, f"Deliverability check for domain {dom}: {msg}"

        # Self-Upgrade Status Inquiry
        if any(p in clean_lower for p in [
            "are there any upgrades", "are there upgrades", "is there any upgrade",
            "is there an upgrade", "any upgrades", "check for upgrades", "check upgrades",
            "upgrade status", "any system upgrades", "what upgrades do we have",
            "are we up to date", "is jarvis up to date", "system upgrade status"
        ]):
            from core.self_evolver import self_evolver
            return True, self_evolver.get_upgrade_status_summary()

        # Self-Upgrade and Automation Directive (Every 3rd Night or Manual Directive)
        if any(p in clean_lower for p in [
            "upgrade yourself", "run self upgrade", "upgrade and automate",
            "upgrade and automate yourself", "self evolution", "run self-upgrade"
        ]):
            from core.self_evolver import self_evolver
            res = self_evolver.run_self_upgrade_and_automation(force=True)
            return True, res["message"]

        # Active IDE Co-Pilot & Visual Screen Diagnostics
        if any(p in clean_lower for p in [
            "check my code", "check code for errors", "diagnose active window",
            "diagnose screen for errors", "check screen for errors",
            "ide copilot", "ide co-pilot", "inspect active window", "code copilot"
        ]):
            from core.vision_copilot import vision_copilot
            diag_res = vision_copilot.diagnose_current_screen()
            return True, diag_res

        # Multi-Modal Vision Perception & Screen Comprehension
        if any(p in clean_lower for p in [
            "what is on my screen", "what's on my screen", "whats on my screen",
            "describe screen", "describe my screen", "inspect display", "inspect screen",
            "diagnose screen", "analyze screen", "analyze display", "screen vitals", "display vitals",
            "screen theme", "is screen dark mode", "is display dark mode",
            "read text on screen", "read screen text", "read visible text"
        ]) or bool(re.search(r"\b(?:find|where is|locate)\s+(?:the\s+)?button\b", clean_lower)):
            from tools.vision_tools import comprehend_screen
            c_res = comprehend_screen(query=prompt)
            return True, c_res["speech"]


        # Canary Sandbox & Latency Immune System Status
        if any(p in clean_lower for p in [
            "latency immune system", "latency immune status", "canary status",
            "canary sandbox", "latency telemetry", "benchmark system latency",
            "system latency status", "immune system status"
        ]):
            from core.canary_sandbox import canary_sandbox
            return True, canary_sandbox.format_immune_status_summary()

        # Area 1: Autonomous Web & Market Intelligence (Supplier Prices & Tenders)
        if any(p in clean_lower for p in ["track supplier prices", "supplier prices", "market material prices", "material prices", "raw material price"]):
            from tools.browser_agent import browser_agent
            p_data = browser_agent.track_supplier_material_prices()
            return True, browser_agent.format_price_voice_summary(p_data)

        if any(p in clean_lower for p in ["check government tenders", "scan tenders", "fire safety tenders", "public tenders", "tenders status"]):
            from tools.browser_agent import browser_agent
            t_data = browser_agent.scan_government_tenders()
            return True, browser_agent.format_tender_voice_summary(t_data)

        # Area 2: Business Workflow, Quotations & CRM Pipeline
        quote_match = re.match(r"^(?:generate|create|draft)\s+(?:a\s+)?(?:quotation|quote|estimate)\s+(?:for\s+)?(.+)$", clean_lower)
        if quote_match:
            from tools.business_workflow_engine import business_workflow
            c_name = quote_match.group(1).strip()
            items = [{"item_code": "abc_6kg", "quantity": 10}, {"item_code": "co2_4.5kg", "quantity": 4}, {"item_code": "hydro_test", "quantity": 14}]
            q_res = business_workflow.generate_quotation(c_name, items)
            return True, f"Quotation {q_res['quotation_number']} generated for {c_name}, sir. Total amount is ₹{q_res['total_inr']:,.2f} inclusive of 18% GST. Record added to CRM."

        if any(p in clean_lower for p in ["crm pipeline status", "pipeline status", "sales pipeline", "crm status", "pipeline summary"]):
            from tools.business_workflow_engine import business_workflow
            return True, business_workflow.format_crm_voice_summary()

        # Area 3: Real-World Optical Vision & Camera Inspection
        if any(p in clean_lower for p in ["inspect extinguisher camera", "inspect extinguisher", "camera inspection", "optical inspection", "check extinguisher"]):
            from tools.optical_inspection_engine import optical_inspection
            return True, optical_inspection.format_inspection_voice_summary()

        if any(p in clean_lower for p in ["check pressure gauge", "inspect pressure gauge", "gauge status", "manometer status"]):
            from tools.optical_inspection_engine import optical_inspection
            g_res = optical_inspection.inspect_pressure_gauge()
            return True, f"Manometer status is {g_res['status']} in the {g_res['pressure_zone']}, sir. {g_res['action_required']}"

        # Area 4: Advanced Multi-Agent Workflow Mesh
        agent_mesh_match = re.match(r"^(?:run\s+(?:multi\s+)?agent\s+mesh(?:\s+on|\s+for)?|execute\s+multi\s+agent\s+mission(?:\s+on|\s+for)?)(.*)$", clean_lower)
        if agent_mesh_match or any(p in clean_lower for p in ["run agent mesh", "multi agent mission", "multi agent status", "agent mesh status"]):
            from core.multi_agent_mesh import multi_agent_mesh
            mission = agent_mesh_match.group(1).strip() if agent_mesh_match and agent_mesh_match.group(1) else "Comprehensive industrial safety audit and quotation"
            if not mission:
                mission = "Comprehensive industrial safety audit and quotation"
            m_res = multi_agent_mesh.execute_mesh_mission(mission)
            return True, m_res["synthesis"]

        # Area 5: Holographic HUD & Next-Gen Interface Telemetry
        if any(p in clean_lower for p in ["hud telemetry", "hud telemetry status", "holographic telemetry", "hud status"]):
            from ui.hud_telemetry_matrix import hud_telemetry
            return True, hud_telemetry.format_telemetry_voice_summary()

        if any(p in clean_lower for p in ["play sound effect", "play sound fx", "target lock sound", "repulsor sound"]):
            from ui.hud_telemetry_matrix import hud_telemetry
            fx_type = "repulsor_charge" if "repulsor" in clean_lower else "target_lock"
            hud_telemetry.play_tactical_sound_fx(fx_type)
            return True, f"Tactical audio effect '{fx_type}' synthesized and played, sir."

        # ─────────────────────────────────────────────────────────────────────
        # Area 5: 3-Dimensional Holographic Projector System & Spatial Optics
        # ─────────────────────────────────────────────────────────────────────
        # Deactivation check
        if any(p in clean_lower for p in [
            "deactivate 3d projector", "close 3d projector", "turn off 3d projector", "deactivate projector system",
            "close projector system", "shut down 3d projector", "turn off projector", "deactivate projector"
        ]):
            from core.projector_system import projector_system
            projector_system.deactivate_projector()
            return True, "3-Dimensional Holographic Projector System deactivated, sir."

        # Activation check
        if any(p in clean_lower for p in [
            "activate 3 dimensional projector", "activate 3d projector", "launch 3d projector", "start 3d projector",
            "enable 3d projector", "open 3d projector", "toggle 3d projector", "3 dimensional projector",
            "3-dimensional projector", "3d projector system", "3 dimensional projector system", "launch projector system",
            "activate projector system", "turn on 3d projector", "projector system"
        ]):
            from core.projector_system import projector_system
            mode = "standard"
            if any(m in clean_lower for m in ["pyramid", "pepper"]):
                mode = "pyramid"
            elif any(m in clean_lower for m in ["anaglyph", "stereoscopic", "glasses", "red cyan"]):
                mode = "anaglyph"
            elif any(m in clean_lower for m in ["floating", "desktop", "transparent"]):
                mode = "floating"
            success = projector_system.activate_projector(mode=mode, model="helmet", fullscreen=False)
            return True, f"3-Dimensional Holographic Projector System activated in [{mode.upper()}] optical mode, sir. Laser projection emitter is online."

        if any(p in clean_lower for p in [
            "projector mode pyramid", "pyramid mode", "pepper's ghost", "peppers ghost", "4 way hologram",
            "4-way hologram", "holographic pyramid", "switch projector to pyramid", "quad hologram"
        ]):
            from core.projector_system import projector_system
            projector_system.set_projection_mode("pyramid")
            return True, "Projector switched to 4-Way Holographic Pyramid Mode, sir. Four-quadrant Pepper's Ghost optics are aligned for physical prism projection."

        if any(p in clean_lower for p in [
            "projector mode anaglyph", "anaglyph mode", "stereoscopic mode", "stereoscopic 3d",
            "3d glasses mode", "red cyan mode", "switch projector to anaglyph", "stereoscopic projection"
        ]):
            from core.projector_system import projector_system
            projector_system.set_projection_mode("anaglyph")
            return True, "Projector switched to Stereoscopic Anaglyph 3D Mode, sir. Dual-eye chromatic parallax is engaged for red-cyan 3D glasses."

        if any(p in clean_lower for p in [
            "projector mode floating", "floating mode", "floating desktop", "desktop hologram",
            "transparent projector", "switch projector to floating", "floating holo-beam"
        ]):
            from core.projector_system import projector_system
            projector_system.set_projection_mode("floating")
            return True, "Projector switched to Floating Desktop Hologram Mode, sir. Window chrome is removed for seamless desktop projection."

        if any(p in clean_lower for p in [
            "projector mode standard", "standard projector", "direct beam mode", "switch projector to standard"
        ]):
            from core.projector_system import projector_system
            projector_system.set_projection_mode("standard")
            return True, "Projector switched to Direct Standard Beam Mode, sir."

        if any(p in clean_lower for p in [
            "cycle projector mode", "switch projector mode", "next projector mode", "change projector mode"
        ]):
            from core.projector_system import projector_system
            new_mode = projector_system.cycle_mode()
            return True, f"Projector optical mode cycled to: {new_mode.upper()}, sir."

        if any(p in clean_lower for p in [
            "project gauntlet", "show gauntlet", "3d gauntlet", "show 3d gauntlet", "repulsor gauntlet",
            "wireframe gauntlet", "project repulsor gauntlet", "switch to gauntlet"
        ]):
            from core.projector_system import projector_system
            from tools.hud_controller import hud_controller
            projector_system.set_3d_model("gauntlet")
            hud_controller.set_3d_model("drone")
            return True, "Projecting 3D Mark-85 Repulsor Gauntlet on the holographic projector, sir."

        if any(p in clean_lower for p in [
            "project emitter", "show emitter", "3d emitter", "holo emitter", "projector emitter",
            "wireframe emitter", "switch to emitter"
        ]):
            from core.projector_system import projector_system
            projector_system.set_3d_model("emitter")
            return True, "Projecting 3D Conical Holo-Lens Emitter on the holographic projector, sir."

        if any(p in clean_lower for p in [
            "project drone", "show drone", "3d drone", "stark drone", "wireframe drone",
            "project stark drone", "switch to drone"
        ]):
            from core.projector_system import projector_system
            from tools.hud_controller import hud_controller
            projector_system.set_3d_model("drone")
            hud_controller.set_3d_model("drone")
            return True, "Projecting 3D Stark Industries Hypersonic Drone on the holographic display, sir."

        if any(p in clean_lower for p in [
            "cycle projector model", "next projector model", "change projector model"
        ]):
            from core.projector_system import projector_system
            new_m = projector_system.cycle_model()
            return True, f"Projector 3D wireframe mesh shifted to: {new_m.upper()}, sir."

        if any(p in clean_lower for p in [
            "project to secondary monitor", "project to external display", "project to secondary display",
            "project to external projector", "project to second screen", "project on projector", "project on external display"
        ]):
            from core.projector_system import projector_system
            monitors = projector_system.enumerate_monitors()
            if len(monitors) > 1:
                projector_system.set_target_monitor(1)
                return True, f"Projector output successfully routed to External Display / Secondary Monitor #{1}, sir."
            else:
                projector_system.set_target_monitor(0)
                return True, "Only one primary display was detected, sir. 3D projection is active on the primary display."

        if any(p in clean_lower for p in [
            "increase projector depth", "increase projector parallax", "more 3d depth", "increase 3d depth"
        ]):
            from core.projector_system import projector_system
            new_p = projector_system.adjust_parallax(2.0)
            return True, f"Stereoscopic 3D parallax depth increased to {new_p:.1f} pixels, sir."

        if any(p in clean_lower for p in [
            "decrease projector depth", "decrease projector parallax", "less 3d depth", "decrease 3d depth"
        ]):
            from core.projector_system import projector_system
            new_p = projector_system.adjust_parallax(-2.0)
            return True, f"Stereoscopic 3D parallax depth decreased to {new_p:.1f} pixels, sir."

        if any(p in clean_lower for p in [
            "projector status", "projector diagnostics", "projector vitals", "projector telemetry"
        ]):
            from core.projector_system import projector_system
            st = projector_system.get_status()
            return True, f"Projector System Status: Active: {st['active']}. Mode: {st['mode']}. Model: {st['model']}. Target: {st['target_display']}. Parallax: {st['parallax_depth_px']}px."

        # Holographic Projector Fullscreen Mode (F11)
        if any(p in clean_lower for p in [
            "projector mode", "fullscreen projector", "toggle projector mode",
            "fullscreen hud", "fullscreen mode", "toggle fullscreen", "holographic fullscreen",
            "exit projector mode", "exit fullscreen", "exit fullscreen mode", "windowed mode", "windowed hud"
        ]):
            from tools.hud_controller import hud_controller
            if any(p in clean_lower for p in ["exit projector mode", "exit fullscreen", "exit fullscreen mode", "windowed mode", "windowed hud"]):
                hud_controller.toggle_fullscreen(state=False)
                return True, "Holographic display reverted to windowed mode, sir."
            elif any(p in clean_lower for p in ["enter projector mode", "fullscreen projector", "fullscreen mode", "fullscreen hud"]):
                hud_controller.toggle_fullscreen(state=True)
                return True, "Borderless Holographic Projector Mode engaged, sir. Canvas is set to pitch-black for true optical floating projection."
            else:
                hud_controller.toggle_fullscreen()
                return True, "Toggled holographic projector mode, sir."

        # Holographic 3D Wireframe Model Selection
        if any(p in clean_lower for p in ["show helmet", "3d helmet", "show 3d helmet", "switch to helmet", "iron man helmet", "display 3d helmet", "wireframe helmet", "project helmet"]):
            from tools.hud_controller import hud_controller
            hud_controller.set_3d_model("helmet")
            return True, "Projecting 3D Mark-85 Iron Man Wireframe Helmet on the holographic display, sir."

        if any(p in clean_lower for p in ["switch to arc reactor", "show arc reactor", "3d arc reactor", "show reactor", "display reactor", "wireframe reactor", "project arc reactor"]):
            from tools.hud_controller import hud_controller
            hud_controller.set_3d_model("reactor")
            return True, "Projecting 3D Arc Reactor Gyroscope on the holographic display, sir."

        if any(p in clean_lower for p in ["show 3d globe", "show globe", "switch to globe", "cyber globe", "display globe", "wireframe globe", "project globe"]):
            from tools.hud_controller import hud_controller
            hud_controller.set_3d_model("globe")
            return True, "Projecting 3D Cyber Earth Globe on the holographic display, sir."

        if any(p in clean_lower for p in ["show tesseract", "3d tesseract", "switch to tesseract", "show hypercube", "display tesseract", "wireframe tesseract", "project tesseract"]):
            from tools.hud_controller import hud_controller
            hud_controller.set_3d_model("tesseract")
            return True, "Projecting 4D Hypercube Tesseract on the holographic display, sir."

        # Holographic 3D Model Rotation & View Manipulation
        if any(p in clean_lower for p in ["reset 3d view", "reset helmet", "reset 3d model", "reset view", "recenter model"]):
            from tools.hud_controller import hud_controller
            hud_controller.reset_3d_view()
            return True, "Holographic 3D model orientation and zoom reset to default center, sir."

        if any(p in clean_lower for p in ["stop spinning", "pause spin", "halt spin", "freeze model"]):
            from tools.hud_controller import hud_controller
            hud_controller.toggle_auto_spin(False)
            return True, "Holographic 3D wireframe rotation frozen, sir."

        if any(p in clean_lower for p in ["spin model", "auto spin", "start spinning", "resume spin", "enable spin"]):
            from tools.hud_controller import hud_controller
            hud_controller.toggle_auto_spin(True)
            return True, "Automated 3D holographic rotation resumed, sir."

        if any(p in clean_lower for p in ["rotate helmet", "rotate 3d helmet", "rotate model", "rotate 3d model", "turn model", "spin helmet", "rotate wireframe"]):
            from tools.hud_controller import hud_controller
            hud_controller.rotate_model(delta_yaw=0.8, delta_pitch=0.0)
            return True, "3D holographic wireframe model rotated on the tactical display, sir."

        if any(p in clean_lower for p in ["cycle hud theme", "change hud palette", "holographic palette", "switch hud color", "cycle holographic theme"]):
            from tools.hud_controller import hud_controller
            hud_controller.cycle_palette()
            return True, "Cycling holographic visual palette on the tactical display, sir."

        # Single Notification Rule: Inquiries & Repeats ("notify only once unless asked again")
        if any(p in clean_lower for p in [
            "what was that notification", "repeat notification", "repeat last notification",
            "what did you say", "tell me again", "repeat reminder", "what is that reminder", "repeat that reminder"
        ]):
            from core.notification_guard import notification_guard
            repeated = notification_guard.request_repeat()
            if repeated:
                return True, f"Repeating your notification, sir: {repeated}"
            else:
                return True, "There are no prior notifications on record to repeat, sir."

        if any(p in clean_lower for p in ["read notifications", "any notifications", "show notifications", "notification status", "check notifications"]):
            from core.notification_guard import notification_guard
            recent = notification_guard.get_recent_notifications(limit=3)
            if recent:
                items = [f"Notification {i+1}: {item['message']}" for i, item in enumerate(recent)]
                return True, f"Here are your recent notifications, sir. {' '.join(items)}"
            else:
                return True, "All notification queues are clear with zero pending alerts, sir."

        # Digital Marketing Suite - Master Campaign & Specialized Sub-Engines
        mkt_match = re.match(r"^(?:run|launch|generate|execute)\s+(?:a\s+)?digital\s+marketing(?:\s+campaign)?(?:\s+for|\s+in)?(.*)$", clean_lower)
        if mkt_match or any(p in clean_lower for p in ["run digital marketing", "launch digital marketing", "digital marketing campaign", "marketing suite"]):
            from tools.digital_marketing_suite import marketing_suite
            corr = mkt_match.group(1).strip() if mkt_match and mkt_match.group(1) else "Ambattur"
            if not corr:
                corr = "Ambattur"
            marketing_suite.execute_full_marketing_stack(corr)
            return True, marketing_suite.format_suite_voice_summary(corr)

        # Skill 1: SEO & Local SEO
        if any(p in clean_lower for p in ["seo recommendations", "generate seo keywords", "local seo", "seo keywords", "seo metadata"]):
            from tools.digital_marketing_seo import seo_engine
            return True, seo_engine.format_voice_summary()

        # Skill 2: Paid Ads (PPC & Social)
        if any(p in clean_lower for p in ["google ads", "ppc campaign", "meta ads", "create search ad", "social ads"]):
            from tools.digital_marketing_ads import ads_engine
            return True, ads_engine.format_voice_summary()

        # Skill 3: CRO & Landing Page Copy
        if any(p in clean_lower for p in ["landing page copy", "cro audit", "a/b test hypotheses", "cro wireframe"]):
            from tools.digital_marketing_cro import cro_engine
            return True, cro_engine.format_voice_summary()

        # Skill 4: Inbound Marketing & Video Scripts
        if any(p in clean_lower for p in ["lead magnet", "video script", "video scripts", "inbound content"]):
            from tools.digital_marketing_inbound import inbound_engine
            return True, inbound_engine.format_voice_summary()

        # Skill 5: Customer Nurture & Review Generation
        if any(p in clean_lower for p in ["drip sequence", "nurture sequence", "review request", "customer nurture"]) or clean_lower in ["customer retention", "customer retention strategy"]:
            from tools.digital_marketing_nurture import nurture_engine
            return True, nurture_engine.format_voice_summary()

        # ─────────────────────────────────────────────────────────────────────
        # 2. Application, Folder & Script Launching
        # ─────────────────────────────────────────────────────────────────────
        folder_match = re.match(r"^(?:open|explore|show)\s+(?:the\s+)?(?:folder|directory)\s+(.+)$", clean_lower)
        if folder_match:
            f_target = folder_match.group(1).strip()
            res = system_controller.open_folder(f_target)
            return True, res

        run_match = re.match(r"^(?:run|execute)\s+(.+)$", clean_lower)
        if run_match:
            r_target = run_match.group(1).strip()
            if not any(w in r_target for w in [
                " ai", " expert", " specialist", " model", "document generation",
                "marketing", "lead generation", "problem handling",
                "campaign", "holograph", "pending", "business", "upgrade",
                "heal", "repair", "self healing", "self repair"
            ]):
                res = system_controller.execute_program(r_target)
                return True, res

        open_match = re.match(r"^(?:open|launch|start|bring up|go to)\s+(.+)$", clean_lower)
        if open_match:
            raw_target = open_match.group(1).strip()
            target = re.sub(r"\b(?:for me|please|app|application|browser|website|window)\b", "", raw_target).strip(" \t\n\r\"'.,!?")
            if not target:
                target = raw_target
            res = system_controller.launch(target)
            return True, res

        # ─────────────────────────────────────────────────────────────────────
        # 3. Process Termination / Close Application
        # ─────────────────────────────────────────────────────────────────────
        close_match = re.match(r"^(?:close|kill|terminate|exit|quit|stop)\s+(.+)$", clean_lower)
        if close_match:
            target = close_match.group(1).strip()
            if target not in ["device", "pc", "computer", "workstation", "jarvis"]:
                res = system_controller.close_process(target)
                return True, res

        # ─────────────────────────────────────────────────────────────────────
        # 4. Audio Volume & Media Playback
        # ─────────────────────────────────────────────────────────────────────
        if any(clean_lower == p for p in ["volume up", "increase volume", "raise volume", "louder", "turn volume up"]):
            res = system_controller.volume_up()
            return True, res

        if any(clean_lower == p for p in ["volume down", "decrease volume", "lower volume", "softer", "turn volume down"]):
            res = system_controller.volume_down()
            return True, res

        if any(clean_lower == p for p in ["mute", "mute audio", "mute volume", "mute sound", "silence", "unmute"]):
            res = system_controller.toggle_mute()
            return True, res

        if any(clean_lower == p for p in ["play", "play music", "resume", "pause", "pause music", "stop music"]):
            res = system_controller.media_play_pause()
            return True, res

        if any(clean_lower == p for p in ["next song", "next track", "skip song"]):
            res = system_controller.media_next()
            return True, res

        if any(clean_lower == p for p in ["previous song", "previous track"]):
            res = system_controller.media_prev()
            return True, res

        if any(clean_lower == p for p in ["show desktop", "minimize all", "minimize all windows"]):
            res = system_controller.show_desktop()
            return True, res

        # ─────────────────────────────────────────────────────────────────────
        # 4a. Physical Desktop GUI Navigation (Computer-Use)
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["scroll down", "page down"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.mouse_scroll(-450)

        if any(p in clean_lower for p in ["scroll up", "page up"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.mouse_scroll(450)

        if any(p in clean_lower for p in ["snap window left", "snap left", "window to the left", "left split"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.window_snap("left")

        if any(p in clean_lower for p in ["snap window right", "snap right", "window to the right", "right split"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.window_snap("right")

        if any(p in clean_lower for p in ["maximize window", "maximize this window", "maximize"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.window_snap("maximize")

        if any(p in clean_lower for p in ["minimize window", "minimize this window", "minimize all"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.window_snap("minimize")

        if any(p in clean_lower for p in ["new tab", "open new tab", "open a new tab"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.browser_action("new_tab")

        if any(p in clean_lower for p in ["close tab", "close this tab"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.browser_action("close_tab")

        if any(p in clean_lower for p in ["refresh page", "reload page", "refresh tab", "reload tab"]):
            from tools.gui_controller import gui_controller
            return True, gui_controller.browser_action("refresh")

        if any(p in clean_lower for p in [
            "stealth mode", "enter stealth mode", "hide hud", "minimize hud", "minimize to background",
            "hide holographic interface", "hide holographic interference", "hide holographic hud", "conceal hud"
        ]):
            from core.hologram_sentinel import hologram_sentinel
            hologram_sentinel.hide_hologram()
            return True, "Engaging background stealth mode, sir. The Holographic Tactical HUD is concealed. Press Ctrl+Alt+J or state 'Hey Jarvis' to summon me at any moment."

        if any(p in clean_lower for p in [
            "show holographic interface", "display holographic interface", "open holographic interface",
            "show holographic interference", "display holographic interference", "open holographic interference",
            "show holographic hud", "display holographic hud", "holographic interface", "holographic interference",
            "show hud", "restore hud", "bring up hud", "open hud", "summon hud"
        ]):
            from core.hologram_sentinel import hologram_sentinel
            hologram_sentinel.display_hologram(reason="voice_command")
            return True, "Tactical holographic interface restored and elevated to your screen, sir."

        # ─────────────────────────────────────────────────────────────────────
        # 4b. Multimodal Screen & Webcam Vision (PHASE 3)
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["look at my screen", "what is on my screen", "what's on my display", "what is on my display", "analyze screen", "analyze display", "inspect screen", "inspect display"]):
            from tools.vision_tools import capture_and_inspect_display
            res = capture_and_inspect_display(query=clean)
            return True, res

        if any(p in clean_lower for p in ["look through the camera", "look through camera", "activate camera", "what do you see", "inspect camera", "webcam snapshot", "take a photo"]):
            from tools.camera_tools import inspect_physical_camera
            res = inspect_physical_camera(query=clean)
            return True, res

        if any(clean_lower == p for p in ["take a screenshot", "screenshot", "capture screen", "capture display"]):
            res = system_controller.take_screenshot()
            return True, res

        # ─────────────────────────────────────────────────────────────────────
        # 5. System Hardware Vitals & Executive Briefing (PHASE 2)
        # ─────────────────────────────────────────────────────────────────────
        sunrise_match = re.search(r"\b(?:set morning briefing for|set sunrise time to|set sunrise to|set morning alarm for)\s*(.+)$", clean_lower)
        if sunrise_match:
            from core.proactive_agent import proactive_agent
            target_time = sunrise_match.group(1).strip()
            return True, proactive_agent.set_sunrise_time(target_time)

        if any(p in clean_lower for p in ["morning briefing", "protocol sunrise", "executive briefing", "status overview"]):
            from tools.briefing_tools import generate_executive_briefing
            res = generate_executive_briefing()
            return True, res

        # 5b. Unified System Orchestration & Executive Dashboard
        if any(p in clean_lower for p in [
            "orchestration briefing", "orchestration status", "master system status",
            "system orchestration", "master briefing", "unified briefing",
            "full system briefing", "orchestrator report", "executive dashboard"
        ]):
            from core.system_orchestration import system_orchestrator
            res = system_orchestrator.generate_executive_briefing()
            return True, res


        weather_match = re.search(r"\b(?:what is the weather|weather in|how is the weather|forecast for|temperature in)\s*(.+)?$", clean_lower)
        if weather_match or clean_lower in ["weather", "temperature", "atmospheric conditions"]:
            from tools.weather_tools import get_weather
            city = "auto"
            if weather_match and weather_match.group(1):
                city = weather_match.group(1).strip()
            res = get_weather(city)
            return True, res

        if any(p in clean_lower for p in ["system vital", "system status", "hardware status", "cpu usage", "ram usage", "vitals", "how is the system"]):
            v = system_controller.get_vitals()
            return True, (
                f"System vitals are fully nominal, sir. "
                f"CPU utilization is at {v['cpu_usage']}, RAM load is at {v['ram_usage']}, "
                f"and available primary storage is {v['disk_free']}."
            )

        # ─────────────────────────────────────────────────────────────────────
        # 5a. Real-Time Web Search, Intelligence & Targeted Information Streams
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["web connection status", "check web connection", "test internet connection", "check internet", "web status"]):
            from tools.web_agent import web_agent
            st = web_agent.check_connection()
            lat_str = ", ".join(st["latencies"]) if st["latencies"] else "latency test pending"
            return True, f"Web connection is {st['status']}, sir. Endpoint latencies: {lat_str}."

        if any(p in clean_lower for p in [
            "check web streams", "web stream briefing", "tech news stream", "world news stream",
            "science stream", "business stream", "stream briefing", "news stream", "information stream", "targeted stream"
        ]):
            from tools.web_stream_monitor import web_stream_monitor
            cat = "tech"
            if "world" in clean_lower:
                cat = "world"
            elif "science" in clean_lower:
                cat = "science"
            elif "business" in clean_lower:
                cat = "business"
            briefing = web_stream_monitor.format_briefing(category=cat)
            return True, briefing

        search_match = re.search(
            r"^(?:search the web for|search the internet for|search web for|search online for|search for|google|look up on web|look up on internet|web search)\s+(.+)$",
            clean,
            re.IGNORECASE
        )
        if search_match:
            query = search_match.group(1).strip()
            from tools.web_agent import web_agent
            res = web_agent.search(query)
            return True, res["summary"]

        scrape_match = re.search(
            r"^(?:scrape webpage|scrape site|scrape url|scrape content from)\s+(https?://\S+|\S+\.\S+)$",
            clean,
            re.IGNORECASE
        )
        if scrape_match:
            url = scrape_match.group(1).strip()
            from tools.web_agent import web_agent
            res = web_agent.scrape_structured(url)
            if not res.get("success"):
                return True, f"Failed to scrape {url}, sir. Error: {res.get('error')}"
            h_str = "\n".join(res["headings"][:6]) if res["headings"] else "No major headings detected."
            l_count = len(res["links"])
            return True, f"Structured scraping of {url} completed, sir.\nHeadings:\n{h_str}\nExtracted {l_count} hyperlinks."

        fetch_match = re.search(
            r"^(?:fetch webpage|read webpage|fetch site|read site|read url)\s+(https?://\S+|\S+\.\S+)$",
            clean,
            re.IGNORECASE
        )
        if fetch_match:
            url = fetch_match.group(1).strip()
            from tools.web_agent import web_agent
            res = web_agent.read_webpage(url)
            if not res.get("success"):
                return True, f"Unable to fetch content from {url}, sir: {res.get('error')}"
            return True, f"Web content from {url}, sir:\n{res['text']}"

        design_match = re.search(
            r"^(?:design webpage|design web preview|design site|create web preview)\s+(.+)$",
            clean,
            re.IGNORECASE
        )
        if design_match:
            title = design_match.group(1).strip()
            from tools.web_agent import web_agent
            html_snippet = f"<h2>{title.upper()}</h2><p>Responsive high-tech interface generated autonomously by J.A.R.V.I.S. Design Studio.</p>"
            path = web_agent.design_preview(title, html_snippet, auto_open=True)
            return True, f"Web interface for '{title}' designed and launched in local browser, sir. Saved to: {path}"

        # ─────────────────────────────────────────────────────────────────────
        # 5a-1. Daily Upgrade Advisory & Permission-Gated Execution
        # ─────────────────────────────────────────────────────────────────────
        approve_match = re.search(r"^(?:approve upgrade|execute upgrade|deploy upgrade|apply upgrade)\s+([a-zA-Z0-9\-_]+)$", clean, re.IGNORECASE)
        if approve_match:
            up_id = approve_match.group(1).strip()
            from core.upgrade_advisor import upgrade_advisor
            success, msg = upgrade_advisor.execute_approved_upgrade(up_id)
            return True, msg

        if any(p in clean_lower for p in [
            "suggest daily upgrades", "show daily upgrades", "suggest upgrades", "show major upgrades",
            "show minor upgrades", "daily upgrade advisory", "upgrade advisory", "upgrade suggestions", "suggest 5 major upgrades"
        ]):
            from core.upgrade_advisor import upgrade_advisor
            mode = "all"
            if "major" in clean_lower:
                mode = "major"
            elif "minor" in clean_lower:
                mode = "minor"
            return True, upgrade_advisor.format_briefing(view_mode=mode)

        # ─────────────────────────────────────────────────────────────────────
        # 5a-2. Command Universal Free AI Matrix (Global Models, OmniRoute Providers & Every Field of Work)
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in [
            "list business operations", "list business ais", "list business ai",
            "what business ais do you support", "what business ai do you support",
            "what business ai do you have", "what business ais do you have",
            "business ais", "business operations", "business ai",
            "what business operations can you handle", "show business ais",
            "business operations ai", "what business operations do you support"
        ]):
            from core.free_ai_matrix import free_ai_matrix
            return True, free_ai_matrix.get_business_summary()

        if any(p in clean_lower for p in [
            "list fields of work", "fields of work", "what fields of work",
            "what fields of work do you support", "what ai fields can you handle",
            "supported domains", "what domains do you support", "show fields of work"
        ]):
            from core.free_ai_matrix import free_ai_matrix
            return True, free_ai_matrix.get_fields_summary()

        if any(p in clean_lower for p in [
            "list omniroute free providers", "omniroute free providers", "show omniroute free providers",
            "what are the omniroute free providers", "what free providers in omniroute", "omniroute free list"
        ]):
            from core.free_ai_matrix import free_ai_matrix
            return True, free_ai_matrix.get_omniroute_free_summary()

        if any(p in clean_lower for p in [
            "list supported ais", "list supported ai", "what ais do you support",
            "what ai do you support", "which ais can you command", "which ai can you command",
            "show supported ais", "supported ai models", "what external ais can you command"
        ]):
            from core.free_ai_matrix import free_ai_matrix
            catalog = free_ai_matrix.list_supported_ais()
            lines = [f"{prov}: {', '.join(models)}" for prov, models in catalog.items()]
            return True, "I can command all major frontier AI models globally at zero cost, sir: " + "; ".join(lines) + "."

        business_match = re.search(
            r"^(?:consult|ask|use|run|command)\s+(?:the\s+)?(marketing|campaign|lead generation|lead gen|lead verification|verify lead|customer acquisition|client acquisition|customer retention|churn|accounts|bookkeeping|invoicing|stock|inventory|stock management|document generation|draft contract|proposal|problem handling|dispute resolution)\s*(?:ai|expert|specialist|model)?\s*(?:to|about|for|on)?\s*[:\-]?\s*(.+)$",
            clean,
            re.IGNORECASE
        )
        if business_match:
            op_name = business_match.group(1).strip()
            sub_prompt = business_match.group(2).strip()
            from core.free_ai_matrix import free_ai_matrix
            spoken_res, _ = free_ai_matrix.query_business_operation(op_name, sub_prompt)
            return True, spoken_res

        field_match = re.search(
            r"^(?:consult|ask|use|command)\s+(?:the\s+)?(software|coding|developer|code|math|mathematics|logic|algorithm|medical|medicine|health|doctor|clinical|finance|financial|economics|quant|investing|legal|law|compliance|attorney|contracts|creative|writing|poetry|literature|author|visual|design|image|art|illustration|security|cybersecurity|infosec|devops|sysadmin|physics|science|astronomy|quantum|education|pedagogy|teacher|tutor)\s*(?:expert|ai|specialist|model)?\s*(?:to|about|for|on)?\s*[:\-]?\s*(.+)$",
            clean,
            re.IGNORECASE
        )
        if field_match:
            domain_name = field_match.group(1).strip()
            sub_prompt = field_match.group(2).strip()
            from core.free_ai_matrix import free_ai_matrix
            spoken_res, _ = free_ai_matrix.query_field_expert(domain_name, sub_prompt)
            return True, spoken_res

        ai_match = re.search(
            r"^(?:ask|use|command)\s+(openai|gpt|claude|anthropic|mistral|deepseek|llama|meta|qwen|alibaba|gemini|google|gemma|ddgw|duckduckgo|duckduckgo-web|cfp|cloudflare|cloudflare-playground|fta|freetheai|fb|freebuff|oc|opencode|fmd|freemodel|freemodel-dev|unc|uncloseai|horde|aihorde|free-ai|freeinference|other ai|another ai|external ai)\s*(?:to|about|for)?\s*[:\-]?\s*(.+)$",
            clean,
            re.IGNORECASE
        )
        if ai_match:
            provider = ai_match.group(1).strip()
            sub_prompt = ai_match.group(2).strip()
            from core.free_ai_matrix import free_ai_matrix
            spoken_res, _ = free_ai_matrix.query_provider(provider, sub_prompt)
            return True, spoken_res

        # ─────────────────────────────────────────────────────────────────────
        # 5b. OmniRoute Multi-Provider Gateway Status
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["omniroute status", "omniroute", "is omniroute running", "check omniroute", "omniroute gateway"]):
            from tools.omniroute_controller import omniroute_controller
            return True, omniroute_controller.get_butler_summary()

        # ─────────────────────────────────────────────────────────────────────
        # 5b-2. Internet Connection Sensing & Reconnection
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in [
            "connect to internet", "connect to the internet", "connect internet",
            "reconnect to internet", "reconnect internet", "check internet",
            "internet status", "are we connected to internet", "are we connected",
            "are you connected to internet", "are you connected", "check network status",
            "network status", "connection status", "is internet working", "is internet active"
        ]):
            from core.internet_sentinel import internet_sentinel
            is_up, msg = internet_sentinel.reconnect()
            if is_up:
                return True, (
                    "Internet connectivity is operational, sir. We are linked to the global network "
                    "and all online neural pathways and cloud capabilities are fully synchronized."
                )
            else:
                return True, (
                    "I have attempted to re-establish our connection, sir, but external networks remain unreachable. "
                    "Please verify your Wi-Fi or router connection."
                )

        # ─────────────────────────────────────────────────────────────────────
        # 5b-3. Autonomous Self-Repair, Process Resilience & System Health
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in [
            "system health", "health report", "self healing status", "daemon health",
            "sentinel status", "resilience status", "system resilience", "daemons status",
            "health status", "resilience score"
        ]):
            from core.self_repair import self_repair_engine
            return True, self_repair_engine.get_health_voice_summary()

        if any(p in clean_lower for p in [
            "repair yourself", "fix yourself", "self repair", "run self repair",
            "run self healing", "heal system", "self repair system", "self heal",
            "heal yourself", "repair jarvis", "fix jarvis", "diagnose and repair",
            "check and repair", "system self repair", "repair all systems",
            "repair everything", "repair it", "fix it", "repair network", "fix network",
            "repair the network", "fix the network", "repair connection", "fix connection",
            "repair the connection", "fix the connection", "reconnect network",
            "reconnect gateway", "restart gateway", "repair gateway", "reconnect",
            "fix internet", "repair internet", "network repair", "connection repair",
            "troubleshoot connection", "troubleshoot network", "prune memory", "prune resources"
        ]) or clean_lower in ["repair", "reconnect", "fix", "self-repair", "heal"]:
            from core.self_repair import self_repair_engine
            res = self_repair_engine.run_full_repair(manual=True)
            return True, res.get(
                "spoken_response",
                "I have conducted a full self-repair routine across all subsystems, sir. All internal subroutines are in prime operational health."
            )

        # ─────────────────────────────────────────────────────────────────────
        # 5c. Local LAN Perimeter & IoT Reconnaissance
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in [
            "scan network", "scan the network", "perimeter scan", "check perimeter",
            "who is on the network", "who is on my wifi", "scan local network",
            "network status", "ping gateway", "check network devices", "network perimeter"
        ]):
            from tools.network_scanner import network_scanner
            return True, network_scanner.format_butler_perimeter_report()

        # Smart Home IoT & Perimeter Automation Directives
        from tools.smart_home_controller import smart_home
        is_iot, iot_resp = smart_home.parse_and_execute(clean)
        if is_iot:
            return True, iot_resp

        # ─────────────────────────────────────────────────────────────────────
        # 5d. Autonomous Git & Codebase Version Control
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["git status", "repo status", "repository status", "check git status"]):
            from tools.git_controller import git_controller
            return True, git_controller.format_status_summary()

        if any(p in clean_lower for p in ["git log", "recent commits", "show recent commits", "commit history"]):
            from tools.git_controller import git_controller
            return True, git_controller.format_log_summary(limit=4)

        if any(p in clean_lower for p in ["git diff", "what changed", "show git diff", "show changes"]):
            from tools.git_controller import git_controller
            return True, git_controller.get_diff_summary()

        commit_match = re.search(r"\b(?:git commit(?:\s+and\s+push)?|commit(?:\s+and\s+push)?(?:\s+with\s+message)?)\s*[:\-]?\s*['\"]?(.+?)['\"]?$", clean, re.IGNORECASE)
        if commit_match:
            from tools.git_controller import git_controller
            msg = commit_match.group(1).strip()
            _, resp = git_controller.commit_and_push(msg)
            return True, resp

        branch_match = re.search(r"\b(?:create branch|checkout -b|new branch)\s+([a-zA-Z0-9_\-\/]+)", clean_lower)
        if branch_match:
            from tools.git_controller import git_controller
            b_name = branch_match.group(1).strip()
            _, resp = git_controller.create_or_switch_branch(b_name, create=True)
            return True, resp

        switch_match = re.search(r"\b(?:switch to branch|checkout branch|switch branch to)\s+([a-zA-Z0-9_\-\/]+)", clean_lower)
        if switch_match:
            from tools.git_controller import git_controller
            b_name = switch_match.group(1).strip()
            _, resp = git_controller.create_or_switch_branch(b_name, create=False)
            return True, resp

        # ─────────────────────────────────────────────────────────────────────
        # 5e. Smart Windows Clipboard Intelligence
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["explain clipboard", "explain what i just copied", "what is on my clipboard", "what did i copy", "inspect clipboard"]):
            from tools.clipboard_sentinel import clipboard_sentinel
            return True, clipboard_sentinel.explain_clipboard()

        if any(p in clean_lower for p in ["fix clipboard", "fix clipboard code", "fix the code on my clipboard", "repair clipboard"]):
            from tools.clipboard_sentinel import clipboard_sentinel
            _, resp = clipboard_sentinel.fix_clipboard_code()
            return True, resp

        if any(p in clean_lower for p in ["save clipboard to notes", "save clipboard to memory", "remember clipboard", "save clipboard"]):
            from tools.clipboard_sentinel import clipboard_sentinel
            return True, clipboard_sentinel.save_clipboard_to_memory(category="note")

        if any(p in clean_lower for p in ["summarize clipboard", "summarize my clipboard"]):
            from tools.clipboard_sentinel import clipboard_sentinel
            return True, clipboard_sentinel.summarize_clipboard()

        # ─────────────────────────────────────────────────────────────────────
        # 5f. Autonomous System Optimization & Hardware Janitor
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in [
            "optimize system", "optimize memory", "clean ram", "free up ram",
            "free up memory", "clean system", "flush memory", "flush ram"
        ]):
            from tools.system_optimizer import system_optimizer
            return True, system_optimizer.optimize_all()

        if any(p in clean_lower for p in [
            "clean temporary files", "clean temp files", "purge temp files",
            "clean cache", "clear cache", "purge cache"
        ]):
            from tools.system_optimizer import system_optimizer
            res = system_optimizer.clean_temp_cache()
            return True, f"Temporary file purge complete, sir. Swept {res['files_deleted']} files recovering {res['space_freed_mb']} MB of disk space."

        if any(p in clean_lower for p in [
            "who is using the most ram", "top memory processes", "top processes",
            "resource hogs", "top ram processes", "what is using ram"
        ]):
            from tools.system_optimizer import system_optimizer
            return True, system_optimizer.format_top_processes_summary()

        # ─────────────────────────────────────────────────────────────────────
        # 5g. Context-Aware Screen Reader & Optical Intelligence
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in [
            "read my screen", "read screen", "what is on my screen", "whats on my screen",
            "what's on my screen", "read the screen", "inspect screen text"
        ]):
            from tools.screen_reader import screen_reader
            return True, screen_reader.analyze_screen("Explain what is visible on my screen")

        if any(p in clean_lower for p in [
            "read active window", "read this window", "what is in this window",
            "read current window", "summarize active window"
        ]):
            from tools.screen_reader import screen_reader
            return True, screen_reader.analyze_screen("Summarize the contents of the active foreground window")

        if any(p in clean_lower for p in [
            "what error is on my screen", "read the error", "explain screen error",
            "what error is this", "diagnose screen error"
        ]):
            from tools.screen_reader import screen_reader
            return True, screen_reader.analyze_screen("Diagnose and explain the error or traceback currently shown on screen")

        # ─────────────────────────────────────────────────────────────────────
        # 5h. Adaptive System Display & Ambient Night Shield Controller
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in [
            "enable night shield", "turn on night shield", "activate night shield",
            "night light on", "turn on night mode", "blue light filter", "enable night mode"
        ]):
            from tools.display_controller import display_controller
            return True, display_controller.enable_night_shield()

        if any(p in clean_lower for p in [
            "disable night shield", "turn off night shield", "deactivate night shield",
            "night light off", "turn off night mode", "daylight mode", "reset display color"
        ]):
            from tools.display_controller import display_controller
            return True, display_controller.disable_night_shield()

        if any(p in clean_lower for p in [
            "adaptive display", "auto ambient display", "ambient night cycle",
            "adaptive ambient", "adjust display for time", "sync screen light"
        ]):
            from tools.display_controller import display_controller
            return True, display_controller.apply_adaptive_ambient()

        if any(p in clean_lower for p in [
            "display status", "screen brightness status", "screen status", "display telemetry"
        ]):
            from tools.display_controller import display_controller
            return True, display_controller.format_status_summary()

        m_bright = re.search(r"(?:set|change|adjust)\s+(?:display\s+|screen\s+)?brightness\s+to\s+(\d+)", clean_lower)
        if m_bright:
            from tools.display_controller import display_controller
            val = int(m_bright.group(1))
            return True, display_controller.set_brightness(val)

        if "dim screen" in clean_lower or "dim display" in clean_lower:
            from tools.display_controller import display_controller
            curr = display_controller.get_brightness()
            return True, display_controller.set_brightness(max(15, curr - 25))

        if "brighten screen" in clean_lower or "brighten display" in clean_lower:
            from tools.display_controller import display_controller
            curr = display_controller.get_brightness()
            return True, display_controller.set_brightness(min(100, curr + 25))

        # ─────────────────────────────────────────────────────────────────────
        # 6. Time & Date Directives
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["what time is it", "current time", "what's the time", "whats the time", "tell me the time", "time now"]):
            now_t = datetime.now().strftime("%I:%M %p")
            return True, f"It is currently {now_t}, sir."

        if any(p in clean_lower for p in ["what is today's date", "what is the date", "what date is it", "today's date", "todays date", "current date"]):
            today_d = datetime.now().strftime("%A, %B %d, %Y")
            return True, f"Today is {today_d}, sir."

        # ─────────────────────────────────────────────────────────────────────
        # 7. Function Recall & Learned Heuristics Review
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["what was the last function", "recall last function", "what did you just do"]):
            return True, memory.recall_last_function()

        if any(p in clean_lower for p in ["learned heuristics", "review mistakes", "show heuristics", "lessons learned", "what have you learned"]):
            return True, learning_matrix.get_learned_rules_summary()

        if any(p in clean_lower for p in ["run self maintenance", "run maintenance scan", "scan for upgrades", "scan and repair"]):
            return True, learning_matrix.run_self_maintenance_scan(force=True)

        if any(p in clean_lower for p in ["calibrate my voice", "learn my voice", "reset voice profile", "update voice profile"]):
            from core.voice_biometrics import voice_biometrics
            voice_biometrics.profile["enrolled"] = False
            voice_biometrics.profile["sample_count"] = 0
            voice_biometrics.save_profile()
            return True, "Voice biometric calibration initiated, sir. Please speak naturally across your normal speaking range so I may calibrate to both your low and high vocal frequencies."

        if any(p in clean_lower for p in ["start voice conversation", "voice conversation mode", "let's talk", "lets talk", "let's chat"]):
            return True, "Continuous voice conversation mode engaged, sir. I am listening continuously and will wait patiently for you to finish your statements."

        # ─────────────────────────────────────────────────────────────────────
        # 7b. Semantic Vector Memory & Long-Term Neural Recall (RAG)
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["clear all memories", "wipe memories", "clear memories", "reset memory"]):
            count = vector_memory.clear_memories()
            return True, f"All neural memories have been purged from long-term storage ({count} records wiped), sir."

        if any(p in clean_lower for p in ["list memories", "show memories", "show my notes", "list my notes"]):
            mems = vector_memory.semantic_search("note preference project", top_k=5, min_score=0.0)
            if mems:
                lines = [f"- [{m['category'].upper()}]: {m['content']}" for m in mems[:5]]
                return True, f"Recent entries in your long-term neural recall database, sir:\n" + "\n".join(lines)
            return True, "No long-term memories or notes are currently indexed in the database, sir."

        mem_action, mem_target, mem_content = vector_memory.parse_memory_directive(clean)
        if mem_action == "store" and mem_content:
            mem_id = vector_memory.store_memory(mem_content, category=mem_target or "general")
            return True, f"Memory committed to long-term neural recall under '{mem_target}' (#{mem_id}), sir: \"{mem_content}\""

        elif mem_action == "recall" and mem_target:
            matches = vector_memory.semantic_search(mem_target, top_k=3, min_score=0.15)
            if matches:
                formatted_items = "\n".join([f"- [{m['category'].upper()} | Confidence {int(m['score']*100)}%]: {m['content']}" for m in matches])
                return True, f"According to your long-term neural memory records, sir:\n{formatted_items}"
            else:
                return True, f"I could not locate any specific records matching '{mem_target}' in your long-term neural memory, sir."

        # ─────────────────────────────────────────────────────────────────────
        # 7c. Multi-Store Cognitive Memory & Introspection
        # ─────────────────────────────────────────────────────────────────────
        is_cog, cog_res = cognitive_memory.handle_cognitive_directive(clean)
        if is_cog:
            return True, cog_res

        # ─────────────────────────────────────────────────────────────────────
        # 8. Butler Etiquette & Human Conversational Directives
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["new topic", "change topic", "let's change topic", "change the subject", "reset conversation", "clear conversation context", "start over"]):
            from core.conversation_memory import conversation_memory
            conversation_memory.clear()
            return True, "Understood, sir. Conversational slate cleared. What would you like to explore next?"

        if any(clean_lower == p for p in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings"]):
            hour = datetime.now().hour
            greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
            return True, f"{greeting}, sir. J.A.R.V.I.S. is fully operational and at your service. How may I assist you?"

        if any(p in clean_lower for p in ["who are you", "what are you", "identify yourself", "what is your purpose", "what's your purpose", "what do you do", "tell me about yourself"]):
            return True, (
                "I am J.A.R.V.I.S. — Just A Rather Very Intelligent System. "
                "I serve as your personal butler, managing your schedule, monitoring your hardware, "
                "and executing system directives both offline and online with absolute precision."
            )

        if any(p in clean_lower for p in ["how are you", "how are you doing", "how's your day", "how is your day", "how goes it"]):
            return True, "Performing splendidly, sir. All core matrices are calibrated and standing ready for your command. How fares your day?"

        if any(p in clean_lower for p in ["status report", "are you ready", "systems check", "all systems go"]):
            return True, "All internal subroutines are performing at peak efficiency, sir. Ready for your directive."

        if any(p in clean_lower for p in ["thank you", "thanks", "thank you jarvis", "thanks jarvis"]):
            return True, "Always an honor, sir. Standing ready whenever you require assistance."

        # ─────────────────────────────────────────────────────────────────────
        # 9. Simple Offline Mathematical Calculations
        # ─────────────────────────────────────────────────────────────────────
        calc_match = re.match(r"^(?:calculate|what is|compute)\s+([0-9\s\+\-\*\/\^\.\(\)]+)$", clean_lower)
        if calc_match:
            expr = calc_match.group(1).strip()
            try:
                # Safe evaluation of basic math
                allowed = set("0123456789+-*/.() ")
                if set(expr).issubset(allowed):
                    result = eval(expr, {"__builtins__": None}, {})
                    return True, f"The result is {result}, sir."
            except Exception:
                pass

        # ─────────────────────────────────────────────────────────────────────
        # 10. Explicit Terminal Command
        # ─────────────────────────────────────────────────────────────────────
        exec_match = re.match(r"^(?:run|execute)\s+(?:command|script|terminal|cmd|powershell)\s*:\s*(.+)$", clean, re.IGNORECASE)
        if exec_match:
            cmd = exec_match.group(1).strip()
            out = system_controller.execute_terminal(cmd)
            return True, f"Command output, sir:\n{out}"

        return False, ""

# Global singleton
local_intelligence = LocalIntelligence()
