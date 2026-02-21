import datetime
import math
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- ACTUAL FUNCTIONS ---
def get_time():
    """Returns current date and time."""
    return datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

def calculate(expression):
    """Evaluates math safely."""
    try:
        allowed = {"sqrt": math.sqrt, "pi": math.pi, "sin": math.sin, "cos": math.cos}
        code = compile(expression, "<string>", "eval")
        for name in code.co_names:
            if name not in allowed: return "Error: Unsafe."
        return str(eval(code, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"Error: {e}"

def ask_gemini_pro(query):
    """Consults Cloud AI for complex knowledge (NOT for editing files)."""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(query)
        return response.text
    except Exception as e:
        return f"Cloud Error: {e}"

# --- TOOL SCHEMA ---
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get current time/date.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate math expressions (e.g. '25 * 4').",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_gemini_pro",
            "description": "Ask the Cloud AI for KNOWLEDGE or WRITING. Do NOT use this for fixing/editing files.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_coder",
            "description": "ACTIVATES THE CODING AGENT. Use this ONLY when the user asks to 'fix', 'create', 'edit', 'debug', or 'run' a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {"type": "string", "description": "The coding task instruction."}
                },
                "required": ["task_description"],
            },
        },
    },
]