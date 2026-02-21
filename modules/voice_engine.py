import speech_recognition as sr
import pyttsx3
import pygame
import asyncio
import os
import io
import torch
import numpy as np
from faster_whisper import WhisperModel

# --- THE ULTIMATE DLL NUKE (V2) ---
# 1. Inject PyTorch core libraries
torch_lib = os.path.join(os.path.dirname(torch.__file__), 'lib')
os.environ['PATH'] = torch_lib + ';' + os.environ.get('PATH', '')

# 2. Find the 'site-packages' folder where torch lives
site_packages = os.path.dirname(os.path.dirname(torch.__file__))
nvidia_base = os.path.join(site_packages, 'nvidia')

# 3. Walk through all NVIDIA folders and inject any DLLs into Windows PATH
if os.path.exists(nvidia_base):
    for root, dirs, files in os.walk(nvidia_base):
        if any(f.endswith('.dll') for f in files):
            os.environ['PATH'] = root + ';' + os.environ['PATH']
# ----------------------------------

class KenVoice:
    def __init__(self):
        print("🔊 Voice Engine: Loading Faster-Whisper (Optimized GPU)...")
        
        # 1. SETUP GPU ENGINE
        # 'float16' is crucial for RTX 4060 speed.
        model_size = "medium.en" # 'medium' is much smarter than 'small'. Since we use faster-whisper, it fits!
        
        try:
            self.model = WhisperModel(model_size, device="cuda", compute_type="float16")
            print(f"   (Model '{model_size}' loaded on GPU)")
        except Exception as e:
            print(f"⚠️ GPU Error: {e}. Falling back to CPU (Slow).")
            self.model = WhisperModel("small.en", device="cpu", compute_type="int8")

        # 2. CONTEXT PRIMING (The "Smart" Hack)
        # We tell the model what words to expect. This fixes 90% of typos.
        self.context_prompt = (
            "Ken, Aider, Python, Code, config.py, main.py, reptile.py, "
            "scheduler, async, await, debug, fix, function, variable."
        )

        # 3. MICROPHONE SETUP
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 150
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 2.0

        # 4. TTS SETUP
        #self.engine = pyttsx3.init()
        #self.engine.setProperty('rate', 175)
        #pygame.mixer.init()

    def listen(self):
        """
        Direct-to-Memory Transcription with Auto-Retry for Bluetooth Locks.
        """
        import time # Added for the retry loop

        # Try to grab the microphone up to 5 times
        for attempt in range(5):
            try:
                with sr.Microphone(device_index=1) as source:
                    print("🎤 [DEBUG] Waiting for sound from WF-C510...") 
                    
                    # Capture Audio
                    audio_data = self.recognizer.listen(source, timeout=None, phrase_time_limit=30)
                    print("🎙️ [DEBUG] Sound captured! Transcribing...") 
                    
                    # Force 16kHz format for Whisper
                    raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
                    audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Transcribe
                    segments, info = self.model.transcribe(
                        audio_np, 
                        beam_size=5, 
                        initial_prompt=self.context_prompt,
                        vad_filter=True 
                    )
                    
                    text = " ".join([segment.text for segment in segments]).strip()
                    print(f"📝 [RAW TRANSCRIPT]: '{text}'") 
                    
                    if not text: return None
                    return text.lower()
                    
            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                # If Windows locks the mic, wait 1 second and try grabbing it again
                print(f"⚠️ [MIC LOCKED] Waiting for Bluetooth mode switch... (Attempt {attempt+1}/5)")
                print(f"   (Error details: {repr(e)})") # This will reveal the invisible error!
                time.sleep(1.0) 
                
        # If it fails 5 times in a row, return None to keep the system alive
        print("❌ [CRITICAL EAR ERROR]: Could not grab microphone after 5 attempts.")
        return None

    async def speak(self, text):
        if not text: return
        clean_text = text.replace("[DEPLOY_CODER]", "").replace("[CHECK_STATUS]", "").replace("*", "")
        if not clean_text.strip(): return

        file_path = "temp_speech.wav"
        
        print(f"🔊 [DEBUG] Generating audio file...")
        await asyncio.to_thread(self._save_audio, clean_text, file_path)
        print(f"🔊 [DEBUG] Audio generated! Playing through speakers...")
        
        try:
            # 1. Turn ON the audio system just to speak
            pygame.mixer.init() 
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            pygame.mixer.music.unload()
            
            # 2. DROP THE LOCK! Shut down the speaker so the mic can work!
            pygame.mixer.quit() 
            print(f"🔊 [DEBUG] Finished speaking. Mic unlocked.")
            
        except Exception as e:
            print(f"❌ Audio Error: {e}")

    def _save_audio(self, text, filename):
        # THE FIX: Create a brand new engine every single time so it never deadlocks
        import pyttsx3
        local_engine = pyttsx3.init()
        local_engine.setProperty('rate', 175)
        local_engine.save_to_file(text, filename)
        local_engine.runAndWait()
        del local_engine # Destroy it immediately after generating the file