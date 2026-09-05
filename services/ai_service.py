import os
from typing import List, Dict, Any, Tuple, Optional
import config
from .rag_service import query_knowledge_base, build_rag_context_and_prompt
from modules.ai_client import (
    is_openai_configured, 
    generate_openai_chat_response, 
    get_masked_api_key,
    OPENAI_SYSTEM_PROMPT
)

def get_configured_provider() -> Tuple[str, bool]:
    """
    Checks which API key is configured.
    Returns (provider_name, is_configured).
    """
    if is_openai_configured() and config.AI_PROVIDER == "openai":
        return ("OpenAI", True)
    if config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_gemini_api_key_here":
        return ("Gemini", True)
    if is_openai_configured():
        return ("OpenAI", True)
    return ("None", False)

def call_gemini(messages: List[Dict[str, str]], system_instruction: str = OPENAI_SYSTEM_PROMPT) -> str:
    """Calls the Google Gemini API using google-generativeai."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        
        # Format chat history for Gemini
        gemini_history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(messages[-1]["content"])
        return response.text
    except Exception as e:
        return f"⚠️ **Gemini API Error:** {str(e)}\n\nPlease check your `GEMINI_API_KEY` in the `.env` file."

def call_openai_client(messages: List[Dict[str, str]], system_instruction: str = OPENAI_SYSTEM_PROMPT) -> str:
    """Calls the secure OpenAI client from modules.ai_client."""
    success, reply = generate_openai_chat_response(
        messages=messages,
        system_prompt=system_instruction,
        model="gpt-4o-mini"
    )
    return reply

def get_demo_rag_response(user_query: str, sources: List[Dict[str, Any]]) -> str:
    """
    Intelligent fallback for RAG responses when running in offline Demo Mode.
    Synthesizes real extracted text from uploaded notes directly into an explanation.
    """
    if sources:
        top_source = sources[0]
        doc_name = top_source["doc_name"]
        page_num = top_source["page_number"]
        relevance = int(top_source["similarity_score"] * 100)
        snippet = top_source['content'][:450].replace('\n', '\n> ')
        
        return (
            f"### 🤖 GATE JARVIS (Offline Knowledge Base Mode)\n\n"
            f"> 📖 **Grounded in Uploaded Knowledge**: Retrieved from your uploaded document **`{doc_name}`** (Page {page_num}, Relevance {relevance}%).\n\n"
            f"---\n\n"
            f"### 1. Grounded Concept Summary (From Your Uploaded Notes)\n\n"
            f"> {snippet}...\n\n"
            f"#### Key Highlights & Governing Equations:\n"
            f"- The principles extracted from your document emphasize step-by-step physical understanding.\n"
            f"- Units, sign conventions, and fundamental boundary conditions apply as stated in your notes.\n\n"
            f"---\n\n"
            f"### 2. GATE Trap Alert ⚠️\n"
            f"*Common Exam Trap*: Ensure you do not confuse diameter with radius in stress equations (e.g., $r = d/2$), and always verify whether the cylinder has closed ends (inducing longitudinal stress $\\sigma_L$) or open ends ($\\sigma_L = 0$).\n\n"
            f"---\n\n"
            f"### 3. 🎯 Check for Understanding:\n"
            f"**Question:** Based on your notes for this topic, what is the primary assumption required when simplifying thin-walled pressure vessel equations?\n"
            f"* A) Thickness $t < d / 20$ so radial stress can be neglected\n"
            f"* B) Material behaves in a non-linear viscoelastic manner\n"
            f"* C) Longitudinal strain is always zero\n"
            f"* D) Temperature gradient is infinite\n\n"
            f"*(To enable live OpenAI GPT-4o reasoning, add your `OPENAI_API_KEY` in `.env`)*"
        )
    else:
        return (
            f"### 🤖 GATE JARVIS (Offline Demo Response)\n\n"
            f"⚠️ **Note**: This specific topic is not found in your uploaded knowledge base documents.\n\n"
            f"---\n\n"
            f"### General Mechanical Engineering Explanation: **\"{user_query}\"**\n\n"
            f"#### 1. Intuitive Physical Concept\n"
            f"In engineering, physical phenomena are governed by fundamental conservation laws:\n"
            f"- **Conservation of Mass** (Continuity Equation: $A_1 V_1 = A_2 V_2$)\n"
            f"- **Conservation of Momentum** (Euler's & Navier-Stokes Equations)\n"
            f"- **Conservation of Energy** (1st Law of Thermo / Bernoulli Equation: $P/(\\rho g) + v^2/(2g) + z = \\text{Constant}$)\n\n"
            f"#### 2. GATE Trap Alert ⚠️\n"
            f"Always check the validity conditions (e.g. steady flow, incompressible, inviscid, along a streamline for Bernoulli's equation).\n\n"
            f"---\n\n"
            f"### 🎯 Check for Understanding:\n"
            f"**Question:** For which flow condition is the classical Bernoulli equation valid?\n"
            f"* A) Unsteady, compressible, turbulent flow\n"
            f"* B) Steady, incompressible, frictionless (inviscid) flow along a streamline\n"
            f"* C) Viscous flow inside boundary layers\n"
            f"* D) Highly rotational vortex core flow\n"
        )

def get_ai_response(
    messages: List[Dict[str, str]], 
    use_rag: bool = True,
    subject_id: Optional[int] = None,
    study_mode: str = "Standard"
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Main AI query dispatcher with RAG pipeline and OpenAI integration.
    Supports Study Modes: Standard, Concept, Numerical, Short Notes, Practice Questions, Test Analysis.
    Returns: (response_text: str, sources_used: List[Dict[str, Any]])
    """
    provider, is_configured = get_configured_provider()
    latest_query = messages[-1]["content"] if messages else "Hello"
    sources_used = []

    # Apply study mode prefixes to prompt if applicable
    mode_instructions = {
        "💡 Concept Explanation": "Focus deeply on first principles, physical analogies, intuitive diagrams in markdown, and step-by-step breakdown.",
        "🔢 Step-by-Step Numerical": "Solve this as a GATE numerical problem. State Given data with SI units, Governing formula, substitution, calculation steps, and final numerical value in NAT format.",
        "📝 Short Notes & Formulas": "Extract high-yield revision notes, formula tables, SI units, and key exam summary bullet points.",
        "❓ Practice Questions": "Generate 2 high-quality GATE questions (1 MCQ and 1 NAT) based on this concept with detailed step-by-step solutions.",
        "📊 Test Analysis & Traps": "Analyze this topic from a GATE exam perspective: common student misconceptions, negative marking traps, and high-frequency question patterns."
    }

    mode_prompt = mode_instructions.get(study_mode, "")

    if use_rag:
        retrieved_chunks = query_knowledge_base(latest_query, top_k=config.TOP_K_RESULTS, subject_id=subject_id)
        rag_prompt, sources_used = build_rag_context_and_prompt(latest_query, retrieved_chunks)
        
        if mode_prompt:
            rag_prompt += f"\n\nSPECIAL STUDY MODE INSTRUCTION ({study_mode}):\n{mode_prompt}\n"

        rag_messages = list(messages[:-1]) + [{"role": "user", "content": rag_prompt}]
    else:
        if mode_prompt:
            enhanced_query = f"{latest_query}\n\n[Instruction: {mode_prompt}]"
            rag_messages = list(messages[:-1]) + [{"role": "user", "content": enhanced_query}]
        else:
            rag_messages = messages

    if not is_configured:
        if use_rag:
            return (get_demo_rag_response(latest_query, sources_used), sources_used)
        else:
            return (get_demo_rag_response(latest_query, []), [])

    if provider == "OpenAI":
        response_text = call_openai_client(rag_messages)
    elif provider == "Gemini":
        response_text = call_gemini(rag_messages)
    else:
        response_text = get_demo_rag_response(latest_query, sources_used)

    return (response_text, sources_used)
