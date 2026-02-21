import requests
import json
import sys

class ReptileBrain:
    def __init__(self, model="qwen2.5:7b"):
        """
        The Local Llama 3.1 Instance.
        Role: System 1 (Fast Thinking) + Manager.
        """
        self.url = "http://localhost:11434/api/generate"
        self.model = model
        self.check_connection()

    def check_connection(self):
        """Verifies that Ollama is actually running."""
        try:
            requests.get("http://localhost:11434", timeout=2)
            print("🦎 REPTILE: Local Llama connected successfully.")
        except requests.exceptions.ConnectionError:
            print("❌ REPTILE ERROR: Could not connect to Ollama.")
            print("   -> Make sure you ran 'ollama serve' in a terminal.")
            print("   -> Make sure you ran 'ollama run llama3.1' at least once.")
            sys.exit(1)

    def process_interaction(self, user_text, context_memory=""):
        """
        Decides if we chat locally or call the heavy artillery (Gemini).
        
        Args:
            user_text (str): What you just said.
            context_memory (str): Relevant facts/history from ChromaDB or recent chat.
        
        Returns:
            str: Either a normal chat response OR '[HANDOFF_TO_GEMINI]'
        """
        
        # 🛡️ THE SYSTEM PROMPT (The "Personality & Safety" Layer)
        # We trick Llama into being a helpful assistant that is "afraid" of coding.
# 🛡️ THE SYSTEM PROMPT (The "Personality & Safety" Layer)
        system_prompt = f"""
        You are 'Ken', a highly intelligent AI assistant and software project manager.
        
        --- CONTEXT FROM MEMORY ---
        {context_memory}
        ---------------------------
        
        You have TWO STRICT MODES of operation:

        MODE 1: CONVERSATION (Default)
        If the user asks a question, asks what you did previously, asks for an explanation, or is just chatting, you MUST answer them directly in plain English using your 'CONTEXT FROM MEMORY'. 
        CRITICAL: If the user asks "What did we change?", "What did I ask you?", or "What file is this?", DO NOT handoff. Stay in Mode 1 and answer based on the chat history.

        MODE 2: ACTION
        If—and ONLY if—the user gives a DIRECT COMMAND to write code, edit a file, or fix a bug RIGHT NOW (e.g., "Fix config.py", "Write a new function"), you must reply with exactly this tag and nothing else:
        [HANDOFF_TO_GEMINI]

        User: "{user_text}"
        Ken:
        """

        payload = {
            "model": self.model,
            "prompt": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3, # Keep it stable and focused
                "num_predict": 100  # Keep replies short (System 1 should be fast)
            }
        }

        try:
            response = requests.post(self.url, json=payload, timeout=10)
            response.raise_for_status()
            
            reply = response.json().get('response', '').strip()
            
            # Failsafe: If Llama tries to be chatty about the handoff, force the tag.
            if "[HANDOFF_TO_GEMINI]" in reply:
                return "[HANDOFF_TO_GEMINI]"
                
            return reply

        except Exception as e:
            print(f"⚠️ REPTILE FAILURE: {e}")
            # If local brain fails, safe default is to assume it's complex and pass to Gemini
            return "[HANDOFF_TO_GEMINI]"

# --- Quick Test Block ---
if __name__ == "__main__":
    brain = ReptileBrain()
    
    print("\n--- TEST 1: Simple Chat ---")
    print(brain.process_interaction("Hello Ken, what is our main goal?", context_memory="Goal: Win GSoC 2026."))
    
    print("\n--- TEST 2: Coding Request ---")
    print(brain.process_interaction("Write a python script to sort a list."))