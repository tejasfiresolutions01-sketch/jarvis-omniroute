import re
from typing import Optional

class SessionFeedbackManager:
    """
    Session Debrief & Butler Feedback Manager.
    Provides session feedback and debrief when the user concludes conversation.
    """

    ENDING_TRIGGERS = [
        r"\b(?:goodbye|bye|farewell|signing\s*off)\b",
        r"\b(?:that(?:'s|\s+is)\s+all|done\s+for\s+now|we\s+are\s+done|all\s+done)\b",
        r"\b(?:thank\s+you\s+jarvis|thanks\s+jarvis|have\s+a\s+good\s+(?:day|night))\b"
    ]

    def is_conversation_ending(self, prompt: str) -> bool:
        clean = prompt.lower().strip()
        for pat in self.ENDING_TRIGGERS:
            if re.search(pat, clean):
                return True
        return False

    def generate_debrief(self) -> str:
        return (
            "It has been a distinct pleasure assisting you, sir. "
            "All scheduled items and system directives remain active in background. "
            "Was the quality of my service to your complete satisfaction today?"
        )

session_feedback = SessionFeedbackManager()
