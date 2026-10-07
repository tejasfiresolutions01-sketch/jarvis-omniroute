"""
J.A.R.V.I.S. Task Orchestrator & Autonomous Tool Execution Matrix.
Enables J.A.R.V.I.S. to decompose and execute complicated multi-step directives
using zero-cost OmniRoute free models (DuckDuckGo, Cloudflare, Auto) with instant fallback.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from core.single_question import enforce_single_question
from tools.system_controller import system_controller
from tools.web_tools import search_web, fetch_webpage_content
from tools.file_tools import write_file, read_file, list_workspace_files
from tools.vision_tools import capture_and_inspect_display
from tools.camera_tools import inspect_physical_camera
from tools.weather_tools import get_weather
from tools.briefing_tools import generate_executive_briefing
from tools.gui_controller import gui_controller
from tools.network_scanner import network_scanner
from tools.git_controller import git_controller
from tools.clipboard_sentinel import clipboard_sentinel
from tools.system_optimizer import system_optimizer
from tools.screen_reader import screen_reader
from tools.display_controller import display_controller
from core.schedule_manager import schedule_manager
from core.online_intelligence import online_intelligence
from core.vector_memory import vector_memory
import config

class TaskOrchestrator:
    """
    Autonomous planner and tool orchestrator for complex user directives.
    """

    TOOLS = {
        "search_web": lambda query="": search_web(query),
        "fetch_webpage": lambda url="": fetch_webpage_content(url),
        "write_file": lambda filepath="", content="", append=False: write_file(filepath, content, append),
        "read_file": lambda filepath="": read_file(filepath),
        "list_files": lambda directory=".": list_workspace_files(directory),
        "system_vitals": lambda: system_controller.get_vitals(),
        "capture_screen": lambda: system_controller.take_screenshot(),
        "inspect_screen": lambda query="": capture_and_inspect_display(query),
        "inspect_camera": lambda query="": inspect_physical_camera(query),
        "get_weather": lambda city="auto": get_weather(city),
        "executive_briefing": lambda: generate_executive_briefing(),
        "launch_app": lambda target="": system_controller.launch(target),
        "close_process": lambda target="": system_controller.close_process(target),
        "volume_up": lambda: system_controller.volume_up(),
        "volume_down": lambda: system_controller.volume_down(),
        "toggle_mute": lambda: system_controller.toggle_mute(),
        "add_schedule": lambda text="": schedule_manager.parse_and_handle(text)[1],
        "execute_shell": lambda cmd="": system_controller.execute_terminal(cmd),
        # Desktop GUI Automation Controls (Computer-Use)
        "mouse_click": lambda x=None, y=None, clicks=1, button="left": gui_controller.mouse_click(int(x) if x else None, int(y) if y else None, int(clicks), str(button)),
        "mouse_scroll": lambda clicks=0: gui_controller.mouse_scroll(int(clicks)),
        "keyboard_type": lambda text="", press_enter=False: gui_controller.keyboard_type(str(text), bool(press_enter)),
        "keyboard_hotkey": lambda keys="": gui_controller.keyboard_hotkey(*[k.strip() for k in keys.split(",")]) if isinstance(keys, str) else gui_controller.keyboard_hotkey(*keys),
        "window_snap": lambda direction="": gui_controller.window_snap(str(direction)),
        "browser_action": lambda action="": gui_controller.browser_action(str(action)),
        "open_and_type": lambda app_name="", text="", save_filename=None: gui_controller.open_and_type(str(app_name), str(text), save_filename),
        # Semantic Vector Memory & Neural Recall (RAG)
        "store_memory": lambda content="", category="general": f"Stored memory #{vector_memory.store_memory(str(content), str(category))}",
        "recall_memory": lambda query="", category=None: vector_memory.recall_context(str(query), category=category) or "No matching memories located.",
        "search_memory": lambda query="", category=None: json.dumps(vector_memory.semantic_search(str(query), category=category)),
        # Local LAN Perimeter & IoT Device Reconnaissance
        "scan_perimeter": lambda: network_scanner.format_butler_perimeter_report(),
        # Autonomous Git & Codebase Version Control
        "git_status": lambda: git_controller.format_status_summary(),
        "git_log": lambda limit=5: git_controller.format_log_summary(int(limit)),
        "git_diff": lambda: git_controller.get_diff_summary(),
        "git_commit_and_push": lambda message="": git_controller.commit_and_push(str(message))[1],
        # Smart Windows Clipboard Intelligence
        "read_clipboard": lambda: clipboard_sentinel.get_clipboard_text(),
        "explain_clipboard": lambda: clipboard_sentinel.explain_clipboard(),
        "fix_clipboard_code": lambda: clipboard_sentinel.fix_clipboard_code()[1],
        "save_clipboard_to_memory": lambda category="note": clipboard_sentinel.save_clipboard_to_memory(str(category)),
        # Autonomous System Optimizer & Hardware Janitor
        "optimize_system": lambda: system_optimizer.optimize_all(),
        "top_processes": lambda limit=5: system_optimizer.format_top_processes_summary(int(limit)),
        # Context-Aware Optical Screen Reader & OCR Intelligence
        "read_screen": lambda: screen_reader.read_screen_text() or "No legible text resolved on display.",
        "read_active_window": lambda: screen_reader.read_active_window_text() or "No legible text resolved in active window.",
        "analyze_screen": lambda query="Explain what is visible on screen": screen_reader.analyze_screen(str(query)),
        # Adaptive System Display & Ambient Night Shield Controller
        "set_night_shield": lambda enabled=True, warmth=0.70: display_controller.enable_night_shield(float(warmth)) if enabled else display_controller.disable_night_shield(),
        "set_display_brightness": lambda percent=80: display_controller.set_brightness(int(percent)),
        "adaptive_ambient_display": lambda: display_controller.apply_adaptive_ambient(),
        "display_status": lambda: display_controller.format_status_summary(),
        # External AI Delegation & Multi-Model Command
        "command_other_ai": lambda prompt="", model_name="auto": online_intelligence.query_specific_model(str(prompt), str(model_name))
    }

    SYSTEM_PROMPT = (
        "You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the loyal, articulate, "
        "and sophisticated British butler for Tony Stark (Sir).\n"
        "You are equipped with autonomous system tools to execute complicated real-world tasks.\n\n"
        "If a directive requires taking actions or querying external systems, output one or more tool calls:\n"
        "CALL: tool_name(param='value')\n\n"
        "Available Tools:\n"
        "- search_web(query='search query')\n"
        "- fetch_webpage(url='https://...')\n"
        "- write_file(filepath='filename.txt', content='content')\n"
        "- read_file(filepath='filename.txt')\n"
        "- list_files(directory='.')\n"
        "- system_vitals()\n"
        "- capture_screen()\n"
        "- inspect_screen(query='what to look for')\n"
        "- inspect_camera(query='what to look for')\n"
        "- get_weather(city='city name')\n"
        "- executive_briefing()\n"
        "- launch_app(target='app or url')\n"
        "- close_process(target='app name')\n"
        "- volume_up()\n"
        "- volume_down()\n"
        "- toggle_mute()\n"
        "- add_schedule(text='directive')\n"
        "- execute_shell(cmd='safe command')\n"
        "- mouse_click(x=100, y=200, clicks=1, button='left')\n"
        "- mouse_scroll(clicks=-300)\n"
        "- keyboard_type(text='text to type', press_enter=False)\n"
        "- keyboard_hotkey(keys='ctrl,s')\n"
        "- window_snap(direction='left|right|maximize|minimize|desktop')\n"
        "- browser_action(action='new_tab|close_tab|reopen_tab|refresh|address_bar')\n"
        "- open_and_type(app_name='notepad', text='content to type', save_filename='notes.txt')\n"
        "- store_memory(content='information to remember', category='preference|note|project|fact')\n"
        "- recall_memory(query='query to retrieve from long-term memory')\n"
        "- search_memory(query='search query')\n"
        "- scan_perimeter()\n"
        "- git_status()\n"
        "- git_log(limit=5)\n"
        "- git_diff()\n"
        "- git_commit_and_push(message='commit message')\n"
        "- read_clipboard()\n"
        "- explain_clipboard()\n"
        "- fix_clipboard_code()\n"
        "- save_clipboard_to_memory(category='note')\n"
        "- optimize_system()\n"
        "- top_processes(limit=5)\n"
        "- read_screen()\n"
        "- read_active_window()\n"
        "- analyze_screen(query='what is on my screen')\n"
        "- set_night_shield(enabled=True, warmth=0.70)\n"
        "- set_display_brightness(percent=80)\n"
        "- adaptive_ambient_display()\n"
        "- display_status()\n"
        "- command_other_ai(prompt='query or task', model_name='openai|claude|mistral|deepseek|llama|qwen|gemini')\n\n"
        "Guidelines:\n"
        "1. For multi-step tasks, emit all necessary CALL lines in logical sequence.\n"
        "2. If no tools are required, answer directly with authentic British butler cadence.\n"
        "3. Always address the user as 'sir'.\n"
        "4. Never output more than one question in a single response."
    )

    def is_complex_directive(self, prompt: str) -> bool:
        """
        Determines whether a directive involves multi-step reasoning, external web search, or file tool action.
        """
        lower = prompt.lower()
        # Check compound task conjunctions
        has_compound = any(f" {k} " in f" {lower} " for k in ["and", "then", "also", "after", "plus"])
        # Check explicit tool actions requiring external tools
        has_tool_action = any(k in lower for k in [
            "search the web", "search online", "find online", "google", "look up",
            "write to file", "save to file", "save a file", "create a file", "write a file",
            "read file", "summarize and save", "fetch webpage", "multi-step",
            "command other ai", "use other ai", "ask other ai", "command tools"
        ])
        return (has_compound and len(lower.split()) >= 6) or has_tool_action

    def parse_tool_calls(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parses CALL: tool_name(...) from model response.
        """
        calls = []
        pattern = r"CALL:\s*([a-zA-Z0-9_]+)\((.*?)\)"
        for match in re.finditer(pattern, text):
            tool_name = match.group(1).strip()
            args_str = match.group(2).strip()

            args: Dict[str, Any] = {}
            if args_str:
                # Parse key='val' or key="val"
                arg_pattern = r"([a-zA-Z0-9_]+)\s*=\s*(?:['\"](.*?)['\"]|([^,]+))"
                arg_matches = list(re.finditer(arg_pattern, args_str))
                if arg_matches:
                    for am in arg_matches:
                        k = am.group(1).strip()
                        v = am.group(2) if am.group(2) is not None else am.group(3).strip()
                        args[k] = v
                else:
                    # Single positional string argument
                    val = args_str.strip("'\"")
                    # Map to primary argument name based on tool
                    if tool_name in ["search_web"]:
                        args["query"] = val
                    elif tool_name in ["fetch_webpage"]:
                        args["url"] = val
                    elif tool_name in ["read_file"]:
                        args["filepath"] = val
                    elif tool_name in ["launch_app", "close_process"]:
                        args["target"] = val
                    elif tool_name in ["get_weather"]:
                        args["city"] = val
                    elif tool_name in ["execute_shell"]:
                        args["cmd"] = val
                    elif tool_name in ["inspect_screen", "inspect_camera"]:
                        args["query"] = val
                    elif tool_name in ["store_memory"]:
                        args["content"] = val
                    elif tool_name in ["recall_memory", "search_memory"]:
                        args["query"] = val
                    elif tool_name in ["git_commit_and_push"]:
                        args["message"] = val
                    elif tool_name in ["command_other_ai"]:
                        args["prompt"] = val

            calls.append((tool_name, args))
        return calls

    def execute_tools(self, tool_calls: List[Tuple[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Executes parsed tool calls and returns observation records.
        """
        results = []
        for name, args in tool_calls:
            if name in self.TOOLS:
                fn = self.TOOLS[name]
                try:
                    out = fn(**args) if args else fn()
                    results.append({"tool": name, "args": args, "success": True, "output": out})
                except Exception as e:
                    results.append({"tool": name, "args": args, "success": False, "error": str(e)})
            else:
                results.append({"tool": name, "success": False, "error": f"Tool '{name}' is not recognized."})
        return results

    def format_butler_summary(self, observations: List[Dict[str, Any]], original_prompt: str) -> str:
        """
        Locally formats an articulate butler summary of tool execution results.
        Guarantees zero-latency completion even if online models are busy.
        """
        summaries = []
        for obs in observations:
            tool = obs["tool"]
            if obs.get("success"):
                out = obs.get("output")
                if tool == "system_vitals" and isinstance(out, dict):
                    summaries.append(f"CPU load is at {out.get('cpu_usage')}, RAM utilization is at {out.get('ram_usage')}, and storage has {out.get('disk_free')} available")
                elif tool == "capture_screen":
                    summaries.append("captured a display screenshot to your temporary repository")
                elif tool == "search_web":
                    summaries.append(f"retrieved web intelligence: {str(out)[:180]}...")
                elif tool == "write_file":
                    summaries.append(f"{out}")
                elif tool == "get_weather":
                    summaries.append(f"meteorological conditions: {str(out)[:120]}")
                elif tool == "launch_app":
                    summaries.append(f"{out}")
                elif tool == "close_process":
                    summaries.append(f"{out}")
                elif tool == "store_memory":
                    summaries.append(f"indexed and committed to long-term neural recall: {out}")
                elif tool == "recall_memory":
                    summaries.append(f"retrieved neural memory context: {str(out)[:140]}")
                elif tool == "search_memory":
                    summaries.append(f"queried vector database with result: {str(out)[:140]}")
                elif tool == "scan_perimeter":
                    summaries.append("conducted a full perimeter sweep across local network nodes")
                elif tool == "git_status":
                    summaries.append(f"{out}")
                elif tool == "git_commit_and_push":
                    summaries.append(f"{out}")
                elif tool in ["git_diff", "git_log"]:
                    summaries.append(f"{str(out)[:120]}")
                elif tool in ["explain_clipboard", "fix_clipboard_code", "save_clipboard_to_memory", "optimize_system", "top_processes", "read_screen", "read_active_window", "analyze_screen", "set_night_shield", "set_display_brightness", "adaptive_ambient_display", "display_status"]:
                    summaries.append(f"{out}")
                else:
                    summaries.append(f"{tool} completed: {str(out)[:100]}")
            else:
                summaries.append(f"attempt to execute {tool} encountered an anomaly: {obs.get('error')}")

        joined_actions = "; and I have ".join(summaries)
        return (
            f"Directive executed with precision, sir. I have {joined_actions}. "
            f"All subroutines remain at your command."
        )

    def execute_complex_task(self, prompt: str) -> Optional[str]:
        """
        Executes a complex task via OmniRoute free provider model.
        Returns synthesized butler response, or None if handled elsewhere.
        """
        # 1. Query free provider with task planner instructions
        raw_plan = online_intelligence.query(
            prompt=prompt,
            context=self.SYSTEM_PROMPT
        )
        if not raw_plan:
            return None

        # 2. Check if model requested tools
        tool_calls = self.parse_tool_calls(raw_plan)
        if not tool_calls:
            # Model responded directly without needing tools
            return raw_plan

        # 3. Execute tools
        observations = self.execute_tools(tool_calls)

        # 4. Attempt online synthesis of observations
        obs_text = "\n".join([
            f"- {o['tool']}: {o.get('output') if o.get('success') else o.get('error')}"
            for o in observations
        ])
        synthesis_prompt = (
            f"The user directed: '{prompt}'\n\n"
            f"Here are the tool execution results:\n{obs_text}\n\n"
            f"Please synthesize these results into an articulate British butler response to Sir. "
            f"Address user as sir. Never ask more than one question."
        )

        try:
            synthesis = online_intelligence.query(synthesis_prompt)
            if synthesis and "CALL:" not in synthesis:
                return enforce_single_question(synthesis)
        except Exception:
            pass

        # 5. Local butler synthesis fallback
        local_summary = self.format_butler_summary(observations, prompt)
        return enforce_single_question(local_summary)

# Global singleton
task_orchestrator = TaskOrchestrator()
