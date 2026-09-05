import os
import sys
from pathlib import Path

# Force UTF-8 on Windows terminal output for tests
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from modules.ai_client import (
    get_openai_api_key,
    is_openai_configured,
    get_masked_api_key,
    generate_openai_chat_response,
    generate_openai_embedding
)
from services.ai_service import get_ai_response, get_configured_provider

def test_openai_module():
    print("=== TESTING SECURE OPENAI INTEGRATION ===")

    # 1. Test Key Retrieval & Masking
    masked = get_masked_api_key()
    print(f"1. Masked Key Output: {masked}")
    raw_key = get_openai_api_key()
    if raw_key:
        assert raw_key not in masked, "Security Violation: Raw API key must not appear in masked string!"
        print("   [PASS] Key masking security verified.")
    else:
        print("   [INFO] No key currently set in .env (Offline mode tested).")

    # 2. Test Safe Error Handling When Key is Missing or Mock
    print("\n2. Testing Error Handling on Missing/Invalid Key")
    success, resp = generate_openai_chat_response([{"role": "user", "content": "Ping"}])
    print(f"   Success Flag: {success}")
    print(f"   Handled Response Preview: {resp[:100]}...")
    print("   [PASS] Safe error handling without crash verified.")

    # 3. Test Study Modes in AI Service
    print("\n3. Testing Study Modes Dispatcher")
    study_modes = [
        "💡 Concept Explanation",
        "🔢 Step-by-Step Numerical",
        "📝 Short Notes & Formulas",
        "❓ Practice Questions",
        "📊 Test Analysis & Traps"
    ]
    for mode in study_modes:
        response, sources = get_ai_response(
            [{"role": "user", "content": "Explain Bernoulli equation"}],
            use_rag=True,
            study_mode=mode
        )
        assert len(response) > 50, f"Failed for study mode {mode}"
        print(f"   [PASS] Mode '{mode}' generated {len(response)} chars with {len(sources)} sources.")

    print("\n=== ALL OPENAI INTEGRATION TESTS PASSED! ===")

if __name__ == "__main__":
    test_openai_module()
