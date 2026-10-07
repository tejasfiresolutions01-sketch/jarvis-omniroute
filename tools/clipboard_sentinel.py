"""
J.A.R.V.I.S. Smart Windows Clipboard Sentinel & Quick-Action Bridge.
Monitors, classifies, explains, debugs, and stores Windows clipboard contents.
Integrates directly with Semantic Vector Memory and Python AST validation.
"""

import re
import ast
import json
import urllib.parse
from typing import Dict, Any, Tuple, Optional
import pyperclip
from core.vector_memory import vector_memory

class ClipboardSentinel:
    """
    Stark Desktop Clipboard Custodian.
    Instantly inspects, explains, fixes, and archives data copied by the user.
    """

    def get_clipboard_text(self) -> str:
        """Retrieves raw text from Windows clipboard."""
        try:
            return pyperclip.paste() or ""
        except Exception:
            return ""

    def set_clipboard_text(self, text: str) -> bool:
        """Copies text onto Windows clipboard."""
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    def classify_content(self, text: str) -> str:
        """Identifies type of content currently on clipboard."""
        clean = text.strip()
        if not clean:
            return "empty"

        if "Traceback (most recent call last)" in clean or re.search(r"\b[A-Za-z]+Error:\s+", clean):
            return "stack_trace"

        if clean.startswith(("http://", "https://", "www.")):
            return "url"

        if (clean.startswith("{") and clean.endswith("}")) or (clean.startswith("[") and clean.endswith("]")):
            try:
                json.loads(clean)
                return "json"
            except Exception:
                pass

        if any(clean.startswith(prefix) for prefix in ["python ", "git ", "npm ", "pip ", "docker ", "powershell "]):
            return "shell_command"

        # Check Python code patterns
        python_keywords = ["def ", "class ", "import ", "from ", "return ", "if __name__", "lambda "]
        if any(kw in clean for kw in python_keywords):
            return "python_code"

        return "prose"

    def explain_clipboard(self) -> str:
        """Analyzes and articulates the contents of the user's active clipboard."""
        text = self.get_clipboard_text().strip()
        if not text:
            return "Your clipboard is currently vacant, sir. Copy any text, error, or code to inspect it."

        c_type = self.classify_content(text)

        if c_type == "stack_trace":
            err_match = re.search(r"([A-Za-z]+Error|[A-Za-z]+Exception):\s*(.+)", text)
            file_match = re.search(r'File "([^"]+)", line (\d+)', text)
            err_name = err_match.group(1) if err_match else "Exception"
            err_desc = err_match.group(2) if err_match else "Traceback anomaly"
            loc = f" in {file_match.group(1)} at line {file_match.group(2)}" if file_match else ""
            return (
                f"Your clipboard contains an active stack trace, sir: `{err_name}`{loc}. "
                f"Issue summary: {err_desc}. State 'Jarvis, fix clipboard' if you would like me to correct it."
            )

        elif c_type == "python_code":
            try:
                tree = ast.parse(text)
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                details = []
                if classes:
                    details.append(f"classes: {', '.join(classes)}")
                if funcs:
                    details.append(f"functions: {', '.join(funcs)}")
                struct_desc = f" ({'; '.join(details)})" if details else ""
                return f"Clipboard contains valid Python code structure{struct_desc}, sir. Total {len(text.splitlines())} lines."
            except SyntaxError as e:
                return f"Clipboard contains Python code with a syntax error on line {e.lineno}, sir: {e.msg}."

        elif c_type == "url":
            parsed = urllib.parse.urlparse(text)
            return f"Clipboard contains a web URL directing to `{parsed.netloc}`, sir: {text[:80]}."

        elif c_type == "json":
            try:
                data = json.loads(text)
                keys = list(data.keys()) if isinstance(data, dict) else [f"array of {len(data)} items"]
                return f"Clipboard contains valid JSON data with attributes: {', '.join(map(str, keys[:6]))}, sir."
            except Exception:
                return "Clipboard contains formatted JSON notation, sir."

        elif c_type == "shell_command":
            return f"Clipboard contains a system terminal command, sir: `{text[:100]}`."

        # Prose / General text
        lines = text.splitlines()
        word_count = len(text.split())
        preview = text[:140].replace("\n", " ")
        return f"Clipboard holds {word_count} words ({len(lines)} lines) of text, sir: \"{preview}...\""

    def fix_clipboard_code(self) -> Tuple[bool, str]:
        """Validates and fixes common syntax mistakes in Python clipboard snippet."""
        text = self.get_clipboard_text().strip()
        if not text:
            return False, "Your clipboard is currently vacant, sir."

        # Test if it already parses
        try:
            ast.parse(text)
            return True, "The code currently on your clipboard is syntactically sound, sir. No syntax corrections needed."
        except SyntaxError:
            pass

        # Attempt automated heuristic corrections (e.g. missing colons on def/if/for/while, mixed indentation)
        lines = text.splitlines()
        fixed_lines = []
        corrections_made = 0

        for line in lines:
            stripped = line.rstrip()
            # Missing trailing colon on control structures
            if re.match(r"^\s*(?:def\s+[a-zA-Z0-9_]+\s*\(.*?\)|class\s+[a-zA-Z0-9_]+(?:\(.*?\))?|if\s+.*|elif\s+.*|else|for\s+.*|while\s+.*|try|except.*|finally)$", stripped):
                if not stripped.endswith(":"):
                    stripped += ":"
                    corrections_made += 1
            fixed_lines.append(stripped)

        candidate = "\n".join(fixed_lines)
        try:
            ast.parse(candidate)
            self.set_clipboard_text(candidate)
            return True, f"Syntax corrections applied successfully, sir ({corrections_made} missing colons restored). The corrected code has been copied back to your clipboard."
        except SyntaxError as e:
            return False, f"Automated syntax repair was unable to resolve all errors, sir: Line {e.lineno}: {e.msg}."

    def save_clipboard_to_memory(self, category: str = "note") -> str:
        """Commits the active clipboard contents into Semantic Vector Memory."""
        text = self.get_clipboard_text().strip()
        if not text:
            return "Your clipboard is currently vacant, sir. Nothing to archive."

        mem_id = vector_memory.store_memory(
            content=text,
            category=category,
            metadata={"source": "windows_clipboard"}
        )
        preview = text[:60].replace("\n", " ")
        return f"Clipboard contents committed to long-term neural recall under '{category}' (#{mem_id}), sir: \"{preview}...\""

    def summarize_clipboard(self) -> str:
        """Returns concise summary of clipboard text."""
        text = self.get_clipboard_text().strip()
        if not text:
            return "Your clipboard is vacant, sir."

        words = text.split()
        if len(words) <= 25:
            return f"Clipboard text is concise ({len(words)} words), sir: \"{text}\""

        # Extract leading and trailing key sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) >= 2:
            summary = f"{sentences[0]} {sentences[-1]}"
        else:
            summary = " ".join(words[:30]) + "..."
        return f"Clipboard executive summary, sir: {summary}"

# Global singleton
clipboard_sentinel = ClipboardSentinel()
