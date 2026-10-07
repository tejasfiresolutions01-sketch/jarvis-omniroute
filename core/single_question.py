import re

def enforce_single_question(text: str) -> str:
    """
    Enforces J.A.R.V.I.S. Single-Question Protocol:
    The butler will only ask at most one clarifying question at a time.
    If multiple question marks are detected, retains only the primary question.
    """
    if not text:
        return text

    q_count = text.count("?")
    if q_count <= 1:
        return text

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    processed = []
    question_found = False

    for s in sentences:
        if "?" in s:
            if not question_found:
                processed.append(s)
                question_found = True
            else:
                # Convert secondary questions to declarative statements or drop them
                clean = s.replace("?", ".")
                # If short secondary question like "Shall I?", drop it
                if len(clean.split()) > 3:
                    processed.append(clean)
        else:
            processed.append(s)

    result = " ".join(processed).strip()
    # Guarantee strict count of '?' is at most 1
    if result.count("?") > 1:
        first_q = result.find("?")
        result = result[:first_q + 1] + result[first_q + 1:].replace("?", ".")
    return result
