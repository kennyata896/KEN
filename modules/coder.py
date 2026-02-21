import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

# Aider Imports
try:
    from aider.coders import Coder
    from aider.models import Model
    from aider.io import InputOutput
except ImportError:
    print("❌ ERROR: Aider is not installed. Run 'pip install aider-chat'")

# 1. Load Environment Variables
load_dotenv()

# 2. Configure Gemini (The Brain that plans the edits)
if not os.getenv("GEMINI_API_KEY"):
    print("⚠️ WARNING: GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

async def analyze_repo_async(task_description):
    """
    Step 1: The Architect.
    It looks at all your files and decides which ones need to be touched.
    """
    # Get a list of all Python files in the project
    file_list = []
    for root, _, files in os.walk("."):
        # Ignore junk folders
        if any(ignore in root for ignore in ["venv", ".git", "__pycache__", "ken_memory_db"]):
            continue
            
        for f in files:
            if f.endswith(".py") or f.endswith(".md") or f.endswith(".txt"):
                file_list.append(os.path.join(root, f))
    
    file_str = "\n".join(file_list)
    
    # Ask Gemini to pick the targets
    prompt = f"""
    You are a Senior Software Engineer.
    
    PROJECT FILES:
    {file_str}
    
    TASK: "{task_description}"
    
    Identify the specific files that must be modified to complete this task.
    Return ONLY a comma-separated list of filenames. Do not explain.
    Example output: main.py, modules/utils.py
    """
    
    print("🤖 CORTEX: Analyzing file structure...")
    try:
        # Run in a thread to keep the voice engine smooth
        response = await asyncio.to_thread(model.generate_content, prompt)
        
        # Clean up the response
        raw_files = response.text.split(',')
        target_files = []
        
        for f in raw_files:
            clean_name = f.strip().replace("`", "").replace("'", "").replace('"', "")
            if os.path.exists(clean_name):
                target_files.append(clean_name)
        
        return target_files

    except Exception as e:
        print(f"❌ ERROR in Analysis: {e}")
        return []

async def execute_aider_async(target_files, task_description, model="gemini/gemini-2.0-flash"):
    # ... inside your subprocess call ...
    cmd = [
        "python", "-m", "aider",
        "--model", model,  # <-- Make sure it uses the dynamic variable here!
        "--yes",
        "--message", task_description
    ]
    
    # Add the target files to the command
    cmd.extend(target_files)

    process = await asyncio.create_subprocess_exec(*cmd)
    await process.wait()

    # CRITICAL: Trigger the fallback if Aider crashes or times out
    if process.returncode != 0:
        raise Exception(f"Aider failed to execute with model: {model}")

def _run_aider_internal(target_files, task_description):
    """
    The internal blocking function that runs the Aider loop.
    """
    try:
        # 1. Setup Input/Output (Auto-approve everything)
        io = InputOutput(yes=True) 
        
        # 2. Select the Model (Using Gemini Pro for the heavy coding)
        # Note: Ensure you have GEMINI_API_KEY set for Aider as well
        coder_model = Model("gemini/gemini-2.0-flash")
        
        # 3. Create the Coder Instance
        coder = Coder.create(
            main_model=coder_model,
            fnames=target_files,
            io=io,
            auto_commits=False, # We manage git manually if needed
            dirty_commits=False
        )
        
        # 4. Run the Task
        coder.run(task_description)
        
    except Exception as e:
        print(f"❌ AIDER CRASHED: {e}")