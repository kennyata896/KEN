import asyncio
import os
import sys
import pygame 
import google.generativeai as genai
from dotenv import load_dotenv
from modules.voice_engine import KenVoice
# 🧱 IMPORT THE LEGO BRICK
from modules.coder import solve_issue_auto
from config import MODEL_NAME # Import configuration

load_dotenv()

# --- 1. CONFIGURATION ---
# MODEL_NAME is now imported from config.py

# --- 2. KEY MANAGER (Brain's Own Supply) ---
class KeyManager:
    def __init__(self):
        self.keys = []
        main_key = os.getenv("GEMINI_API_KEY")
        if main_key: self.keys.append(main_key)
        for i in range(2, 11):
            k = os.getenv(f"GEMINI_API_KEY_{i}")
            if k: self.keys.append(k)
        
        if not self.keys:
            print("❌ CRITICAL: No GEMINI_API_KEY found.")
            sys.exit()
        self.current_index = 0

    def get_key(self):
        return self.keys[self.current_index]

    def rotate(self):
        if len(self.keys) > 1:
            prev = self.current_index
            self.current_index = (self.current_index + 1) % len(self.keys)
            print(f"🔄 BRAIN: Rotating Key #{prev+1} -> #{self.current_index+1}")
            genai.configure(api_key=self.get_key())
            return True
        return False

key_manager = KeyManager()
genai.configure(api_key=key_manager.get_key())

# --- 3. QUEUES ---
listen_queue = asyncio.Queue()

# --- 4. THREADED LOOPS ---

async def ear_loop(ken, loop):
    """Brain 1: The Ears"""
    print("👂 Ears Online (Threaded)...")
    while True:
        text = await loop.run_in_executor(None, ken.listen)
        if text:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop() 
                print("🛑 INTERRUPTED!")
            await listen_queue.put(text)

async def brain_loop(ken):
    """Brain 2: The Mind"""
    print("🧠 Neocortex Online...")
    history = []
    
    while True:
        user_text = await listen_queue.get()
        if not user_text or len(user_text) < 4: continue
        print(f"🧠 Processing: {user_text}")

        # A. CHECK FOR CODING COMMANDS
        # We rely on keywords to trigger the Coder Module
        if any(w in user_text.lower() for w in ["fix", "code", "edit", "change file", "create"]):
            await ken.speak("Activating Coder Module.")
            
            # 🧱 CALL THE LEGO BRICK (Running in thread to not block ears)
            result = await asyncio.to_thread(solve_issue_auto, user_text)
            
            if result == "SUCCESS":
                await ken.speak("Coding task complete. Changes applied.")
            elif result == "NO_FILES_FOUND":
                await ken.speak("I couldn't find any relevant files to fix.")
            else:
                await ken.speak("I encountered an error while coding.")
            continue

        # B. NORMAL CHAT
        max_retries = len(key_manager.keys)
        response_sent = False
        
        for attempt in range(max_retries):
            try:
                genai.configure(api_key=key_manager.get_key())
                model = genai.GenerativeModel(MODEL_NAME)
                chat = model.start_chat(history=history)
                
                response = chat.send_message(user_text)
                answer = response.text
                
                await ken.speak(answer)
                history.append({"role": "user", "parts": [user_text]})
                history.append({"role": "model", "parts": [answer]})
                response_sent = True
                break 
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    print("⚡ RATE LIMIT. Rotating...")
                    key_manager.rotate()
                    await ken.speak("Rerouting power...")
                else:
                    print(f"❌ Brain Error: {e}")
                    break
        
        if not response_sent:
            await ken.speak("I am having trouble connecting.")

# --- 5. MAIN ---
async def main():
    print("--- 🚀 KEN OS: MODULAR ARCHITECTURE ---")
    ken = KenVoice()
    try: pygame.mixer.init()
    except: pass
    
    await ken.speak("Hey, Ken OS is online and ready.")

    loop = asyncio.get_running_loop()
    await asyncio.gather(ear_loop(ken, loop), brain_loop(ken))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 SHUTDOWN.")
