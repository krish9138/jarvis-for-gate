"""
api_key_manager.py
-------------------
Drop-in Streamlit component that lets the user add/update their OpenAI and
Gemini API keys directly from the app UI instead of hand-editing .env.
"""

import os
from pathlib import Path
import streamlit as st
from dotenv import set_key, load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


def _mask_key(key: str) -> str:
    """Never display a raw key. Show only a short prefix/suffix."""
    if not key or key in ["your_gemini_api_key_here", "your_openai_api_key_here"]:
        return "Not set"
    if len(key) <= 8:
        return "•" * len(key)
    return f"{key[:4]}{'•' * 6}{key[-4:]}"


def _ensure_env_file():
    if not ENV_PATH.exists():
        ENV_PATH.touch()


def _save_key(env_var_name: str, value: str) -> bool:
    """Persist a key to .env and refresh the current process's environment."""
    try:
        _ensure_env_file()
        set_key(str(ENV_PATH), env_var_name, value)
        os.environ[env_var_name] = value  # make it available immediately
        return True
    except Exception as e:
        st.session_state[f"_{env_var_name}_error"] = str(e)
        return False


def _test_openai_key(key: str):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        client.models.list()
        return True, "✅ OpenAI connection successful!"
    except Exception as e:
        return False, f"❌ OpenAI connection failed: {e}"


def _test_gemini_key(key: str):
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        # Test model listing or simple handshake
        models = list(genai.list_models())
        return True, "✅ Google Gemini connection successful!"
    except Exception as e:
        return False, f"❌ Google Gemini connection failed: {e}"


def _provider_block(label: str, env_var: str, get_url: str, tester):
    load_dotenv(ENV_PATH, override=True)
    current_value = os.getenv(env_var, "").strip()

    st.markdown(f"**{label}**")
    st.caption(f"Current: `{_mask_key(current_value)}`  ·  [Get a key]({get_url})")

    with st.form(key=f"form_{env_var}", clear_on_submit=False):
        new_value = st.text_input(
            f"New {label}",
            type="password",
            placeholder="Paste your key here — it is masked everywhere else",
            key=f"input_{env_var}",
        )
        col1, col2 = st.columns([1, 1])
        save_clicked = col1.form_submit_button("💾 Save Key")
        test_clicked = col2.form_submit_button("🧪 Test Connection")

    if save_clicked:
        if not new_value.strip():
            st.warning("Enter a key before saving.")
        elif _save_key(env_var, new_value.strip()):
            st.success(f"{label} saved. It is active immediately — no restart needed.")
            st.rerun()
        else:
            err = st.session_state.get(f"_{env_var}_error", "Unknown error")
            st.error(f"Could not save key: {err}")

    if test_clicked:
        key_to_test = new_value.strip() or current_value
        if not key_to_test or key_to_test in ["your_gemini_api_key_here", "your_openai_api_key_here"]:
            st.warning("No key to test — paste one first.")
        else:
            with st.spinner("Testing connection..."):
                ok, message = tester(key_to_test)
            (st.success if ok else st.error)(message)

    st.divider()


def render_api_key_settings():
    """Main entry point — call this from your Settings page."""
    st.subheader("🔑 In-App API Key Management")
    st.caption(
        "Keys are stored locally in your `.env` file and never leave your machine "
        "except when securely contacting the AI provider's API."
    )

    _provider_block(
        label="Google Gemini API Key",
        env_var="GEMINI_API_KEY",
        get_url="https://aistudio.google.com/app/apikey",
        tester=_test_gemini_key,
    )

    _provider_block(
        label="OpenAI API Key",
        env_var="OPENAI_API_KEY",
        get_url="https://platform.openai.com/api-keys",
        tester=_test_openai_key,
    )

    load_dotenv(ENV_PATH, override=True)
    provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
    st.markdown(f"**Active AI Provider:** `{provider}`")
    new_provider = st.selectbox(
        "Switch Default Provider",
        options=["gemini", "openai"],
        index=0 if provider == "gemini" else 1,
    )
    if new_provider != provider and st.button("Apply Provider Change"):
        _save_key("AI_PROVIDER", new_provider)
        st.success(f"Active provider switched to {new_provider}.")
        st.rerun()
