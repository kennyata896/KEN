import chromadb
import uuid
import os
from datetime import datetime

class LimbicSystem:
    def __init__(self):
        print("🧠 Limbic System: Initializing ChromaDB...")
        # PersistentClient saves data to disk so Ken remembers after restart
        self.client = chromadb.PersistentClient(path="./ken_memory_db")
        
        # 'chat_history': Stores conversation turns (You + Ken)
        self.chat_memory = self.client.get_or_create_collection(name="chat_history")
        
        # 'documentation': Stores facts/docs (for later use)
        self.knowledge_base = self.client.get_or_create_collection(name="documentation")

    def remember(self, role, text):
        """
        Stores a single message in the database.
        role: 'user' or 'assistant'
        text: The actual message
        """
        self.chat_memory.add(
            documents=[text],
            metadatas=[{"role": role, "timestamp": str(datetime.now())}],
            ids=[str(uuid.uuid4())]  # Unique ID for every memory
        )

    def recall(self, query, n_results=2):
        """
        Searches past conversations for the most relevant messages.
        """
        try:
            results = self.chat_memory.query(
                query_texts=[query],
                n_results=n_results
            )
            # If we found something, return the text list
            if results["documents"]:
                return results["documents"][0]
            return []
        except Exception as e:
            print(f"⚠️ Memory Recall Error: {e}")
            return []
        
    def ingest_codebase(self, root_path="."):
        """
        Scans the project folder and memorizes every code file.
        This gives Ken 'Context' about your actual code.
        """
        print(f"📖 LIMBIC: Scanning codebase at '{root_path}'...")
        
        # Files to ignore (save space and tokens)
        ignore_dirs = {'.git', 'venv', '__pycache__', 'node_modules', 'ken_memory_db'}
        allowed_ext = {'.py', '.js', '.ts', '.html', '.css', '.md'}
        
        count = 0
        for root, dirs, files in os.walk(root_path):
            # Remove ignored directories from the walk
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in allowed_ext:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            
                        # Store the file content in Vector DB
                        self.knowledge_base.add(
                            documents=[content],
                            metadatas=[{"source": file_path, "type": "code"}],
                            ids=[file_path] # Use path as ID to prevent duplicates
                        )
                        count += 1
                        print(f"   Saved: {file}")
                    except Exception as e:
                        print(f"   ❌ Skipped {file}: {e}")
                        
        print(f"✅ LIMBIC: Memorized {count} files. I now know this project.")

    def recall_code(self, query, n_results=3):
        """
        Finds the specific code files relevant to your question.
        """
        results = self.knowledge_base.query(
            query_texts=[query],
            n_results=n_results
        )
        # Returns a list of the actual code found in the files
        return results["documents"][0] if results["documents"] else []