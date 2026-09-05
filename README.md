# 🚀 GATE JARVIS — Stage 2: Personal Knowledge Base & RAG System

**GATE JARVIS** is a personal AI study assistant, knowledge base, and preparation system built specifically for a Mechanical Engineering student (2026–2030) aiming for an **All India Rank (AIR) under 100 in GATE Mechanical Engineering**.

---

## 🌟 Stage 2 Key Capabilities (Knowledge Base & Grounded RAG)

1. **Multi-Format Document Upload**:
   - Supports **PDF (.pdf)**, **Word (.docx)**, and **Text/Markdown (.txt, .md)**.
   - Tag uploaded files with Subject (`Strength of Materials`, `Fluid Mechanics`, `Thermodynamics`, etc.) and Type (`Notes`, `PYQ`, `DPP`, `Formula Sheet`, `Textbook`, `Syllabus`).
2. **Intelligent Text Extraction & Chunking**:
   - Extracts text page-by-page.
   - Sliding-window chunker with overlap to maintain mathematical context across boundaries.
   - Preserves page numbers, headings, and character offsets.
3. **Dual-Engine Vector Store & Semantic Search**:
   - Cloud embeddings via **Google Gemini** (`models/text-embedding-004`) or **OpenAI** (`text-embedding-3-small`).
   - High-speed local **Semantic Feature Vectorizer (NumPy + Cosine Similarity)** fallback ensuring 100% offline functionality without API keys or crashes.
   - Hybrid ranking (Dense Cosine Similarity + BM25 keyword matching) for exact formula and symbol matching.
4. **Retrieval-Augmented Generation (RAG)**:
   - When you ask a question (e.g. *"Explain Bernoulli's equation"* or *"Lame's equation for thick cylinders"*), JARVIS searches your uploaded notes first.
   - Prefer uploaded notes when relevant.
   - Strict anti-hallucination rules: If a concept is not in your documents, JARVIS clearly alerts you before providing general textbook knowledge.
   - Displays an expandable **"📚 Sources Used"** section with document names, page numbers, similarity match scores, and excerpts.
5. **Complete Document Library Management**:
   - View metadata (Pages, Chunks, File Size, Upload Date, Subject).
   - Re-index documents with one click.
   - Delete documents and automatically purge vector embeddings from SQLite.

---

## 📁 Project Architecture & File Directory

```
GATE STUDY AGENT/
├── data/
│   └── documents/            # Storage directory for uploaded PDFs, DOCXs, and TXTs
├── database/
│   ├── connection.py         # SQLite schema (subjects, sessions, tasks, documents, document_chunks)
│   └── queries.py            # Complete CRUD & vector query operations
├── services/
│   ├── ai_service.py         # Gemini & OpenAI LLM logic + RAG prompt routing
│   ├── extractor_service.py  # PDF, DOCX, and TXT page-by-page text extractors
│   ├── chunker_service.py    # Overlapping text chunker with metadata tracking
│   ├── vector_service.py     # Cloud & Local Vectorizer + Cosine Similarity engine
│   └── rag_service.py        # Ingestion pipeline, re-indexer, & grounded RAG synthesizer
├── views/
│   ├── dashboard_view.py     # Command dashboard with stats & Knowledge Base overview
│   ├── assistant_view.py     # AI Study Assistant chat with RAG toggle & Sources Used badges
│   ├── knowledge_view.py     # Knowledge Base tabs (Upload, Library, Semantic Explorer)
│   ├── timer_view.py         # Deep work study stopwatch & session recorder
│   ├── subjects_view.py      # Curriculum tracker & task planner
│   └── settings_view.py      # System diagnostics, vector counts, & 4-year roadmap
├── app.py                    # Main Streamlit web app & navigation router
├── config.py                 # Application settings, paths, and RAG thresholds
├── requirements.txt          # Complete Python dependencies
├── seed_knowledge_base.py    # Auto-seed initial GATE notes & DPPs
├── test_stage2.py            # Comprehensive Stage 2 verification test suite
└── README.md                 # Complete documentation
```

---

## 📦 What Every Dependency Does (For Beginners)

| Dependency | Purpose | Why We Use It |
| :--- | :--- | :--- |
| `streamlit` | Web Application UI | Creates interactive browser dashboards and chat interfaces with pure Python. |
| `pypdf` | PDF Processing | Extracts text and page numbers from uploaded GATE PDF books and question sets. |
| `python-docx` | Word Document Processing | Reads `.docx` lecture notes, assignments, and notes. |
| `numpy` | Vector Math & Linear Algebra | Calculates vector embeddings, dot products, and cosine similarity in milliseconds. |
| `google-generativeai` | Google Gemini AI | Generates grounded explanations and dense neural embeddings. |
| `openai` | OpenAI GPT-4o | Optional alternative AI provider for completions and embeddings. |
| `python-dotenv` | Environment Variables | Securely loads your API keys from `.env` without hardcoding them in code. |

---

## 🛠️ Step-by-Step Installation & Setup (Windows)

### Step 1: Open Terminal in Project Directory
```powershell
cd "c:\Users\krris\Downloads\GATE STUDY AGENT"
```

### Step 2: Install Dependencies
```powershell
py -m pip install -r requirements.txt
```

### Step 3: Configure Your API Key (Optional for Live AI)
1. Copy `.env.example` to `.env` if you haven't already:
   ```powershell
   copy .env.example .env
   ```
2. Open `.env` in Notepad:
   ```powershell
   notepad .env
   ```
3. Get a **Free** Google Gemini API Key from: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
4. Paste your key in `GEMINI_API_KEY=your_actual_key_here` and save.

*(Note: If no API key is provided, GATE JARVIS runs in **Offline Knowledge Base Mode**, retrieving exact formulas, answers, and sources from your uploaded documents without errors!)*

### Step 4: (Optional) Seed Sample DPPs & Notes
To pre-load the Strength of Materials DPPs and Bernoulli's Equation notes:
```powershell
py seed_knowledge_base.py
```

### Step 5: Run the Comprehensive Test Suite
```powershell
py test_stage2.py
```

### Step 6: Launch GATE JARVIS
```powershell
py -m streamlit run app.py
```

The application will launch in your browser at `http://localhost:8501`.

---

## 🧪 How to Test Every Stage 2 Feature

1. **📖 Knowledge Base -> 📤 Upload & Ingest**:
   - Drag and drop any PDF, Word `.docx`, or `.txt` file.
   - Select the Subject and Document Type (e.g., `Strength of Materials (SOM)` / `Notes`).
   - Click **🚀 Process & Index Documents**.
   - Watch the extraction, chunking, and embedding progress.

2. **📖 Knowledge Base -> 📂 Document Library**:
   - View your uploaded documents with metadata (Pages, Chunks, File Size, Date).
   - Test the **🔄 Re-Index** button to refresh chunks.
   - Test the **🗑️ Delete** button to remove a document and its vectors.

3. **📖 Knowledge Base -> 🔍 Semantic Search Explorer**:
   - Type a query like: `Explain Bernoulli's equation` or `Lame's equation for thick cylinders`.
   - Adjust the Top-K slider.
   - Inspect the retrieved chunks, page numbers, and similarity percentage breakdown (Dense Vector % vs Lexical %).

4. **💬 AI Study Assistant (RAG Chat)**:
   - Ensure `[x] Search My Uploaded Notes First (RAG)` is checked.
   - Ask: `"Explain Bernoulli's equation"` -> Notice how it cites `Fluid_Mechanics_Bernoullis_Equation.txt` with page numbers and displays the **"📚 Sources Used"** expandable card!
   - Ask: `"What is the condition for pure shear in a thin cylinder under pressure and axial load?"` -> Cites `SOM_DPP01_Pressure_Vessels.txt` and shows $F = 3\pi p r^2$.
   - Ask an out-of-domain question (e.g., `"Explain quantum computing entanglement"`) -> JARVIS notes that this topic is not in your uploaded notes, and provides the general explanation separately.

5. **🏠 Dashboard & ⚙️ Settings**:
   - Check the **Knowledge Base** metric card showing total indexed documents and chunks.
   - View the database health diagnostics in Settings.
