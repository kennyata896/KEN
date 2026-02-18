import asyncio
import sys
import pygame
from modules.voice_engine import KenVoice
from modules.reptile import ReptileBrain
from modules.scheduler import JobScheduler

# --- GLOBAL NERVOUS SYSTEM ---
# These queues connect the specialized organs (Ears, Brain, Mouth, Hands)
listen_queue = asyncio.Queue()  # Ears -> Brain
speech_queue = asyncio.Queue()  # Brain -> Mouth

# --- LOOP 1: EARS (The Listener) ---
async def ear_loop(ken, loop):
    print("👂 Ears: Online (With Ghost Filter & Interrupts)")
    while True:
        # If the Mouth is moving, we pause listening slightly to avoid echo
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1) 
            continue

        # Run the listening operation (blocking) in a separate thread
        text = await loop.run_in_executor(None, ken.listen)
        
        if text:
            clean_text = text.strip().lower()

            # --- 🛡️ GHOST FILTER ---
            # Whisper often hallucinates these phrases during silence.
            hallucinations = ["thank you.", "thank you", "thanks.", "you.", "bye.", "subtitles by"]
            if clean_text in hallucinations:
                print(f"   (Ignoring Ghost Input: '{text}')")
                continue
            
            if len(clean_text) < 2: continue # Ignore noise
            # -----------------------

            # ⚡ REFLEX: Stop speaking INSTANTLY if user speaks
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                
            await listen_queue.put(text)

# --- LOOP 2: MOUTH (The Speaker) ---
async def mouth_loop(ken):
    print("👄 Mouth: Online")
    while True:
        text = await speech_queue.get()
        if text:
            # Clear ears before speaking (Echo Cancellation)
            while not listen_queue.empty(): 
                listen_queue.get_nowait()
            await ken.speak(text)
        speech_queue.task_done()

# --- LOOP 3: BRAIN (The Executive) ---
async def brain_loop(reptile, scheduler):
    print("🧠 Brain: Online (Llama 3.1 8B)")
    while True:
        user_text = await listen_queue.get()
        if not user_text: continue
        
        user_text_lower = user_text.lower()

        # --- 🚨 1. EMERGENCY REFLEX LAYER (Hard-Coded) ---
        # Checks for "Stop" BEFORE asking the AI. This fixes the safety issue.
        stop_words = ["stop task", "abort", "cancel", "terminate", "stop everything"]
        
        # If user wants to kill the Task
        if any(word in user_text_lower for word in stop_words):
            print("🛑 EMERGENCY STOP TRIGGERED")
            await speech_queue.put("Aborting mission.")
            await scheduler.stop_current_task()
            listen_queue.task_done()
            continue

        # If user just wants silence ("Shut up", "Stop talking")
        if "shut up" in user_text_lower or "stop talking" in user_text_lower:
            # We already stopped audio in ear_loop, so just ignore processing
            listen_queue.task_done()
            continue

        print(f"📨 PROCESSING: '{user_text}'")

        # --- 2. COGNITIVE LAYER (Llama Manager) ---
        handled, reply = await asyncio.to_thread(reptile.process, user_text)
        
        if handled:
            # CASE A: System Shutdown
            if reply == "SYSTEM_EXIT":
                await speech_queue.put("Shutting down systems.")
                await asyncio.sleep(2)
                sys.exit(0)

            # CASE B: Deploy Coder
            elif reply and reply.startswith("ACTIVATING_CODER::"):
                task = reply.split("::")[1]
                # Verbal Confirmation FIRST (So you know he heard you)
                await speech_queue.put(f"On it. Deploying Coding Agent.") 
                await scheduler.add_task("CODER", task)
            
            # CASE C: Deploy Researcher
            elif reply and reply.startswith("ACTIVATING_RESEARCHER::"):
                task = reply.split("::")[1]
                # Verbal Confirmation FIRST
                await speech_queue.put(f"Checking that now.") 
                await scheduler.add_task("RESEARCHER", task)

            # CASE D: Status Check
            elif reply == "CHECKING_STATUS":
                # Ask the Scheduler directly
                current_state = scheduler.get_status()
                await speech_queue.put(f"Status Report: {current_state}")
            
            # CASE E: Abort Signal (From Llama)
            elif reply == "ABORT_MISSION":
                 await scheduler.stop_current_task()
                 await speech_queue.put("Task cancelled.")

            # CASE F: Standard Conversation
            elif reply:
                await speech_queue.put(reply)
        
        listen_queue.task_done()

# --- MAIN SYSTEM ---
async def main():
    print("--- 🐙 KEN OS: HIVE MIND ACTIVE ---")
    
    # 1. Initialize Organs
    ken = KenVoice()
    reptile = ReptileBrain()
    scheduler = JobScheduler(speech_queue)
    
    # 2. Start the Background Worker (The Hive)
    worker_task = asyncio.create_task(scheduler.run())

    # 3. Start Life Loops
    loop = asyncio.get_running_loop()
    await asyncio.gather(
        ear_loop(ken, loop),
        mouth_loop(ken),
        brain_loop(reptile, scheduler),
        worker_task
    )

if __name__ == "__main__":
    try:
        # Windows Asyncio Fix
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🐙 KEN OS: Powered Off.")