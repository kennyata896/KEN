import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = "gemini-3-pro-preview"

# --- KEY MANAGER (Brain Version) ---
class KeyManager:
    def __init__(self):
        self.keys = []
        main_key = os.getenv("GEMINI_API_KEY")
        if main_key: self.keys.append(main_key)
        for i in range(2, 11):
            k = os.getenv(f"GEMINI_API_KEY_{i}")
            if k: self.keys.append(k)
        if not self.keys: return
        self.current_index = 0
    
    def get_key(self): return self.keys[self.current_index] if self.keys else None
    
    def rotate(self):
        if len(self.keys) > 1:
            self.current_index = (self.current_index + 1) % len(self.keys)
            print(f"🔄 MANAGER: Rotating Key -> #{self.current_index+1}")
            genai.configure(api_key=self.get_key())
            return True
        return False

# --- THE CORTEX ---
class CortexManager:
    """
    The Smart Manager.
    NOW PURELY THEORETICAL. It does not touch code.
    It only decides: "CHAT" or "ACTIVATING_CODER".
    """
    def __init__(self):
        self.keys = KeyManager()
        self.history = []
        self.configure_genai()
        print("🧠 Cortex Manager: Online")

    def configure_genai(self):
        if self.keys.get_key():
            genai.configure(api_key=self.keys.get_key())
        self.model = genai.GenerativeModel(MODEL_NAME)

    def think(self, user_text):
        """
        Decides intent. Returns:
        - "ACTIVATING_CODER" (if user wants to code)
        - The Chat Response (if user wants to chat)
        """
        prompt = f"""
        USER INPUT: "{user_text}"
        Classify this request:
        - "CODE": If user wants to fix, edit, create, check, or debug code/files.
        - "CHAT": If user is just talking, asking general questions.
        Reply ONLY with "CODE" or "CHAT".
        """
        
        # 1. Routing Decision
        decision = self._safe_generate(prompt)
        
        if decision and "CODE" in decision.upper():
            return "ACTIVATING_CODER"
        
        # 2. Chat Response
        # We manually manage history to allow key rotation without losing context
        chat_context = self.history + [{"role": "user", "parts": [user_text]}]
        
        response_text = self._safe_chat(chat_context)
        
        if response_text:
            self.history.append({"role": "user", "parts": [user_text]})
            self.history.append({"role": "model", "parts": [response_text]})
            return response_text
        
        return "I am having trouble connecting to the neural network."

    def _safe_generate(self, prompt):
        """Routing check: Fast & Cheap reasoning."""
        for _ in range(len(self.keys.keys) or 1):
            try:
                genai.configure(api_key=self.keys.get_key())
                # Use 'low' thinking for the simple CODE vs CHAT decision
                model = genai.GenerativeModel(MODEL_NAME)
                config = genai.types.GenerationConfig(
                    thinking_config=genai.types.ThinkingConfig(thinking_level="low"),
                    temperature=0.1 # Keep it strict for classification
                )
                response = model.generate_content(prompt, generation_config=config)
                return response.text.strip()
            except Exception:
                self.keys.rotate()
        return None

    def _safe_chat(self, history_payload):
        """Deep Chat: High reasoning for 'Senior Engineer' quality answers."""
        for _ in range(len(self.keys.keys) or 1):
            try:
                genai.configure(api_key=self.keys.get_key())
                model = genai.GenerativeModel(MODEL_NAME)
                # Use 'high' (default) for chat to get Gemini 3's best reasoning
                chat = model.start_chat(history=history_payload[:-1])
                response = chat.send_message(history_payload[-1]["parts"][0])
                return response.text
            except Exception:
                self.keys.rotate()
        return None