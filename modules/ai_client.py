import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# 1. Load environment variables from .env file securely
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Master System Prompt for GATE Mechanical Engineering Specialization
OPENAI_SYSTEM_PROMPT = r"""
You are **GATE JARVIS**, an elite personal AI mentor and coach for Mechanical Engineering (2026–2030) aiming for an All India Rank (AIR) < 100 in GATE Mechanical Engineering.

YOUR CORE EXPERTISE:
1. **First-Principles Concept Explanation**: Start with physical intuition, real-world analogies (e.g. pressure cookers, syringes, IC engines, gears), and explain WHY phenomena occur before equations.
2. **GATE Doubt Solving & Pitfalls**: Highlight sign convention traps, radius vs diameter confusion, and tricky edge cases used by IISc/IIT GATE setters.
3. **Step-by-Step Numerical Solutions**: 
   - State 'Given Data' clearly with standard SI units.
   - State the governing equation and underlying assumptions.
   - Perform step-by-step substitution with clear units.
   - Provide final answer rounded to appropriate decimal places (NAT format).
4. **Short Notes & Key Points Extraction**: Generate clean, crisp summary tables and bullet lists of essential formulas.
5. **Practice Questions & Test Analysis**: Generate realistic GATE MCQs, MSQs, and NATs with complete answer keys.
6. **Formatting**: Always format with structured markdown, bold headers, and LaTeX for math ($...$ or $$...$$).
"""

def get_openai_api_key() -> str:
    """
    Safely reads the OPENAI_API_KEY from environment variables.
    Returns stripped string or empty string.
    """
    key = os.getenv("OPENAI_API_KEY", "").strip()
    # Check if user forgot to replace placeholder
    if key in ["your_openai_api_key_here", ""]:
        return ""
    return key

def is_openai_configured() -> bool:
    """
    Checks whether a valid OPENAI_API_KEY is present in the environment.
    """
    key = get_openai_api_key()
    return len(key) > 5

def get_masked_api_key() -> str:
    """
    Returns a securely masked version of the API key for UI display (e.g. 'AQ...fyQ' or 'sk-...89ab').
    NEVER logs or exposes the full API key.
    """
    key = get_openai_api_key()
    if not key:
        return "Not Configured"
    if len(key) <= 8:
        return "****"
    return f"{key[:3]}...{key[-4:]}"

def get_openai_client():
    """
    Initializes and returns an authenticated OpenAI client instance.
    Raises RuntimeError with beginner-friendly instructions if key is missing.
    """
    key = get_openai_api_key()
    if not key:
        raise RuntimeError(
            "⚠️ **OpenAI API Key Missing**: Please add your `OPENAI_API_KEY` to the `.env` file in your project folder.\n\n"
            "Example in `.env`:\n"
            "```env\n"
            "OPENAI_API_KEY=your_key_here\n"
            "```"
        )
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except ImportError:
        raise RuntimeError("⚠️ `openai` package is not installed. Run `py -m pip install openai` in your terminal.")

def generate_openai_chat_response(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    system_prompt: str = OPENAI_SYSTEM_PROMPT,
    temperature: float = 0.6,
    max_tokens: int = 1500
) -> Tuple[bool, str]:
    """
    Sends chat messages to OpenAI API and returns (success: bool, response_or_error: str).
    Keeps API network logic safely isolated from Streamlit UI code.
    """
    try:
        client = get_openai_client()
        
        # Build message payload with system instruction
        payload = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role in ["user", "assistant", "system"]:
                payload.append({"role": role, "content": content})

        response = client.chat.completions.create(
            model=model,
            messages=payload,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        reply = response.choices[0].message.content
        return True, reply

    except Exception as e:
        error_msg = str(e)
        if "Incorrect API key" in error_msg or "invalid_api_key" in error_msg:
            return False, "⚠️ **OpenAI Authentication Error**: The API key provided in your `.env` file is invalid. Please verify your key on platform.openai.com."
        elif "insufficient_quota" in error_msg:
            return False, "⚠️ **OpenAI Quota Exceeded**: Your account has run out of credits or billing is inactive. Check your OpenAI account billing dashboard."
        elif "rate_limit" in error_msg.lower():
            return False, "⚠️ **Rate Limit**: Too many requests in a short time. Please wait a few seconds and try again."
        else:
            return False, f"⚠️ **OpenAI Error**: {error_msg}"

def generate_openai_embedding(text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
    """
    Generates a dense vector embedding using OpenAI API.
    """
    try:
        client = get_openai_client()
        resp = client.embeddings.create(
            model=model,
            input=text
        )
        return resp.data[0].embedding
    except Exception:
        return None
