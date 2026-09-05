import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Preferred Provider ('gemini' or 'openai')
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower().strip()

# Database Path
DB_PATH = BASE_DIR / os.getenv("DATABASE_NAME", "gate_jarvis.db")

# Knowledge Base & Documents Storage Directory
DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

# RAG & Chunking Configuration
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "650"))       # Target characters per chunk
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))   # Overlap characters between chunks
TOP_K_RESULTS = int(os.getenv("RAG_TOP_K", "4"))            # Number of top chunks to retrieve
SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.15")) # Minimum similarity threshold

# Exact Canonical Subject Taxonomy: GATE MECHANICAL & FIRST YEAR
DEFAULT_SUBJECTS = [
    # --- GATE MECHANICAL (Core & High Weightage) ---
    {"name": "Engineering Mathematics", "category": "GATE Mechanical", "target_hours": 70},
    {"name": "Applied Mechanics", "category": "GATE Mechanical", "target_hours": 45},
    {"name": "Strength of Materials", "category": "GATE Mechanical", "target_hours": 60},
    {"name": "Theory of Machines", "category": "GATE Mechanical", "target_hours": 50},
    {"name": "Vibrations", "category": "GATE Mechanical", "target_hours": 35},
    {"name": "Machine Design", "category": "GATE Mechanical", "target_hours": 45},
    {"name": "Fluid Mechanics", "category": "GATE Mechanical", "target_hours": 55},
    {"name": "Heat Transfer", "category": "GATE Mechanical", "target_hours": 50},
    {"name": "Thermodynamics", "category": "GATE Mechanical", "target_hours": 60},
    {"name": "IC Engines", "category": "GATE Mechanical", "target_hours": 30},
    {"name": "Refrigeration & AC", "category": "GATE Mechanical", "target_hours": 30},
    {"name": "Manufacturing", "category": "GATE Mechanical", "target_hours": 65},
    {"name": "Industrial Engineering", "category": "GATE Mechanical", "target_hours": 40},
    {"name": "General Aptitude", "category": "GATE Mechanical", "target_hours": 30},

    # --- FIRST YEAR (Foundation & Fundamentals) ---
    {"name": "Engineering Physics", "category": "First Year", "target_hours": 45},
    {"name": "Engineering Chemistry", "category": "First Year", "target_hours": 40},
    {"name": "Basic Electrical", "category": "First Year", "target_hours": 45},
    {"name": "Engineering Graphics", "category": "First Year", "target_hours": 50},
    {"name": "Programming", "category": "First Year", "target_hours": 60},
    {"name": "Workshop", "category": "First Year", "target_hours": 30},
]
