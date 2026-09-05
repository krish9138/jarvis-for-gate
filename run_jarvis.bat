@echo off
title GATE JARVIS Launcher
cd /d "%~dp0"
echo ========================================================
echo Starting GATE JARVIS - Mechanical Engineering AI System
echo ========================================================
py -m streamlit run "%~dp0app.py" --server.port 8503
pause
