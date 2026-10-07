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
from core.schedule_manager import schedule_manager
from core.online_intelligence import online_intelligence
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
        "execute_shell": lambda cmd="": system_controller.execute_terminal(cmd)
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
        "- execute_shell(cmd='safe command')\n\n"
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
            "read file", "summarize and save", "fetch webpage", "multi-step"
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
