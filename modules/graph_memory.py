import os
import ast
import networkx as nx
import chromadb
import shutil
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

class CodeGraphMemory:
    def __init__(self, target_dir=None): 
        # 1. Determine where we are working (Global Mode)
        if target_dir:
            self.root_dir = os.path.abspath(target_dir)
        else:
            self.root_dir = os.getcwd() # The folder you opened the terminal in
            
        self.graph = nx.DiGraph() 
        
        # 2. Store the Memory DB INSIDE the project folder (Hidden)
        # This ensures every project has its own separate brain cells
        db_path = os.path.join(self.root_dir, ".ken_memory")
        
        print(f"📂 MEMORY: Mapping project at -> {self.root_dir}")
        print(f"💾 DATABASE: Storing context in -> {db_path}")

        # --- AUTO-HEALING DATABASE CONNECTION ---
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.vector_store = self.client.get_or_create_collection("code_nodes")
        except BaseException as e: 
            print(f"⚠️ CRITICAL: Memory Panic Detected ({e})")
            print("🏥 PROTOCOL: Wiping corrupted memory...")
            
            if os.path.exists(db_path):
                shutil.rmtree(db_path)
            
            self.client = chromadb.PersistentClient(path=db_path)
            self.vector_store = self.client.get_or_create_collection("code_nodes")
            print("✨ SUCCESS: Memory re-initialized.")
        # ----------------------------------------
        
        self.symbol_table = {} 
        print("🕸️ GRAPH MEMORY: Initialized.")

    def _normalize_path(self, path):
        try:
            rel = os.path.relpath(path, self.root_dir)
        except ValueError: return path
        return rel.replace("\\", "/")

    def build_graph(self):
        print("🕸️ GRAPH: Starting Deep Scan...")
        self.graph.clear()
        self.symbol_table = {}
        python_files = []
        
        # Pass 1: Index
        for root, _, files in os.walk(self.root_dir):
            # Exclude the memory folder itself to prevent infinite loops
            if any(x in root for x in ["venv", ".git", "__pycache__", ".ken_memory"]): continue
            
            for file in files:
                if file.endswith(".py"):
                    full = os.path.join(root, file)
                    rel = self._normalize_path(full)
                    self.graph.add_node(rel)
                    python_files.append((full, rel))
                    self._scan_definitions(full, rel)

        print(f"   -> Indexed {len(self.symbol_table)} symbols.")

        # Pass 2: Link
        print("   -> Resolving dependencies...")
        for full, rel in python_files:
            self._scan_references(full, rel)

        print(f"✅ GRAPH: Built {self.graph.number_of_nodes()} files.")
        self._enrich_nodes_if_needed()

    def _scan_definitions(self, full_path, rel_path):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    self.symbol_table[node.name] = rel_path
        except: pass 

    def _scan_references(self, full_path, rel_path):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
            
            # Imports
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    target = node.module.replace(".", "/") + ".py"
                    self._link_by_path_guess(rel_path, target)

            # Symbols
            for symbol, source in self.symbol_table.items():
                if source != rel_path and symbol in content:
                    self.graph.add_edge(rel_path, source)
        except: pass

    def _link_by_path_guess(self, source, target_ending):
        for node in self.graph.nodes:
            if node.endswith(target_ending):
                self.graph.add_edge(source, node)
                return

    def _enrich_nodes_if_needed(self):
        print("🧠 GRAPH: Verifying AI Summaries...")
        for node in self.graph.nodes:
            existing = self.vector_store.get(ids=[node])
            if existing['ids']: continue 
            
            print(f"   📝 Summarizing: {node}")
            full_path = os.path.join(self.root_dir, node)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                summary = model.generate_content(f"Summarize code in 1 sentence:\n{content[:2000]}").text.strip()
                self.vector_store.add(
                    documents=[summary + "\n\n" + content],
                    metadatas={"path": node, "summary": summary},
                    ids=[node]
                )
            except: pass

    def retrieval_augmented_search(self, query):
        results = self.vector_store.query(query_texts=[query], n_results=1)
        if not results['ids'] or not results['ids'][0]: return []
        center = results['ids'][0][0]
        
        print(f"📍 GRAPH: Entry point found -> {center}")

        neighbors = list(self.graph.successors(center)) + list(self.graph.predecessors(center))
        cluster = set([center] + neighbors)
        print(f"🕸️ GRAPH: Expanded context -> {list(cluster)}")
        
        context_data = []
        for file in cluster:
            data = self.vector_store.get(ids=[file])
            if data['documents']:
                context_data.append(f"\n--- FILE: {file} ---\n" + data['documents'][0])
        return context_data