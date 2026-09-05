"""
agent/command_interpreter.py
----------------------------
Multilingual Natural Language Understanding (NLU) Engine for GATE JARVIS.
Parses user voice/text commands in English, Hindi, and Marathi into structured intents & parameters.
"""

import re
from typing import Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class CommandIntent:
    intent_name: str
    detected_language: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_prompt: str = ""
    suggested_tool: str = ""


# Common Mechanical & Engineering Subject Keywords
SUBJECT_KEYWORDS = {
    "thermodynamics": "Thermodynamics",
    "thermo": "Thermodynamics",
    "entropy": "Thermodynamics",
    "som": "Strength of Materials",
    "strength of materials": "Strength of Materials",
    "bending": "Strength of Materials",
    "torsion": "Strength of Materials",
    "fluids": "Fluid Mechanics",
    "fluid mechanics": "Fluid Mechanics",
    "bernoulli": "Fluid Mechanics",
    "heat transfer": "Heat Transfer",
    "conduction": "Heat Transfer",
    "convection": "Heat Transfer",
    "radiation": "Heat Transfer",
    "tom": "Theory of Machines",
    "theory of machines": "Theory of Machines",
    "vibrations": "Vibrations",
    "machine design": "Machine Design",
    "maths": "Engineering Mathematics",
    "mathematics": "Engineering Mathematics",
    "calculus": "Engineering Mathematics",
    "manufacturing": "Manufacturing",
    "production": "Manufacturing",
    "industrial": "Industrial Engineering",
    "aptitude": "General Aptitude",
}


def detect_language(text: str) -> str:
    """Identifies if text contains Devanagari script for Marathi / Hindi or Roman script."""
    text_lower = text.lower()
    # Check Devanagari characters
    devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
    if devanagari_count > 0:
        # Check specific Marathi marker words vs Hindi
        marathi_markers = ["आहे", "करा", "करायचं", "मला", "शिकायचं", "बघ", "सांग", "काय", "होते", "नाही", "माझे"]
        for m in marathi_markers:
            if m in text:
                return "mr"
        return "hi"

    # Check transliterated markers
    if any(w in text_lower for w in ["aaj", "mujhe", "karna", "batao", "samjhao", "padhna"]):
        return "hi"
    if any(w in text_lower for w in ["mala", "aaj", "karaycha", "shikaycha", "sang", "bagha"]):
        return "mr"

    return "en"


def _extract_duration_minutes(text: str) -> float:
    """Extracts duration from phrases like '45 minutes', '1 hour', '2 तास', '30 min', '1.5 hours'."""
    text_lower = text.lower()
    # Check hours
    hr_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs|तास|घंटे|घंटा)', text_lower)
    if hr_match:
        return float(hr_match.group(1)) * 60.0

    # Check minutes
    min_match = re.search(r'(\d+)\s*(?:minute|minutes|min|mins|मिनीट|मिनिट)', text_lower)
    if min_match:
        return float(min_match.group(1))

    return 45.0  # default study pomodoro


def _extract_subject(text: str) -> str:
    """Extracts subject name from keywords."""
    text_lower = text.lower()
    for kw, canon in SUBJECT_KEYWORDS.items():
        if kw in text_lower:
            return canon
    return "General Study"


def interpret_command(prompt: str) -> CommandIntent:
    """
    Parses a user's voice or text command into an actionable CommandIntent.
    Supports English, Hindi, Marathi, and mixed-language commands.
    """
    clean_text = prompt.strip()
    lang = detect_language(clean_text)
    lower = clean_text.lower()

    # 1. STUDY STATUS / PROGRESS
    if any(p in lower for p in [
        "what should i study", "today's plan", "study status", "how much did i study",
        "आज काय शिकू", "आजचा प्लॅन", "प्रोग्रेस दाखव", "किती वेळ अभ्यास केला", "प्लॅन सांग",
        "aaj kya padhu", "aaj ka plan", "kitna padha", "progress dikhao", "today's mission"
    ]) or re.search(r'(?:study|revision|aaj|today).*(?:plan|status|mission)', lower):
        return CommandIntent(
            intent_name="GET_STUDY_STATUS",
            detected_language=lang,
            confidence=0.92,
            parameters={},
            raw_prompt=clean_text,
            suggested_tool="get_study_status"
        )

    # 2. START STUDY SESSION / TIMER
    if any(p in lower for p in [
        "start study", "start timer", "start session", "studied for", "study session",
        "अभ्यास सुरू", "टाइमर लावा", "सुरू कर", "अभ्यास करायचा", "तास अभ्यास",
        "padhai shuru", "timer lagao", "study start"
    ]) or re.search(r'(?:start|log|record).*(?:study|session|timer|pomodoro)', lower) or re.search(r'(?:अभ्यास|शिकायचं).*(?:तास|मिनिट|सुरू)', lower):
        duration = _extract_duration_minutes(clean_text)
        subject = _extract_subject(clean_text)
        return CommandIntent(
            intent_name="START_STUDY_SESSION",
            detected_language=lang,
            confidence=0.95,
            parameters={"subject_name": subject, "duration_minutes": duration},
            raw_prompt=clean_text,
            suggested_tool="start_study_session"
        )

    # 3. WEAK TOPICS / MISTAKES
    if any(p in lower for p in [
        "weak topic", "weak subjects", "my mistakes", "error book", "mistakes",
        "कमकुवत विषय", "माझ्या चुका", "मिस्टेक बुक", "weak topics", "चुका",
        "kamjor topic", "meri galtiyan", "weak areas", "galtiyan"
    ]) or re.search(r'(?:weak|mistake|error|कमकुवत|चूक|ग़लती)', lower):
        return CommandIntent(
            intent_name="GET_WEAK_TOPICS",
            detected_language=lang,
            confidence=0.94,
            parameters={},
            raw_prompt=clean_text,
            suggested_tool="get_weak_topics"
        )

    # 4. CREATE TASK / REVISION
    if any(p in lower for p in [
        "create task", "add task", "remind me to", "schedule revision", "plan to",
        "टास्क तयार करा", "रिव्हिजन प्लॅन करा", "लक्षात ठेवा",
        "task banao", "revision plan karo", "yaad dilao"
    ]):
        subject = _extract_subject(clean_text)
        return CommandIntent(
            intent_name="CREATE_STUDY_TASK",
            detected_language=lang,
            confidence=0.90,
            parameters={"title": clean_text, "subject_name": subject, "priority": "High"},
            raw_prompt=clean_text,
            suggested_tool="create_study_task"
        )

    # 5. CREATE NOTE / MEMORY
    if any(p in lower for p in [
        "note this", "remember this", "save note", "add to notes",
        "हे नोट करा", "लक्षात ठेव", "नोट्स मध्ये टाका",
        "isko note karo", "yaad rakhna", "notes me dalo"
    ]):
        subject = _extract_subject(clean_text)
        return CommandIntent(
            intent_name="CREATE_NOTE",
            detected_language=lang,
            confidence=0.93,
            parameters={"title": f"Note: {clean_text[:40]}", "content": clean_text, "subject_name": subject},
            raw_prompt=clean_text,
            suggested_tool="create_note"
        )

    # 6. KNOWLEDGE BASE SEARCH / RAG
    if any(p in lower for p in [
        "search notes", "explain from notes", "find in pdf", "uploaded notes",
        "नोट्स मध्ये शोधा", "पुस्तकातून सांगा", "पीडीएफ मध्ये काय आहे",
        "notes me dhoondo", "pdf me search karo"
    ]):
        subject = _extract_subject(clean_text)
        return CommandIntent(
            intent_name="SEARCH_KNOWLEDGE_BASE",
            detected_language=lang,
            confidence=0.91,
            parameters={"query": clean_text, "subject_filter": subject if subject != "General Study" else None},
            raw_prompt=clean_text,
            suggested_tool="search_knowledge_base"
        )

    # 7. BACKUP DATABASE
    if any(p in lower for p in ["backup database", "save backup", "बॅकअप घ्या", "डेटा सुरक्षित करा", "backup lo"]):
        return CommandIntent(
            intent_name="BACKUP_DATABASE",
            detected_language=lang,
            confidence=0.98,
            parameters={},
            raw_prompt=clean_text,
            suggested_tool="backup_database"
        )

    # 8. DEFAULT: EXPLAIN / TUTOR QUERY
    subject = _extract_subject(clean_text)
    return CommandIntent(
        intent_name="SOCRATIC_TUTOR_QUERY",
        detected_language=lang,
        confidence=0.85,
        parameters={"query": clean_text, "subject_name": subject},
        raw_prompt=clean_text,
        suggested_tool="search_knowledge_base"
    )
