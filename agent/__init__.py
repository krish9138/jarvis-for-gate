"""
agent package
-------------
Core Agentic architecture for GATE JARVIS.
Includes Tool Registry, Multilingual Intent Parser (EN/HI/MR), and Execution Engine.
"""

from .tool_registry import ToolRegistry, register_default_tools
from .command_interpreter import interpret_command, CommandIntent
from .agent_core import JarvisAgentCore, get_agent_instance
