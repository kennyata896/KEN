import asyncio
import sys
import pygame
from modules.voice_engine import KenVoice

# Import our newly modularized Brain!
from integrated_brain import CognitiveCore 
import os
from dotenv import load_dotenv

# Load the secret vault
load_dotenv()

# --- GLOBAL NERVOUS SYSTEM ---
listen_queue = asyncio.Queue()  
speech_queue = asyncio.Queue()  

# --- LOOP 1: EARS (The Listener) ---
async def ear_loop(ken, loop):
    print("👂 Ears: Online (With Ghost Filter & Interrupts)")
    while True:
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1) 
            continue

        text = await loop.run_in_executor(None, ken.listen)
        
        if text:
            clean_text = text.strip().lower()
            hallucinations = ["thank you.", "thank you", "thanks.", "you.", "bye.", "subtitles by"]
            if clean_text in hallucinations: continue
            if len(clean_text) < 2: continue

            # REFLEX: Stop speaking INSTANTLY if user speaks
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                
            await listen_queue.put(text)

# --- LOOP 2: MOUTH (The Speaker) ---
async def mouth_loop(ken):
    print("👄 Mouth: Online")
    while True:
        text = await speech_queue.get()
        if text:
            while not listen_queue.empty(): 
                listen_queue.get_nowait()
            await ken.speak(text)
        speech_queue.task_done()

# --- LOOP 3: BRAIN (The Executive) ---
async def brain_loop(core):
    print("🧠 Brain: Cognitive Core Linked.")
    while True:
        user_text = await listen_queue.get()
        if not user_text: continue
        
        user_text_lower = user_text.lower()

        # 🚨 EMERGENCY REFLEX LAYER
        stop_words = ["stop task", "abort", "cancel", "terminate", "stop everything"]
        if any(word in user_text_lower for word in stop_words):
            print("🛑 EMERGENCY STOP TRIGGERED")
            await speech_queue.put("Aborting mission.")
            listen_queue.task_done()
            continue

        if "shut up" in user_text_lower or "stop talking" in user_text_lower:
            listen_queue.task_done()
            continue

        print(f"📨 PROCESSING: '{user_text}'")

        # --- ASK THE COGNITIVE CORE ---
        reply = await asyncio.to_thread(core.think, user_text)
        
        if "[HANDOFF_TO_GEMINI]" in reply:
            print("⚠️ REPTILE: Escalating to Cortex.")
            await speech_queue.put("On it. Analyzing repository in the background.")
            
            # LAUNCH BACKGROUND WORKER (Ears stay open!)
            asyncio.create_task(core.run_coding_workflow(user_text, speech_queue))
            
            # Inject action into Working Memory
            core.recent_chat_history += f"\n[SYSTEM MEMORY: The user commanded '{user_text}'. The AI coding worker executed this change.]"
        
        elif reply:
            print(f"🦎 REPTILE: {reply}")
            await speech_queue.put(reply)
            
            # Inject conversation into Working Memory
            core.recent_chat_history += f"\nUser: {user_text}\nKen: {reply}"
            if len(core.recent_chat_history) > 2000:
                core.recent_chat_history = core.recent_chat_history[-1000:]
                
        listen_queue.task_done()

# --- MAIN SYSTEM ---
async def main():
    print("--- 🐙 KEN OS: HIVE MIND ACTIVE ---")
    
    # 1. Initialize Organs & Brain
    ken = KenVoice()
    core = CognitiveCore()
    
    # 2. Start Life Loops
    loop = asyncio.get_running_loop()
    await asyncio.gather(
        ear_loop(ken, loop),
        mouth_loop(ken),
        brain_loop(core)
    )

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🐙 KEN OS: Powered Off.")