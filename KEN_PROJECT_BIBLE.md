# PROJECT KEN: MASTER DOCUMENTATION

## 1. The Core Concept
**Identity:** Ken is a "Proactive Freelance OS" & "Synthetic Organism."
**Role:** A localized AI Project Manager that lives on Harsh's laptop.
**Vibe:** Professional, slightly "Greedy" for perfection, ambitious.
**Architecture:** The "Triune Brain" (Biological Agent Architecture).

## 2. The Architecture (The 3 Brains)
1.  **Reptilian Brain (Local/Fast):**
    * *Role:* Reflexes, Voice Interface, OS Control.
    * *Tech:* Llama 3.2 (Ollama), Whisper (STT), EdgeTTS (TTS).
    * *Latency:* <200ms.
2.  **Limbic System (Memory/Soul):**
    * *Role:* Long-term memory, Personality, Preferences.
    * *Tech:* ChromaDB (Vector Store), `user_profile.json`.
    * *Structure:* 4 Lobes (Journal, Codex, Project Alpha, Archive).
3.  **Neocortex (Intelligence/Cloud):**
    * *Role:* Deep reasoning, Coding, Complex Planning.
    * *Tech:* Gemini 1.5 Pro API, DeepSeek V3 API.
    * *Feature:* "Greedy Router" (Switches to best tool for the job).

## 3. The Tech Stack (Free Tier Optimized)
* **Language:** Python 3.10+
* **Coding Agent:** Aider (CLI) + GitPython.
* **Vision:** Moondream (Local) - Watches screen every 10s.
* **Search:** Tavily API (for Agentic Research).
* **Design:** Figma API + Vercel v0.
* **Finance (Safe Mode):** yfinance + TA-Lib (Analysis only, no trading).

## 4. The "Lego" Roadmap (Execution Order)
* **Pack 1: The Coder (GSoC Priority)** -> `modules/coder.py` (Aider Integration).
* **Pack 2: The Voice (Hackathon Priority)** -> `modules/voice_engine.py` (Whisper/EdgeTTS).
* **Pack 3: The Brain (Cloud Logic)** -> `modules/neocortex.py` (Gemini API).
* **Pack 4: The Memory (Context)** -> `modules/limbic.py` (ChromaDB).
* **Pack 5: The Eyes (Vision)** -> `modules/vision.py` (Moondream).
* **Pack 6: The Evolution (Self-Improvement)** -> `modules/arena.py`.

## 5. Current Status
* Phase: **Planning Complete.**
* Immediate Next Step: Building **Pack 1 (The Coder)**.