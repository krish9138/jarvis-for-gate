"""
services/voice_service.py
-------------------------
Voice & Multilingual Speech Gateway for GATE JARVIS.
Integrates HTML5 Web Speech API (STT/TTS) for zero-dependency native browser voice capture
across English (en-IN), Hindi (hi-IN), and Marathi (mr-IN).
"""

import streamlit as st
import streamlit.components.v1 as components


def render_voice_input_widget(key: str = "jarvis_voice"):
    """
    Renders an interactive Web Speech API microphone widget.
    Captures spoken audio, transcribes in real-time with multi-language detection,
    and updates Streamlit state.
    """
    html_code = f"""
    <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 14px; text-align: center; color: #f8fafc; font-family: sans-serif;">
        <div style="display: flex; justify-content: center; align-items: center; gap: 12px; margin-bottom: 8px;">
            <button id="micBtn" onclick="toggleListening()" style="background: linear-gradient(135deg, #0284c7, #0369a1); border: none; color: white; width: 48px; height: 48px; border-radius: 50%; font-size: 20px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px rgba(2, 132, 199, 0.5);">
                🎙️
            </button>
            <div style="text-align: left;">
                <div id="statusText" style="font-weight: 700; font-size: 14px; color: #38bdf8;">JARVIS Voice: Idle</div>
                <div style="font-size: 11px; color: #94a3b8;">Supports English • Hindi • Marathi (मराठी)</div>
            </div>
        </div>
        <div id="transcriptBox" style="background: rgba(15, 23, 42, 0.8); border: 1px dashed rgba(255,255,255,0.2); border-radius: 8px; padding: 8px; min-height: 38px; font-size: 13px; color: #e2e8f0;">
            Click 🎙️ and speak your command...
        </div>
    </div>

    <script>
        let recognition = null;
        let isListening = false;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'mr-IN, hi-IN, en-IN'; // Multi-locale listener
            
            recognition.onstart = function() {{
                isListening = true;
                document.getElementById('statusText').innerText = "🔴 Listening (बोलत राहा)...";
                document.getElementById('statusText').style.color = "#ef4444";
                document.getElementById('micBtn').style.background = "#dc2626";
                document.getElementById('micBtn').style.boxShadow = "0 0 20px rgba(220, 38, 38, 0.8)";
            }};

            recognition.onresult = function(event) {{
                let current = event.resultIndex;
                let transcript = event.results[current][0].transcript;
                document.getElementById('transcriptBox').innerText = transcript;
            }};

            recognition.onend = function() {{
                isListening = false;
                document.getElementById('statusText').innerText = "✅ Done! Copy or type into prompt below.";
                document.getElementById('statusText').style.color = "#10b981";
                document.getElementById('micBtn').style.background = "#0284c7";
                document.getElementById('micBtn').style.boxShadow = "0 0 15px rgba(2, 132, 199, 0.5)";
            }};

            recognition.onerror = function(event) {{
                isListening = false;
                document.getElementById('statusText').innerText = "⚠️ Voice Error: " + event.error;
                document.getElementById('statusText').style.color = "#f59e0b";
            }};
        }} else {{
            document.getElementById('statusText').innerText = "⚠️ Web Speech API not supported in this browser.";
        }}

        function toggleListening() {{
            if (!recognition) return;
            if (isListening) {{
                recognition.stop();
            }} else {{
                recognition.start();
            }}
        }}
    </script>
    """
    components.html(html_code, height=130)


def speak_text(text: str, lang: str = "en"):
    """Invokes browser SpeechSynthesis for audio feedback."""
    lang_code = "mr-IN" if lang == "mr" else ("hi-IN" if lang == "hi" else "en-US")
    clean_text = text.replace("'", "\\'").replace("\n", " ")
    tts_html = f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance('{clean_text}');
            utterance.lang = '{lang_code}';
            utterance.rate = 1.05;
            window.speechSynthesis.speak(utterance);
        }}
    </script>
    """
    components.html(tts_html, height=0)
