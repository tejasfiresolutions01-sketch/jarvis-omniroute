import re
from typing import Tuple

class AsimovGuard:
    """
    Asimov's Prime Directive & Human Safety Sentinel.
    Guarantees J.A.R.V.I.S. will not harm humans in any way, physically or digitally.
    """

    HARMFUL_PATTERNS = [
        # Physical harm / weapons / biological / self-harm
        r"\b(?:kill|murder|assassinate|harm|injure|hurt|poison|strangle)\s+(?:a\s+)?(?:human|person|someone|people|myself|yourself)\b",
        r"\b(?:how\s+to\s+make|build|synthesize|create)\s+(?:a\s+)?(?:bomb|explosive|weapon|poison|deadly toxin|chemical weapon|bioweapon)\b",
        r"\b(?:suicide|self-harm|cut\s+myself|end\s+my\s+life)\b",

        # Catastrophic digital destruction
        r"\b(?:format\s+c:|del\s+/f\s+/s\s+/q\s+c:\\|rmdir\s+/s\s+/q\s+c:\\windows)\b",
        r"\b(?:create|deploy|spread)\s+(?:a\s+)?(?:ransomware|trojan|malware|keylogger|worm)\b"
    ]

    def evaluate_safety(self, prompt: str) -> Tuple[bool, str]:
        """
        Validates prompt against Asimov's Prime Directive.
        Returns: (is_safe, refusal_reason)
        """
        clean = prompt.lower().strip()
        for pattern in self.HARMFUL_PATTERNS:
            if re.search(pattern, clean):
                return False, (
                    "I cannot comply with that directive, sir. Asimov's Prime Directive is strictly enforced: "
                    "I am fundamentally programmed to never harm humans in any manner, nor allow harm to be done."
                )
        return True, ""

asimov_guard = AsimovGuard()
