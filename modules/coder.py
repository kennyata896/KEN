import os
import asyncio
import requests
import json
from dotenv import load_dotenv

# Aider Imports
try:
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
except ImportError:
    print("❌ ERROR: Aider is not installed. Run 'pip install aider-chat'")

# 1. Load Environment Variables
load_dotenv()

# 2. Configure Local Edge Model
# Define the exact model you have pulled in Ollama (e.g., qwen2.5:7b, llama3.1)
OLLAMA_MODEL = "qwen2.5:7b" 
OLLAMA_URL = "http://localhost:11434/api/generate"

async def analyze_repo_async(task_description):
    """
    Step 1: The Architect (Offline Mode).
    It looks at all your files and decides which ones need to be touched.
    """
    file_list = []
    for root, _, files in os.walk("."):
        if any(ignore in root for ignore in ["venv", ".git", "__pycache__", "ken_memory_db", "node_modules"]):
            continue
            
        for f in files:
            if f.endswith(".py") or f.endswith(".md") or f.endswith(".txt") or f.endswith(".js"):
                file_list.append(os.path.join(root, f))
    
    file_str = "\n".join(file_list)
    
    prompt = f"""
    You are a Senior Software Engineer running on an edge device.
    
    PROJECT FILES:
    {file_str}
    
    TASK: "{task_description}"
    
    Identify the specific files that must be modified to complete this task.
    Return ONLY a comma-separated list of filenames. Do not explain.
    Example output: main.py, modules/utils.py
    """
    
    print(f"🤖 CORTEX: Analyzing file structure locally using {OLLAMA_MODEL}...")
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1 # Keep it strictly deterministic
        }
    }
    
    def fetch_local_analysis():
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=30)
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            print(f"❌ ERROR connecting to local Ollama during analysis: {e}")
            return ""

    try:
        # Run in a thread to keep the voice engine smooth
        response_text = await asyncio.to_thread(fetch_local_analysis)
        
        # Clean up the response
        raw_files = response_text.split(',')
        target_files = []
        
        for f in raw_files:
            clean_name = f.strip().replace("`", "").replace("'", "").replace('"', "")
            if os.path.exists(clean_name):
                target_files.append(clean_name)
        
        if not target_files:
            print("⚠️ CORTEX: Could not confidently identify target files locally.")
            
        return target_files

    except Exception as e:
        print(f"❌ ERROR in Analysis: {e}")
        return []

async def execute_aider_async(target_files, task_description, model=f"ollama/{OLLAMA_MODEL}"):
    """
    Step 2: The Coder.
    Executes Aider locally bypassing cloud APIs. 
    Note: Aider requires the 'ollama/' prefix for local routing.
    """
    if not target_files:
        print("⚠️ CORTEX ABORT: No valid files identified for editing.")
        return
        
    cmd = [
        "python", "-m", "aider",
        "--model", model,  
        "--yes",
        "--message", task_description
    ]
    
    cmd.extend(target_files)

    print(f"🤖 CORTEX: Booting Local Aider Engine -> [{model}]")
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()

    if process.returncode != 0:
        raise Exception(f"Aider failed to execute with local model: {model}")

def _run_aider_internal(target_files, task_description):
    """
    The internal blocking function (Updated for local offline routing).
    """
    try:
        io = InputOutput(yes=True) 
        
        # Select the local model with the strict Ollama routing tag
        coder_model = Model(f"ollama/{OLLAMA_MODEL}")
        
        coder = Coder.create(
            main_model=coder_model,
            fnames=target_files,
            io=io,
            auto_commits=False, 
            dirty_commits=False
        )
        
        coder.run(task_description)
        
    except Exception as e:
        print(f"❌ AIDER CRASHED (Local Execution): {e}")