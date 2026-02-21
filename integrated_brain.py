import os
import asyncio
import pickle
import sys
from dotenv import load_dotenv

# Load the secret vault (API Keys)
load_dotenv()

ken_home = os.path.dirname(os.path.abspath(__file__))
if ken_home not in sys.path:
    sys.path.append(ken_home)

from modules.reptile import ReptileBrain
from modules.manager import CortexManager
from modules.coder import execute_aider_async, analyze_repo_async
from modules.graph_memory import CodeGraphMemory 

MAX_AUTO_RETRIES = 2

class CognitiveCore:
    def __init__(self):
        print("🧠 MEMORY: Initializing Graph Neural Network...")
        
        self.reptile = ReptileBrain()
        self.cortex = CortexManager()
        
        current_project_dir = os.getcwd()
        self.memory = CodeGraphMemory(target_dir=current_project_dir) 
        cache_path = os.path.join(current_project_dir, ".ken_memory", "brain_map_cache.pkl")
        
        # Load Cache
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
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "wb") as f:
                    pickle.dump(self.memory.graph, f)
            except: pass

        self.recent_chat_history = "" 

    def think(self, user_input):
        """Processes text, searches memory, and returns Ken's response."""
        print("🕸️ GRAPH: Querying knowledge base...")
        context_list = self.memory.retrieval_augmented_search(user_input)
        relevant_context = "\n".join(context_list)

        response = self.reptile.process_interaction(
            user_input, 
            context_memory=f"{self.recent_chat_history}\n\n[MEMORIES]:\n{relevant_context}"
        )
        return response

    async def run_coding_workflow(self, task_description, speech_queue):
        """Runs Aider in the background with Waterfall Fallback."""
        print("🕸️ GRAPH: Performing deep structural search...")
        
        target_files = await analyze_repo_async(task_description)
        if not target_files:
            await speech_queue.put("I could not identify the files. Aborting.")
            return

        await speech_queue.put(f"Targeting {len(target_files)} files.")

        # --- THE SUPER PROMPT ENRICHMENT ---
        enriched_prompt = f"""
        You are an expert AI software engineer. The user has given you a verbal command to edit the codebase.
        
        --- RECENT CONVERSATION CONTEXT ---
        {self.recent_chat_history}
        
        --- YOUR EXACT TASK ---
        The user's direct command is: "{task_description}"
        
        Execute this task precisely. Do not add unnecessary features.
        """

        # --- THE WATERFALL FALLBACK ---
        fallback_chain = [
            "openrouter/deepseek/deepseek-r1:free",
            "gemini/gemini-2.0-flash"
        ]

        success = False

        for model in fallback_chain:
            try:
                print(f"🔧 WORKER: Attempting to code using -> {model}")
                await execute_aider_async(target_files, enriched_prompt, model=model)
                success = True
                break 
                
            except Exception as e:
                print(f"⚠️ WORKER ERROR: Model {model} failed or timed out. Error: {e}")
                print("🔄 FALLBACK: Switching to next available AI model...")
        
        if not success:
            await speech_queue.put("All coding models timed out. Please check your API keys.")
            return

        # Update the Graph Memory because files were successfully changed
        self.memory.build_graph() 
        try:
            cache_path = os.path.join(self.memory.root_dir, ".ken_memory", "brain_map_cache.pkl")
            with open(cache_path, "wb") as f:
                pickle.dump(self.memory.graph, f)
        except: pass
        
        await speech_queue.put("Task complete. Codebase updated.")