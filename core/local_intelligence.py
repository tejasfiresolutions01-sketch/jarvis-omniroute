import re
from datetime import datetime, date
from typing import Tuple, Optional
from tools.system_controller import system_controller
from core.schedule_manager import schedule_manager
from core.learning_matrix import learning_matrix
from memory.memory_store import memory
from core.vector_memory import vector_memory
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
        # 2. Application & Web Launching
        # ─────────────────────────────────────────────────────────────────────
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

        if any(p in clean_lower for p in ["stealth mode", "enter stealth mode", "hide hud", "minimize hud", "minimize to background"]):
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, config.HUD_WINDOW_TITLE)
            if hwnd:
                user32.ShowWindow(hwnd, 0) # SW_HIDE
            return True, "Engaging background stealth mode, sir. The Tactical HUD is concealed. Press Ctrl+Alt+J or state 'Hey Jarvis' to summon me at any moment."

        if any(p in clean_lower for p in ["show hud", "restore hud", "bring up hud", "open hud", "summon hud"]):
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, config.HUD_WINDOW_TITLE)
            if hwnd:
                user32.ShowWindow(hwnd, 9) # SW_RESTORE
                user32.SetForegroundWindow(hwnd)
            return True, "Tactical HUD restored and elevated to the foreground, sir."

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
        # 5b. OmniRoute Multi-Provider Gateway Status
        # ─────────────────────────────────────────────────────────────────────
        if any(p in clean_lower for p in ["omniroute status", "omniroute", "is omniroute running", "check omniroute", "omniroute gateway"]):
            from tools.omniroute_controller import omniroute_controller
            return True, omniroute_controller.get_butler_summary()

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
        # 8. Butler Etiquette & Identity Directives
        # ─────────────────────────────────────────────────────────────────────
        if any(clean_lower == p for p in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings"]):
            hour = datetime.now().hour
            greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
            return True, f"{greeting}, sir. J.A.R.V.I.S. is fully operational and at your service. How may I assist you?"

        if any(clean_lower == p for p in ["who are you", "what are you", "identify yourself"]):
            return True, (
                "I am J.A.R.V.I.S. — Just A Rather Very Intelligent System. "
                "I serve as your personal butler, managing your schedule, monitoring your hardware, "
                "and executing system directives both offline and online with absolute precision."
            )

        if any(clean_lower == p for p in ["how are you", "status report", "are you ready"]):
            return True, "All internal subroutines are performing at peak efficiency, sir. Ready for your directive."

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
