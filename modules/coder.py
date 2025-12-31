# modules/coder.py
import subprocess
import os
import sys
from dotenv import load_dotenv

# 1. FORCE LOAD API KEYS
load_dotenv() 

def run_aider(file_path, instruction):
    """
    Spawns Aider to edit a specific file using Gemini 1.5 Pro.
    """
    print(f"🔧 KEN CODER: Spawning Aider on {file_path}...")

    # Check if API key is loaded
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ CRITICAL ERROR: GEMINI_API_KEY not found in environment.")
        print("   -> Did you create the .env file with your key?")
        return False
    
    # 2. CREATE FILE IF MISSING (Aider needs a target)
    if not os.path.exists(file_path):
        print(f"⚠️  File {file_path} not found. Creating it first...")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Created by Ken Coder for task: {instruction}\n")

    # 3. THE COMMAND (Updated for Gemini)
    command = [
        "aider",
        file_path,
        "--model", "gemini/gemini-1.5-pro",  # <--- FORCE GEMINI
        "--message", instruction,
        "--auto-commits",
        "--no-show-model-warnings",          # <--- STOP BROWSER POPUPS
        "--yes"                              # <--- AUTO CONFIRM
    ]
    
    try:
        # Run Aider and capture output
        log_path = "logs/aider_execution.log"
        with open(log_path, "w", encoding='utf-8') as log_file:
            print("   ↳ Aider is thinking... (This may take 30s)")
            
            process = subprocess.run(
                command,
                stdout=log_file,
                stderr=log_file,
                text=True,
                env=os.environ.copy() # Pass the loaded env vars
            )
        
        if process.returncode == 0:
            print(f"✅ SUCCESS: Aider finished editing {file_path}.")
            return True
        else:
            print(f"❌ ERROR: Aider failed. Check {log_path} for details.")
            return False
            
    except FileNotFoundError:
        print("❌ CRITICAL: 'aider' command not found. Run 'pip install aider-chat'.")
        return False

# --- TEST AREA ---
if __name__ == "__main__":
    print("🧪 TEST MODE: Testing Ken Coder Module...")
    
    test_file = "test_math.py"
    task = "Write a python script that calculates the factorial of a number using recursion."
    
    success = run_aider(test_file, task)
    
    if success and os.path.exists(test_file):
        print("\n--- RESULTING CODE ---")
        with open(test_file, 'r') as f:
            print(f.read())
        print("----------------------")