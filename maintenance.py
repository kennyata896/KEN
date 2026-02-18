import os
import time
import pickle
import hashlib
import google.generativeai as genai
from dotenv import load_dotenv
from modules.graph_memory import CodeGraphMemory

load_dotenv()

# --- FIX: INITIALIZE GEMINI ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
# ------------------------------

def get_file_hash(filepath):
    """Generates a fingerprint of the file to check if it changed."""
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except: return None

class NightShift:
    def __init__(self):
        self.memory = CodeGraphMemory()
        # Force a fresh scan
        self.memory.build_graph()
        self.vector_store = self.memory.vector_store

    def run(self):
        print("🌙 NIGHT SHIFT: Starting system optimization...")
        
        self.ghost_busting()
        self.refine_memory_cells() # The function that needs 'model'
        self.cache_graph()
        
        print("\n🌞 NIGHT SHIFT COMPLETE. System optimized.")

    def ghost_busting(self):
        print("\n--- PHASE 1: GHOST BUSTING ---")
        all_data = self.vector_store.get()
        if not all_data['ids']: return

        deleted_count = 0
        for file_id in all_data['ids']:
            full_path = os.path.abspath(file_id)
            if not os.path.exists(full_path):
                print(f"   👻 Removing Ghost: {file_id}")
                self.vector_store.delete(ids=[file_id])
                deleted_count += 1
        print(f"   ✅ Removed {deleted_count} ghosts.")

    def refine_memory_cells(self):
        print("\n--- PHASE 2: CELL REFINEMENT ---")
        all_data = self.vector_store.get()
        if not all_data['ids']: return
        
        for i, doc in enumerate(all_data['documents']):
            if not doc: continue
            file_id = all_data['ids'][i]
            
            # Check summary length (first line)
            summary = doc.split("\n\n")[0]
            
            if len(summary) < 50 or "helper" in summary.lower():
                print(f"   🔧 Refining vague memory: {file_id}")
                full_path = os.path.abspath(file_id)
                
                if os.path.exists(full_path):
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # USES THE MODEL WE DEFINED ABOVE
                        new_summary = model.generate_content(
                            f"State the technical role and module (Auth, DB, etc) of this code:\n{content[:2000]}"
                        ).text.strip()
                        
                        self.vector_store.update(
                            ids=[file_id],
                            documents=[new_summary + "\n\n" + content],
                            metadatas={"path": file_id, "summary": new_summary}
                        )
                    except Exception as e:
                        print(f"   ⚠️ Skipped {file_id}: {e}")

    def cache_graph(self):
        print("\n--- PHASE 3: CACHING MAP ---")
        with open("brain_map_cache.pkl", "wb") as f:
            pickle.dump(self.memory.graph, f)
        print("   🧊 Map frozen.")

if __name__ == "__main__":
    shift = NightShift()
    shift.run()