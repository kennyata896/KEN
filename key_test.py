import os
from dotenv import load_dotenv
import google.generativeai as genai

# 1. Load your .env file
dotenv_path = r"C:\Users\Harsh Gupta\Ken_Project\.env"
load_dotenv(dotenv_path)

def audit_keys():
    # Identify all keys in the .env that start with GEMINI_API_KEY
    keys_to_check = {k: v for k, v in os.environ.items() if "GEMINI_API_KEY" in k}
    
    print(f"🔍 Found {len(keys_to_check)} keys to audit.\n")

    for key_name, key_value in keys_to_check.items():
        print(f"--- 🔑 Auditing: {key_name} ---")
        try:
            # Configure the SDK with this specific key
            genai.configure(api_key=key_value)
            
            # Fetch the list of models supported by this key
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name.replace('models/', ''))
            
            if available_models:
                print(f"✅ Access Verified. {len(available_models)} models found.")
                # Show the most important ones for your project
                core_models = [m for m in available_models if "flash" in m or "pro" in m]
                print(f"📋 Core Models: {', '.join(core_models)}")
            else:
                print("⚠️ Key connected, but no 'GenerateContent' models found.")
                
        except Exception as e:
            print(f"❌ Error with {key_name}: {str(e)[:100]}...")
        
        print("\n")

if __name__ == "__main__":
    audit_keys()