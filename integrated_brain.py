import sys
import os
import asyncio
import pickle

# --- MAGIC PATH FIX ---
# This ensures Ken can find his 'modules' even if you run him from D:\Projects
# It tells Python: "Look for modules in the folder where THIS script lives."
ken_home = os.path.dirname(os.path.abspath(__file__))
if ken_home not in sys.path:
    sys.path.append(ken_home)
# ----------------------

# --- MODULE IMPORTS ---
try:
    from modules.voice_engine import KenVoice as VoiceEngine
    from modules.reptile import ReptileBrain
    from modules.manager import CortexManager
    from modules.coder import execute_aider_async, analyze_repo_async
    from modules.graph_memory import CodeGraphMemory 

except ImportError as e:
    print(f"❌ CRITICAL IMPORT ERROR: {e}")
    print(f"   (Ken Home detected at: {ken_home})")
    sys.exit(1)

MAX_AUTO_RETRIES = 2

class KenSystem:
    def __init__(self):
        print("\n🔌 KEN: Booting Neural Interfaces...")
        
        # Initialize Organs
        self.voice = VoiceEngine()
        self.reptile = ReptileBrain()
        self.cortex = CortexManager()
        
        # --- MEMORY INITIALIZATION ---
        print("🧠 MEMORY: Initializing Graph Neural Network...")
        
        # GLOBAL MODE: We pass the Current Working Directory (CWD)
        # This tells Ken: "Don't scan yourself. Scan the folder the user is standing in."
        current_project_dir = os.getcwd()
        self.memory = CodeGraphMemory(target_dir=current_project_dir) 
        
        # Fast Boot Cache Check (Project Specific)
        # We look for the cache inside the HIDDEN .ken_memory folder
        cache_path = os.path.join(current_project_dir, ".ken_memory", "brain_map_cache.pkl")
        
        if os.path.exists(cache_path):
            print("   ⚡ FAST BOOT: Cache found. Loading memory map...")
            try:
                with open(cache_path, "rb") as f:
                    self.memory.graph = pickle.load(f)
                print(f"   ✅ Loaded {self.memory.graph.number_of_nodes()} memory nodes instantly.")
            except:
                print(f"   ⚠️ Cache Corrupt. Rebuilding...")
                self.memory.build_graph()
        else:
            print("   🐢 No cache found. Performing full scan...")
            self.memory.build_graph()
            
            # Save the cache immediately for next time
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "wb") as f:
                    pickle.dump(self.memory.graph, f)
            except: pass

        self.recent_chat_history = "" 

    async def start_life_cycle(self):
        print("🤖 KEN: Online and Listening.")
        await self.voice.speak("Ken is online. Project mapped.")

        while True:
            # --- STEP 1: LISTEN ---
            print("👂 Listening...")
            user_input = await asyncio.to_thread(self.voice.listen)
            
            if not user_input: continue
            print(f"👂 USER: {user_input}")

            # --- STEP 2: RECALL ---
            relevant_context = ""
            if any(k in user_input.lower() for k in ["remember", "plan", "how", "where", "code", "fix"]):
                print("🕸️ GRAPH: Querying knowledge base...")
                context_list = self.memory.retrieval_augmented_search(user_input)
                relevant_context = "\n".join(context_list)

            # --- STEP 3: DECIDE ---
            response = self.reptile.process_interaction(
                user_input, 
                context_memory=f"{self.recent_chat_history}\n\n[MEMORIES]:\n{relevant_context}"
            )
            
            # --- STEP 4: ACT ---
            if "[HANDOFF_TO_GEMINI]" in response:
                print("⚠️ REPTILE: Escalating to Cortex.")
                await self.voice.speak("Analyzing repository...")
                await self.run_coding_workflow(user_input)
            else:
                print(f"🦎 REPTILE: {response}")
                await self.voice.speak(response)
                self.recent_chat_history += f"\nUser: {user_input}\nKen: {response}"
                
                if len(self.recent_chat_history) > 2000:
                    self.recent_chat_history = self.recent_chat_history[-1000:]

    async def run_coding_workflow(self, task_description):
        # A. DEEP SEARCH
        print("🕸️ GRAPH: Performing deep structural search...")
        context_list = self.memory.retrieval_augmented_search(task_description)
        
        # B. GEMINI ANALYSIS
        target_files = await analyze_repo_async(task_description)
        if not target_files:
            await self.voice.speak("I could not identify the files. Aborting.")
            return

        # C. FIX LOOP
        await self.voice.speak(f"Targeting {len(target_files)} files.")
        for attempt in range(MAX_AUTO_RETRIES):
            print(f"🔧 WORKER: Attempt {attempt+1}/{MAX_AUTO_RETRIES}")
            await execute_aider_async(target_files, task_description)
            
            # Re-build graph because files changed
            self.memory.build_graph() 
            
            # Update Cache
            try:
                cache_path = os.path.join(self.memory.root_dir, ".ken_memory", "brain_map_cache.pkl")
                with open(cache_path, "wb") as f:
                    pickle.dump(self.memory.graph, f)
            except: pass
            
            await self.voice.speak("Task complete. Codebase updated.")
            return

if __name__ == "__main__":
    try:
        ken = KenSystem()
        asyncio.run(ken.start_life_cycle())
    except KeyboardInterrupt:
        print("\n🔌 KEN: Manual Shutdown.")