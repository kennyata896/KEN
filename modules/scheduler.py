import asyncio
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class JobScheduler:
    def __init__(self, speech_queue):
        self.queue = asyncio.Queue()
        self.speech_queue = speech_queue
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # --- STATE TRACKING ---
        self.current_status = "Idle. Waiting for commands."
        self.current_process = None # Holds the active "Aider" process so we can kill it
        
        if self.api_key:
            genai.configure(api_key=self.api_key)

    async def add_task(self, task_type, payload):
        """Adds a task to the queue."""
        await self.queue.put((task_type, payload))

    def get_status(self):
        """Returns the live status for the [CHECK_STATUS] command."""
        return self.current_status

    async def run(self):
        print("👷 Scheduler: Online (Multi-Agent + Process Control)")
        while True:
            # 1. Wait for a job
            task_type, payload = await self.queue.get()
            
            # 2. Route to the correct specialist
            if task_type == "CODER":
                await self.run_coder(payload)
            elif task_type == "RESEARCHER":
                await self.run_researcher(payload)
            
            # Reset
            self.current_process = None
            self.current_status = "Idle. Last task finished."
            self.queue.task_done()

    async def run_researcher(self, query):
        self.current_status = f"Researching: '{query}'"
        # Researcher is fast/API based, so we just await it (harder to kill mid-stream without complexity)
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await asyncio.to_thread(model.generate_content, query)
            result = response.text
            
            # Summary
            summary = result[:200] + "..." if len(result) > 200 else result
            await self.speech_queue.put(f"Research complete. {summary}")
            
        except Exception as e:
            print(f"Research Error: {e}")
            await self.speech_queue.put("I could not complete the research.")

    async def run_coder(self, task):
        self.current_status = f"Coding: '{task}' (Initializing...)"
        
        tool_env = os.environ.copy()
        tool_env["GEMINI_API_KEY"] = self.api_key
        
        # Force Gemini Pro for better coding architecture
        cmd = ["aider", "--model", "gemini/gemini-1.5-pro", "--yes", "--message", task]

        try:
            self.current_status = f"Coding: '{task}' (Writing code...)"
            
            # Start the process and SAVE the reference
            self.current_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=tool_env
            )
            
            # Wait for it to finish
            stdout, stderr = await self.current_process.communicate()
            
            if self.current_process.returncode == 0:
                self.current_status = "Coding complete. Verifying..."
                await self.speech_queue.put("Changes applied successfully.")
            else:
                # Check if it was killed intentionally
                if self.current_process.returncode == -9 or self.current_process.returncode == 1:
                    pass # It was aborted, don't complain
                else:
                    await self.speech_queue.put("The coder reported an error.")
                
        except asyncio.CancelledError:
            print("Task cancelled via Async.")
        except Exception as e:
            print(f"Coder Error: {e}")
            await self.speech_queue.put("Could not start coder.")

    async def stop_current_task(self):
        """The Emergency Brake."""
        self.current_status = "Aborting..."
        
        # 1. Kill the active subprocess (Aider) if it exists
        if self.current_process:
            try:
                print("🛑 Killing active process...")
                self.current_process.terminate() # Try soft kill
                # await asyncio.sleep(1)
                # if self.current_process.returncode is None:
                #    self.current_process.kill() # Hard kill
                print("🛑 Process terminated.")
            except Exception as e:
                print(f"Error killing process: {e}")
        
        await self.speech_queue.put("Task aborted.")
        self.current_status = "Idle (Aborted)."