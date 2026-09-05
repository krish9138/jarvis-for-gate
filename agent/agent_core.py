"""
agent/agent_core.py
-------------------
Central Autonomous Agent Execution Engine for GATE JARVIS.
Coordinates NLU parsing, tool execution, safety permission gating, activity logging, and response synthesis.
"""

import time
import json
from typing import Dict, Any, Optional
from database.connection import get_db_connection
from .tool_registry import ToolRegistry, ToolPermissionLevel
from .command_interpreter import interpret_command, CommandIntent


def log_agent_activity(
    user_prompt: str,
    detected_language: str,
    intent: str,
    tool_name: str,
    input_summary: str,
    result_status: str,
    result_summary: str,
    approval_level: int,
    user_approved: int,
    duration_ms: float
) -> int:
    """Records an immutable audit trace of every agent action in SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agent_activity_log (
            user_prompt, detected_language, intent, tool_name, input_summary,
            result_status, result_summary, approval_level, user_approved, duration_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_prompt[:500], detected_language, intent, tool_name,
        input_summary[:500], result_status, result_summary[:1000],
        approval_level, user_approved, duration_ms
    ))
    conn.commit()
    act_id = cursor.lastrowid
    conn.close()
    return act_id


class JarvisAgentCore:
    def __init__(self):
        self.registry = ToolRegistry.get_instance()

    def process_user_input(
        self,
        prompt: str,
        user_approved: bool = False,
        active_view_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main autonomous loop:
        1. Parse intent & language (EN / HI / MR)
        2. Resolve corresponding tool
        3. Check safety & human-in-the-loop constraints
        4. Execute tool
        5. Synthesize multilingual response
        6. Log activity to database
        """
        start_time = time.time()
        intent = interpret_command(prompt)

        tool_name = intent.suggested_tool
        tool = self.registry.get_tool(tool_name) if tool_name else None
        approval_level = int(tool.permission_level) if tool else 0

        # Execute Tool if available
        if tool:
            exec_res = self.registry.execute_tool(
                name=tool_name,
                user_approved=user_approved,
                **intent.parameters
            )
            status = "SUCCESS" if exec_res.get("success", False) else (
                "PENDING_APPROVAL" if exec_res.get("requires_approval") else "FAILED"
            )
            raw_msg = exec_res.get("message", "")
        else:
            exec_res = {"success": True, "message": "Query processed directly."}
            status = "SUCCESS"
            raw_msg = "Command understood."

        # Multilingual response formulation
        response_text = self._synthesize_response(intent, exec_res, raw_msg)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Record activity
        log_id = log_agent_activity(
            user_prompt=prompt,
            detected_language=intent.detected_language,
            intent=intent.intent_name,
            tool_name=tool_name or "direct_reply",
            input_summary=json.dumps(intent.parameters),
            result_status=status,
            result_summary=response_text,
            approval_level=approval_level,
            user_approved=1 if (user_approved or approval_level <= 1) else 0,
            duration_ms=duration_ms
        )

        return {
            "success": exec_res.get("success", True),
            "log_id": log_id,
            "intent": intent.intent_name,
            "detected_language": intent.detected_language,
            "tool_name": tool_name,
            "requires_approval": exec_res.get("requires_approval", False),
            "response_text": response_text,
            "details": exec_res,
            "duration_ms": duration_ms
        }

    def _synthesize_response(self, intent: CommandIntent, exec_res: Dict[str, Any], raw_msg: str) -> str:
        lang = intent.detected_language
        
        # Marathi Synthesis
        if lang == "mr":
            if intent.intent_name == "GET_STUDY_STATUS":
                tot = exec_res.get("total_hours", 0)
                tod = exec_res.get("today_hours", 0)
                pend = exec_res.get("pending_tasks", 0)
                return f"तुमचा आतापर्यंत एकूण {tot} तास अभ्यास झाला आहे. आज {tod} तास पूर्ण झाले आहेत आणि {pend} प्रलंबित टास्क्स आहेत."
            elif intent.intent_name == "START_STUDY_SESSION":
                subj = intent.parameters.get("subject_name", "General")
                dur = intent.parameters.get("duration_minutes", 45)
                return f"मी {subj} विषयासाठी {dur} मिनिटांचा अभ्यास सत्र यशस्वीपणे नोंदवला आहे."
            elif intent.intent_name == "GET_WEAK_TOPICS":
                return f"तुमच्या मिस्टेक हिस्ट्रीनुसार कमकुवत विषय आणि चुका विश्लेषित केल्या आहेत: {raw_msg}"
            elif intent.intent_name == "CREATE_NOTE":
                return f"महत्त्वाची नोंद जतन केली: {raw_msg}"
            return f"JARVIS: {raw_msg}"

        # Hindi Synthesis
        elif lang == "hi":
            if intent.intent_name == "GET_STUDY_STATUS":
                tot = exec_res.get("total_hours", 0)
                tod = exec_res.get("today_hours", 0)
                pend = exec_res.get("pending_tasks", 0)
                return f"आपका कुल अध्ययन समय {tot} घंटे है। आज {tod} घंटे पूरे हुए हैं और {pend} कार्य शेष हैं।"
            elif intent.intent_name == "START_STUDY_SESSION":
                subj = intent.parameters.get("subject_name", "General")
                dur = intent.parameters.get("duration_minutes", 45)
                return f"मैंने {subj} के लिए {dur} मिनट का स्टडी सेशन सुरक्षित रूप से रिकॉर्ड कर लिया है।"
            elif intent.intent_name == "GET_WEAK_TOPICS":
                return f"कमजोर टॉपिक्स और गलतियों का विश्लेषण प्राप्त हुआ: {raw_msg}"
            elif intent.intent_name == "CREATE_NOTE":
                return f"महत्वपूर्ण नोट सुरक्षित किया गया: {raw_msg}"
            return f"JARVIS: {raw_msg}"

        # English (Default)
        return raw_msg or f"Processed command '{intent.intent_name}' successfully."


def get_agent_instance() -> JarvisAgentCore:
    return JarvisAgentCore()
