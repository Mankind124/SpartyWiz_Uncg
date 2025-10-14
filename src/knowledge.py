from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml

_FACTS_PATH = Path("data/facts.yaml")
_PROGRAMS_PATH = Path("data/programs.json")


def load_facts(path: Path = _FACTS_PATH) -> Dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_programs(path: Path = _PROGRAMS_PATH) -> Dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f) or {}


def quick_answer(question: str, profile: Optional[Dict] = None) -> Optional[Tuple[str, list]]:
    """Return a direct answer for common facts/program queries if available.
    Returns (answer, sources) or None if not handled.
    """
    q = (question or "").lower()
    facts = load_facts()
    progs = load_programs()

    # Enrollment / facts
    if any(k in q for k in ["enrollment", "student enrollment", "number of students", "student population"]):
        data = facts.get("enrollment")
        if data and data.get("value"):
            answer = f"UNCG enrollment is about {data['value']} (as of {data.get('as_of','N/A')})."
            srcs = [data.get("source")] if data.get("source") else []
            return answer, srcs

    # Student-faculty ratio
    if "student-faculty" in q or "student faculty" in q:
        data = facts.get("student_faculty_ratio")
        if data and data.get("value"):
            answer = f"UNCG's student–faculty ratio is {data['value']} (as of {data.get('as_of','N/A')})."
            srcs = [data.get("source")] if data.get("source") else []
            return answer, srcs

    # Program credit hours queries
    if any(k in q for k in ["credit hour", "credit-hour", "credit hours", "credits required", "minimum credits"]):
        # try to match a known program in the question
        for prog_name, meta in progs.items():
            if prog_name.lower() in q:
                min_cred = meta.get("min_credits")
                if min_cred:
                    answer = f"The {prog_name} typically requires {min_cred} credit hours."
                    url = meta.get("catalog_url")
                    srcs = [url] if url else []
                    return answer, srcs

    return None
