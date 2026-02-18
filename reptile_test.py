import asyncio
from modules.voice_engine import KenVoice

async def main():
    # 1. Initialize the Component
    print("--- 🦎 STARTING REPTILIAN BRAIN ---")
    ken = KenVoice()
    
    # 2. Test Reflexes
    await ken.speak("Reptile systems online. I am ready to echo.")
    
    # 3. The Reflex Loop
    while True:
        # Listen (Blocking for now)
        user_text = ken.listen()
        
        if user_text:
            # Speak (Non-Blocking / Async)
            await ken.speak(f"You said: {user_text}")
        
        # Small breathing room for the CPU
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 System Offline.")